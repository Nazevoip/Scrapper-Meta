# Oferta: Ficha de Anamnese para Massoterapia

| Arquivo | O que é |
| --- | --- |
| `ficha-anamnese-massoterapia.pdf` | O produto. PDF A4 editável com 2 páginas, 8 seções e 70 campos |
| `gerar_ficha.py` | Gera o PDF de novo, caso você queira mudar algum texto (`python gerar_ficha.py`) |
| `gerar_imagens.py` | Gera os mockups da página a partir do PDF (rode depois de mudar a ficha) |
| `pagina/` | Página de vendas: `index.html` e a pasta `assets/` com os mockups |

## Colocar no ar em 4 passos

1. **Checkout:** crie o produto no Kiwify ou na Hotmart, suba o PDF como entregável, defina o preço de R$ 19,90 e copie o link do checkout.
2. **Página:** abra `pagina/index.html` num editor de texto e troque:
   - O bloco `CONFIG`, perto do fim do arquivo: link do checkout, seu nome ou razão social com CNPJ ou CPF, e-mail de suporte e links de privacidade e termos. Cada linha está marcada com `TROQUE`.
   - O código do Pixel da Meta, colado no `<head>` onde indica o comentário. A página já dispara `ViewContent` quando a oferta aparece e `InitiateCheckout` no clique do botão.
3. **Publicar:** arraste a pasta `pagina/` em https://app.netlify.com/drop. É grátis e te dá um link na hora.
4. **Testar:** abra o link no celular, clique em cada botão e faça uma compra de teste.

## O que a página não tem, de propósito

- **Depoimento.** Só entra quando você tiver depoimentos reais de clientes.
- **Contador regressivo.** O do modelo reiniciava a cada visita, então era escassez falsa.
- **Preço "de R$ 97 por R$ 19,90".** Esse preço de referência nunca existiu.
- **Promessa de resultado de saúde.**

Isso mantém a página dentro das regras de anúncio da Meta e do Código de Defesa do Consumidor.
