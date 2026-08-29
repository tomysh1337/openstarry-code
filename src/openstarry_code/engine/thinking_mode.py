"""Thinking Mode: 复杂任务前的需求澄清系统

在用户发起复杂项目时自动触发，通过交互式问答明确需求细节。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ComplexityAnalysis:
    """复杂度分析结果"""
    
    score: float
    should_trigger: bool
    reasons: list[str] = field(default_factory=list)
    detected_features: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Question:
    """澄清问题"""
    
    id: str
    question: str
    purpose: str
    category: str
    options: tuple[str, ...] | None = None


@dataclass
class ThinkingModeResult:
    """Thinking Mode 执行结果"""
    
    triggered: bool
    questions: list[Question] = field(default_factory=list)
    preparation_checklist: list[str] = field(default_factory=list)
    user_answers: dict[str, str] | None = None
    skipped: bool = False


class ComplexityDetector:
    """任务复杂度检测器"""
    
    ACTION_VERBS = frozenset({
        "create", "build", "implement", "develop", "design", "write",
        "add", "integrate", "setup", "configure", "deploy", "migrate",
        "refactor", "optimize", "test", "fix", "debug", "analyze",
        "创建", "构建", "实现", "开发", "设计", "编写",
        "添加", "集成", "配置", "部署", "迁移",
        "重构", "优化", "测试", "修复", "调试", "分析"
    })
    
    TECH_KEYWORDS = frozenset({
        "react", "vue", "angular", "node", "python", "java", "go", "rust",
        "docker", "kubernetes", "aws", "azure", "gcp",
        "mongodb", "postgresql", "redis", "elasticsearch",
        "api", "rest", "graphql", "websocket", "grpc",
        "frontend", "backend", "fullstack", "database", "microservice"
    })
    
    AMBIGUOUS_WORDS = frozenset({
        "system", "platform", "solution", "architecture", "framework",
        "application", "service", "module", "component",
        "系统", "平台", "解决方案", "架构", "框架",
        "应用", "服务", "模块", "组件"
    })
    
    COMPLEX_PROJECT_INDICATORS = frozenset({
        "multi-tenant", "scalable", "distributed", "real-time",
        "high-availability", "load-balancing", "auto-scaling",
        "分布式", "高可用", "负载均衡", "自动扩缩容", "实时"
    })
    
    __slots__ = ("threshold",)
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def analyze(self, message: str) -> ComplexityAnalysis:
        """分析消息复杂度"""
        if not message.strip():
            return ComplexityAnalysis(score=0.0, should_trigger=False)
        
        message_lower = message.lower()
        score = 0.0
        reasons = []
        features = {}
        
        # 1. 检测动作动词（多任务特征）
        action_verbs = [v for v in self.ACTION_VERBS if v in message_lower]
        verb_count = len(action_verbs)
        if verb_count >= 3:
            verb_score = min(verb_count * 0.15, 0.45)
            score += verb_score
            reasons.append(f"检测到 {verb_count} 个动作动词，表示多个子任务")
            features["action_verbs"] = action_verbs[:5]  # 只保留前5个
        
        # 2. 检测技术栈关键词
        tech_keywords = [k for k in self.TECH_KEYWORDS if k in message_lower]
        tech_count = len(tech_keywords)
        if tech_count >= 2:
            tech_score = min(tech_count * 0.10, 0.30)
            score += tech_score
            reasons.append(f"涉及多个技术栈：{', '.join(tech_keywords[:3])}")
            features["tech_stack"] = tech_keywords[:5]
        
        # 3. 检测模糊词汇
        ambiguous = [w for w in self.AMBIGUOUS_WORDS if w in message_lower]
        amb_count = len(ambiguous)
        if amb_count > 0:
            amb_score = min(amb_count * 0.08, 0.20)
            score += amb_score
            reasons.append(f"包含模糊描述需要澄清：{', '.join(ambiguous[:2])}")
            features["ambiguous_terms"] = ambiguous[:3]
        
        # 4. 检测复杂项目指标
        complex_indicators = [i for i in self.COMPLEX_PROJECT_INDICATORS if i in message_lower]
        if complex_indicators:
            score += 0.25
            reasons.append(f"检测到复杂项目特征：{', '.join(complex_indicators)}")
            features["complex_indicators"] = complex_indicators[:3]
        
        # 5. 消息长度
        msg_len = len(message)
        if msg_len > 200:
            length_score = min((msg_len - 200) / 1000, 0.15)
            score += length_score
            features["message_length"] = msg_len
        
        # 6. 多文件操作预测（编译一次正则）
        file_patterns = re.findall(r'\b\w+\.(?:py|js|ts|jsx|tsx|java|go|rs|cpp)\b', message)
        file_count = len(file_patterns)
        if file_count >= 3:
            score += 0.20
            reasons.append("涉及多个文件操作")
            features["file_count"] = file_count
        
        return ComplexityAnalysis(
            score=min(score, 1.0),
            should_trigger=score >= self.threshold,
            reasons=reasons,
            detected_features=features
        )


class QuestionGenerator:
    """澄清问题生成器"""
    
    __slots__ = ()
    
    def generate_questions(self, analysis: ComplexityAnalysis, message: str) -> list[Question]:
        """根据分析结果生成澄清问题"""
        questions = []
        features = analysis.detected_features
        
        # 1. 如果有多个动作动词，询问优先级
        if features.get("action_verbs") and len(features["action_verbs"]) >= 3:
            questions.append(Question(
                id="priority",
                question="这个任务涉及多个子任务，请问它们的优先级是什么？",
                purpose="确定开发顺序，避免资源浪费",
                category="priority",
                options=("按顺序依次实现", "优先实现核心功能", "并行开发所有功能")
            ))
        
        # 2. 如果有技术栈提及，询问约束
        tech_stack = features.get("tech_stack")
        if tech_stack:
            tech_list = tech_stack[:3]
            questions.append(Question(
                id="tech_constraints",
                question=f"项目涉及 {', '.join(tech_list)}，请问有没有技术版本或依赖约束？",
                purpose="避免版本不兼容问题",
                category="constraints"
            ))
        
        # 3. 如果有模糊描述，针对性澄清
        ambiguous_terms = features.get("ambiguous_terms")
        if ambiguous_terms:
            term = ambiguous_terms[0]
            questions.append(Question(
                id="scope_clarification",
                question=f"你提到了'{term}'，能否具体说明它包含哪些模块或功能？",
                purpose="明确功能范围，避免过度设计或遗漏",
                category="scope"
            ))
        
        # 4. 通用功能范围问题（高复杂度任务）
        if analysis.score >= 0.8:
            questions.append(Question(
                id="mvp_scope",
                question="这个项目是需要完整实现所有功能，还是先做一个最小可行版本（MVP）？",
                purpose="控制项目规模，快速验证可行性",
                category="scope",
                options=("完整实现", "MVP优先", "分阶段交付")
            ))
        
        # 5. 性能和规模问题
        if features.get("complex_indicators"):
            questions.append(Question(
                id="performance_requirements",
                question="对于性能和规模有什么具体要求？（例如：并发用户数、响应时间、数据量）",
                purpose="确定架构设计方向",
                category="constraints"
            ))
        
        # 6. 验收标准
        questions.append(Question(
            id="acceptance_criteria",
            question="什么情况下你会认为这个任务已经完成？",
            purpose="明确验收标准，避免反复返工",
            category="acceptance"
        ))
        
        return questions[:6]
    
    def generate_preparation_checklist(self, analysis: ComplexityAnalysis) -> list[str]:
        """生成准备目录"""
        checklist = []
        features = analysis.detected_features
        
        if features.get("tech_stack"):
            checklist.append("确认技术栈版本和兼容性")
        
        file_count = features.get("file_count", 0)
        if file_count >= 3:
            checklist.append("梳理文件结构和模块依赖关系")
        
        if features.get("complex_indicators"):
            checklist.append("设计系统架构和数据流")
            checklist.append("确定性能监控和测试方案")
        
        checklist.extend([
            "明确开发优先级和里程碑",
            "准备必要的开发环境和工具",
            "确定验收标准和测试用例"
        ])
        
        return checklist[:8]


async def check_thinking_mode(
    message: str,
    *,
    threshold: float = 0.7,
    min_message_length: int = 50
) -> ThinkingModeResult:
    """检查是否需要触发 Thinking Mode
    
    Args:
        message: 用户输入消息
        threshold: 复杂度阈值（0-1）
        min_message_length: 最小消息长度
    
    Returns:
        ThinkingModeResult 包含是否触发、问题列表、准备清单
    """
    if not message:
        return ThinkingModeResult(triggered=False)
    
    message_stripped = message.strip()
    
    # 显式命令触发
    if message_stripped.startswith(("/thinking", "/think")):
        clean_message = re.sub(r"^/think(?:ing)?\s*", "", message_stripped)
        detector = ComplexityDetector(threshold=0.0)  # 强制触发
        analysis = detector.analyze(clean_message or message)
    else:
        # 消息太短，不触发
        if len(message_stripped) < min_message_length:
            return ThinkingModeResult(triggered=False)
        
        detector = ComplexityDetector(threshold=threshold)
        analysis = detector.analyze(message)
        
        if not analysis.should_trigger:
            return ThinkingModeResult(triggered=False)
    
    # 生成问题和清单
    generator = QuestionGenerator()
    questions = generator.generate_questions(analysis, message)
    checklist = generator.generate_preparation_checklist(analysis)
    
    return ThinkingModeResult(
        triggered=True,
        questions=questions,
        preparation_checklist=checklist
    )
