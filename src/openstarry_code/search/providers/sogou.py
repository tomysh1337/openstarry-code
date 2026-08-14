"""Sogou HTML search provider."""

from openstarry_code.search.html_scraper import HtmlSearchDefinition, HtmlSearchProvider
from openstarry_code.search.registry import register_provider

_SEARCH_URL = "https://m.sogou.com/web/searchList.jsp"


class SogouSearchProvider(HtmlSearchProvider):
    """Search Sogou's public web results without requiring an API key."""

    name = "sogou"
    definition = HtmlSearchDefinition(
        provider_id=name,
        endpoint=_SEARCH_URL,
        query_parameter="keyword",
        result_selectors=(".vrResult",),
        title_selector="h3 a.resultLink",
        snippet_selectors=(".txt-summary",),
        extra_parameters={"pid": "sogouwap"},
        blocked_markers=("请输入验证码", "访问过于频繁", "用户您好，我们的系统检测到"),
        no_results_markers=("没有找到相关的网页", "未找到相关结果"),
    )


register_provider("sogou", SogouSearchProvider)
