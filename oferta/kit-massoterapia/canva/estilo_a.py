"""Paginas 1 a 10: estilo aquarela (folhas, lotus dourada, faixas salvia).

Cada pagina e desenhada duas vezes: a primeira so mede onde o conteudo termina,
a segunda estica os espacos (ESC["v"]) e um pouco as fontes (ESC["t"]) para
preencher a folha A4.
"""

from PIL import Image
from pptx.enum.shapes import MSO_SHAPE

from base import ASSETS, H, W, largura, quebrar

A = dict(bg="#FAF6EC", painel="#FCFAF4", borda="#CDD1BF", faixa="#DFE2CB", titulo="#1F3326",
         texto="#3C3C36", rotulo="#4A4A43", linha="#B5B5AA", bege="#F1ECE0", ouro="#B8975A",
         zebra="#F4F1E7")
SERIF, SANS = "Cormorant Garamond", "Montserrat"
X0, LW = 30, W - 60
ESC = {"v": 1.0, "t": 1.0}
LINHA_FONTE = 1.22  # altura de linha de uma fonte em relacao ao tamanho


def V(x):
    return x * ESC["v"]


def T(x):
    return x * ESC["t"]


def _alt(nome, w):
    im = Image.open(ASSETS / nome)
    return w * im.height / im.width


def pagina(doc, titulo, sub):
    p = doc.pagina(A["bg"])
    p.imagem("folha-esq.png", 0, 0, w=92)
    p.imagem("folha-dir.png", W - 80, 0, w=80)
    p.imagem("folha-esq-baixo.png", 0, H - _alt("folha-esq-baixo.png", 70), w=70)
    p.imagem("folha-dir-baixo.png", W - 58, H - _alt("folha-dir-baixo.png", 58), w=58)
    p.imagem("lotus.png", W / 2 - 72, 12, w=144)
    n = titulo.count("\n") + 1
    tam = 33
    y = 50
    p.texto(70, y, W - 140, tam * 1.05 * n + 4, titulo, SERIF, tam, A["titulo"], negrito=True,
            alinha="c", entrelinha=0.9)
    y += tam * 1.06 * n + 4
    p.texto(60, y, W - 120, 11, sub, SANS, 7, A["texto"], alinha="c", espaco=2.1)
    return p, y + 22


def gap():
    return V(10)


