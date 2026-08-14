"""Contract tests for key-free Chinese web search providers."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from openstarry_code.search.providers.baidu import BaiduSearchProvider
from openstarry_code.search.providers.bing_cn import BingChinaSearchProvider
from openstarry_code.search.providers.sogou import SogouSearchProvider
from openstarry_code.search.types import SearchProviderError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_cls", "html", "expected_source", "expected_url"),
    [
        (
            BingChinaSearchProvider,
            '<ol><li class="b_algo"><h2><a href="https://example.com/bing">Bing title</a></h2>'
            '<div class="b_caption"><p>Bing snippet</p></div></li></ol>',
            "bing_cn",
            "https://example.com/bing",
        ),
        (
            BaiduSearchProvider,
            '<div class="result c-container"><h3>'
            '<a href="https://example.com/baidu">Baidu title</a></h3>'
            '<div class="c-abstract">Baidu snippet</div></div>',
            "baidu",
            "https://example.com/baidu",
        ),
        (
            SogouSearchProvider,
            '<div class="vrResult"><h3><a class="resultLink" href="/link?url=test">'
            'Sogou title</a></h3><a class="txt-summary">Sogou snippet</a></div>',
            "sogou",
            "https://m.sogou.com/link?url=test",
        ),
    ],
)
async def test_provider_normalizes_html_results(
    provider_cls: Callable[..., object],
    html: str,
    expected_source: str,
    expected_url: str,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params
        return httpx.Response(200, text=html, request=request)

    provider = provider_cls(transport=httpx.MockTransport(handler))
    results = await provider.search("OpenStarry", max_results=1)  # type: ignore[attr-defined]

    assert len(results) == 1
    assert results[0].provider == expected_source
    assert results[0].source == expected_source
    assert results[0].url == expected_url
    assert results[0].snippet.endswith("snippet")


@pytest.mark.asyncio
async def test_provider_reports_verification_challenge() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>百度安全验证</html>", request=request)

    provider = BaiduSearchProvider(transport=httpx.MockTransport(handler))

    with pytest.raises(SearchProviderError) as exc_info:
        await provider.search("OpenStarry")

    assert exc_info.value.provider == "baidu"
    assert exc_info.value.kind == "blocked"


@pytest.mark.asyncio
async def test_provider_reports_unexpected_markup_as_parse_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><p>layout changed</p></html>", request=request)

    provider = BingChinaSearchProvider(transport=httpx.MockTransport(handler))

    with pytest.raises(SearchProviderError) as exc_info:
        await provider.search("OpenStarry")

    assert exc_info.value.provider == "bing_cn"
    assert exc_info.value.kind == "parse"
