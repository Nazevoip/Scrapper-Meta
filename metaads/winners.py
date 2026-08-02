"""Agrupa anuncios por produto e ranqueia os vencedores.

A Biblioteca de Anuncios NAO publica visualizacoes nem cliques de anuncios
comerciais (so faixas de impressao para anuncios politicos, e alcance para
campanhas com entrega na UE). O ranking abaixo usa os sinais que a biblioteca
de fato expoe e que se correlacionam com investimento — quanto um anuncio e
duplicado, ha quanto tempo roda, quantos anunciantes o copiaram.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone

from metaads.parser import Ad, normalize_link

# Pesos do score final. Somam 1.0.
WEIGHTS = {
    "variants": 0.35,  # criativos duplicados = orcamento escalado
    "longevity": 0.25,  # anuncio ruim e desligado rapido
    "ad_count": 0.20,  # muitos anuncios distintos para o mesmo destino
    "active_ratio": 0.10,  # ainda no ar hoje
    "reach": 0.10,  # alcance real, quando divulgado (UE)
}


@dataclass
class Product:
    """Um destino de compra e todos os anuncios que apontam para ele."""

    key: str
    label: str
    landing_url: str
    ads: list[Ad] = field(default_factory=list)
    score: float = 0.0
    signals: dict[str, float] = field(default_factory=dict)

    @property
    def n_ads(self) -> int:
        return len(self.ads)

    @property
    def total_variants(self) -> int:
        return sum(a.collation_count for a in self.ads)

    @property
    def advertisers(self) -> list[str]:
        return sorted({a.page_name for a in self.ads if a.page_name})

    @property
    def active_ads(self) -> int:
        return sum(1 for a in self.ads if a.is_active)

    @property
    def active_ratio(self) -> float:
        return self.active_ads / self.n_ads if self.ads else 0.0

    @property
    def total_eu_reach(self) -> int:
        return sum(a.eu_total_reach or 0 for a in self.ads)

    def max_days_running(self, now: datetime | None = None) -> float:
        return max((a.days_running(now) for a in self.ads), default=0.0)

    def median_days_running(self, now: datetime | None = None) -> float:
        return statistics.median([a.days_running(now) for a in self.ads]) if self.ads else 0.0

    def top_ads(self, limit: int = 3) -> list[Ad]:
        """Anuncios mais representativos: mais duplicados primeiro."""
        return sorted(
            self.ads,
            key=lambda a: (a.collation_count, a.days_running()),
            reverse=True,
        )[:limit]


def _product_key(ad: Ad) -> tuple[str, str]:
    """Chave de agrupamento e rotulo legivel para um anuncio."""
    link = normalize_link(ad.link_url)
    if link:
        return link, link
    # Sem link de destino, o par anunciante + titulo e a melhor aproximacao.
    fallback = f"{ad.page_name.lower()}|{ad.title.lower()[:60]}"
    return fallback, ad.title or ad.page_name or ad.archive_id


def group_by_product(ads: list[Ad]) -> list[Product]:
    """Agrupa anuncios pelo destino normalizado, deduplicando por archive_id."""
    products: dict[str, Product] = {}
    seen: set[str] = set()

    for ad in ads:
        if ad.archive_id in seen:
            continue
        seen.add(ad.archive_id)

        key, label = _product_key(ad)
        product = products.get(key)
        if product is None:
            product = Product(key=key, label=label, landing_url=normalize_link(ad.link_url))
            products[key] = product
        product.ads.append(ad)

    for product in products.values():
        # Titulo mais frequente descreve o produto melhor que a URL crua.
        titles = [a.title for a in product.ads if a.title]
        if titles:
            product.label = max(set(titles), key=titles.count)

    return list(products.values())


def _normalize(values: list[float]) -> list[float]:
    """Min-max para 0..1. Sinal sem variacao vira 0.5 (nao altera o ranking)."""
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return [0.5] * len(values)
    return [(v - low) / (high - low) for v in values]


def score_products(products: list[Product], now: datetime | None = None) -> list[Product]:
    """Preenche `score` (0-100) e `signals` de cada produto."""
    if not products:
        return products

    now = now or datetime.now(timezone.utc)
    raw = {
        "variants": [math.log1p(p.total_variants) for p in products],
        "longevity": [math.log1p(p.max_days_running(now)) for p in products],
        "ad_count": [math.log1p(p.n_ads) for p in products],
        "active_ratio": [p.active_ratio for p in products],
        "reach": [math.log1p(p.total_eu_reach) for p in products],
    }

    weights = dict(WEIGHTS)
    # Fora da UE a biblioteca nao publica alcance; redistribui o peso.
    if all(p.total_eu_reach == 0 for p in products):
        spare = weights.pop("reach")
        total = sum(weights.values())
        weights = {k: w + spare * w / total for k, w in weights.items()}

    normalized = {name: _normalize(raw[name]) for name in weights}
    for i, product in enumerate(products):
        product.signals = {name: normalized[name][i] for name in weights}
        product.score = round(
            100 * sum(weights[name] * product.signals[name] for name in weights), 1
        )
    return products


def rank_products(
    ads: list[Ad], min_ads: int = 1, now: datetime | None = None
) -> list[Product]:
    """Agrupa, pontua e ordena os produtos do melhor para o pior.

    `min_ads` descarta destinos com poucos anuncios — util para tirar ruido
    de resultados de busca amplos.
    """
    products = [p for p in group_by_product(ads) if p.n_ads >= min_ads]
    score_products(products, now=now)
    return sorted(products, key=lambda p: (p.score, p.total_variants), reverse=True)
