# Scrapper-Meta

Analisa a Biblioteca de Anúncios da Meta e ranqueia os **produtos vencedores** de
um nicho. Coleta feita com [Scrapling](https://github.com/D4Vinci/Scrapling).

## Leia isto antes de usar

**A Biblioteca de Anúncios não publica visualizações nem cliques de anúncios
comerciais.** Não existe endpoint, oficial ou interno, que devolva esse dado.
O que a Meta expõe é:

| Dado | Disponível? |
| --- | --- |
| Visualizações / impressões | Só para anúncios políticos e de temas sociais, em faixas ("1K–5K") |
| Cliques | Nunca |
| Gasto | Só para anúncios políticos, em faixas |
| Alcance na UE (`euTotalReach`) | Só para campanhas com entrega na União Europeia |
| Duplicações do criativo (`collationCount`) | Sempre |
| Data de início e status | Sempre |

Então o ranking aqui **não** ordena por visualização/clique — ele ordena por
sinais que se correlacionam com investimento. É a mesma lógica que ferramentas
pagas de espionagem de anúncios usam, e a leitura correta é "provável vencedor",
não "vencedor medido".

## Como o score é montado

Anúncios são agrupados por **destino de compra** (URL normalizada: sem UTM,
sem `fbclid`, sem redirecionador `l.facebook.com`, sem `www.`). Isso junta o
mesmo produto anunciado por várias páginas e vários criativos.

Cada produto recebe um score de 0 a 100:

| Sinal | Peso | Por quê |
| --- | --- | --- |
| `variants` — soma de `collationCount` | 0,35 | Anunciante duplica o criativo para escalar orçamento |
| `longevity` — dias no ar do anúncio mais antigo | 0,25 | Anúncio que não vende é desligado em dias |
| `ad_count` — anúncios distintos para o mesmo destino | 0,20 | Volume de teste criativo |
| `active_ratio` — fração ainda ativa | 0,10 | Continua sendo pago hoje |
| `reach` — alcance na UE somado | 0,10 | Único número real de alcance, quando divulgado |

Cada sinal passa por `log1p` e é normalizado (min–max) **dentro do conjunto
coletado** — o score é relativo à busca, não absoluto entre buscas diferentes.
Fora da UE ninguém tem `reach`; nesse caso o peso é redistribuído
proporcionalmente entre os outros quatro sinais.

## Quem está escalando agora (coleta ao vivo)

O endpoint `/ads/library/async/search_ads/` usado por `fetcher.py` **foi removido
pela Meta** — hoje responde 404 mesmo com o desafio anti-bot resolvido. A coleta
que funciona está em `metaads/live.py`: abre a biblioteca num Chrome real,
captura o POST `AdLibrarySearchPaginationQuery` que a própria página emite e
repagina de dentro dela. Assim `doc_id`, `lsd`, `fb_dtsg` e o cookie do desafio
vêm da sessão, e uma rotação desses tokens não quebra a coleta.

```bash
python -m metaads.cli_escalando "colageno" --country BR --pages 6
```

```
60 anuncios coletados · 46 anunciantes · 4 escalando agora

>> 1. Kokeshi  [ESCALANDO]
     6 ativos · 15 copias · 1 criativos · 64 dias no ar
     porque: 15 copias do criativo no ar; 6 anuncios ativos ao mesmo tempo; ha 64 dias no ar
     destino: https://kokeshi.com.br/collections/mais-vendidos
```

Um card por **anunciante** (`page_id`), não por anúncio: um anunciante com 28
criativos no ar aparece uma vez. O corte de "escalando" usa só o que a
biblioteca publica — `ativos`, `copias` (`collation_count`, contado pela própria
Meta), `criativos` distintos e `dias` do anúncio ativo mais antigo:

- **ESCALANDO** — tem volume rodando agora **e** já passou de `DIAS_VALIDACAO`
- **subindo** — volume, mas novo demais para ter sido validado
- **no ar** — antigo, mas sem volume (anúncio esquecido ligado)
- **testando** / **parado** — sem sinal de escala / sem anúncio ativo

Limiares no topo de `metaads/advertisers.py` (`MIN_VARIACOES`, `MIN_ATIVOS`,
`DIAS_VALIDACAO`). `--todos` mostra quem não passou e por quê.

Custa mais que uma API: sobe um Chrome e rola a página, então leva dezenas de
segundos por busca. Vale cachear se for chamar com frequência.

## Instalação

```bash
pip install -r requirements.txt
playwright install chromium   # ou use o Chrome já instalado (channel="chrome")
```

## Uso

```bash
python -m metaads.cli "caneca termica"
python -m metaads.cli "luminaria" --country BR --pages 10 --min-ads 2
python -m metaads.cli "corda de pular" --status all --json ranking.json --csv ranking.csv
```

Saída:

```
6 anuncios coletados, 3 produtos distintos.

#  Score  Produto                     Anuncios  Variacoes  Dias  Ativos  Paginas
-  -----  --------------------------  --------  ---------  ----  ------  -------
1  77.8   Caneca Termica 500ml        3         37         91    2/3     2
2  43.2   Corda de Pular Inteligente  1         3          123   1/1     1
3  20.0   Luminaria Astronauta        1         1          3     1/1     1

=== PRODUTO VENCEDOR ===
Produto   : Caneca Termica 500ml
Score     : 77.8/100
Destino   : https://lojaalpha.com.br/produtos/caneca-termica
Volume    : 3 anuncios / 37 variacoes / 2 ativos
Tempo     : 91 dias no ar (maximo), 39 dias (mediana)
Anunciante: Loja Alpha, Revendedor Beta
Criativos :
  - https://www.facebook.com/ads/library/?id=1001  (24x, 91 dias)
```

Opções: `--country` (padrão `BR`), `--pages` (padrão 5, 30 anúncios por página),
`--status` (`active`/`inactive`/`all`), `--min-ads` (corta destinos com poucos
anúncios), `--top`, `--delay`, `--json`, `--csv`.

## Uso como biblioteca

```python
from metaads import rank_products
from metaads.fetcher import collect_ads

produtos = rank_products(collect_ads("caneca termica", country="BR", max_pages=10), min_ads=2)
vencedor = produtos[0]
print(vencedor.label, vencedor.score, vencedor.total_variants, vencedor.advertisers)
```

## Estrutura

- `metaads/fetcher.py` — pagina o endpoint `/ads/library/async/search_ads/` via Scrapling
- `metaads/parser.py` — normaliza a resposta crua em `Ad`, normaliza URLs de destino
- `metaads/winners.py` — agrupa por produto, pontua e ordena
- `metaads/cli.py` — linha de comando e exportação

## Testes

```bash
python -m pytest tests/ -q
```

28 testes rodam offline sobre um payload de exemplo em
`tests/fixtures/search_response.json` — cobrem parsing, agrupamento,
deduplicação, normalização de URL e o score.

## Limitações conhecidas

- **`fetcher.py` está morto.** A Meta removeu `/ads/library/async/search_ads/`;
  todas as variantes do caminho retornam 404. O bloqueio anterior (HTTP 403) era
  um desafio anti-bot do proxy de borda, resolvível com um POST em
  `/__rd_verify_...` — mas depois dele o que aparece é o 404. Use `live.py`.
- `live.py` precisa de um Chrome real. Não roda em container sem browser.
- Sem login, a biblioteca limita a paginação e pode exigir checkpoint. Evite
  muitas buscas seguidas do mesmo IP.
- Coleta automatizada não é o uso previsto no ToS da Meta, ainda que o dado seja
  público de transparência. A Ad Library API oficial existe para isso.
- `collationCount` conta duplicatas do criativo, não impressões. Um anunciante
  pode duplicar sem escalar orçamento.
- O agrupamento por URL falha quando o anunciante usa link único por anúncio;
  nesses casos o fallback é anunciante + título.
- Anúncios sem link de destino (tráfego para perfil, Messenger) viram um
  "produto" por anunciante + título.
