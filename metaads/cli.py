"""CLI: busca uma palavra-chave na Biblioteca de Anuncios e ranqueia produtos."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from metaads.fetcher import AdLibraryError, collect_ads
from metaads.winners import Product, rank_products

DISCLAIMER = (
    "Nota: a Biblioteca de Anuncios nao publica visualizacoes nem cliques de "
    "anuncios comerciais. O score combina duplicacao de criativo, tempo no ar, "
    "numero de anuncios e alcance na UE (quando divulgado)."
)


def _row(rank: int, product: Product) -> list[str]:
    return [
        str(rank),
        f"{product.score:.1f}",
        product.label[:48] or "(sem titulo)",
        str(product.n_ads),
        str(product.total_variants),
        f"{product.max_days_running():.0f}",
        f"{product.active_ads}/{product.n_ads}",
        str(len(product.advertisers)),
    ]


def _print_table(products: list[Product]) -> None:
    header = ["#", "Score", "Produto", "Anuncios", "Variacoes", "Dias", "Ativos", "Paginas"]
    rows = [header] + [_row(i, p) for i, p in enumerate(products, 1)]
    widths = [max(len(r[c]) for r in rows) for c in range(len(header))]

    for i, row in enumerate(rows):
        print("  ".join(cell.ljust(widths[c]) for c, cell in enumerate(row)).rstrip())
        if i == 0:
            print("  ".join("-" * w for w in widths))


def _print_winner(product: Product) -> None:
    print("\n=== PRODUTO VENCEDOR ===")
    print(f"Produto   : {product.label or '(sem titulo)'}")
    print(f"Score     : {product.score:.1f}/100")
    print(f"Destino   : {product.landing_url or '(sem link)'}")
    print(
        f"Volume    : {product.n_ads} anuncios / {product.total_variants} variacoes"
        f" / {product.active_ads} ativos"
    )
    print(
        f"Tempo     : {product.max_days_running():.0f} dias no ar (maximo),"
        f" {product.median_days_running():.0f} dias (mediana)"
    )
    print(f"Anunciante: {', '.join(product.advertisers[:5]) or '(desconhecido)'}")
    if product.total_eu_reach:
        print(f"Alcance UE: {product.total_eu_reach:,}".replace(",", "."))
    print("Criativos :")
    for ad in product.top_ads():
        print(f"  - {ad.permalink}  ({ad.collation_count}x, {ad.days_running():.0f} dias)")


def _export_json(products: list[Product], path: str) -> None:
    payload = [
        {
            "rank": i,
            "produto": p.label,
            "score": p.score,
            "destino": p.landing_url,
            "anuncios": p.n_ads,
            "variacoes": p.total_variants,
            "ativos": p.active_ads,
            "dias_max": round(p.max_days_running(), 1),
            "dias_mediana": round(p.median_days_running(), 1),
            "anunciantes": p.advertisers,
            "alcance_ue": p.total_eu_reach or None,
            "sinais": {k: round(v, 3) for k, v in p.signals.items()},
            "criativos": [a.permalink for a in p.top_ads()],
        }
        for i, p in enumerate(products, 1)
    ]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _export_csv(products: list[Product], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["rank", "produto", "score", "destino", "anuncios", "variacoes",
             "ativos", "dias_max", "dias_mediana", "anunciantes", "alcance_ue"]
        )
        for i, p in enumerate(products, 1):
            writer.writerow([
                i, p.label, p.score, p.landing_url, p.n_ads, p.total_variants,
                p.active_ads, round(p.max_days_running(), 1),
                round(p.median_days_running(), 1), "; ".join(p.advertisers),
                p.total_eu_reach or "",
            ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metaads",
        description="Ranqueia produtos vencedores na Biblioteca de Anuncios da Meta.",
        epilog=DISCLAIMER,
    )
    parser.add_argument("query", help="palavra-chave ou nicho (ex.: 'caneca termica')")
    parser.add_argument("--country", default="BR", help="codigo do pais (padrao: BR)")
    parser.add_argument("--pages", type=int, default=5, help="paginas a coletar (padrao: 5)")
    parser.add_argument(
        "--status", default="active", choices=["active", "inactive", "all"],
        help="status dos anuncios (padrao: active)",
    )
    parser.add_argument(
        "--min-ads", type=int, default=1,
        help="descarta produtos com menos anuncios que isso (padrao: 1)",
    )
    parser.add_argument("--top", type=int, default=10, help="linhas na tabela (padrao: 10)")
    parser.add_argument("--delay", type=float, default=1.5, help="pausa entre paginas em s")
    parser.add_argument("--json", dest="json_path", help="salva o ranking completo em JSON")
    parser.add_argument("--csv", dest="csv_path", help="salva o ranking completo em CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        ads = collect_ads(
            args.query,
            country=args.country,
            max_pages=args.pages,
            active_status=args.status,
            delay=args.delay,
        )
    except AdLibraryError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1

    products = rank_products(ads, min_ads=args.min_ads)
    if not products:
        print(f"Nenhum produto encontrado para '{args.query}'.", file=sys.stderr)
        return 1

    print(f"{len(ads)} anuncios coletados, {len(products)} produtos distintos.\n")
    _print_table(products[: args.top])
    _print_winner(products[0])

    if args.json_path:
        _export_json(products, args.json_path)
        print(f"\nJSON salvo em {args.json_path}")
    if args.csv_path:
        _export_csv(products, args.csv_path)
        print(f"CSV salvo em {args.csv_path}")

    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
