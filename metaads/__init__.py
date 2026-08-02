"""Analise a Biblioteca de Anuncios da Meta e ranqueie produtos vencedores."""

from metaads.parser import Ad, parse_payload
from metaads.winners import Product, rank_products

__all__ = ["Ad", "Product", "parse_payload", "rank_products"]
