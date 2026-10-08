# Recuperação automática de vendas no WhatsApp

Funciona sozinho, sem você mexer:

1. A Wiapy avisa este projeto quando alguém gera um Pix, tem o cartão recusado ou abandona o carrinho.
2. O projeto espera **20 minutos** (Pix ou cartão) ou **30 minutos** (carrinho abandonado).
3. Se a pessoa ainda não pagou, ela recebe **uma** mensagem no WhatsApp com o link do checkout.
4. Se pagou nesse meio tempo, não recebe nada. Cada telefone recebe no máximo uma mensagem a cada 48 horas.

O envio usa a **API oficial do WhatsApp** (Cloud API da Meta). Ferramentas que conectam
pelo QR Code são de graça, mas o número costuma ser banido quando manda mensagem para quem
não tem o seu contato salvo.

## Quanto custa

| Serviço | Para quê | Custo |
| --- | --- | --- |
| Vercel | Roda o código | Grátis, a mesma conta da página |
| Upstash QStash | Espera os 20 minutos | Grátis até 1.000 mensagens por dia |
| Upstash Redis | Lembra quem pagou e quem já recebeu mensagem | Grátis no plano free |
| WhatsApp Cloud API | Manda a mensagem | Cobrado por mensagem pela Meta |

A Meta cobra conforme a categoria do modelo de mensagem. "Utilidade" sai por centavos. "Marketing"
custa mais, em torno de R$ 0,30 a R$ 0,40. Confira a tabela atual em
https://developers.facebook.com/docs/whatsapp/pricing. Você só paga pelas mensagens enviadas,
sem mensalidade.

## Passo a passo

### 1. Upstash (Redis e QStash)

1. Crie uma conta grátis em https://console.upstash.com.
2. **Redis:** clique em *Create Database*, escolha a região São Paulo (`sa-east-1`) e o plano Free.
   Na aba *REST API*, copie `UPSTASH_REDIS_REST_URL` e `UPSTASH_REDIS_REST_TOKEN`.
3. **QStash:** abra a aba *QStash* e copie `QSTASH_TOKEN`, `QSTASH_CURRENT_SIGNING_KEY` e
   `QSTASH_NEXT_SIGNING_KEY`. Se a página também mostrar um `QSTASH_URL`, copie esse também.

### 2. WhatsApp Cloud API

Você precisa de um **número só para isso**: um chip novo, ou um número que não esteja
instalado no aplicativo do WhatsApp nem no WhatsApp Business.

1. Entre em https://developers.facebook.com, clique em *Meus apps*, depois em *Criar app*, e
   escolha o tipo *Empresa*. Ligue o app ao seu Gerenciador de Negócios, o mesmo dos anúncios.
2. No app, adicione o produto **WhatsApp**.
3. Em *WhatsApp > Configuração da API*, adicione o seu número e confirme pelo SMS.
   Copie o **Identificação do número de telefone**. Esse é o `WHATSAPP_PHONE_NUMBER_ID`.
4. **Token permanente.** O token que aparece nessa página expira em 24 horas. Para criar um que
   não expira:
   - Abra o *Gerenciador de Negócios*, depois *Configurações*, depois *Usuários do sistema*.
   - Crie um usuário do sistema com função *Admin* e dê a ele acesso ao app e à conta do WhatsApp.
   - Clique em *Gerar token* e marque `whatsapp_business_messaging` e `whatsapp_business_management`.
   - Esse token é o `WHATSAPP_TOKEN`.
5. No *WhatsApp Manager*, adicione uma forma de pagamento. Sem ela, a Meta não envia mensagens.

### 3. Modelo de mensagem

A Meta só deixa mandar a primeira mensagem para um cliente usando um modelo aprovado.

No *WhatsApp Manager*, abra *Modelos de mensagem* e clique em *Criar modelo*:

- **Categoria:** Utilidade. A Meta pode trocar para Marketing quando analisar.
- **Nome:** `recuperar_pedido`. Esse é o `WHATSAPP_TEMPLATE`.
- **Idioma:** Português (BR).
- **Corpo** (pode ajustar o texto, mas mantenha o `{{1}}` e o `{{2}}`):

  ```
  Oi, {{1}}! Vi que seu pedido do Kit Massoterapia Organizada ficou pendente e o pagamento ainda não foi concluído.

  Se quiser finalizar, é só acessar: {{2}}

  Qualquer dúvida, é só responder esta mensagem.
  ```

