"""CLI: roteiros para avatar de IA a partir de quem esta escalando no nicho.

    python -m metaads.cli_roteiros "massoterapia" \\
        --produto "Ficha de anamnese para massoterapeutas, PDF editavel, R$ 19,90"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import anthropic

from metaads.advertisers import quem_esta_escalando
from metaads.live import CollectError, collect_raw
from metaads.parser import parse_ad
from metaads.roteiros import gerar, para_markdown, referencias


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Gera roteiros para avatar de IA.")
    ap.add_argument("query", help="termo de busca do nicho na Biblioteca de Anuncios")
    ap.add_argument("--produto", required=True,
                    help="o que voce vende, para quem e por quanto")
    ap.add_argument("--country", default="BR")
    ap.add_argument("--pages", type=int, default=5, help="paginas de 30 anuncios (padrao 5)")
    ap.add_argument("--quantidade", type=int, default=10, help="roteiros (padrao 10)")
    ap.add_argument("--saida", default="roteiros.md")
    ap.add_argument("--mostrar-browser", action="store_true", help="roda o Chrome visivel")
    args = ap.parse_args(argv)

    try:
        brutos = collect_raw(args.query, country=args.country, max_pages=args.pages,
                             headless=not args.mostrar_browser)
    except CollectError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    ads = [ad for raw in brutos if (ad := parse_ad(raw))]

    # Quem esta escalando vem primeiro; se ninguem passou no corte, os
    # anunciantes com mais volume ainda servem de referencia.
    now = datetime.now(timezone.utc)
    todos = quem_esta_escalando(ads, now=now, incluir_todos=True)
    todos.sort(key=lambda g: g.status(now)[0], reverse=True)
    refs = referencias(todos, now=now)
    if not refs:
        print("nenhum anuncio ativo com texto nesta busca. Tente outro termo.",
              file=sys.stderr)
        return 1

    print(f"{len(ads)} anuncios coletados. Referencias:")
    for r in refs:
        print(f"  - {r['anunciante']} [{r['status']}] {r['dias']} dias, {r['copias']} copias")
    print(f"gerando {args.quantidade} roteiros...")

    try:
        roteiros = gerar(args.produto, refs, args.quantidade)
    except (anthropic.APIError, RuntimeError) as exc:
        print(f"erro ao gerar roteiros: {exc}", file=sys.stderr)
        return 1

    with open(args.saida, "w", encoding="utf-8") as fh:
        fh.write(para_markdown(args.produto, roteiros))
    print(f"{len(roteiros)} roteiros salvos em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
