"""Converte a resposta crua da Biblioteca de Anuncios em registros normalizados."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit

# A Meta prefixa as respostas JSON com um guard anti-hijacking.
_JSON_GUARD = re.compile(r"^\s*for\s*\(\s*;\s*;\s*\)\s*;")

# Parametros de rastreamento que nao fazem parte da identidade do produto.
_TRACKING_PARAMS = re.compile(
    r"^(utm_|fb|ttclid|gclid|gbraid|wbraid|msclkid|epik|ref|referrer|"
    r"campaign|adset|ad_id|placement|site_source_name|h$|s$)",
    re.IGNORECASE,
)

# Encurtadores/redirecionadores: o path nao identifica o produto.
_REDIRECTORS = {"l.facebook.com", "lm.facebook.com", "l.instagram.com"}


@dataclass
class Ad:
    """Um anuncio individual da biblioteca."""

    archive_id: str
    page_id: str
    page_name: str
    title: str
    body: str
    caption: str
    cta_text: str
    link_url: str
    display_format: str
    platforms: list[str] = field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool = False
    collation_count: int = 1
    eu_total_reach: int | None = None
    impressions_text: str | None = None

    @property
    def permalink(self) -> str:
        return f"https://www.facebook.com/ads/library/?id={self.archive_id}"

    def days_running(self, now: datetime | None = None) -> float:
        """Dias entre o inicio da veiculacao e o fim (ou agora, se ativo)."""
        if self.start_date is None:
            return 0.0
        now = now or datetime.now(timezone.utc)
        end = self.end_date or now
        if self.is_active or end > now:
            end = now
        return max((end - self.start_date).total_seconds() / 86400.0, 0.0)


def strip_json_guard(text: str) -> str:
    return _JSON_GUARD.sub("", text, count=1).strip()


def normalize_link(url: str) -> str:
    """Reduz uma URL de destino a uma chave estavel de produto.

    Remove parametros de rastreamento, fragmento, `www.` e barra final, e
    desembrulha redirecionadores da Meta (`l.facebook.com/l.php?u=...`).
    """
    if not url:
        return ""
    url = unquote(url.strip())
    if "://" not in url:
        url = "https://" + url

    parts = urlsplit(url)
    host = parts.netloc.lower().split(":")[0]

    if host in _REDIRECTORS:
        target = parse_qs(parts.query).get("u", [""])[0]
        if target:
            return normalize_link(target)

    if host.startswith("www."):
        host = host[4:]

    kept = sorted(
        (k, v)
        for k, vs in parse_qs(parts.query).items()
        if not _TRACKING_PARAMS.match(k)
        for v in vs
    )
    query = "&".join(f"{k}={v}" for k, v in kept)
    path = parts.path.rstrip("/")
    return urlunsplit(("https", host, path, query, ""))


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _text(node: Any) -> str:
    """Campos de texto vem como str ou como {"text": ...}."""
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return str(node.get("text") or "").strip()
    return ""


def _iter_raw_ads(payload: dict) -> Iterator[dict]:
    """`results` vem como lista de grupos ou como lista plana, conforme a versao."""
    for entry in payload.get("results") or []:
        if isinstance(entry, list):
            yield from (a for a in entry if isinstance(a, dict))
        elif isinstance(entry, dict):
            yield entry


def _eu_reach(raw: dict) -> int | None:
    for key in ("euTotalReach", "eu_total_reach"):
        value = raw.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
    return None


def parse_ad(raw: dict) -> Ad | None:
    """Converte um anuncio cru. Retorna None se nao houver ID de arquivo."""
    archive_id = str(raw.get("adArchiveID") or raw.get("ad_archive_id") or "").strip()
    if not archive_id:
        return None

    snapshot = raw.get("snapshot") or {}
    cards = snapshot.get("cards") or []
    first_card = cards[0] if cards and isinstance(cards[0], dict) else {}

    # Anuncios em carrossel deixam o snapshot raiz vazio; caia para o 1o card.
    link_url = snapshot.get("link_url") or first_card.get("link_url") or ""
    title = _text(snapshot.get("title")) or _text(first_card.get("title"))
    body = _text(snapshot.get("body")) or _text(first_card.get("body"))

    return Ad(
        archive_id=archive_id,
        page_id=str(raw.get("pageID") or snapshot.get("page_id") or ""),
        page_name=str(raw.get("pageName") or snapshot.get("page_name") or "").strip(),
        title=title,
        body=body,
        caption=_text(snapshot.get("caption")) or _text(first_card.get("caption")),
        cta_text=_text(snapshot.get("cta_text")) or _text(first_card.get("cta_text")),
        link_url=str(link_url or "").strip(),
        display_format=str(snapshot.get("display_format") or "").lower(),
        platforms=[str(p) for p in (raw.get("publisherPlatform")
                                    or raw.get("publisher_platform") or [])],
        start_date=_timestamp(raw.get("startDate") or raw.get("start_date")),
        end_date=_timestamp(raw.get("endDate") or raw.get("end_date")),
        is_active=bool(raw.get("isActive", raw.get("is_active", False))),
        collation_count=max(int(raw.get("collationCount")
                                or raw.get("collation_count") or 1), 1),
        eu_total_reach=_eu_reach(raw),
        impressions_text=(raw.get("impressionsWithIndex") or {}).get("impressionsText"),
    )


def parse_payload(body: str | bytes) -> tuple[list[Ad], str | None]:
    """Extrai anuncios e o cursor da proxima pagina de uma resposta da busca.

    Retorna `([], None)` quando a resposta nao e o JSON esperado — util para
    detectar bloqueio/checkpoint sem derrubar a coleta.
    """
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")

    try:
        data = json.loads(strip_json_guard(body))
    except json.JSONDecodeError:
        return [], None

    payload = data.get("payload") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        return [], None

    ads = [ad for raw in _iter_raw_ads(payload) if (ad := parse_ad(raw))]
    cursor = payload.get("forwardCursor") or None
    if payload.get("isResultComplete"):
        cursor = None
    return ads, cursor