- **Exemplos:** `{{1}}` = `Maria`, `{{2}}` = `https://pay.wiapy.com/6ac4fb683f18161e1e3aaae8`

`{{1}}` vira o primeiro nome do cliente. `{{2}}` vira o link do mesmo checkout em que ele
estava. A aprovação costuma levar de minutos a algumas horas.

### 4. Subir na Vercel

Este é um **projeto separado da página de vendas**. A página não muda em nada.

```bash
cd recuperacao
vercel --prod
```

Quando a Vercel perguntar *Link to existing project?*, responda **N** e dê um nome novo, por
exemplo `recuperacao-massoterapia`. **Não** ligue ao projeto `massoterapia`.

Depois, abra o projeto novo no painel da Vercel, vá em *Settings*, depois *Environment
Variables*, e cadastre estas variáveis:

| Variável | De onde vem |
| --- | --- |
| `WEBHOOK_SECRET` | Invente uma senha só com letras e números, ex.: `k7Qm2xVb9`. Ela vai no link da Wiapy |
| `UPSTASH_REDIS_REST_URL` | Upstash, passo 1 |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash, passo 1 |
| `QSTASH_TOKEN` | Upstash, passo 1 |
| `QSTASH_CURRENT_SIGNING_KEY` | Upstash, passo 1 |
| `QSTASH_NEXT_SIGNING_KEY` | Upstash, passo 1 |
| `QSTASH_URL` | Só se o Upstash mostrou esse valor |
| `WHATSAPP_TOKEN` | Meta, passo 2 |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta, passo 2 |
| `WHATSAPP_TEMPLATE` | `recuperar_pedido` |

Rode `vercel --prod` de novo para o projeto pegar as variáveis.

### 5. Webhook na Wiapy

Crie um webhook **novo**. O webhook do ntfy continua como está.

- **URL:** `https://recuperacao-massoterapia.vercel.app/api/wiapy?s=SUA_SENHA`
  (troque pelo endereço que a Vercel deu e pela senha do `WEBHOOK_SECRET`)
- **Checkouts:** Todos os checkouts
- **Eventos:** Pagamento pendente, Pagamento aprovado, Cartão recusado e Carrinho Abandonado

O evento **Pagamento aprovado** é obrigatório. É ele que impede o sistema de cobrar quem já pagou.

### 6. Testar

1. Clique em **TESTAR** na Wiapy. O teste manda uma venda paga, e a resposta deve ser `pago`.
2. Faça um teste real: gere um Pix na sua página com **outro** número seu (não o número da API)
   e não pague. Em uns 20 minutos a mensagem deve chegar.
3. Clique no link da mensagem e confira se abre o checkout certo.

Se a mensagem não chegar:

- Na Vercel, abra o projeto, depois *Logs*, e procure erros do WhatsApp. O motivo vem escrito.
- No Upstash, a aba *QStash > Logs* mostra se a chamada saiu e o que voltou.

## Bom saber

- **Limite inicial da Meta:** um número novo manda para até 250 clientes diferentes por dia.
  Esse limite sobe sozinho conforme você usa. Se verificar a empresa no Gerenciador de
  Negócios, ele sobe mais rápido.
- **Respostas:** se o cliente responder, a resposta chega no número da API. Para ler e responder,
  conecte esse número a uma caixa de entrada que aceite a Cloud API. O aplicativo comum do
  WhatsApp não serve.
- **Bloqueios:** se muita gente bloquear ou denunciar a mensagem, a Meta baixa a qualidade do
  número. Por isso o sistema manda uma mensagem só por pessoa. Mantenha o texto educado e útil.
- **Consentimento:** a Meta pede que o cliente tenha aceitado receber mensagens. Uma frase no
  checkout como "Ao informar seu WhatsApp, você aceita receber avisos sobre seu pedido" ajuda.

## Arquivos

| Arquivo | O que faz |
| --- | --- |
| `api/wiapy.js` | Recebe o webhook da Wiapy, marca quem pagou e agenda a recuperação |
| `api/recuperar.js` | Chamado pelo QStash depois da espera. Confere se a pessoa pagou e manda o WhatsApp |
| `lib/servicos.js` | Chamadas ao Redis, ao QStash e ao WhatsApp, além de utilitários de telefone e nome |
| `test/` | Testes. Rode `npm test` (precisa do Node 20 ou mais novo) |
