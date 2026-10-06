"""Paginas 11 a 27: estilo eucalipto (faixas verde-floresta, titulo em caixa alta)."""

import math

from pptx.enum.shapes import MSO_SHAPE

from base import H, W, largura, quebrar

B = dict(bg="#F8F5EE", painel="#FDFCF8", borda="#D7D4C9", faixa="#3F5C4A", titulo="#3F5C4A",
         texto="#2A2A26", linha="#B4B2A8", tile="#EDEAE0", ouro="#B08D4F", salvia="#8FA388",
         cinza="#77776E", zebra="#F6F4EC")
SERIF, SANS = "Libre Baskerville", "Montserrat"
X0, LW = 30, W - 60
XI, WI = X0 + 12, LW - 24
ESC = {"v": 1.0, "t": 1.0}
LINHA_FONTE = 1.22


def V(x):
    return x * ESC["v"]


def T(x):
    return x * ESC["t"]


def eucalipto(p, esquerda=True):
    s = 1 if esquerda else -1
    x0 = 3 if esquerda else W - 3
    p.linha(x0, 2, x0 + s * 52, 54, B["ouro"], 1.1)
    for t, (ew, eh) in zip((0.3, 0.52, 0.74), ((15, 17), (16, 18), (15, 17))):
        cx, cy = x0 + s * 52 * t, 2 + 52 * t
        p.oval(cx - ew / 2 + s * 4, cy - eh / 2 - 3, ew, eh, B["salvia"])


def ornamento(p):
    cx = W / 2
    for i in range(5):
        p.oval(cx - 22 + i * 7.5, 10, 9, 17, None, B["ouro"], 0.8)
    p.arco(cx - 27, 13, 54, 30, B["ouro"], 0.8, 180, 0)


def pagina(doc, titulo, sub):
    p = doc.pagina(B["bg"])
    eucalipto(p, True)
    eucalipto(p, False)
    ornamento(p)
    tam = 26
    while largura(titulo, SERIF, tam, True) > W - 60 and tam > 14:
        tam -= 0.5
    p.texto(20, 50, W - 40, tam * 1.4, titulo, SERIF, tam, B["titulo"], negrito=True, alinha="c")
    y = 50 + tam * 1.35
    p.texto(40, y, W - 80, 14, sub, SANS, 9.5, B["texto"], alinha="c")
    rodape(p)
    return p, y + 30


def rodape(p):
    p.texto(60, H - 39, W - 120, 10, "MASSOTERAPIA • CUIDADO • BEM-ESTAR", SANS, 6.5, B["cinza"], alinha="c")
    p.linha(155, H - 28, W - 155, H - 28, B["ouro"], 0.7)


def gap():
    return V(10)


