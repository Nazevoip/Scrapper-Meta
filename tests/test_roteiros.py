from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from metaads.advertisers import group_by_advertiser
from metaads.parser import Ad
from metaads.roteiros import (
    MAX_CHARS_REFERENCIA,
    Roteiro,
    Roteiros,
    gerar,
    montar_pedido,
    para_markdown,
    referencias,
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def mk(aid, page_id="p1", nome="Loja", coll=1, dias=30, ativo=True, body="copy"):
    return Ad(
        archive_id=aid, page_id=page_id, page_name=nome, title="", body=body,
        caption="", cta_text="", link_url="", display_format="video",
        start_date=NOW - timedelta(days=dias), is_active=ativo, collation_count=coll,
    )


def test_referencias_ordena_por_copias_deduplica_e_ignora_inativos():
    ads = [
        mk("1", body="pouco copiado", coll=1),
        mk("2", body="mais   copiado", coll=9),
        mk("3", body="mais copiado", coll=2),       # mesmo texto apos normalizar
        mk("4", body="desligado", coll=50, ativo=False),
    ]
    refs = referencias(group_by_advertiser(ads), now=NOW)
    assert refs[0]["textos"] == ["mais copiado", "pouco copiado"]


def test_referencias_respeita_limites_e_pula_anunciante_sem_texto():
    ads = [mk("0", page_id="vazio", body="")]
    ads += [mk(f"{p}{i}", page_id=p, body=f"{p} texto {i}") for p in "abcdefg" for i in range(5)]
    refs = referencias(group_by_advertiser(ads), now=NOW, max_anunciantes=3, por_anunciante=2)
    assert len(refs) == 3
    assert all(len(r["textos"]) == 2 for r in refs)


def test_referencias_corta_texto_longo():
    refs = referencias(group_by_advertiser([mk("1", body="x" * 1000)]), now=NOW)
    assert len(refs[0]["textos"][0]) == MAX_CHARS_REFERENCIA


def test_pedido_leva_produto_quantidade_e_textos():
    refs = [{"anunciante": "A", "status": "ESCALANDO", "dias": 40, "copias": 12,
             "textos": ["gancho do concorrente"]}]
    pedido = montar_pedido("Ficha de anamnese", refs, 7)
    assert "Ficha de anamnese" in pedido
    assert "gancho do concorrente" in pedido
    assert "7 roteiros" in pedido


ROTEIRO = Roteiro(angulo="dor", gancho="Gancho.", desenvolvimento="Meio.",
                  cta="Clique.", texto_do_anuncio="Legenda.")


def _client(resp):
    return SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=lambda **kw: resp)))


def test_gerar_devolve_roteiros():
    resp = SimpleNamespace(stop_reason="end_turn", parsed_output=Roteiros(roteiros=[ROTEIRO]))
    assert gerar("produto", [], client=_client(resp)) == [ROTEIRO]


def test_gerar_falha_em_recusa():
    resp = SimpleNamespace(stop_reason="refusal", parsed_output=None)
    with pytest.raises(RuntimeError):
        gerar("produto", [], client=_client(resp))


def test_markdown_junta_fala_numa_linha():
    md = para_markdown("Ficha", [ROTEIRO])
    assert "> Gancho. Meio. Clique." in md
    assert "Legenda." in md
