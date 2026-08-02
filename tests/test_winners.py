from datetime import datetime, timezone
from pathlib import Path

import pytest

from metaads.parser import Ad, parse_payload
from metaads.winners import group_by_product, rank_products, score_products

FIXTURE = Path(__file__).parent / "fixtures" / "search_response.json"
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


@pytest.fixture
def ads():
    parsed, _ = parse_payload(FIXTURE.read_text(encoding="utf-8"))
    return parsed


@pytest.fixture
def ranked(ads):
    return rank_products(ads, now=NOW)


def _find(products, fragment):
    return next(p for p in products if fragment in p.key)


def test_groups_same_landing_page_across_advertisers(ads):
    caneca = _find(group_by_product(ads), "caneca-termica")
    assert caneca.n_ads == 3  # 1001, 1002, 1003 - a duplicata de 1002 sai
    assert caneca.advertisers == ["Loja Alpha", "Revendedor Beta"]
    assert caneca.total_variants == 24 + 11 + 2


def test_landing_url_is_normalized(ads):
    caneca = _find(group_by_product(ads), "caneca-termica")
    assert caneca.landing_url == "https://lojaalpha.com.br/produtos/caneca-termica"


def test_deduplicates_repeated_archive_ids(ads):
    caneca = _find(group_by_product(ads), "caneca-termica")
    assert [a.archive_id for a in caneca.ads] == ["1001", "1002", "1003"]


def test_ads_without_link_group_by_advertiser_and_title(ads):
    corda = _find(group_by_product(ads), "delta fit")
    assert corda.n_ads == 1
    assert corda.label == "Corda de Pular Inteligente"


def test_label_uses_most_common_title(ads):
    caneca = _find(group_by_product(ads), "caneca-termica")
    assert caneca.label == "Caneca Termica 500ml"


def test_winner_is_the_most_duplicated_and_longest_running(ranked):
    assert "caneca-termica" in ranked[0].key
    assert ranked[0].score > ranked[-1].score


def test_metrics_of_the_winner(ranked):
    winner = ranked[0]
    assert winner.active_ads == 2
    assert winner.active_ratio == pytest.approx(2 / 3)
    assert winner.max_days_running(NOW) == pytest.approx(90.0)
    assert winner.median_days_running(NOW) == pytest.approx(39.0)
    assert winner.total_eu_reach == 0


def test_scores_are_bounded(ranked):
    assert all(0 <= p.score <= 100 for p in ranked)


def test_reach_weight_is_redistributed_when_no_eu_data():
    ads = [
        Ad(archive_id="1", page_id="1", page_name="A", title="A", body="", caption="",
           cta_text="", link_url="https://a.com/p", display_format="", collation_count=5,
           start_date=datetime(2026, 1, 1, tzinfo=timezone.utc), is_active=True),
        Ad(archive_id="2", page_id="2", page_name="B", title="B", body="", caption="",
           cta_text="", link_url="https://b.com/p", display_format="", collation_count=1,
           start_date=datetime(2026, 7, 1, tzinfo=timezone.utc), is_active=True),
    ]
    products = sorted(score_products(group_by_product(ads), now=NOW),
                      key=lambda p: p.score, reverse=True)
    assert all("reach" not in p.signals for p in products)
    assert sum(p.signals["variants"] for p in products) == pytest.approx(1.0)
    # Ambos 100% ativos: o sinal sem variacao vale 0.5 para os dois e nao
    # desempata, mas os demais sinais ainda separam os produtos.
    assert all(p.signals["active_ratio"] == 0.5 for p in products)
    assert products[0].score > products[1].score


def test_reach_signal_is_kept_when_eu_data_exists(ads):
    products = score_products(group_by_product(ads), now=NOW)
    assert all("reach" in p.signals for p in products)
    luminaria = _find(products, "luminaria")
    assert luminaria.signals["reach"] == pytest.approx(1.0)


def test_min_ads_filters_noise(ads):
    assert len(rank_products(ads, min_ads=1, now=NOW)) == 3
    assert [p.n_ads for p in rank_products(ads, min_ads=2, now=NOW)] == [3]


def test_empty_input_is_safe():
    assert rank_products([], now=NOW) == []