def card(p, y, titulo, corpo, x=X0, w=LW, pad=10, faixa=21, tam_titulo=8.4):
    topo = y + (faixa if titulo else 0) + V(pad)
    fim = corpo(topo)
    h = fim + V(pad) - y
    painel = p.caixa(x, y, w, h, B["painel"], B["borda"], 0.8, raio=8)
    if titulo:
        banda = p.caixa(x, y, w, faixa, B["faixa"], raio=min(8, faixa), forma=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
        p._atras(painel, banda)
        p.texto(x + 10, y, w - 20, faixa, titulo.upper(), SANS, tam_titulo, "#FFFFFF", negrito=True, ancora="m")
    else:
        p._atras(painel)
    return y + h


def paragrafo(p, x, y, w, txt, tam=8.6, entre=1.4, cor=None):
    tam = T(tam)
    n = quebrar(txt, SANS, tam, w)
    h = n * tam * entre * LINHA_FONTE
    p.texto(x, y, w, h, txt, SANS, tam, cor or B["texto"], entrelinha=entre)
    return y + h


def linhas(p, x, y, w, n, gap=16):
    g = V(gap)
    for i in range(n):
        yy = y + (i + 1) * g - 3
        p.linha(x, yy, x + w, yy, B["linha"], 0.6)
    return y + n * g


def campos(p, x, y, w, rotulos, gap=19, tam=8.6, negrito=False):
    tam, g = T(tam), V(gap)
    for i, r in enumerate(rotulos):
        yy = y + i * g
        p.texto(x, yy, w, tam * 1.4, r, SANS, tam, B["texto"], negrito=negrito)
        x1 = x + largura(r, SANS, tam, negrito) + 6
        p.linha(x1, yy + tam * 1.2, x + w, yy + tam * 1.2, B["linha"], 0.6)
    return y + len(rotulos) * g


def campos_2col(p, x, y, w, pares, gap=19, tam=8.6, negrito=False):
    cw = (w - 30) / 2
    campos(p, x, y, cw, [a for a, _ in pares], gap, tam, negrito)
    return campos(p, x + cw + 30, y, cw, [b for _, b in pares], gap, tam, negrito)


def checks(p, x, y, w, itens, colunas=1, gap=20, tam=7.8):
    tam, g = T(tam), V(gap)
    cw = w / colunas
    for i, it in enumerate(itens):
        cx = x + (i % colunas) * cw
        cy = y + (i // colunas) * g
        p.caixa(cx, cy + 0.5, 8.5, 8.5, B["painel"], B["texto"], 0.6)
        p.texto(cx + 14, cy, cw - 16, tam * 1.4, it, SANS, tam, B["texto"])
    return y + math.ceil(len(itens) / colunas) * g


def tabela(p, x, y, w, cab, fracs, n, alt=19, primeira=None, tam_cab=7.4):
    a = V(alt)
    p.tabela(x, y, [w * f for f in fracs], a, cab, n, dict(
        fundo_cab=B["faixa"], fonte_cab=SANS, tam_cab=tam_cab, negrito_cab=False, cor_cab="#FFFFFF",
        fundo=[B["painel"]], fonte=SANS, tam=7.4, cor=B["texto"], borda="#D9D7CE", alt_cab=20,
        cab_centro=True), primeira_coluna=primeira)
    return y + 20 + n * a


def mensagens(doc, titulo, sub, itens, extra=None):
    p, y = pagina(doc, titulo, sub)
    for cab, txt in itens:
        y = card(p, y, cab, lambda t, txt=txt: paragrafo(p, XI, t, WI, txt) + V(18)) + gap()
    if extra:
        y = card(p, y, extra, lambda t: linhas(p, XI, t, WI, 5, gap=17)) + gap()
    return p, y - gap()


# --------------------------------------------------------------------------- #

def como_funciona(doc):
    p, y = pagina(doc, "COMO FUNCIONA O ATENDIMENTO", "Informações essenciais para seu atendimento em massoterapia")
    itens = [
        ("Sessões", "Cada sessão possui duração aproximada de ______ minutos e ocorrerá com a frequência combinada "
                    "entre cliente e profissional, podendo ser ajustada conforme a evolução e os objetivos do "
                    "atendimento."),
        ("Preparação para a sessão", "Use roupas confortáveis, evite refeições muito pesadas imediatamente antes do "
                                     "atendimento, mantenha-se hidratado(a) e informe qualquer alteração importante no "
                                     "estado de saúde."),
        ("Durante o atendimento", "O atendimento será realizado com respeito, privacidade e atenção às suas "
                                  "necessidades. Comunique qualquer dor, desconforto ou preferência de pressão durante "
                                  "a sessão."),
        ("Contato entre sessões", "O canal __________________ será utilizado para confirmações, lembretes e assuntos "
                                  "administrativos."),
        ("Faltas e reagendamentos", "Caso precise cancelar ou reagendar, avise com pelo menos ______ horas de "
                                    "antecedência. As condições específicas devem seguir a política do profissional."),
        ("Em situação de urgência", "A massoterapia não substitui atendimento médico de urgência. Em caso de sintomas "
                                    "intensos ou intercorrência clínica, procure o serviço de saúde adequado."),
    ]
    for cab, txt in itens:
        y = card(p, y, cab, lambda t, txt=txt: paragrafo(p, XI, t, WI, txt) + V(10)) + gap()
    return y - gap(), H - 52


def informacoes_espaco(doc):
    p, y = pagina(doc, "INFORMAÇÕES DO ESPAÇO", "Guarde esta ficha para consultas rápidas")
    y = card(p, y, "Informações profissionais", lambda t: campos_2col(p, XI, t, WI, [
        ("Nome do(a) massoterapeuta:", "Registro profissional (se aplicável):"),
        ("Telefone / WhatsApp:", "E-mail:"), ("Endereço do espaço:", "Link / localização:"),
        ("Dias e horários de atendimento:", "Duração média da sessão:")], gap=24, tam=8.2)) + gap()

    def dois_sub(t, a, b, n):
        cw = (WI - 14) / 2
        f = t
        for i, tit in enumerate((a, b)):
            f = card(p, t, tit, lambda tt: linhas(p, XI + i * (cw + 14) + 10, tt, cw - 20, n, gap=15),
                     x=XI + i * (cw + 14) - 2, w=cw, faixa=19, tam_titulo=7.6, pad=6)
        return f
    y = card(p, y, "Combinações importantes", lambda t: dois_sub(t, "Forma e data de pagamento",
                                                                    "Prazo para cancelamento / reagendamento", 4)) + gap()
    y = card(p, y, "Pós-atendimento", lambda t: dois_sub(t, "Cuidados recomendados", "Observações importantes", 3)) + gap()
    y = card(p, y, "Outras informações importantes", lambda t: linhas(p, XI, t, WI, 6, gap=17))
    return y, H - 52


def lembretes_agendamentos(doc):
    _, y = mensagens(doc, "LEMBRETES DE AGENDAMENTOS", "Textos prontos para adaptar e enviar", [
        ("Confirmação — 24 horas antes", "Olá, [nome]! Passando para confirmar nosso atendimento amanhã, [data], às "
                                         "[horário]. Se precisar ajustar o horário, me avise por aqui."),
        ("Confirmação — no mesmo dia", "Olá, [nome]! Lembrete do nosso atendimento hoje, às [horário]. [Endereço ou "
                                       "referência, se necessário]. Até mais!"),
        ("Atendimento domiciliar / empresarial", "Olá, [nome]! Nosso atendimento está confirmado para [data], às "
                                                 "[horário]. Estarei no local combinado. Se houver qualquer ajuste, me "
                                                 "avise com antecedência."),
        ("Próxima sessão agendada", "Oi, [nome]! Sua próxima sessão ficou agendada para [data], às [horário]. Qualquer "
                                    "necessidade de alteração, avise com a antecedência combinada."),
    ], extra="Minha versão personalizada")
    return y, H - 60


def lembretes_pagamentos(doc):
    _, y = mensagens(doc, "LEMBRETES DE PAGAMENTOS", "Comunicação clara e respeitosa", [
        ("Antes do vencimento", "Oi, [nome]! Lembrete de que o pagamento referente a [sessão/pacote/período] vence em "
                                "[data]. O valor é R$ [valor] e pode ser pago por [forma]."),
        ("No dia do vencimento", "Olá, [nome]! Passando para lembrar que o pagamento de R$ [valor], referente a "
                                 "[sessão/pacote/período], vence hoje. Se já realizou, desconsidere esta mensagem."),
        ("Pagamento não identificado", "Oi, [nome]! Ainda não consegui identificar o pagamento referente a "
                                       "[sessão/pacote/período]. Poderia verificar, por favor? Se já foi realizado, "
                                       "envie o comprovante para atualização do controle."),
        ("Confirmação de recebimento", "Olá, [nome]! Pagamento recebido com sucesso. Obrigado(a)! Se precisar de "
                                       "recibo, ele será enviado por [canal/prazo]."),
    ])
    return y, H - 120


def mensagens_faltas(doc):
    _, y = mensagens(doc, "MENSAGENS PARA FALTAS", "Modelos acolhedores e objetivos", [
        ("Falta sem aviso", "Olá, [nome]. Notei que você não conseguiu comparecer ao horário de hoje. Espero que esteja "
                            "tudo bem. Quando puder, me avise para alinharmos o ocorrido e o possível reagendamento."),
        ("Após o tempo de tolerância", "Olá, [nome]. Estou disponível para nosso atendimento agendado às [horário]. "
                                       "Como já ultrapassamos o tempo de tolerância combinado, o atendimento de hoje "
                                       "não poderá ser realizado. Depois conversamos sobre o próximo horário."),
        ("Faltas recorrentes", "Olá, [nome]. Percebi que tivemos algumas ausências recentes. Gostaria de alinhar "
                               "horários e condições de acompanhamento para verificarmos o que funciona melhor neste "
                               "momento."),
        ("Retomada de contato", "Olá, [nome]. Como não tivemos retorno após o último agendamento, estou entrando em "
                                "contato para saber se deseja continuar o acompanhamento. Fico disponível para "
                                "alinharmos."),
    ], extra="Minha versão personalizada")
    return y, H - 60


def mensagens_reagendamento(doc):
    _, y = mensagens(doc, "MENSAGENS PARA REAGENDAMENTO", "Modelos para diferentes situações", [
        ("Pedido recebido", "Olá, [nome]! Recebi seu pedido de reagendamento. Tenho disponibilidade em [opção 1] ou "
                            "[opção 2]. Algum desses horários funciona para você?"),
        ("Sem horário na semana", "Olá, [nome]. Nesta semana não tenho outro horário disponível. Podemos manter nossa "
                                  "próxima sessão em [data] ou, se preferir, te aviso em caso de encaixe."),
        ("Alteração pelo profissional", "Olá, [nome]. Preciso solicitar a alteração excepcional da nossa sessão de "
                                        "[data/horário]. Posso oferecer [opções]. Peço desculpas pelo transtorno e "
                                        "agradeço sua compreensão."),
        ("Confirmação do novo horário", "Reagendamento confirmado: [data], às [horário]. Obrigado(a) pelo retorno. "
                                        "Caso precise de novo ajuste, avise com antecedência."),
    ], extra="Outras opções de horário / observações")
    return y, H - 60


def guia_organizacao(doc):
    p, y = pagina(doc, "GUIA DE ORGANIZAÇÃO DO ESPAÇO", "Uma rotina simples, segura e sustentável")
    y = card(p, y, "", lambda t: paragrafo(p, XI, t + V(4), WI,
        "Organizar não é guardar tudo. É saber o que precisa ser registrado, onde encontrar cada informação e "
        "quando revisar a rotina.") + V(8)) + gap()

    pilares = [("Agenda", "Sessões, confirmações, cancelamentos e pausas."),
               ("Atendimento", "Anamnese, evolução, fichas e observações."),
               ("Financeiro", "Pagamentos, pacotes, vencimentos e pendências."),
               ("Comunicação", "Lembretes, retornos, orientações e canais profissionais.")]

    def grade(t):
        cw, ch, gp = (WI - 20) / 2, V(40), V(10)
        for i, (tit, txt) in enumerate(pilares):
            cx, cy = XI + (i % 2) * (cw + 20), t + (i // 2) * (ch + gp)
            p.caixa(cx, cy, cw, ch, B["tile"], B["borda"], 0.6, raio=6)
            p.texto(cx + 10, cy + ch / 2 - 13, cw - 20, 12, tit.upper(), SANS, T(8.6), B["titulo"], negrito=True)
            p.texto(cx + 10, cy + ch / 2 + 1, cw - 20, 12, txt, SANS, T(7.2), B["texto"])
        return t + 2 * ch + gp
    y = card(p, y, "Os 4 pilares", grade) + gap()
    y = card(p, y, "Mapa da minha rotina", lambda t: tabela(
        p, XI, t, WI, ["ÁREA", "FERRAMENTA / CANAL", "COMO ORGANIZO HOJE"], [.2, .36, .44], 6, alt=30,
        primeira=["Agenda", "Prontuário / fichas", "Financeiro", "Materiais", "Mensagens / retorno",
                  "Backup e segurança"])) + gap()
    y = card(p, y, "O que mais consome tempo hoje?", lambda t: linhas(p, XI, t, WI, 4, gap=18))
    return y, H - 52


def rotina_semanal(doc):
    p, y = pagina(doc, "ROTINA SEMANAL DO ESPAÇO", "Checklist de 15 a 30 minutos")
    blocos = [
        ("Antes da semana começar", ["Rever agenda e horários", "Confirmar pagamentos previstos",
                                     "Separar retornos pendentes", "Preparar fichas ou materiais"]),
        ("Após cada atendimento", ["Atualizar registro da evolução", "Anotar retorno necessário",
                                   "Registrar observações importantes", "Higienizar materiais e organizar o espaço"]),
        ("No fim do dia", ["Conferir mensagens administrativas", "Fechar caixa ou anotar recebimentos",
                           "Confirmar agenda seguinte", "Registrar pendências breves"]),
        ("No fim da semana", ["Revisar faltas e reagendamentos", "Verificar clientes sem retorno",
                              "Planejar prioridades da próxima semana", "Realizar backup seguro"]),
    ]
    cw = (LW - 20) / 2
    for linha in range(2):
        fins = []
        for col in range(2):
            tit, itens = blocos[linha * 2 + col]
            x = X0 + col * (cw + 20)
            fins.append(card(p, y, tit, lambda t, x=x, itens=itens: checks(p, x + 12, t + 2, cw - 24, itens, gap=26)
                             + V(4), x=x, w=cw))
        y = max(fins) + gap()
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(6), WI, [("Dia da revisão semanal:", "Horário reservado:")],
                                             tam=9) + V(4)) + gap()
    y = card(p, y, "Três prioridades da próxima semana", lambda t: linhas(p, XI, t, WI, 5, gap=19))
    return y, H - 52


def arquivamento(doc):
    p, y = pagina(doc, "ARQUIVAMENTO E PROTEÇÃO", "Organize por acesso, finalidade e segurança")

    def estrutura(t):
        p.texto(XI, t, WI, 18, "ATENDIMENTO", SERIF, T(12.5), B["titulo"], negrito=True)
        t += V(24)
        g = V(21)
        for i, it in enumerate(["Agenda e calendário de atendimentos", "Fichas de anamnese e evolução",
                                "Termos, autorizações e documentos", "Financeiro e recibos",
                                "Contatos e comunicação profissional", "Backups"]):
            yy = t + i * g
            p.texto(XI, yy, 24, 12, f"{i + 1:02d}", SANS, T(8.6), B["ouro"], negrito=True)
            p.texto(XI + 30, yy, WI - 30, 12, it, SANS, T(8.6), B["texto"])
            p.linha(XI + 28, yy + g - 6, XI + WI, yy + g - 6, "#CFCCC1", 0.8)
        return t + 6 * g
    y = card(p, y, "Estrutura sugerida", estrutura) + gap()
    y = card(p, y, "Checklist de segurança", lambda t: checks(p, XI, t + 2, WI, [
        "Acesso protegido por senha", "Tela com bloqueio automático", "Arquivos físicos em local seguro",
        "Backup periódico de conteúdo", "Compartilhamento restrito", "Descarte seguro de cópias",
        "Dados mínimos necessários", "Separação entre uso pessoal e profissional"], colunas=2, gap=22)) + gap()
    y = card(p, y, "Onde cada categoria será armazenada?", lambda t: linhas(p, XI, t, WI, 7, gap=17))
    return y, H - 52


def revisao_mensal(doc):
    p, y = pagina(doc, "REVISÃO MENSAL", "Fechamento e melhorias contínuas")
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(6), WI, [("Mês / ano:", "Data da revisão:")], tam=9)
             + V(4)) + gap()
    y = card(p, y, "Indicadores administrativos", lambda t: campos_2col(p, XI, t + V(4), WI, [
        ("Atendimentos realizados:", "Faltas / cancelamentos:"), ("Clientes ativos:", "Novos clientes:"),
        ("Valor recebido:", "Pendências financeiras:")], gap=24, tam=8.8) + V(6)) + gap()
    y = card(p, y, "Revisão da rotina", lambda t: checks(p, XI, t + 2, WI, [
        "Agenda atualizada", "Registros em dia", "Recibos emitidos", "Mensagens respondidas",
        "Estoque / materiais conferidos", "Metas acompanhadas"], colunas=2, gap=19)) + gap()
    y = card(p, y, "O que funcionou bem neste mês?", lambda t: linhas(p, XI, t, WI, 4, gap=17)) + gap()
    y = card(p, y, "O que precisa ser ajustado?", lambda t: linhas(p, XI, t, WI, 4, gap=17)) + gap()
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(6), WI, [
        ("Uma melhoria para o próximo mês:", "Data para revisar:")], tam=8.8) + V(2))
    return y, H - 50


