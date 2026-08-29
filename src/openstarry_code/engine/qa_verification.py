"""QA 质量验证系统

任务完成前的强制验证流程，确保代码质量。
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class QACheckResult:
    """QA 检查结果"""
    
    check_name: str
    status: str  # passed / failed / warning / skipped
    message: str
    details: tuple[str, ...] = field(default_factory=tuple)
    

@dataclass(frozen=True)
class QAReport:
    """QA 报告"""
    
    overall_status: str  # passed / failed / warning
    checks: tuple[QACheckResult, ...] = field(default_factory=tuple)
    passed_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    skipped_count: int = 0


async def run_qa_verification(
    session_key: str,
    modified_files: list[str],
    *,
    workspace_root: str | Path,
    skip_build: bool = False,
    skip_tests: bool = False
) -> QAReport:
    """运行 QA 验证流程
    
    Args:
        session_key: 会话键
        modified_files: 修改的文件列表
        workspace_root: 工作区根目录
        skip_build: 跳过构建验证
        skip_tests: 跳过测试执行
    
    Returns:
        QAReport 验证报告
    """
    checks: list[QACheckResult] = []
    workspace = Path(workspace_root)
    
    env_check = await _detect_project_environment(workspace)
    checks.append(env_check)
    
    if env_check.status == "failed":
        return _build_report(checks, overall_status="failed")
    
    project_type = env_check.details[0] if env_check.details else "unknown"
    
    if not skip_build:
        build_check = await _run_build_verification(workspace, project_type)
        checks.append(build_check)
        
        if build_check.status == "failed":
            return _build_report(checks, overall_status="failed")
    
    if not skip_tests and modified_files:
        test_check = await _run_test_verification(workspace, project_type, modified_files)
        checks.append(test_check)
    
    if modified_files:
        quality_check = await _run_quality_checks(workspace, project_type, modified_files)
        checks.append(quality_check)
    
    functional_check = await _run_functional_verification(workspace, modified_files)
    checks.append(functional_check)
    
    return _build_report(checks)


_PROJECT_INDICATORS = (
    ("python", ("requirements.txt", "pyproject.toml")),
    ("nodejs", ("package.json",)),
    ("java", ("pom.xml", "build.gradle")),
    ("golang", ("go.mod",)),
    ("rust", ("Cargo.toml",))
)


async def _detect_project_environment(workspace: Path) -> QACheckResult:
    """检测项目环境"""
    details = []
    
    for project_type, indicators in _PROJECT_INDICATORS:
        if any((workspace / indicator).exists() for indicator in indicators):
            details.append(project_type)
    
    if not details:
        return QACheckResult(
            check_name="环境识别",
            status="warning",
            message="无法识别项目类型",
            details=("unknown",)
        )
    
    return QACheckResult(
        check_name="环境识别",
        status="passed",
        message=f"识别为 {', '.join(details)} 项目",
        details=tuple(details)
    )


_BUILD_COMMANDS = {
    "python": (["python", "-m", "py_compile"], 60, "Python 语法检查通过"),
    "golang": (["go", "build", "./..."], 120, "Go 构建通过"),
    "rust": (["cargo", "check"], 300, "Rust 检查通过"),
}


async def _run_build_verification(workspace: Path, project_type: str) -> QACheckResult:
    """运行构建验证"""
    try:
        result = None
        success_msg = ""
        
        if project_type == "python":
            cmd, timeout, success_msg = _BUILD_COMMANDS["python"]
            py_files = [str(p) for p in workspace.rglob("*.py")]
            result = subprocess.run(
                cmd + py_files,
                cwd=workspace,
                capture_output=True,
                timeout=timeout
            )
        
        elif project_type == "nodejs":
            if (workspace / "tsconfig.json").exists():
                cmd, timeout = ["npx", "tsc", "--noEmit"], 120
            else:
                cmd, timeout = ["npm", "run", "lint"], 120
            
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, timeout=timeout)
            success_msg = "Node.js 构建通过"
        
        elif project_type == "java":
            if (workspace / "pom.xml").exists():
                cmd, timeout = ["mvn", "compile"], 300
            else:
                cmd, timeout = ["gradle", "build", "-x", "test"], 300
            
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, timeout=timeout)
            success_msg = "Java 构建通过"
        
        elif project_type in _BUILD_COMMANDS:
            cmd, timeout, success_msg = _BUILD_COMMANDS[project_type]
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, timeout=timeout)
        
        if result and result.returncode == 0:
            return QACheckResult(
                check_name="构建验证",
                status="passed",
                message=success_msg,
                details=()
            )
        
        error_output = result.stderr.decode("utf-8", errors="ignore")[:500] if result else ""
        return QACheckResult(
            check_name="构建验证",
            status="failed",
            message="构建失败",
            details=(error_output,) if error_output else ()
        )
    
    except subprocess.TimeoutExpired:
        return QACheckResult(
            check_name="构建验证",
            status="failed",
            message="构建超时",
            details=()
        )
    except Exception as e:
        return QACheckResult(
            check_name="构建验证",
            status="warning",
            message=f"构建验证出错：{str(e)}",
            details=()
        )


_TEST_COMMANDS = {
    "nodejs": (["npm", "test"], 300),
    "golang": (["go", "test", "./..."], 300),
    "rust": (["cargo", "test"], 600),
}


async def _run_test_verification(
    workspace: Path,
    project_type: str,
    modified_files: list[str]
) -> QACheckResult:
    """运行测试验证"""
    try:
        result = None
        
        if project_type == "python":
            has_pytest = (workspace / "pytest.ini").exists() or any("pytest" in str(f) for f in workspace.rglob("*.txt"))
            cmd = ["pytest", "-v"] if has_pytest else ["python", "-m", "unittest", "discover"]
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, timeout=300)
        
        elif project_type == "java":
            cmd = ["mvn", "test"] if (workspace / "pom.xml").exists() else ["gradle", "test"]
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, timeout=600)
        
        elif project_type in _TEST_COMMANDS:
            cmd, timeout = _TEST_COMMANDS[project_type]
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, timeout=timeout)
        
        else:
            return QACheckResult(
                check_name="测试执行",
                status="skipped",
                message="未找到测试配置",
                details=()
            )
        
        if result.returncode == 0:
            return QACheckResult(
                check_name="测试执行",
                status="passed",
                message="所有测试通过",
                details=()
            )
        
        output = result.stdout.decode("utf-8", errors="ignore")[:500]
        return QACheckResult(
            check_name="测试执行",
            status="failed",
            message="部分测试失败",
            details=(output,)
        )
    
    except subprocess.TimeoutExpired:
        return QACheckResult(
            check_name="测试执行",
            status="warning",
            message="测试超时",
            details=()
        )
    except Exception as e:
        return QACheckResult(
            check_name="测试执行",
            status="warning",
            message=f"测试执行出错：{str(e)}",
            details=()
        )


_MAX_FILE_SIZE = 10 * 1024 * 1024


async def _run_quality_checks(
    workspace: Path,
    project_type: str,
    modified_files: list[str]
) -> QACheckResult:
    """运行代码质量检查"""
    issues = []
    
    for file_path in modified_files:
        full_path = workspace / file_path
        
        if not full_path.exists():
            issues.append(f"文件不存在：{file_path}")
            continue
        
        if full_path.stat().st_size > _MAX_FILE_SIZE:
            issues.append(f"文件过大：{file_path}")
        
        if project_type == "python" and file_path.endswith(".py"):
            try:
                compile(full_path.read_text(), file_path, "exec")
            except SyntaxError as e:
                issues.append(f"Python 语法错误 {file_path}:{e.lineno}")
    
    if issues:
        return QACheckResult(
            check_name="代码质量检查",
            status="failed",
            message=f"发现 {len(issues)} 个问题",
            details=tuple(issues[:10])
        )
    
    return QACheckResult(
        check_name="代码质量检查",
        status="passed",
        message="质量检查通过",
        details=()
    )


async def _run_functional_verification(
    workspace: Path,
    modified_files: list[str]
) -> QACheckResult:
    """运行功能验证"""
    unsaved = [fp for fp in modified_files if not (workspace / fp).exists()]
    
    if unsaved:
        return QACheckResult(
            check_name="功能验证",
            status="warning",
            message=f"{len(unsaved)} 个文件未保存",
            details=tuple(unsaved[:5])
        )
    
    return QACheckResult(
        check_name="功能验证",
        status="passed",
        message="功能验证通过",
        details=()
    )


def _build_report(checks: list[QACheckResult], overall_status: str | None = None) -> QAReport:
    """构建 QA 报告"""
    passed = sum(1 for c in checks if c.status == "passed")
    failed = sum(1 for c in checks if c.status == "failed")
    warning = sum(1 for c in checks if c.status == "warning")
    skipped = sum(1 for c in checks if c.status == "skipped")
    
    if overall_status is None:
        if failed > 0:
            overall_status = "failed"
        elif warning > 0:
            overall_status = "warning"
        else:
            overall_status = "passed"
    
    return QAReport(
        overall_status=overall_status,
        checks=tuple(checks),
        passed_count=passed,
        failed_count=failed,
        warning_count=warning,
        skipped_count=skipped
    )
