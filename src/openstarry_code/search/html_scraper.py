"""Shared runtime for key-free HTML search providers."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from openstarry_code.search.retry_policy import is_retryable_http_status
from openstarry_code.search.types import SearchErrorKind, SearchProviderError, SearchResult

_HEADERS = {
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class HtmlSearchDefinition:
    provider_id: str
    endpoint: str
    query_parameter: str
    result_selectors: tuple[str, ...]
    title_selector: str
    snippet_selectors: tuple[str, ...]
    extra_parameters: dict[str, str]
    blocked_markers: tuple[str, ...]
    no_results_markers: tuple[str, ...]


class HtmlSearchProvider:
    definition: HtmlSearchDefinition
    name: str

    def __init__(
        self,
        proxy: str = "",
        use_env_proxy: bool = False,
        diagnostics: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._proxy = proxy or None
        self._trust_env = bool(use_env_proxy) and not self._proxy
        self._diagnostics = bool(diagnostics)
        self._transport = transport

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        params = {
            self.definition.query_parameter: query,
            **self.definition.extra_parameters,
        }
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                proxy=self._proxy,
                trust_env=self._trust_env,
                transport=self._transport,
                follow_redirects=True,
            ) as client:
                response = await client.get(
                    self.definition.endpoint,
                    params=params,
                    headers=_HEADERS,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise _provider_error(self.name, exc) from exc

        lowered = response.text.lower()
        if any(marker.lower() in lowered for marker in self.definition.blocked_markers):
            raise SearchProviderError(
                provider=self.name,
                kind="blocked",
                message=f"{self.name} returned a verification challenge.",
                retryable=False,
                status_code=response.status_code,
            )

        soup = BeautifulSoup(response.text, "html.parser")
        results = self._parse_results(soup, max_results=max_results)
        if not results and not any(
            marker.lower() in lowered for marker in self.definition.no_results_markers
        ):
            raise SearchProviderError(
                provider=self.name,
                kind="parse",
                message=f"{self.name} response did not contain parseable results.",
                retryable=False,
                status_code=response.status_code,
            )
        return results

    def _parse_results(
        self,
        soup: BeautifulSoup,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        nodes: list[Tag] = []
        seen_nodes: set[int] = set()
        for selector in self.definition.result_selectors:
            for node in soup.select(selector):
                if not isinstance(node, Tag) or id(node) in seen_nodes:
                    continue
                nodes.append(node)
                seen_nodes.add(id(node))

        results: list[SearchResult] = []
        seen_urls: set[str] = set()
        for node in nodes:
            anchor = node.select_one(self.definition.title_selector)
            if not isinstance(anchor, Tag):
                continue
            href_value = anchor.get("href", "")
            href = href_value if isinstance(href_value, str) else ""
            href = urljoin(self.definition.endpoint, href.strip())
            title = anchor.get_text(" ", strip=True)
            if not title or not href.startswith(("http://", "https://")) or href in seen_urls:
                continue

            snippet = ""
            for selector in self.definition.snippet_selectors:
                snippet_node = node.select_one(selector)
                if snippet_node is not None:
                    snippet = snippet_node.get_text(" ", strip=True)
                    if snippet:
                        break

            results.append(
                SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet,
                    source=self.name,
                    provider=self.name,
                )
            )
            seen_urls.add(href)
            if len(results) >= max_results:
                break
        return results


def _provider_error(provider: str, exc: httpx.HTTPError) -> SearchProviderError:
    if isinstance(exc, httpx.TimeoutException):
        kind: SearchErrorKind = "timeout"
        retryable = True
    elif isinstance(exc, httpx.HTTPStatusError):
        kind = "http"
        retryable = is_retryable_http_status(exc.response.status_code)
    else:
        kind = "network"
        retryable = True
    return SearchProviderError(
        provider=provider,
        kind=kind,
        message=str(exc) or f"{provider} search request failed.",
        retryable=retryable,
        status_code=(
            exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
        ),
    )