def registro_sensacoes(doc):
    p, y = pagina(doc, "REGISTRO DE SENSAÇÕES", "Acompanhe como o corpo responde aos atendimentos")
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(6), WI, [("Data:", "Horário:")], tam=9.2, negrito=True)
             + V(4)) + gap()

    def antes(t):
        t = paragrafo(p, XI, t, WI, "Registre tensões, desconfortos, cansaço ou sensações percebidas antes do "
                      "atendimento.", tam=7.6)
        return linhas(p, XI, t + 2, WI, 2, gap=19)
    y = card(p, y, "Antes da sessão — como meu corpo estava?", antes) + gap()
    y = card(p, y, "Regiões de maior tensão ou desconforto", lambda t: linhas(p, XI, t, WI, 2, gap=19)) + gap()

    def escala(t):
        passo = (WI - 40) / 10
        for n in range(11):
            cx = XI + 8 + n * passo
            p.oval(cx, t, 13, 13, None, B["ouro"], 0.7)
            p.texto(cx - 6, t + 16, 25, 10, str(n), SANS, 7.4, B["texto"], alinha="c")
        return t + 28
    y = card(p, y, "Intensidade do desconforto (0–10)", escala) + gap()
    y = card(p, y, "Depois da sessão — o que mudou?", lambda t: linhas(p, XI, t, WI, 2, gap=19)) + gap()
    y = card(p, y, "Reações nas horas seguintes", lambda t: linhas(p, XI, t, WI, 2, gap=19)) + gap()
    y = card(p, y, "O que posso observar até o próximo atendimento?", lambda t: linhas(p, XI, t, WI, 3, gap=19))
    return y, H - 52


