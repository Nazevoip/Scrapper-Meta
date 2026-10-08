import assert from "node:assert/strict";
import { createHash, createHmac } from "node:crypto";
import { beforeEach, describe, it } from "node:test";

import { POST as recuperar } from "../api/recuperar.js";
import { POST as wiapy } from "../api/wiapy.js";
import { normalizarTelefone, primeiroNome } from "../lib/servicos.js";

Object.assign(process.env, {
  WEBHOOK_SECRET: "segredo123",
  UPSTASH_REDIS_REST_URL: "https://redis.teste",
  UPSTASH_REDIS_REST_TOKEN: "tok-redis",
  QSTASH_TOKEN: "tok-qstash",
  QSTASH_CURRENT_SIGNING_KEY: "chave-atual",
  QSTASH_NEXT_SIGNING_KEY: "chave-proxima",
  WHATSAPP_TOKEN: "tok-wa",
  WHATSAPP_PHONE_NUMBER_ID: "123456",
  WHATSAPP_TEMPLATE: "recuperar_pedido",
});

// Redis em memoria + registro das chamadas de rede.
let banco, chamadas, falharWhatsApp;
beforeEach(() => {
  banco = new Map();
  chamadas = [];
  falharWhatsApp = false;
  globalThis.fetch = async (url, opcoes) => {
    const corpo = JSON.parse(opcoes.body);
    chamadas.push({ url: String(url), headers: opcoes.headers, corpo });
    if (url === process.env.UPSTASH_REDIS_REST_URL) {
      const [cmd, chave, valor, , , nx] = corpo;
      let result = null;
      if (cmd === "GET") result = banco.get(chave) ?? null;
      if (cmd === "DEL") result = Number(banco.delete(chave));
      if (cmd === "SET" && !(nx === "NX" && banco.has(chave))) {
        banco.set(chave, valor);
        result = "OK";
      }
      return Response.json({ result });
    }
    if (String(url).startsWith("https://graph.facebook.com") && falharWhatsApp) {
      return new Response("erro", { status: 400 });
    }
    return Response.json({ ok: true });
  };
});

const BASE = "https://recuperacao.vercel.app";

function webhook(dados, segredo = "segredo123") {
  return wiapy(new Request(`${BASE}/api/wiapy?s=${segredo}`, {
    method: "POST",
    body: JSON.stringify(dados),
  }));
}

function pedido(status) {
  return {
    ...(status && { payment: { id: "p1", status, amount: 2790, payment_method: "pix" } }),
    customer: { name: "MARIA da Silva", mobile_phone: "(11) 98765-4321" },
    checkout: { id: "6ac4fb683f18161e1e3aaae8" },
  };
}

function assinar(corpo, chave = "chave-atual", extra = {}) {
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString("base64url");
  const agora = Math.floor(Date.now() / 1000);
  const carga = b64({
    iss: "Upstash", sub: `${BASE}/api/recuperar`, nbf: agora, exp: agora + 300,
    body: createHash("sha256").update(corpo).digest("base64url"), ...extra,
  });
  const cab = b64({ alg: "HS256", typ: "JWT" });
  const assinatura = createHmac("sha256", chave).update(`${cab}.${carga}`).digest("base64url");
  return `${cab}.${carga}.${assinatura}`;
}

function chamadaQStash(corpo, assinatura = assinar(corpo)) {
  return recuperar(new Request(`${BASE}/api/recuperar`, {
    method: "POST",
    headers: { "Upstash-Signature": assinatura },
    body: corpo,
  }));
}

const MSG = JSON.stringify({ telefone: "5511987654321", nome: "Maria", link: "https://pay.wiapy.com/x" });
const enviosWhatsApp = () => chamadas.filter((c) => c.url.startsWith("https://graph.facebook.com"));

describe("auxiliares", () => {
  it("normaliza telefone brasileiro", () => {
    assert.equal(normalizarTelefone("(11) 98765-4321"), "5511987654321");
    assert.equal(normalizarTelefone("+55 11 3456-7890"), "551134567890");
    assert.equal(normalizarTelefone("123"), null);
    assert.equal(normalizarTelefone(undefined), null);
  });

  it("pega o primeiro nome", () => {
    assert.equal(primeiroNome("MARIA da Silva"), "Maria");
    assert.equal(primeiroNome(""), "cliente");
  });
});

