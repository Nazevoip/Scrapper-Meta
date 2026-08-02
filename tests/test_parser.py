from datetime import datetime, timezone
from pathlib import Path

import pytest

from metaads.parser import normalize_link, parse_payload, strip_json_guard

FIXTURE = Path(__file__).parent / "fixtures" / "search_response.json"
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


@pytest.fixture
def parsed():
    return parse_payload(FIXTURE.read_text(encoding="utf-8"))


def test_strip_json_guard():
    assert strip_json_guard('for (;;);{"a": 1}') == '{"a": 1}'
    assert strip_json_guard('{"a": 1}') == '{"a": 1}'


def test_parses_guarded_response():
    ads, cursor = parse_payload('for (;;);' + FIXTURE.read_text(encoding="utf-8"))
    assert len(ads) == 6  # a deduplicacao acontece no agrupamento, nao aqui
    assert cursor == "AQHR_cursor_pagina_2"


def test_drops_ads_without_archive_id(parsed):
    ads, _ = parsed
    assert all(ad.archive_id for ad in ads)
    assert "Anuncio quebrado" not in {ad.page_name for ad in ads}


def test_flattens_grouped_results(parsed):
    ads, _ = parsed
    # 1001, 1002, 1002 (duplicado), 1003, 2001, 3001 -> o sem ID e descartado.
    assert [ad.archive_id for ad in ads] == ["1001", "1002", "1002", "1003", "2001", "3001"]


def test_reads_creative_fields(parsed):
    ads, _ = parsed
    ad = ads[0]
    assert ad.title == "Caneca Termica 500ml"
    assert ad.body == "Mantem gelado por 24h"
    assert ad.cta_text == "Comprar agora"
    assert ad.display_format == "video"
    assert ad.platforms == ["FACEBOOK", "INSTAGRAM"]
    assert ad.collation_count == 24
    assert ad.is_active is True
    assert ad.permalink == "https://www.facebook.com/ads/library/?id=1001"


def test_falls_back_to_first_carousel_card(parsed):
    ads, _ = parsed
    carousel = next(ad for ad in ads if ad.archive_id == "2001")
    assert carousel.title == "Luminaria Astronauta"
    assert carousel.body == "Decore o quarto"
    assert carousel.link_url.startswith("https://gammastore.com/p/luminaria-astronauta")
    assert carousel.eu_total_reach == 45000


def test_days_running_uses_end_date_when_inactive(parsed):
    ads, _ = parsed
    finished = next(ad for ad in ads if ad.archive_id == "1003")
    assert finished.is_active is False
    assert finished.days_running(NOW) == pytest.approx(39.0)  # 16/06 -> 25/07

    running = next(ad for ad in ads if ad.archive_id == "1001")
    assert running.days_running(NOW) == pytest.approx(90.0)  # 03/05 -> 01/08


def test_incomplete_result_keeps_cursor(parsed):
    _, cursor = parsed
    assert cursor == "AQHR_cursor_pagina_2"


def test_complete_result_clears_cursor():
    body = '{"payload": {"results": [], "forwardCursor": "x", "isResultComplete": true}}'
    assert parse_payload(body) == ([], None)


def test_non_json_response_is_not_fatal():
    assert parse_payload("<html>checkpoint</html>") == ([], None)
    assert parse_payload(b'for (;;);{"error": 1357004}') == ([], None)


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://www.lojaalpha.com.br/produtos/caneca-termica/?utm_source=fb&fbclid=1",
            "https://lojaalpha.com.br/produtos/caneca-termica",
        ),
        (
            "http://lojaalpha.com.br/produtos/caneca-termica?utm_source=ig",
            "https://lojaalpha.com.br/produtos/caneca-termica",
        ),
        (
            "https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.lojaalpha.com.br%2Fprodutos%2Fcaneca-termica%2F%3Futm_source%3Dstories&h=AT1",
            "https://lojaalpha.com.br/produtos/caneca-termica",
        ),
        (
            "https://gammastore.com/p/luminaria-astronauta?variant=12#reviews",
            "https://gammastore.com/p/luminaria-astronauta?variant=12",
        ),
        ("lojaalpha.com.br/produto", "https://lojaalpha.com.br/produto"),
        ("", ""),
    ],
)
def test_normalize_link(url, expected):
    assert normalize_link(url) == expected
