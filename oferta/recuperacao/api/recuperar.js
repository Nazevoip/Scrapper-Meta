// Chamado pelo QStash depois do atraso. Se o cliente ainda nao pagou e ainda nao
// recebeu mensagem, manda o modelo aprovado no WhatsApp (uma vez so por telefone).

import { assinaturaValida, enviarWhatsApp, redis } from "../lib/servicos.js";

export async function POST(request) {
  const corpo = await request.text();
  if (!assinaturaValida(request.headers.get("upstash-signature"), corpo)) {
    return new Response("assinatura invalida", { status: 401 });
  }

  const { telefone, nome, link } = JSON.parse(corpo);
  if (await redis("GET", `pago:${telefone}`)) return new Response("ja pagou");
  if (!(await redis("SET", `enviado:${telefone}`, "1", "EX", "172800", "NX"))) {
    return new Response("ja enviado");
  }

  try {
    await enviarWhatsApp(telefone, [nome, link]);
  } catch (erro) {
    // Libera o telefone para o QStash tentar de novo.
    await redis("DEL", `enviado:${telefone}`);
    console.error(erro);
    return new Response("falhou", { status: 500 });
  }
  return new Response("enviado");
}
