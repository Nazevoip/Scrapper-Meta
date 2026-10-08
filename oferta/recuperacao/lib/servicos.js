// Chamadas aos servicos externos (Upstash Redis, Upstash QStash e WhatsApp Cloud API).
// Sem dependencias: so fetch e crypto do proprio Node.

import { createHash, createHmac, timingSafeEqual } from "node:crypto";

export function normalizarTelefone(bruto) {
  const d = String(bruto ?? "").replace(/\D/g, "");
  if (d.length === 10 || d.length === 11) return "55" + d;
  if ((d.length === 12 || d.length === 13) && d.startsWith("55")) return d;
  return null;
}

export function primeiroNome(nome) {
  const p = String(nome ?? "").trim().split(/\s+/)[0];
  return p ? p[0].toUpperCase() + p.slice(1).toLowerCase() : "cliente";
}

export function iguais(a, b) {
  const x = Buffer.from(String(a ?? ""));
  const y = Buffer.from(String(b ?? ""));
  return x.length > 0 && x.length === y.length && timingSafeEqual(x, y);
}

async function chamar(url, opcoes, servico) {
  const r = await fetch(url, opcoes);
  if (!r.ok) throw new Error(`${servico} respondeu ${r.status}: ${await r.text()}`);
  return r.json();
}

export async function redis(...comando) {
  const { result } = await chamar(process.env.UPSTASH_REDIS_REST_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.UPSTASH_REDIS_REST_TOKEN}` },
    body: JSON.stringify(comando),
  }, "Redis");
  return result;
}

// Pede ao QStash para chamar `destino` com `corpo` depois de `atraso` (ex.: "20m").
export async function agendar(destino, corpo, atraso) {
  const base = process.env.QSTASH_URL || "https://qstash.upstash.io";
  return chamar(`${base}/v2/publish/${destino}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.QSTASH_TOKEN}`,
      "Content-Type": "application/json",
      "Upstash-Delay": atraso,
    },
    body: JSON.stringify(corpo),
  }, "QStash");
}

// Confere o cabecalho Upstash-Signature (JWT HS256) com a chave atual ou a proxima.
export function assinaturaValida(jwt, corpo, agora = Date.now() / 1000) {
  return [process.env.QSTASH_CURRENT_SIGNING_KEY, process.env.QSTASH_NEXT_SIGNING_KEY]
    .some((chave) => chave && conferirJwt(jwt, corpo, chave, agora));
}

function conferirJwt(jwt, corpo, chave, agora) {
  const [cab, carga, assinatura] = String(jwt ?? "").split(".");
  if (!assinatura) return false;
  const esperada = createHmac("sha256", chave).update(`${cab}.${carga}`).digest("base64url");
  if (!iguais(assinatura, esperada)) return false;
  let c;
  try {
    c = JSON.parse(Buffer.from(carga, "base64url").toString());
  } catch {
    return false;
  }
  if (c.iss !== "Upstash" || !(c.exp > agora) || c.nbf > agora) return false;
  const hash = createHash("sha256").update(corpo).digest("base64url");
  return String(c.body).replace(/=+$/, "") === hash;
}

export async function enviarWhatsApp(telefone, parametros) {
  return chamar(`https://graph.facebook.com/v23.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.WHATSAPP_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messaging_product: "whatsapp",
      to: telefone,
      type: "template",
      template: {
        name: process.env.WHATSAPP_TEMPLATE,
        language: { code: "pt_BR" },
        components: [{ type: "body", parameters: parametros.map((text) => ({ type: "text", text })) }],
      },
    }),
  }, "WhatsApp");
}