def card(p, y, titulo, corpo, x=X0, w=LW, pad=10, ramo=True, faixa=24):
    topo = y + faixa + V(pad)
    fim = corpo(topo)
    h = fim + V(pad) - y
    painel = p.caixa(x, y, w, h, A["painel"], A["borda"], 0.9, raio=9)
    if faixa > 0:
        banda = p.caixa(x + 0.45, y + 0.45, w - 0.9, faixa, A["faixa"], raio=min(8.5, faixa),
                        forma=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
        p._atras(painel, banda)
    else:
        p._atras(painel)
    if titulo:
        p.texto(x + 14, y, w - 70, faixa, titulo, SERIF, 15, A["titulo"], negrito=True, ancora="m")
    if ramo:
        rw = 30 if faixa >= 20 else 22
        p.imagem("ramo.png", x + w - rw - 10, y + max(1, (faixa - _alt("ramo.png", rw)) / 2), w=rw)
    return y + h


def campos(p, x, y, w, rotulos, gap=16.5, tam=7.6):
    tam, g = T(tam), V(gap)
    for i, r in enumerate(rotulos):
        yy = y + i * g
        if r:
            p.texto(x, yy, w, tam * 1.4, r, SANS, tam, A["rotulo"])
            x1 = x + largura(r, SANS, tam) + 5
        else:
            x1 = x
        p.linha(x1, yy + tam * 1.15, x + w, yy + tam * 1.15, A["linha"], 0.6)
    return y + len(rotulos) * g


def campo_acima(p, x, y, w, rotulo, tam=7.6):
    tam = T(tam)
    p.texto(x, y, w, tam * 1.4, rotulo, SANS, tam, A["rotulo"])
    p.linha(x, y + tam + V(15), x + w, y + tam + V(15), A["linha"], 0.6)
    return y + tam + V(20)


def linhas(p, x, y, w, n, gap=16):
    g = V(gap)
    for i in range(n):
        yy = y + (i + 1) * g - 3
        p.linha(x, yy, x + w, yy, A["linha"], 0.6)
    return y + n * g


def caixa_texto(p, x, y, w, txt, tam=8.1, entre=1.45, fonte=SANS, cor=None):
    tam = T(tam)
    n = quebrar(txt, fonte, tam, w - 24)
    paras = txt.count("\n")
    h = n * tam * entre * LINHA_FONTE + paras * 5 + V(16)
    p.caixa(x, y, w, h, A["bege"], raio=6)
    p.texto(x + 11, y + V(8), w - 22, h - V(10), txt, fonte, tam, cor or A["texto"], entrelinha=entre,
            apos=5 if paras else 0)
    return y + h


def pilula(p, x, y, w, txt, h=18, tam=11.5):
    p.caixa(x, y, w, h, A["bege"], raio=6)
    p.texto(x + 9, y, w - 18, h, txt, SERIF, tam, A["titulo"], negrito=True, ancora="m")
    return y + h


def legenda_status(p, x, y, w, itens):
    h = 20
    p.caixa(x, y, w, h, A["bege"], raio=7)
    p.texto(x + 12, y, 50, h, "Status:", SERIF, 11, A["titulo"], negrito=True, ancora="m")
    xx = x + 70
    passo = (w - 80) / len(itens)
    for nome, cor in itens:
        p.oval(xx, y + 5.5, 9, 9, cor)
        p.texto(xx + 13, y, passo - 15, h, nome, SANS, 7.4, A["texto"], ancora="m")
        xx += passo
    return y + h


def totais(p, x, y, w, rotulos, prefixo=None, caixa_vazia=False):
    gp = 9
    cw = (w - gp * (len(rotulos) - 1)) / len(rotulos)
    alt = V(44)
    for i, r in enumerate(rotulos):
        cx = x + i * (cw + gp)
        if caixa_vazia:
            p.caixa(cx, y, cw, 15, A["faixa"], raio=5)
            p.texto(cx, y, cw, 15, r, SERIF, 10.5, A["titulo"], negrito=True, alinha="c", ancora="m")
            p.caixa(cx, y + 19, cw, alt - 18, A["bege"], raio=5)
            continue
        p.caixa(cx, y, cw, alt, A["painel"], A["borda"], 0.7, raio=6)
        p.caixa(cx + 0.35, y + 0.35, cw - 0.7, 15, A["faixa"], raio=5.5, forma=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
        p.texto(cx, y, cw, 15, r, SERIF, 10.5, A["titulo"], negrito=True, alinha="c", ancora="m")
        pre = prefixo[i] if prefixo else ""
        ly = y + alt - 10
        if pre:
            p.texto(cx + 8, ly - 9, 20, 10, pre, SANS, 7.6, A["rotulo"])
        p.linha(cx + 8 + (16 if pre else 0), ly, cx + cw - 8, ly, A["linha"], 0.6)
    return y + alt


def tabela(p, x, y, w, cab, fracs, n, alt=16.5):
    larg = [w * f for f in fracs]
    a = V(alt)
    p.tabela(x, y, larg, a, cab, n, dict(
        fundo_cab=A["faixa"], fonte_cab=SERIF, tam_cab=10.5, negrito_cab=True, cor_cab=A["titulo"],
        fundo=[A["painel"], A["zebra"]], fonte=SANS, tam=7.5, cor=A["texto"], borda=A["borda"],
        alt_cab=20))
    return y + 20 + n * a


def rodape_lotus(p, txt):
    p.imagem("lotus.png", W / 2 - 50, H - 50, w=100)
    p.texto(60, H - 30, W - 120, 10, txt, SANS, 6.6, A["texto"], alinha="c", espaco=2)


def rodape_frase(p, txt):
    y = H - 32
    lw = largura(txt, SERIF, 11) + 24
    p.linha(W / 2 - lw / 2 - 90, y + 7, W / 2 - lw / 2, y + 7, A["ouro"], 0.6)
    p.linha(W / 2 + lw / 2, y + 7, W / 2 + lw / 2 + 90, y + 7, A["ouro"], 0.6)
    p.texto(W / 2 - lw / 2, y, lw, 14, txt, SERIF, 11, A["titulo"], italico=True, alinha="c")


# --------------------------------------------------------------------------- #
# Paginas (cada uma devolve onde o conteudo terminou e o limite inferior)
# --------------------------------------------------------------------------- #

XI, WI = X0 + 12, LW - 24


def contrato_1(doc):
    p, y = pagina(doc, "Contrato de Atendimento\nem Massoterapia", "MODELO PARA PERSONALIZAÇÃO PROFISSIONAL")
    cw = (WI - 18) / 2

    def partes(t):
        pilula(p, XI, t, cw, "Massoterapeuta (Profissional)")
        pilula(p, XI + cw + 18, t, cw, "Cliente (Pessoa Atendida)")
        t2 = t + 18 + V(8)
        f1 = campos(p, XI, t2, cw, ["Nome:", "CPF:", "CNPJ (se houver):", "Registro profissional (se aplicável):",
                                     "Telefone / WhatsApp:", "E-mail:", "Endereço profissional:", ""])
        f2 = campos(p, XI + cw + 18, t2, cw, ["Nome:", "CPF:", "Data de nascimento:", "Contato:", "Endereço:", "",
                                              "Responsável legal (se aplicável):", "Contato do responsável:"])
        p.linha(XI + cw + 9, t + 2, XI + cw + 9, max(f1, f2) - 2, A["borda"], 0.8)
        return max(f1, f2)
    y = card(p, y, "Identificação das Partes", partes) + gap()
    y = card(p, y, "Condições do Atendimento", lambda t: campos(p, XI, t, WI, [
        "Modalidade:", "Frequência:", "Duração média da sessão:", "Local de atendimento:", "Dia e horário:"])) + gap()
    y = card(p, y, "Objeto do Contrato", lambda t: caixa_texto(p, XI, t, WI,
        "O presente contrato estabelece as condições para a prestação de serviços de massoterapia, com foco em "
        "bem-estar, relaxamento e cuidado corporal, respeitando as necessidades individuais, os limites de atuação "
        "profissional e as orientações acordadas entre as partes.")) + gap()
    return card(p, y, "Observações e Combinações Iniciais", lambda t: linhas(p, XI, t, WI, 4)), H - 50


def contrato_2(doc):
    p, y = pagina(doc, "Contrato de Atendimento\nem Massoterapia", "HONORÁRIOS, POLÍTICA DE ATENDIMENTO E COMBINAÇÕES")
    y = card(p, y, "Honorários e Pagamento", lambda t: campos(p, XI, t, WI, [
        "Valor por sessão:", "Forma de pagamento:", "Data / prazo de pagamento:", "Pacote ou plano (se houver):",
        "Reajuste previsto para:"])) + gap()
    y = card(p, y, "Faltas, Cancelamentos e Reagendamentos", lambda t: caixa_texto(p, XI, t, WI,
        "Cancelamentos e solicitações de reagendamento devem ser informados com antecedência mínima de "
        "____________________. Em caso de não comparecimento, poderá ser cobrado o valor integral da sessão, "
        "conforme a política do profissional.")) + gap()
    y = card(p, y, "Atrasos", lambda t: caixa_texto(p, XI, t, WI,
        "Em caso de atraso, a sessão será encerrada no horário previamente acordado, a fim de respeitar a "
        "organização da agenda e o atendimento dos demais clientes. O tempo de atraso não será automaticamente "
        "acrescido à duração da sessão.")) + gap()
    y = card(p, y, "Comunicação", lambda t: caixa_texto(p, XI, t, WI,
        "Lembretes de sessão, informações administrativas e demais comunicados poderão ser enviados por "
        "WhatsApp, telefone ou e-mail, conforme os contatos fornecidos.")) + gap()
    fim = card(p, y, "Condições Adicionais Acordadas", lambda t: linhas(p, XI, t, WI, 4))
    rodape_lotus(p, "CUIDADO PROFISSIONAL PARA O SEU BEM-ESTAR")
    return fim, H - 62


def contrato_3(doc):
    p, y = pagina(doc, "Contrato de Atendimento\nem Massoterapia", "SIGILO, PROTEÇÃO DE DADOS E FINALIZAÇÃO")
    y = card(p, y, "Sigilo Profissional", lambda t: caixa_texto(p, XI, t, WI,
        "Todas as informações compartilhadas durante o atendimento são confidenciais e serão utilizadas "
        "exclusivamente para o acompanhamento profissional, respeitando a ética e o sigilo inerentes à prática "
        "da massoterapia.")) + gap()
    y = card(p, y, "Registro e Proteção de Dados", lambda t: caixa_texto(p, XI, t, WI,
        "Os dados pessoais do(a) cliente serão armazenados de forma segura e utilizados apenas para finalidades "
        "relacionadas ao atendimento, em conformidade com a Lei Geral de Proteção de Dados Pessoais "
        "(LGPD – Lei nº 13.709/2018).")) + gap()

    def contra(t):
        t = caixa_texto(p, XI, t, WI,
            "O(a) cliente declara, neste espaço, eventuais condições de saúde, restrições, alergias ou outras "
            "informações relevantes para a realização do atendimento de forma segura e adequada.")
        return linhas(p, XI, t + 2, WI, 4, gap=15)
    y = card(p, y, "Contraindicações Declaradas", contra) + gap()
    y = card(p, y, "Encerramento do Atendimento", lambda t: caixa_texto(p, XI, t, WI,
        "O acompanhamento em massoterapia poderá ser concluído por acordo entre as partes ou por decisão "
        "do(a) massoterapeuta, quando identificado que os objetivos foram alcançados ou quando não for mais "
        "indicado dar continuidade ao atendimento.")) + gap()

    def assin(t):
        tam = T(8.1)
        txt = ("Declaro que li e estou de acordo com todas as condições estabelecidas neste contrato de "
               "atendimento em massoterapia.")
        n = quebrar(txt, SANS, tam, WI)
        p.texto(XI, t, WI, n * tam * 1.8, txt, SANS, tam, A["texto"], entrelinha=1.4)
        t = campos(p, XI, t + n * tam * 1.75 + V(6), WI * 0.75, ["Local e data:"])
        cw = (WI - 40) / 2
        for i, r in enumerate(["Assinatura do(a) cliente", "Assinatura do(a) massoterapeuta"]):
            cx = XI + i * (cw + 40)
            p.linha(cx, t + V(22), cx + cw, t + V(22), A["rotulo"], 0.6)
            p.texto(cx, t + V(22) + 4, cw, 10, r, SANS, 7.4, A["rotulo"], alinha="c")
        return t + V(22) + 16
    fim = card(p, y, "Declaração e Assinaturas", assin)
    rodape_frase(p, "Cuidado hoje, bem-estar sempre")
    return fim, H - 48


def controle_sessoes(doc):
    p, y = pagina(doc, "Controle de Sessões", "ACOMPANHAMENTO ADMINISTRATIVO DOS ATENDIMENTOS")

    def topo(t):
        t = campos(p, XI, t, WI, ["Nome do(a) cliente:"])
        meio = XI + WI * 0.5
        campos(p, XI, t, WI * 0.5 - 14, ["Período:"])
        fim = campos(p, meio + 6, t, WI * 0.5 - 6, ["Frequência combinada:", "Profissional:"])
        p.linha(meio - 4, t - 2, meio - 4, fim - 4, A["borda"], 0.8)
        return fim
    y = card(p, y, "", topo, faixa=11) + gap()

    def corpo(t):
        t = tabela(p, XI, t, WI, ["Data", "Horário", "Modalidade", "Técnica / serviço", "Status", "Rubrica"],
                   [.14, .13, .17, .26, .13, .17], 14)
        return legenda_status(p, XI, t + V(8), WI, [("realizado", "#8FA388"), ("falta", "#D9B36C"),
                                                     ("cancelado", "#C9726B"), ("reagendado", "#8A93A8")])
    y = card(p, y, "", corpo, faixa=0, ramo=False) + gap()
    y = card(p, y, "", lambda t: totais(p, XI, t, WI, ["Total realizado", "Total de faltas", "Total cancelado",
                                                        "Próxima revisão"]), faixa=0, ramo=False) + gap()
    return card(p, y, "Observações administrativas", lambda t: linhas(p, XI, t, WI, 3)), H - 45


def registro_evolucao(doc):
    p, y = pagina(doc, "Registro de Evolução", "USO RESERVADO AO PROFISSIONAL")

    def topo(t):
        x = XI
        fim = t
        for r, f in zip(["Nome / código:", "Data:", "Sessão:", "Modalidade:"], [.4, .2, .18, .22]):
            fim = campo_acima(p, x, t, WI * f - 10, r)
            x += WI * f
        return fim
    y = card(p, y, "", topo, faixa=11) + gap()
    for tit in ["Queixa principal / objetivo da sessão", "Técnicas, manobras e recursos utilizados",
                "Respostas observadas e evolução relevante"]:
        y = card(p, y, tit, lambda t: linhas(p, XI, t, WI, 4, gap=15)) + gap()

    def conduta(t):
        g = V(15)
        for i, r in enumerate(["Sem indicação atual", "Reavaliar na próxima sessão", "Necessita encaminhamento"]):
            yy = t + i * g
            p.caixa(XI, yy + 1, 8.5, 8.5, A["painel"], A["rotulo"], 0.7, raio=2)
            p.texto(XI + 14, yy, WI * 0.5, 12, r, SANS, T(7.8), A["texto"])
        meio = XI + WI * 0.55
        p.linha(meio - 12, t, meio - 12, t + 3 * g - 3, A["borda"], 0.8)
        campo_acima(p, meio, t, WI * 0.45, "Data da próxima sessão:")
        return t + 3 * g
    y = card(p, y, "Encaminhamento e conduta", conduta) + gap()
    y = card(p, y, "Plano, encaminhamentos ou pontos para continuidade",
             lambda t: linhas(p, XI, t, WI, 4, gap=15)) + gap()

    def fim(t):
        campo_acima(p, XI, t, WI * 0.45, "Assinatura / rubrica:")
        p.linha(XI + WI * 0.5, t, XI + WI * 0.5, t + V(26), A["borda"], 0.8)
        return campo_acima(p, XI + WI * 0.55, t, WI * 0.45, "Registro profissional (se aplicável):")
    return card(p, y, "", fim, faixa=8, ramo=False), H - 40


def controle_pagamentos(doc):
    p, y = pagina(doc, "Controle de Pagamentos", "ORGANIZAÇÃO FINANCEIRA DOS ATENDIMENTOS")

    def dados(t):
        campos(p, XI, t, WI * 0.5 - 12, ["Nome / código:", "Valor combinado:"])
        return campos(p, XI + WI * 0.5 + 6, t, WI * 0.5 - 6, ["Período:", "Forma de pagamento:"])
    y = card(p, y, "Dados do Atendimento", dados) + gap()

    def lanc(t):
        t = tabela(p, XI, t, WI, ["Vencimento", "Pagamento", "Valor", "Forma", "Status"],
                   [.2, .2, .2, .22, .18], 13)
        return legenda_status(p, XI + WI * 0.35, t + V(8), WI * 0.65, [
            ("pago", "#8FA388"), ("pendente", "#D9B36C"), ("parcial", "#C98B5A"), ("cancelado", "#C9726B")])
    y = card(p, y, "Lançamentos", lanc) + gap()
    y = card(p, y, "", lambda t: totais(p, XI, t, WI, ["Total previsto", "Total recebido", "Total pendente",
                                                        "Próximo vencimento"], prefixo=["R$", "R$", "R$", ""]),
             faixa=0, ramo=False) + gap()
    return card(p, y, "Observações", lambda t: linhas(p, XI, t, WI, 3)), H - 45


def declaracao(doc):
    p, y = pagina(doc, "Declaração de\nComparecimento", "MODELO SIMPLES PARA USO PROFISSIONAL")
    xi, wi = X0 + 14, LW - 28

    def decl(t):
        tam = T(10.2)
        txt = ("Eu, ____________________________________________________________,\n"
               "inscrito(a) no CPF nº ________________________________, declaro que\n"
               "a pessoa __________________________________ compareceu ao serviço\n"
               "de massoterapia em minha responsabilidade no dia _____ / _____ / ______,\n"
               "no período das _________ às _________.")
        alt = 5 * tam * 1.85 * LINHA_FONTE
        p.texto(xi, t + 2, wi, alt, txt, SANS, tam, A["texto"], entrelinha=1.85)
        t += alt + V(10)
        txt2 = ("Esta declaração é emitida a pedido da pessoa interessada e tem como única finalidade comprovar o "
                "comparecimento ao atendimento, não abrangendo informações clínicas, diagnósticos, tratamentos ou "
                "outros dados confidenciais.")
        tam2 = T(9.6)
        n = quebrar(txt2, SANS, tam2, wi)
        alt2 = n * tam2 * 1.45 * LINHA_FONTE
        p.texto(xi, t, wi, alt2, txt2, SANS, tam2, A["texto"], entrelinha=1.45)
        return t + alt2
    y = card(p, y, "Declaração", decl) + gap()
    y = card(p, y, "Finalidade informada pela pessoa solicitante", lambda t: linhas(p, xi, t, wi, 4, gap=20)) + gap()

    def assin(t):
        tam = T(10.2)
        p.texto(xi, t, 60, 14, "Cidade:", SANS, tam, A["texto"])
        p.linha(xi + largura("Cidade:", SANS, tam) + 4, t + tam * 1.15, xi + wi * 0.52, t + tam * 1.15,
                A["rotulo"], 0.6)
        p.texto(xi + wi * 0.6, t, wi * 0.4, 14, "Data:  _____ / _____ / ________", SANS, tam, A["texto"])
        t += V(46)
        p.linha(W / 2 - 120, t, W / 2 + 120, t, A["rotulo"], 0.6)
        p.texto(W / 2 - 150, t + 5, 300, 14, "Massoterapeuta / responsável", SERIF, 11.5, A["titulo"], negrito=True,
                alinha="c")
        p.texto(W / 2 - 150, t + 21, 300, 22, "nome completo\nassinatura/carimbo", SANS, 7.4, A["texto"], alinha="c",
                entrelinha=1.3)
        return t + 46
    return card(p, y, "", assin, faixa=0, ramo=False), H - 45


def recibo(doc):
    p, y = pagina(doc, "Recibo de Atendimento\nem Massoterapia", "COMPROVANTE DE PAGAMENTO")
    xi, wi = X0 + 14, LW - 28

    def topo(t):
        cw = (wi - 30) / 2
        pilula(p, xi, t, cw, "Recibo nº", h=20, tam=12.5)
        pilula(p, xi + cw + 30, t, cw, "Valor – R$", h=20, tam=12.5)
        ly = t + 20 + V(24)
        p.linha(xi + 4, ly, xi + cw - 4, ly, A["rotulo"], 0.6)
        p.linha(xi + cw + 34, ly, xi + wi - 4, ly, A["rotulo"], 0.6)
        p.linha(xi + cw + 15, t, xi + cw + 15, ly + 4, A["borda"], 0.8)
        return ly + 6
    y = card(p, y, "", topo, faixa=11) + gap()

    def corpo(t):
        tam = T(14)
        txt = ("Recebi de ______________________________________________,\n"
               "CPF nº ___________________________, a importância de\n"
               "R$ ____________________________, referente ao(s) atendimento(s)\n"
               "de massoterapia realizado(s) no período de ____________________.")
        alt = 4 * tam * 1.5 * 1.1
        p.texto(xi, t + 2, wi, alt, txt, SERIF, tam, A["titulo"], entrelinha=1.5)
        return t + alt
    y = card(p, y, "", corpo, faixa=0, ramo=False) + gap()
    y = card(p, y, "Dados do pagamento", lambda t: campos(p, xi, t, wi, [
        "Data do pagamento:", "Forma de pagamento:", "Quantidade de sessões:", "Competência / período:",
        "Nome do(a) massoterapeuta:", "Registro profissional (se aplicável):", "CPF / CNPJ:",
        "Contato profissional:"], gap=17.5)) + V(30)
    p.linha(W / 2 - 130, y + 14, W / 2 + 130, y + 14, A["rotulo"], 0.6)
    p.texto(W / 2 - 150, y + 19, 300, 11, "Assinatura do(a) profissional", SANS, 8, A["texto"], alinha="c")
    return y + 30, H - 45


def controle_clientes(doc):
    p, y = pagina(doc, "Controle de Clientes", "VISÃO GERAL DA AGENDA, PAUSAS E RETORNOS")

    def topo(t):
        campos(p, XI, t, WI * 0.5 - 14, ["Período de referência:"])
        fim = campos(p, XI + WI * 0.5 + 6, t, WI * 0.5 - 6, ["Profissional:"])
        p.linha(XI + WI * 0.5 - 4, t - 3, XI + WI * 0.5 - 4, fim - 2, A["borda"], 0.8)
        return fim
    y = card(p, y, "", topo, faixa=11) + gap()
    y = card(p, y, "Acompanhamento da carteira", lambda t: tabela(
        p, XI, t, WI, ["Nome / código", "Início", "Frequência", "Última sessão", "Status", "Próxima ação"],
        [.24, .11, .14, .16, .12, .23], 12)) + gap()
    y = card(p, y, "", lambda t: totais(p, XI, t, WI, ["Total ativos", "Total pausados", "Total encerrados",
                                                        "Retornos pendentes"], caixa_vazia=True),
             faixa=0, ramo=False) + gap()
    return card(p, y, "Ações de acompanhamento administrativo", lambda t: linhas(p, XI, t, WI, 5)), H - 45


def boas_vindas(doc):
    p, y = pagina(doc, "Seja Bem-vindo(a)", "UM ESPAÇO DE ACOLHIMENTO, CUIDADO E BEM-ESTAR")
    y = card(p, y, "", lambda t: caixa_texto(p, XI, t, WI,
        "Cada atendimento de massoterapia é planejado para promover o seu conforto, relaxamento e bem-estar, "
        "com um olhar atento às suas necessidades individuais.\n"
        "Aqui, você encontra um espaço seguro e acolhedor, onde o cuidado, o respeito e a escuta são sempre "
        "prioridades. Sinta-se à vontade para compartilhar suas preferências, eventuais desconfortos e "
        "expectativas, para que possamos tornar sua experiência ainda mais positiva e personalizada.",
        tam=8.6, entre=1.5), faixa=11) + gap()

    passos = [
        ("icone-1.png", "Reserve um momento tranquilo",
         "Procure vir com tempo, para que possa aproveitar o atendimento com calma e sem pressa."),
        ("icone-2.png", "Use roupas confortáveis",
         "Vista algo leve e confortável para facilitar seu bem-estar antes e após a sessão."),
        ("icone-3.png", "Chegue alguns minutos antes",
         "Isso nos ajuda a acolher você com tranquilidade e preparar o ambiente com todo o cuidado."),
        ("icone-4.png", "Informe restrições ou condições de saúde",
         "Compartilhe qualquer condição, restrição ou necessidade especial para que o atendimento seja seguro "
         "e adequado a você."),
    ]

    def grade(t):
        cw, gp = (WI - 10) / 2, V(8)
        ttit, ttxt = T(8.4), T(7.3)
        tw = cw - 66
        ch = max(V(70), max(quebrar(a, SANS, ttit, tw, True) * ttit * 1.3 + quebrar(b, SANS, ttxt, tw) * ttxt * 1.55
                            for _, a, b in passos) + 20)
        for i, (ic, tit, txt) in enumerate(passos):
            cx = XI + (i % 2) * (cw + 10)
            cy = t + (i // 2) * (ch + gp)
            p.caixa(cx, cy, cw, ch, A["bege"], raio=7)
            p.imagem(ic, cx + 10, cy + (ch - 40) / 2, w=40)
            nt = quebrar(tit, SANS, ttit, tw, negrito=True)
            p.texto(cx + 58, cy + 9, tw, nt * ttit * 1.35, tit, SANS, ttit, A["titulo"], negrito=True, entrelinha=1.1)
            p.texto(cx + 58, cy + 12 + nt * ttit * 1.3, tw, ch - 18, txt, SANS, ttxt, A["texto"], entrelinha=1.3)
        return t + 2 * ch + gp
    y = card(p, y, "Seus primeiros passos", grade) + gap()
    return card(p, y, "O que gostaria de lembrar para o primeiro atendimento?", lambda t: linhas(p, XI, t, WI, 5)), H - 45


PAGINAS = [contrato_1, contrato_2, contrato_3, controle_sessoes, registro_evolucao, controle_pagamentos,
           declaracao, recibo, controle_clientes, boas_vindas]
