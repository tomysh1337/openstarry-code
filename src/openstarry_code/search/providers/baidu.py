"""Baidu HTML search provider."""

from openstarry_code.search.html_scraper import HtmlSearchDefinition, HtmlSearchProvider
from openstarry_code.search.registry import register_provider

_SEARCH_URL = "https://www.baidu.com/s"


class BaiduSearchProvider(HtmlSearchProvider):
    """Search Baidu's public web results without requiring an API key."""

    name = "baidu"
    definition = HtmlSearchDefinition(
        provider_id=name,
        endpoint=_SEARCH_URL,
        query_parameter="wd",
        result_selectors=("div.result", "div.c-container"),
        title_selector="h3 a",
        snippet_selectors=(".c-abstract", ".content-right_8Zs40", ".c-span-last"),
        extra_parameters={"rn": "20", "ie": "utf-8"},
        blocked_markers=("百度安全验证", "请输入验证码", "安全验证"),
        no_results_markers=("抱歉，没有找到", "没有找到相关结果"),
    )


register_provider("baidu", BaiduSearchProvider)
