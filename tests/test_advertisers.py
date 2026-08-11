from datetime import datetime, timedelta, timezone

from metaads.advertisers import (
    DIAS_VALIDACAO,
    MIN_ATIVOS,
    MIN_VARIACOES,
    group_by_advertiser,
    quem_esta_escalando,
)
from metaads.parser import Ad

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def mk(aid, page_id="p1", nome="Loja", coll=1, dias=30, ativo=True, link="", body="copy"):
    return Ad(
        archive_id=aid, page_id=page_id, page_name=nome, title="t", body=body,
        caption="", cta_text="", link_url=link, display_format="image",
        start_date=NOW - timedelta(days=dias), is_active=ativo, collation_count=coll,
    )


def test_agrupa_por_page_id_e_deduplica_archive_id():
    ads = [mk("1"), mk("1"), mk("2"), mk("3", page_id="p2", nome="Outra")]
    grupos = {g.page_id: g for g in group_by_advertiser(ads)}
    assert len(grupos) == 2
    assert grupos["p1"].n_ativos == 2  # o archive_id repetido nao conta duas vezes
    assert grupos["p2"].n_ativos == 1


def test_28_anuncios_do_mesmo_anunciante_viram_um_card():
    ads = [mk(str(i), coll=1, dias=60) for i in range(28)]
    grupos = group_by_advertiser(ads)
    assert len(grupos) == 1
    assert grupos[0].n_ativos == 28


def test_escala_por_variacoes():
    ads = [mk("1", coll=MIN_VARIACOES, dias=DIAS_VALIDACAO + 1)]
    escalando, rotulo, motivos = group_by_advertiser(ads)[0].status(NOW)
    assert escalando and rotulo == "ESCALANDO"
    assert any("copias" in m for m in motivos)


def test_escala_por_numero_de_ativos():
    ads = [mk(str(i), coll=1, dias=DIAS_VALIDACAO + 1) for i in range(MIN_ATIVOS)]
    escalando, _, motivos = group_by_advertiser(ads)[0].status(NOW)
    assert escalando
    assert any("ativos" in m for m in motivos)


def test_volume_sem_tempo_e_subindo_nao_escalando():
    ads = [mk(str(i), coll=9, dias=1) for i in range(MIN_ATIVOS)]
    escalando, rotulo, motivos = group_by_advertiser(ads)[0].status(NOW)
    assert not escalando and rotulo == "subindo"
    assert any("min" in m for m in motivos)


def test_tempo_sem_volume_nao_escala():
    escalando, rotulo, _ = group_by_advertiser([mk("1", coll=1, dias=400)])[0].status(NOW)
    assert not escalando and rotulo == "no ar"


def test_anunciante_sem_anuncio_ativo_esta_parado():
    escalando, rotulo, _ = group_by_advertiser([mk("1", ativo=False, coll=50)])[0].status(NOW)
    assert not escalando and rotulo == "parado"


def test_inativos_nao_contam_como_volume():
    ads = [mk("1", coll=1, dias=30)] + [mk(str(i), coll=20, ativo=False) for i in range(2, 6)]
    g = group_by_advertiser(ads)[0]
    assert g.n_ativos == 1 and g.variacoes == 1
    assert not g.status(NOW)[0]


def test_quem_esta_escalando_filtra_e_ordena():
    ads = (
        [mk(f"a{i}", page_id="forte", nome="Forte", coll=10, dias=90) for i in range(6)]
        + [mk(f"b{i}", page_id="medio", nome="Medio", coll=1, dias=30) for i in range(MIN_ATIVOS)]
        + [mk("c1", page_id="fraco", nome="Fraco", coll=1, dias=2)]
    )
    resultado = quem_esta_escalando(ads, now=NOW)
    assert [g.name for g in resultado] == ["Forte", "Medio"]  # "Fraco" fica de fora

    todos = quem_esta_escalando(ads, now=NOW, incluir_todos=True)
    assert len(todos) == 3


def test_criativos_distintos_e_destinos():
    ads = [
        mk("1", coll=1, dias=30, body="copy A", link="https://x.com/p?utm_source=fb"),
        mk("2", coll=1, dias=30, body="copy A", link="https://www.x.com/p"),
        mk("3", coll=1, dias=30, body="copy B", link="https://y.com/z"),
    ]
    g = group_by_advertiser(ads)[0]
    assert g.n_criativos == 2                      # copy A aparece duas vezes
    assert g.destinos == ["https://x.com/p", "https://y.com/z"]  # UTM e www normalizados