describe("api/wiapy", () => {
  it("recusa segredo errado", async () => {
    const r = await webhook(pedido("pending"), "errado");
    assert.equal(r.status, 401);
    assert.equal(chamadas.length, 0);
  });

  it("pagamento aprovado marca o telefone como pago", async () => {
    const r = await webhook(pedido("paid"));
    assert.equal(await r.text(), "pago");
    assert.equal(banco.get("pago:5511987654321"), "1");
    assert.deepEqual(chamadas[0].corpo, ["SET", "pago:5511987654321", "1", "EX", "86400"]);
  });

  it("pix pendente agenda a recuperacao em 20 minutos", async () => {
    const r = await webhook(pedido("pending"));
    assert.equal(await r.text(), "agendado");
    assert.equal(chamadas.length, 1);
    const [c] = chamadas;
    assert.equal(c.url, `https://qstash.upstash.io/v2/publish/${BASE}/api/recuperar`);
    assert.equal(c.headers["Upstash-Delay"], "20m");
    assert.equal(c.headers.Authorization, "Bearer tok-qstash");
    assert.deepEqual(c.corpo, {
      telefone: "5511987654321",
      nome: "Maria",
      link: "https://pay.wiapy.com/6ac4fb683f18161e1e3aaae8",
    });
  });

  it("carrinho abandonado (sem pagamento) agenda em 30 minutos", async () => {
    await webhook(pedido(null));
    assert.equal(chamadas[0].headers["Upstash-Delay"], "30m");
  });

  it("estorno e chargeback sao ignorados", async () => {
    for (const status of ["refunded", "chargeback"]) {
      assert.equal(await (await webhook(pedido(status))).text(), "ignorado");
    }
    assert.equal(chamadas.length, 0);
  });

  it("sem telefone nao faz nada", async () => {
    const r = await webhook({ payment: { status: "pending" }, customer: { name: "Ana" } });
    assert.equal(await r.text(), "sem telefone");
    assert.equal(chamadas.length, 0);
  });
});

describe("api/recuperar", () => {
  it("recusa assinatura invalida", async () => {
    for (const assinatura of [assinar(MSG, "chave-errada"), assinar("outro corpo"), assinar(MSG, "chave-atual", { exp: 1 }), ""]) {
      assert.equal((await chamadaQStash(MSG, assinatura)).status, 401);
    }
    assert.equal(chamadas.length, 0);
  });

  it("aceita a chave proxima do QStash", async () => {
    assert.equal(await (await chamadaQStash(MSG, assinar(MSG, "chave-proxima"))).text(), "enviado");
  });

  it("manda o modelo no WhatsApp e marca como enviado", async () => {
    const r = await chamadaQStash(MSG);
    assert.equal(await r.text(), "enviado");
    const [wa] = enviosWhatsApp();
    assert.equal(wa.url, "https://graph.facebook.com/v23.0/123456/messages");
    assert.equal(wa.headers.Authorization, "Bearer tok-wa");
    assert.deepEqual(wa.corpo, {
      messaging_product: "whatsapp",
      to: "5511987654321",
      type: "template",
      template: {
        name: "recuperar_pedido",
        language: { code: "pt_BR" },
        components: [{
          type: "body",
          parameters: [{ type: "text", text: "Maria" }, { type: "text", text: "https://pay.wiapy.com/x" }],
        }],
      },
    });
    assert.equal(banco.get("enviado:5511987654321"), "1");
  });

  it("nao manda se o cliente ja pagou", async () => {
    await webhook(pedido("paid"));
    assert.equal(await (await chamadaQStash(MSG)).text(), "ja pagou");
    assert.equal(enviosWhatsApp().length, 0);
  });

  it("manda uma vez so por telefone", async () => {
    await chamadaQStash(MSG);
    assert.equal(await (await chamadaQStash(MSG)).text(), "ja enviado");
    assert.equal(enviosWhatsApp().length, 1);
  });

  it("se o WhatsApp falhar, libera para nova tentativa", async () => {
    falharWhatsApp = true;
    assert.equal((await chamadaQStash(MSG)).status, 500);
    assert.equal(banco.has("enviado:5511987654321"), false);
    falharWhatsApp = false;
    assert.equal(await (await chamadaQStash(MSG)).text(), "enviado");
  });
});
