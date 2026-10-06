# Oferta: Ficha de Anamnese para Massoterapia

| Arquivo | O que é |
| --- | --- |
| `ficha-anamnese-massoterapia.pdf` | O produto. PDF A4 editável com 2 páginas, 8 seções e 70 campos |
| `gerar_ficha.py` | Gera o PDF de novo, caso você queira mudar algum texto (`python gerar_ficha.py`) |
| `pagina/` | Página de vendas: `index.html` e as duas imagens de prévia |

## Colocar no ar em 4 passos

1. **Checkout:** crie o produto no Kiwify ou na Hotmart, suba o PDF como entregável, defina o preço de R$ 19,90 e copie o link do checkout.
2. **Página:** abra `pagina/index.html` num editor de texto e troque estas 3 coisas:
   - O `CHECKOUT` no fim do arquivo, pelo link do passo 1.
   - O rodapé, com seu nome ou razão social, CNPJ ou CPF e e-mail.
   - O código do Pixel da Meta, colado no `<head>` onde indica o comentário.
3. **Publicar:** arraste a pasta `pagina/` em https://app.netlify.com/drop. É grátis e te dá um link na hora.
4. **Testar:** abra o link no celular, clique em cada botão e faça uma compra de teste.

## O que a página não tem, de propósito

- **Depoimento.** Só entra quando você tiver depoimentos reais de clientes.
- **Contador regressivo ou "últimas unidades".** É escassez falsa.
- **Promessa de resultado de saúde.**

Isso mantém a página dentro das regras de anúncio da Meta e do Código de Defesa do Consumidor.
