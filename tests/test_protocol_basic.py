"""
简单测试脚本，验证 starry:// 协议处理器的基本功能

运行方式：
    python tests/test_protocol_basic.py
"""

import sys
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openstarry_code.protocol import (
    parse_starry_url,
    validate_parsed_url,
    ProtocolAction,
    ProtocolParseError,
)


def test_parse_api_import():
    """测试 API 导入 URL 解析"""
    url = "starry://api/import?provider=openai&key=env:OPENAI_API_KEY"
    
    parsed = parse_starry_url(url)
    
    assert parsed.scheme == "starry"
    assert parsed.action == ProtocolAction.API_IMPORT
    assert parsed.params["provider"] == "openai"
    assert parsed.params["key"] == "env:OPENAI_API_KEY"
    
    # 验证参数
    validate_parsed_url(parsed)
    
    print("✅ test_parse_api_import passed")


def test_parse_skill_install():
    """测试 Skill 安装 URL 解析"""
    url = "starry://skill/install?github=openstarry/deep-research&ref=main"
    
    parsed = parse_starry_url(url)
    
    assert parsed.action == ProtocolAction.SKILL_INSTALL
    assert parsed.params["github"] == "openstarry/deep-research"
    assert parsed.params["ref"] == "main"
    
    validate_parsed_url(parsed)
    
    print("✅ test_parse_skill_install passed")


def test_parse_extension_load():
    """测试扩展加载 URL 解析"""
    url = "starry://extension/load?path=file:///plugins/ext.py&type=python"
    
    parsed = parse_starry_url(url)
    
    assert parsed.action == ProtocolAction.EXTENSION_LOAD
    assert parsed.params["path"] == "file:///plugins/ext.py"
    assert parsed.params["type"] == "python"
    
    validate_parsed_url(parsed)
    
    print("✅ test_parse_extension_load passed")


def test_invalid_scheme():
    """测试无效的协议前缀"""
    url = "https://api/import?provider=openai"
    
    try:
        parse_starry_url(url)
        assert False, "应该抛出 ProtocolParseError"
    except ProtocolParseError as e:
        assert "Invalid protocol scheme" in str(e)
    
    print("✅ test_invalid_scheme passed")


def test_invalid_action():
    """测试无效的 action"""
    url = "starry://unknown/action?param=value"
    
    try:
        parse_starry_url(url)
        assert False, "应该抛出 ProtocolParseError"
    except ProtocolParseError as e:
        assert "Unknown action" in str(e)
    
    print("✅ test_invalid_action passed")


def test_missing_required_params():
    """测试缺少必需参数"""
    url = "starry://api/import"  # 缺少 provider 或 url 参数
    
    try:
        parsed = parse_starry_url(url)
        validate_parsed_url(parsed)
        assert False, "应该抛出 ProtocolParseError"
    except ProtocolParseError as e:
        assert "requires either" in str(e).lower()
    
    print("✅ test_missing_required_params passed")


def test_get_param_methods():
    """测试参数获取方法"""
    url = "starry://api/import?provider=openai&model=gpt-4"
    parsed = parse_starry_url(url)
    
    # 测试 get_param
    assert parsed.get_param("provider") == "openai"
    assert parsed.get_param("model") == "gpt-4"
    assert parsed.get_param("nonexistent") is None
    assert parsed.get_param("nonexistent", "default") == "default"
    
    # 测试 require_param
    assert parsed.require_param("provider") == "openai"
    
    try:
        parsed.require_param("nonexistent")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "Missing required parameter" in str(e)
    
    print("✅ test_get_param_methods passed")


def main():
    """运行所有测试"""
    print("开始测试 starry:// 协议解析器...\n")
    
    tests = [
        test_parse_api_import,
        test_parse_skill_install,
        test_parse_extension_load,
        test_invalid_scheme,
        test_invalid_action,
        test_missing_required_params,
        test_get_param_methods,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print(f"{'='*60}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
