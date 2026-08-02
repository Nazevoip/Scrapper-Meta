"""Coleta anuncios da Biblioteca de Anuncios da Meta usando Scrapling.

Usa o mesmo endpoint interno que a propria pagina da biblioteca chama
(`/ads/library/async/search_ads/`). O Scrapling entra pela impersonacao de TLS
e pelos cabecalhos de navegador — sem isso a Meta responde com HTML de
checkpoint em vez de JSON.
"""

from __future__ import annotations

import time
import uuid
from typing import Iterator

from scrapling.fetchers import Fetcher

from metaads.parser import Ad, parse_payload

SEARCH_URL = "https://www.facebook.com/ads/library/async/search_ads/"
PAGE_SIZE = 30


class AdLibraryError(RuntimeError):
    """A biblioteca respondeu algo que nao e o JSON de resultados."""


def _params(
    query: str,
    country: str,
    active_status: str,
    cursor: str | None,
    session_id: str,
    collation_token: str,
) -> dict[str, str]:
    return {
        "q": query,
        "count": str(PAGE_SIZE),
        "active_status": active_status,
        "ad_type": "all",
        "countries[0]": country.upper(),
        "media_type": "all",
        "search_type": "keyword_unordered",
        "session_id": session_id,
        "collation_token": collation_token,
        "forward_cursor": cursor or "",
        "backward_cursor": "",
        "sort_data[direction]": "desc",
        "sort_data[mode]": "relevancy_monthly_grouped",
    }


def _headers(country: str) -> dict[str, str]:
    return {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.facebook.com",
        "referer": f"https://www.facebook.com/ads/library/?active_status=active&country={country.upper()}",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
    }


def iter_ads(
    query: str,
    country: str = "BR",
    max_pages: int = 5,
    active_status: str = "active",
    delay: float = 1.5,
    timeout: int = 60,
) -> Iterator[Ad]:
    """Percorre as paginas de resultados e emite os anuncios encontrados.

    Levanta `AdLibraryError` se a primeira pagina nao vier em JSON (bloqueio,
    checkpoint ou mudanca de endpoint). Paginas seguintes vazias apenas
    encerram a coleta.
    """
    session_id = str(uuid.uuid4())
    collation_token = str(uuid.uuid4())
    cursor: str | None = None

    for page in range(max_pages):
        if page:
            time.sleep(delay)

        response = Fetcher.post(
            SEARCH_URL,
            params=_params(query, country, active_status, cursor, session_id, collation_token),
            data={"__a": "1"},
            headers=_headers(country),
            stealthy_headers=True,
            impersonate="chrome",
            timeout=timeout,
        )
        if response.status != 200:
            raise AdLibraryError(f"HTTP {response.status} ao buscar '{query}' (pagina {page + 1})")

        ads, cursor = parse_payload(response.body)
        if not ads:
            if page == 0:
                raise AdLibraryError(
                    "Resposta sem anuncios utilizaveis. A Meta provavelmente exigiu "
                    "verificacao; tente outro IP/pais ou reduza a frequencia."
                )
            return

        yield from ads
        if not cursor:
            return


def collect_ads(query: str, **kwargs) -> list[Ad]:
    """Versao materializada de `iter_ads`."""
    return list(iter_ads(query, **kwargs))
