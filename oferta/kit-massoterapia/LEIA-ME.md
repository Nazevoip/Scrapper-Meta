# Kit Massoterapia Organizada

A página de vendas segue o layout do modelo enviado, com o produto trocado para
massoterapia. As fichas e os mockups seguem as cores da página.

| Arquivo | O que é |
| --- | --- |
| `pagina/` | Página de vendas: `index.html` e a pasta `assets/` com as imagens. Suba essa pasta inteira |
| `fichas/` | As 4 fichas que já existem, em PDF editável |
| `gerar_fichas.py` | Gera as fichas de novo (`python gerar_fichas.py`) |
| `gerar_imagens.py` | Gera os mockups, as prévias e as capas dos bônus a partir das fichas |

## O produto

A página vende dois planos e uma oferta de upgrade, com os mesmos preços do modelo.
O que está marcado com ✅ já existe. O resto você precisa criar antes de vender,
porque a página promete esses itens.

### Kit Massoterapia Essencial: R$ 10,00
Fichas prontas para usar e imprimir, sem edição no Canva.

| Item da página | Material | Status |
| --- | --- | --- |
| Cadastro, anamnese e avaliação de clientes | Ficha de Anamnese (2 páginas) | ✅ `fichas/ficha-anamnese.pdf` |
| Registro de atendimentos e evolução | Evolução e Acompanhamento | ✅ `fichas/evolucao-acompanhamento.pdf` |
| Controle de sessões e pacotes | Controle de Sessões e Pacotes | ✅ `fichas/controle-sessoes-pacotes.pdf` |
| Agenda, faltas e retornos | Agenda semanal com faltas, reagendamentos e próximos retornos | Criar |
| Pagamentos e valores pendentes | Controle de recebimentos por cliente | Criar |

### Kit Massoterapia Organizada (Completo): R$ 27,90, ou R$ 19,90 no upgrade
Tudo do Essencial, mais:

| Item da página | Material | Status |
| --- | --- | --- |
| Financeiro completo, caixa e fechamento mensal | Fechamento Mensal | ✅ `fichas/fechamento-mensal.pdf` |
| | Caixa diário | Criar |
| Despesas, contas a receber e metas de faturamento | Receitas e despesas, contas a receber, metas | Criar |
| Estoque, validade, fornecedores e compras | Estoque de óleos e cremes com validade, fornecedores, lista de compras | Criar |
| Materiais, equipamentos e gestão do espaço | Maca, equipamentos, manutenção e limpeza do espaço | Criar |
| Clientes inativos, indicações e acompanhamento | Lista de clientes inativos e controle de indicações | Criar |
| 100% editável no Canva | Versão de todas as fichas em Canva (link de modelo) | Criar |

**Os 3 bônus (só no Completo):**
- **Pack de Mimos para Clientes:** cartão fidelidade, vale-massagem para presente e cupom de indicação, prontos para imprimir.
- **Kit Agenda Cheia no WhatsApp:** 50 respostas prontas pra dúvidas e pedidos de preço de massagem.
- **Calculadora de Preço & Lucro:** planilha que calcula o custo da sessão, a margem e o preço de massagens e pacotes.

Posso criar qualquer um desses itens. É só pedir.

## Antes de publicar: o bloco `CONFIG` do `index.html`

Fica perto do fim do arquivo, e cada linha a trocar está marcada com `TROQUE`:

- **Os 3 links de checkout:** Essencial a R$ 10, Completo a R$ 27,90 e upgrade a R$ 19,90.
- **`fimDaCondicao`:** a data em que a condição especial acaba. O cronômetro conta até ela. Depois dessa data, o preço tem que subir de verdade para o valor do "De" (`anchorPrice...`).
- **`testimonialsEnabled`:** começa em `false`. A seção de depoimentos está na página com a mesma estrutura de conversas de WhatsApp. Troque os `[colchetes]` por conversas reais de clientes, com autorização, e mude para `true`.
- **Links de privacidade, termos e suporte.**

Fora do `CONFIG`, troque também:
- **Pixel da Meta:** `SEU_PIXEL_ID` aparece em 2 lugares, no `<head>` e no `<noscript>`.
- **LowTrack:** `SEU_ID_LOWTRACK`. Se não usar LowTrack, pode deixar como está.
- **Vídeo da seção "Veja por dentro":** `SEU_VIDEO_WISTIA`, no player do Wistia. Grave um vídeo de tela mostrando as fichas e suba no Wistia.

## Publicar

1. Crie os 3 produtos (ou ofertas) no checkout e cole os links.
2. Arraste a pasta `pagina/` em https://app.netlify.com/drop.
3. Abra no celular, teste os 3 botões (o Essencial abre a janela de upgrade) e faça uma compra de teste.