def roda_bem_estar(doc):
    p, y = pagina(doc, "RODA DO BEM-ESTAR", "Avalie como está seu corpo e sua rotina hoje")
    r = V(88)
    cx, cy = W / 2, y + r + 26
    for k in range(5, 0, -1):
        rr = r * k / 5
        p.oval(cx - rr, cy - rr, 2 * rr, 2 * rr, None, "#B9B8AE", 0.7)
    for ang in (0, 45, 90, 135):
        a = math.radians(ang)
        dx, dy = math.cos(a) * (r + 14), math.sin(a) * (r + 14)
        p.linha(cx - dx, cy - dy, cx + dx, cy + dy, "#B9B8AE", 0.7)
    rotulos = ["SONO", "ESTRESSE", "ENERGIA", "MOBILIDADE", "ATIVIDADE FÍSICA", "HIDRATAÇÃO", "DOR / DESCONFORTO",
               "AUTOCUIDADO"]
    for i, rot in enumerate(rotulos):
        a = math.radians(-90 + i * 45)
        d = r + 34
        lx, ly = cx + math.cos(a) * d, cy + math.sin(a) * d
        lw = largura(rot, SANS, 8.2, True) + 6
        p.texto(lx - lw / 2, ly - 6, lw, 12, rot, SANS, 8.2, B["titulo"], negrito=True, alinha="c")
    y = cy + r + 50
    p.texto(60, y, W - 120, 12, "Avalie cada área de 0 a 10 e marque o nível correspondente.", SANS, 8.4,
            B["texto"], alinha="c")
    y += V(22)
    y = card(p, y, "", lambda t: campos(p, XI, t + V(4), WI, ["Área que mais precisa de atenção:", "Nota atual:"],
                                        gap=21, tam=8.6, negrito=True)) + gap()
    y = card(p, y, "O que explica essa nota?", lambda t: linhas(p, XI, t, WI, 3, gap=18)) + gap()
    y = card(p, y, "Qual seria um sinal de melhora?", lambda t: linhas(p, XI, t, WI, 3, gap=18)) + gap()
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(4), WI, [("Primeiro passo possível:",
                                                                    "Quando posso começar:")], tam=8.6,
                                             negrito=True) + V(2))
    return y, H - 50


