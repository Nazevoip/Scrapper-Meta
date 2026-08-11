"""CLI: quem esta escalando agora num nicho. Um card por anunciante.

    python -m metaads.cli_escalando "colageno" --country BR --pages 5
    python -m metaads.cli_escalando "encapsulado" --todos --json saida.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from metaads.advertisers import quem_esta_escalando
from metaads.live import CollectError, collect_raw
from metaads.parser import parse_ad


def _coletar(args) -> list:
    brutos = collect_raw(args.query, country=args.country, max_pages=args.pages,
                         active_status=args.status, headless=not args.mostrar_browser)
    return [ad for raw in brutos if (ad := parse_ad(raw))]


def main(argv=None) -> int:
    # Consoles do Windows abrem em cp1252 e estouram no primeiro acento.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Quem esta escalando agora na Biblioteca de Anuncios.")
    ap.add_argument("query")
    ap.add_argument("--country", default="BR")
    ap.add_argument("--pages", type=int, default=5, help="paginas de 30 anuncios (padrao 5)")
    ap.add_argument("--status", default="active", choices=["active", "inactive", "all"])
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--todos", action="store_true",
                    help="mostra tambem quem nao esta escalando, com o motivo")
    ap.add_argument("--mostrar-browser", action="store_true", help="roda o Chrome visivel")
    ap.add_argument("--json", dest="json_out", help="salva a saida em JSON")
    args = ap.parse_args(argv)

    try:
        ads = _coletar(args)
    except CollectError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1

    if not ads:
        print("nenhum anuncio coletado.")
        return 1

    now = datetime.now(timezone.utc)
    todos = quem_esta_escalando(ads, now=now, incluir_todos=True)
    escalando = [g for g in todos if g.status(now)[0]]

    print(f"\n{len(ads)} anuncios coletados · {len(todos)} anunciantes · "
          f"{len(escalando)} escalando agora\n")

    mostrar = todos if args.todos else escalando
    if not mostrar:
        print("Ninguem passou no corte de escala nesta busca.")
        print("Tente --pages maior, outro termo, ou --todos para ver os motivos.")
        return 0

    for i, g in enumerate(mostrar[: args.top], 1):
        ok, rotulo, motivos = g.status(now)
        marca = ">>" if ok else "  "
        print(f"{marca} {i}. {g.name}  [{rotulo}]")
        print(f"     {g.n_ativos} ativos · {g.variacoes} copias · "
              f"{g.n_criativos} criativos · {g.dias(now):.0f} dias no ar")
        print(f"     porque: {'; '.join(motivos)}")
        for destino in g.destinos[:2]:
            print(f"     destino: {destino}")
        top = g.top_ad()
        if top:
            texto = " ".join((top.body or top.title or "").split())[:88]
            print(f"     criativo: {texto}")
            print(f"     {top.permalink}")
        print()

    if args.json_out:
        payload = [{
            "anunciante": g.name, "page_id": g.page_id,
            "escalando": g.status(now)[0], "status": g.status(now)[1],
            "motivos": g.status(now)[2], "ativos": g.n_ativos,
            "variacoes": g.variacoes, "criativos": g.n_criativos,
            "dias": round(g.dias(now), 1), "destinos": g.destinos,
            "forca": round(g.forca(now), 1),
        } for g in mostrar]
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        print(f"salvo em {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
