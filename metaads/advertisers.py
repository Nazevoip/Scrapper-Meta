"""Agrupa por ANUNCIANTE e responde uma pergunta so: quem esta escalando agora.

`winners.py` agrupa por produto (URL de destino) e ranqueia dentro do lote. Aqui
o eixo e outro: um card por anunciante, e um corte binario de "esta escalando
agora" baseado so no que a biblioteca publica de fato.

Sinais usados (todos verificaveis na Biblioteca de Anuncios):

    ativos      anuncios distintos ATIVOS do anunciante nesta busca
    variacoes   soma do collation_count — quantas copias do criativo a propria
                Meta conta rodando agora
    dias        dias no ar do anuncio ativo mais antigo
    criativos   textos de anuncio distintos (largura do teste criativo)

Um anunciante escala quando ha volume rodando AGORA e prova de que aquilo ja
sobreviveu ao teste. Volume sem tempo e lancamento; tempo sem volume e um
anuncio esquecido no ar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from metaads.parser import Ad, normalize_link

# Um anuncio precisa passar disto para contar como "no ar ha tempo suficiente
# para ter sido validado". Abaixo disso ainda e teste.
DIAS_VALIDACAO = 7

# Portas de escala: qualquer uma delas, combinada com validacao, ja indica
# investimento ativo. Sao propositalmente baixas — o Brasil roda mais enxuto
# que a gringa, e o objetivo e nao perder anunciante escalando.
MIN_VARIACOES = 5   # a Meta conta 5+ copias do mesmo criativo no ar
MIN_ATIVOS = 4      # 4+ anuncios distintos ativos ao mesmo tempo


@dataclass
class Advertiser:
    page_id: str
    name: str
    ads: list[Ad] = field(default_factory=list)

    @property
    def ativos(self) -> list[Ad]:
        return [a for a in self.ads if a.is_active]

    @property
    def n_ativos(self) -> int:
        return len(self.ativos)

    @property
    def variacoes(self) -> int:
        """Copias do criativo que a Meta conta rodando (so entre os ativos)."""
        return sum(a.collation_count for a in self.ativos)

    @property
    def n_criativos(self) -> int:
        return len({(a.body or a.title or a.archive_id)[:120] for a in self.ativos})

    @property
    def destinos(self) -> list[str]:
        return sorted({normalize_link(a.link_url) for a in self.ativos if a.link_url})

    def dias(self, now: datetime | None = None) -> float:
        """Dias no ar do anuncio ativo mais antigo."""
        return max((a.days_running(now) for a in self.ativos), default=0.0)

    def top_ad(self) -> Ad | None:
        """Anuncio mais representativo: mais copiado, depois mais antigo."""
        return max(self.ativos, key=lambda a: (a.collation_count, a.days_running()),
                   default=None)

    # -- veredito ---------------------------------------------------------- #

    def status(self, now: datetime | None = None) -> tuple[bool, str, list[str]]:
        """(escalando, rotulo, motivos). Motivos sao sempre numeros verificaveis."""
        if not self.ativos:
            return False, "parado", ["nenhum anuncio ativo agora"]

        dias = self.dias(now)
        validado = dias >= DIAS_VALIDACAO
        provas = []
        if self.variacoes >= MIN_VARIACOES:
            provas.append(f"{self.variacoes} copias do criativo no ar")
        if self.n_ativos >= MIN_ATIVOS:
            provas.append(f"{self.n_ativos} anuncios ativos ao mesmo tempo")

        if provas and validado:
            return True, "ESCALANDO", provas + [f"ha {dias:.0f} dias no ar"]
        if provas and not validado:
            return False, "subindo", provas + [
                f"so {dias:.0f} dias no ar (min {DIAS_VALIDACAO} para confirmar)"]
        if validado:
            return False, "no ar", [
                f"{dias:.0f} dias no ar, mas so {self.n_ativos} anuncio(s) "
                f"e {self.variacoes} copia(s)"]
        return False, "testando", [
            f"{self.n_ativos} anuncio(s), {dias:.0f} dias — sem sinal de escala"]

    def forca(self, now: datetime | None = None) -> float:
        """Ordena os ESCALANDO entre si. Volume atual pesa mais que idade."""
        return (self.variacoes * 3.0
                + self.n_ativos * 2.0
                + min(self.dias(now), 180) * 0.15
                + self.n_criativos)


def group_by_advertiser(ads: list[Ad]) -> list[Advertiser]:
    """Um Advertiser por page_id, deduplicando anuncios por archive_id."""
    grupos: dict[str, Advertiser] = {}
    vistos: set[str] = set()

    for ad in ads:
        if ad.archive_id in vistos:
            continue
        vistos.add(ad.archive_id)

        chave = ad.page_id or ad.page_name or ad.archive_id
        grupo = grupos.get(chave)
        if grupo is None:
            grupo = Advertiser(page_id=ad.page_id, name=ad.page_name or "(sem nome)")
            grupos[chave] = grupo
        grupo.ads.append(ad)

    return list(grupos.values())


def quem_esta_escalando(
    ads: list[Ad], now: datetime | None = None, incluir_todos: bool = False
) -> list[Advertiser]:
    """Anunciantes ordenados por forca. Por padrao devolve so os ESCALANDO."""
    now = now or datetime.now(timezone.utc)
    grupos = group_by_advertiser(ads)
    if not incluir_todos:
        grupos = [g for g in grupos if g.status(now)[0]]
    return sorted(grupos, key=lambda g: g.forca(now), reverse=True)