def cartoes(doc, sub, itens):
    p, y = pagina(doc, "CARTÕES DE SENSAÇÕES CORPORAIS", sub)
    gp = 12
    cw = (LW - 2 * gp) / 3
    ch = (H - 70 - y - 2 * gp) / 3
    for i, (simb, tit, perg) in enumerate(itens):
        x = X0 + (i % 3) * (cw + gp)
        yy = y + (i // 3) * (ch + gp)
        p.caixa(x, yy, cw, ch, B["painel"], B["ouro"], 0.8, raio=10)
        p.oval(x + cw / 2 - 14, yy + 18, 28, 28, None, B["titulo"], 0.9)
        p.texto(x + cw / 2 - 14, yy + 18, 28, 28, simb, SERIF, 11, B["titulo"], negrito=True, alinha="c", ancora="m")
        p.texto(x + 8, yy + 56, cw - 16, 16, tit, SERIF, 11.5, B["titulo"], negrito=True, alinha="c")
        p.texto(x + 11, yy + 78, cw - 22, 40, perg, SANS, 7.6, B["texto"], entrelinha=1.3)
    return H - 70, H - 70


def cartoes_1(doc):
    return cartoes(doc, "Recorte e use para facilitar a percepção corporal", [
        ("~", "LEVEZA", "Em que parte do corpo você percebe mais leveza?"),
        ("!", "TENSÃO", "Onde seu corpo parece mais preso ou rígido?"),
        ("+", "DOR", "Qual região está mais sensível agora?"),
        ("Z", "CANSAÇO", "Seu corpo pede pausa ou recuperação?"),
        ("♡", "RELAXAMENTO", "O que ajudou seu corpo a desacelerar?"),
        ("|", "RIGIDEZ", "Em qual movimento você sente limitação?"),
        ("○", "CONFORTO", "Qual posição ou toque traz mais bem-estar?"),
        ("↓", "PESO", "Há alguma região que parece pesada ou sobrecarregada?"),
        ("...", "FORMIGAMENTO", "Onde você percebe formigamento ou alteração de sensibilidade?"),
    ])


def cartoes_2(doc):
    return cartoes(doc, "Segunda folha para recorte", [
        ("~", "CALOR", "Em qual região você percebe aumento de calor?"),
        ("*", "FRIO", "Existe alguma região que parece mais fria?"),
        ("+", "INCHAÇO", "Onde você percebe retenção ou sensação de volume?"),
        ("<>", "MOBILIDADE", "Qual movimento está mais fácil hoje?"),
        ("!", "SENSIBILIDADE", "Alguma área está mais sensível ao toque?"),
        ("↑", "ENERGIA", "Como está sua disposição corporal agora?"),
        ("Z", "SONOLÊNCIA", "Seu corpo pede descanso depois da sessão?"),
        ("≈", "RESPIRAÇÃO", "Sua respiração está mais livre ou profunda?"),
        ("♡", "BEM-ESTAR", "O que melhor descreve como você se sente agora?"),
    ])


def rastreador(doc):
    p, y = pagina(doc, "RASTREADOR DE HÁBITOS E BEM-ESTAR", "Consistência, não perfeição")
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(4), WI, [("Mês / ano:", "Intenção do mês:")], tam=8.8,
                                             negrito=True) + V(2)) + gap()
    y = card(p, y, "Acompanhamento diário", lambda t: tabela(
        p, XI, t, WI, ["DIA", "DOR 0–10", "SONO 0–10", "ÁGUA", "MOVIMENTO", "AUTOCUIDADO", "OBSERVAÇÃO"],
        [.07, .12, .12, .12, .15, .15, .27], 31, alt=13, primeira=[str(d) for d in range(1, 32)])) + gap()
    cw = (LW - 20) / 2
    f1 = card(p, y, "Hábito que quero fortalecer", lambda t: linhas(p, X0 + 10, t, cw - 20, 3, gap=16), w=cw)
    f2 = card(p, y, "O que pode facilitar", lambda t: linhas(p, X0 + cw + 30, t, cw - 20, 3, gap=16),
              x=X0 + cw + 20, w=cw)
    return max(f1, f2), H - 52


