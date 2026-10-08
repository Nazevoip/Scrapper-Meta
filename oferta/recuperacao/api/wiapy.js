// Recebe os webhooks da Wiapy.
// Pagamento aprovado: marca o telefone como pago.
// Pix pendente, cartao recusado ou carrinho abandonado: agenda a mensagem de recuperacao.

import { agendar, iguais, normalizarTelefone, primeiroNome, redis } from "../lib/servicos.js";

const PAGINA = "https://massoterapia-eight.vercel.app";
const PAGO = new Set(["paid", "approved"]);
const IGNORAR = new Set(["refunded", "chargeback", "chargedback", "canceled", "cancelled"]);

export async function POST(request) {
  const url = new URL(request.url);
  if (!iguais(url.searchParams.get("s"), process.env.WEBHOOK_SECRET)) {
    return new Response("nao autorizado", { status: 401 });
  }

  let dados;
  try {
    dados = await request.json();
  } catch {
    return new Response("json invalido", { status: 400 });
  }

  const telefone = normalizarTelefone(dados.customer?.mobile_phone);
  if (!telefone) return new Response("sem telefone");

  const status = String(dados.payment?.status ?? "").toLowerCase();
  if (PAGO.has(status)) {
    await redis("SET", `pago:${telefone}`, "1", "EX", "86400");
    return new Response("pago");
  }
  if (IGNORAR.has(status)) return new Response("ignorado");

  const checkout = dados.checkout?.id;
  await agendar(new URL("/api/recuperar", url).href, {
    telefone,
    nome: primeiroNome(dados.customer?.name),
    link: checkout ? `https://pay.wiapy.com/${checkout}` : PAGINA,
  }, dados.payment ? "20m" : "30m");
  return new Response("agendado");
}
