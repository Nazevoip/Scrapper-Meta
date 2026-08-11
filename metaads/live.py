"""Coleta ao vivo da Biblioteca de Anuncios via browser real.

Substitui `fetcher.py`, cujo endpoint (`/ads/library/async/search_ads/`) a Meta
removeu — hoje ele responde 404 mesmo com o desafio anti-bot resolvido.

A pagina publica da biblioteca chama `POST /api/graphql/` com a query
`AdLibrarySearchPaginationQuery`. Em vez de replicar essa chamada por fora
(o que exigiria doc_id, lsd, fb_dtsg e o cookie do desafio, todos rotativos),
abrimos a pagina num browser, capturamos o corpo do POST que ela mesma emite e
repaginamos a partir de dentro. Assim tokens, cookies e desafio vem de graca, e
uma troca de doc_id nao quebra a coleta.
"""

from __future__ import annotations

import json
import urllib.parse

from playwright.sync_api import sync_playwright

QUERY_NAME = "AdLibrarySearchPaginationQuery"
PAGE_SIZE = 30


class CollectError(RuntimeError):
    """Nao foi possivel capturar a query de paginacao da biblioteca."""


def _library_url(query: str, country: str, active_status: str) -> str:
    params = urllib.parse.urlencode({
        "active_status": active_status,
        "ad_type": "all",
        "country": country.upper(),
        "q": query,
        "search_type": "keyword_unordered",
        "media_type": "all",
    })
    return f"https://www.facebook.com/ads/library/?{params}"


# Repagina de dentro da pagina: mesmo corpo do POST original, so trocando
# `cursor` e `first`. `credentials: include` reaproveita a sessao ja liberada.
_PAGINATE_JS = """
async ([form, pages, first]) => {
  const base = JSON.parse(form.variables);
  const out = [];
  let cursor = base.cursor || null;
  let hasNext = true;

  for (let i = 0; i < pages && hasNext; i++) {
    const vars = Object.assign({}, base, { first: first, cursor: cursor });
    const body = new URLSearchParams(
      Object.assign({}, form, { variables: JSON.stringify(vars) })
    );
    const resp = await fetch("/api/graphql/", {
      method: "POST",
      credentials: "include",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    const text = await resp.text();

    let data;
    try {
      data = JSON.parse(text.split("\\n")[0]);
    } catch (e) {
      return { error: "resposta nao-JSON: " + text.slice(0, 200), ads: out };
    }
    const conn = data?.data?.ad_library_main?.search_results_connection;
    if (!conn) {
      return { error: JSON.stringify(data).slice(0, 240), ads: out };
    }

    for (const edge of conn.edges || []) {
      for (const ad of edge.node?.collated_results || []) out.push(ad);
    }
    cursor = conn.page_info?.end_cursor;
    hasNext = !!conn.page_info?.has_next_page;
    await new Promise(r => setTimeout(r, 400));
  }
  return { error: null, ads: out };
}
"""


def collect_raw(
    query: str,
    country: str = "BR",
    max_pages: int = 5,
    active_status: str = "active",
    headless: bool = True,
    timeout_ms: int = 90_000,
) -> list[dict]:
    """Devolve os anuncios crus (dicts do GraphQL) para uma busca.

    Levanta `CollectError` se a pagina nunca emitir a query de paginacao —
    sinal de bloqueio, mudanca de layout ou busca sem nenhum resultado.
    """
    captured: dict[str, dict] = {}

    def on_request(req):
        if captured or "/api/graphql/" not in req.url:
            return
        body = req.post_data
        if not body:
            return
        fields = {k: v[0] for k, v in urllib.parse.parse_qs(body).items()}
        if fields.get("fb_api_req_friendly_name") == QUERY_NAME:
            captured["form"] = fields

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=headless)
        page = browser.new_context(
            locale="pt-BR", viewport={"width": 1400, "height": 900}
        ).new_page()
        page.on("request", on_request)
        page.goto(_library_url(query, country, active_status),
                  wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(8_000)

        # A query de paginacao so nasce quando a lista rola.
        for _ in range(15):
            if captured:
                break
            page.mouse.wheel(0, 9_000)
            page.wait_for_timeout(1_800)

        if not captured:
            browser.close()
            raise CollectError(
                f"A biblioteca nao emitiu {QUERY_NAME} para '{query}'. "
                "Pode ser bloqueio, mudanca de layout ou busca sem resultados."
            )

        result = page.evaluate(_PAGINATE_JS, [captured["form"], max_pages, PAGE_SIZE])
        browser.close()

    if result.get("error") and not result.get("ads"):
        raise CollectError(f"GraphQL recusou a paginacao: {result['error']}")
    return result.get("ads") or []