def autocuidado(doc):
    p, y = pagina(doc, "PLANO DE AUTOCUIDADO CORPORAL", "Cuidar de si também pode ser planejado")
    y = card(p, y, "Como percebo que meu corpo está precisando de cuidado?",
             lambda t: linhas(p, XI, t, WI, 3, gap=18)) + gap()
    areas = [("Corpo", "descanso, alimentação, movimento"), ("Hidratação", "água e rotina de consumo"),
             ("Sono", "horários, ambiente e descanso"), ("Movimento", "caminhada, mobilidade, alongamento"),
             ("Rotina", "organização e pausas"), ("Relaxamento", "respiração, banho, silêncio, lazer")]

    def grade(t):
        cw, ch, gp = (WI - 20) / 2, V(60), V(10)
        for i, (tit, txt) in enumerate(areas):
            cx, cy = XI + (i % 2) * (cw + 20), t + (i // 2) * (ch + gp)
            p.caixa(cx, cy, cw, ch, B["tile"], B["borda"], 0.6, raio=6)
            p.texto(cx + 10, cy + 8, cw - 20, 12, tit.upper(), SANS, T(8.6), B["titulo"], negrito=True)
            p.texto(cx + 10, cy + 21, cw - 20, 11, txt, SANS, T(7.2), B["texto"])
            for k in range(2):
                ly = cy + ch - 18 + k * 9 - (0 if k else 0)
                p.linha(cx + 10, ly, cx + cw - 10, ly, B["linha"], 0.6)
        return t + 3 * ch + 2 * gp
    y = card(p, y, "O que me ajuda em cada área", grade) + gap()
    y = card(p, y, "Três atitudes possíveis nesta semana", lambda t: linhas(p, XI, t, WI, 5, gap=18)) + gap()
    y = card(p, y, "", lambda t: campos_2col(p, XI, t + V(6), WI, [("Vou começar em:", "Com quem posso contar:")],
                                             tam=8.8, negrito=True) + V(4))
    return y, H - 52


def dias_de_dor(doc):
    p, y = pagina(doc, "PLANO PARA DIAS DE DOR E TENSÃO",
                  "Prepare um caminho de cuidado para quando o corpo pedir atenção")

    def alerta(t):
        t = paragrafo(p, XI, t, WI, "Quais sinais mostram que meu corpo está sobrecarregado, dolorido ou precisando "
                      "reduzir o ritmo?", tam=7.6)
        return linhas(p, XI, t + 2, WI, 3, gap=17)
    y = card(p, y, "Meus sinais de alerta", alerta) + gap()

    def estrategias(t):
        t = checks(p, XI, t + 2, WI, ["Descanso e pausa", "Hidratação", "Alongamento leve", "Banho morno",
                                      "Respiração / relaxamento", "Caminhada leve", "Compressa conforme orientação",
                                      "Outra"], colunas=4, gap=20, tam=7.4)
        return linhas(p, XI, t, WI, 2, gap=16)
    y = card(p, y, "Estratégias que costumam me ajudar", estrategias) + gap()
    y = card(p, y, "Pessoas e serviços de apoio", lambda t: tabela(
        p, XI, t, WI, ["NOME / SERVIÇO", "COMO PODE AJUDAR", "CONTATO"], [.36, .38, .26], 4, alt=22)) + gap()
    y = card(p, y, "Movimentos ou situações que posso evitar temporariamente",
             lambda t: linhas(p, XI, t, WI, 4, gap=17)) + gap()
    y = card(p, y, "Uma frase ou lembrete importante para mim", lambda t: linhas(p, XI, t, WI, 3, gap=17))
    p.texto(X0, y + 8, LW, 12, "Se houver dor intensa, trauma, perda de força, falta de ar, febre ou qualquer sintoma "
            "preocupante, procure avaliação médica.", SANS, 7.4, B["texto"], alinha="c")
    return y + 20, H - 50


PAGINAS = [como_funciona, informacoes_espaco, lembretes_agendamentos, lembretes_pagamentos, mensagens_faltas,
           mensagens_reagendamento, guia_organizacao, rotina_semanal, arquivamento, revisao_mensal,
           registro_sensacoes, roda_bem_estar, cartoes_1, cartoes_2, rastreador, autocuidado, dias_de_dor]
