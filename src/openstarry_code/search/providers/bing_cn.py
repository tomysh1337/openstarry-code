"""Bing China HTML search provider."""

from openstarry_code.search.html_scraper import HtmlSearchDefinition, HtmlSearchProvider
from openstarry_code.search.registry import register_provider

_SEARCH_URL = "https://cn.bing.com/search"


class BingChinaSearchProvider(HtmlSearchProvider):
    """Search cn.bing.com without requiring an API key."""

    name = "bing_cn"
    definition = HtmlSearchDefinition(
        provider_id=name,
        endpoint=_SEARCH_URL,
        query_parameter="q",
        result_selectors=("li.b_algo",),
        title_selector="h2 a",
        snippet_selectors=(".b_caption p", ".b_snippet"),
        extra_parameters={"count": "20", "setlang": "zh-hans"},
        blocked_markers=("unusual traffic", "verify you are a human", "captcha"),
        no_results_markers=("there are no results for", "没有与此相关的结果"),
    )


register_provider("bing_cn", BingChinaSearchProvider)
