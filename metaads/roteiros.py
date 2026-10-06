"""Roteiros de video para avatar de IA, a partir de quem esta escalando no nicho.

Pega a copy dos anunciantes com mais volume no ar e pede ao Claude roteiros
NOVOS para o seu produto. Os concorrentes entram so como referencia de angulo e
gancho — o texto deles nao e copiado.
"""

from __future__ import annotations

from datetime import datetime

import anthropic
from pydantic import BaseModel

from metaads.advertisers import Advertiser

MODEL = "claude-opus-5-5"

# Corta textos longos de concorrente: o gancho esta no comeco, e o resto so
# encarece o pedido.
MAX_CHARS_REFERENCIA = 400

SYSTEM = """Voce e copywriter de resposta direta no Brasil e escreve roteiros \
curtos de video para anuncios no Facebook e Instagram. O video sera falado por \
um avatar de IA, que le o texto literalmente.

Regras do roteiro:
- Portugues do Brasil falado, natural, frases curtas. Sem emoji, hashtag, \
marcacao de cena ou instrucao entre parenteses: tudo que voce escrever sera lido \
em voz alta.
- Gancho com no maximo 12 palavras. Roteiro completo com 70 a 90 palavras \
(cerca de 30 segundos).
- Cada roteiro usa um angulo diferente (dor, desejo, erro comum, comparacao, \
curiosidade, objecao...).

Regras de honestidade (o anuncio nao pode enganar):
- O avatar e apresentador. Pode falar em primeira pessoa, mas nunca diz que \
tem profissao, formacao ou experiencia propria com o produto, e nunca da \
depoimento de resultado.
- Nada de numeros, estudos, clientes ou resultados inventados. Nada de promessa \
de cura ou resultado de saude.
- Os anuncios de concorrentes sao so referencia de angulo e estrutura. Nao \
copie frases deles nem cite o nome deles."""


class Roteiro(BaseModel):
    angulo: str
    gancho: str
    desenvolvimento: str
    cta: str
    texto_do_anuncio: str


class Roteiros(BaseModel):
    roteiros: list[Roteiro]


def referencias(
    anunciantes: list[Advertiser],
    now: datetime | None = None,
    max_anunciantes: int = 5,
    por_anunciante: int = 3,
) -> list[dict]:
    """Copy dos anuncios ativos mais copiados de cada anunciante, sem repetir."""
    refs = []
    for g in anunciantes:
        if len(refs) == max_anunciantes:
            break
        ativos = sorted(g.ativos, key=lambda a: (a.collation_count, a.days_running(now)),
                        reverse=True)
        textos: list[str] = []
        for ad in ativos:
            texto = " ".join((ad.body or ad.title or "").split())[:MAX_CHARS_REFERENCIA]
            if texto and texto not in textos:
                textos.append(texto)
            if len(textos) == por_anunciante:
                break
        if textos:
            refs.append({
                "anunciante": g.name,
                "status": g.status(now)[1],
                "dias": round(g.dias(now)),
                "copias": g.variacoes,
                "textos": textos,
            })
    return refs


def montar_pedido(produto: str, refs: list[dict], quantidade: int) -> str:
    blocos = []
    for r in refs:
        textos = "\n".join(f"  - {t}" for t in r["textos"])
        blocos.append(f"* {r['anunciante']} ({r['status']}, {r['dias']} dias no ar, "
                      f"{r['copias']} copias):\n{textos}")
    return (
        f"Meu produto: {produto}\n\n"
        f"Anuncios de concorrentes que estao no ar agora neste nicho:\n\n"
        + "\n\n".join(blocos)
        + f"\n\nEscreva {quantidade} roteiros para o MEU produto. "
        "Em texto_do_anuncio, escreva a legenda que vai acima do video "
        "(2 a 4 linhas)."
    )


def gerar(
    produto: str, refs: list[dict], quantidade: int = 10,
    client: anthropic.Anthropic | None = None,
) -> list[Roteiro]:
    client = client or anthropic.Anthropic()
    resp = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        # Se o modelo recusar, a API tenta de novo num modelo alternativo.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        messages=[{"role": "user", "content": montar_pedido(produto, refs, quantidade)}],
        output_format=Roteiros,
    )
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError(f"o modelo nao gerou os roteiros (stop_reason={resp.stop_reason})")
    return resp.parsed_output.roteiros


def para_markdown(produto: str, roteiros: list[Roteiro]) -> str:
    linhas = [f"# Roteiros — {produto}", ""]
    for i, r in enumerate(roteiros, 1):
        linhas += [
            f"## {i}. {r.angulo}", "",
            "**Fala do avatar** (cole inteiro na ferramenta de avatar):", "",
            f"> {r.gancho} {r.desenvolvimento} {r.cta}", "",
            "**Legenda do anuncio:**", "",
            r.texto_do_anuncio, "",
        ]
    return "\n".join(linhas)
