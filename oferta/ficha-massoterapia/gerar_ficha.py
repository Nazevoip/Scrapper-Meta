"""Gera a Ficha de Anamnese de Massoterapia (PDF editavel, A4, 2 paginas).

    python oferta/ficha-massoterapia/gerar_ficha.py

Os campos sao preenchiveis no computador e no celular (Adobe, navegador) e a
ficha tambem funciona impressa.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAIDA = Path(__file__).with_name("ficha-anamnese-massoterapia.pdf")

VERDE = HexColor("#2F6F62")
VERDE_CLARO = HexColor("#EAF2EF")
TINTA = HexColor("#22302C")
CINZA = HexColor("#6B7A75")
BORDA = HexColor("#B9CBC4")

W, H = A4
M = 36                      # margem lateral
LARGURA = W - 2 * M


class Ficha:
    def __init__(self, path: Path):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle("Ficha de Anamnese - Massoterapia")
        self.c.setAuthor("Ficha de Anamnese - Massoterapia")
        self.form = self.c.acroForm
        self.y = H
        self.pagina = 0

    # -- estrutura --------------------------------------------------------- #

    def nova_pagina(self):
        if self.pagina:
            self._rodape()
            self.c.showPage()
        self.pagina += 1
        self.y = H - M

    def _rodape(self):
        c = self.c
        c.setFont("Helvetica", 7)
        c.setFillColor(CINZA)
        c.drawString(M, 22, "Esta ficha registra informações para o atendimento e não substitui "
                            "avaliação médica.")
        c.drawRightString(W - M, 22, f"Página {self.pagina} de 2")

    def cabecalho(self):
        c = self.c
        c.setFillColor(VERDE)
        c.rect(0, H - 78, W, 78, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(M, H - 42, "Ficha de Anamnese")
        c.setFont("Helvetica", 11)
        c.drawString(M, H - 60, "Massoterapia")
        c.setFont("Helvetica", 7.5)
        c.drawRightString(W - M, H - 30, "PROFISSIONAL / ESPAÇO")
        self._campo("profissional", W - M - 200, H - 56, 200, 18, borda=white,
                    fundo=HexColor("#3E8273"), cor_texto=white)
        self.y = H - 96

    def secao(self, numero: int, titulo: str):
        c = self.c
        self.y -= 8
        c.setFillColor(VERDE_CLARO)
        c.roundRect(M, self.y - 16, LARGURA, 20, 4, stroke=0, fill=1)
        c.setFillColor(VERDE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(M + 8, self.y - 10, f"{numero}. {titulo.upper()}")
        self.y -= 26

    def aviso(self, texto: str):
        c = self.c
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(CINZA)
        c.drawString(M, self.y - 8, texto)
        self.y -= 16

    # -- campos ------------------------------------------------------------ #

    def _campo(self, nome, x, y, w, h, multilinha=False, borda=BORDA,
               fundo=white, cor_texto=TINTA):
        self.form.textfield(
            name=nome, x=x, y=y, width=w, height=h, borderWidth=0.8,
            borderColor=borda, fillColor=fundo, textColor=cor_texto,
            fontName="Helvetica", fontSize=0 if multilinha else 9,
            fieldFlags="multiline" if multilinha else "",
        )

    def linha(self, campos: list[tuple[str, str, float]], altura: float = 18):
        """Campos lado a lado: (rotulo, nome, fracao_da_largura)."""
        c = self.c
        gap = 8
        livre = LARGURA - gap * (len(campos) - 1)
        x = M
        for rotulo, nome, frac in campos:
            w = livre * frac
            c.setFont("Helvetica", 7.5)
            c.setFillColor(CINZA)
            c.drawString(x, self.y - 8, rotulo.upper())
            self._campo(nome, x, self.y - 12 - altura, w, altura, multilinha=altura > 20)
            x += w + gap
        self.y -= altura + 20

    def caixa(self, rotulo: str, nome: str, altura: float):
        self.linha([(rotulo, nome, 1.0)], altura=altura)

    def marcadores(self, itens: list[str], prefixo: str, colunas: int = 3,
                   rotulo: str | None = None, extra: dict[str, float] | None = None):
        """Grade de caixas de marcar. `extra` poe um campo de texto ao lado do item."""
        c = self.c
        if rotulo:
            c.setFont("Helvetica", 7.5)
            c.setFillColor(CINZA)
            c.drawString(M, self.y - 8, rotulo.upper())
            self.y -= 14
        col_w = LARGURA / colunas
        extra = extra or {}
        for i, item in enumerate(itens):
            col, lin = i % colunas, i // colunas
            x = M + col * col_w
            y = self.y - lin * 18 - 12
            self.form.checkbox(
                name=f"{prefixo}_{_slug(item)}", x=x, y=y, size=10, borderWidth=0.8,
                borderColor=VERDE, fillColor=white, textColor=VERDE, buttonStyle="check",
            )
            c.setFont("Helvetica", 8.5)
            c.setFillColor(TINTA)
            c.drawString(x + 15, y + 2, item)
            if item in extra:
                tx = x + 15 + c.stringWidth(item, "Helvetica", 8.5) + 6
                self._campo(f"{prefixo}_{_slug(item)}_qual", tx, y - 2,
                            col_w * extra[item], 14)
        linhas = (len(itens) + colunas - 1) // colunas
        self.y -= linhas * 18 + 8

    def escala(self, rotulo: str, nome: str, esquerda: str, direita: str):
        """Escala 0 a 10 com um unico valor marcavel."""
        c = self.c
        c.setFont("Helvetica", 7.5)
        c.setFillColor(CINZA)
        c.drawString(M, self.y - 8, rotulo.upper())
        y = self.y - 36
        x0 = M + 70
        passo = (LARGURA - 140) / 10
        c.setFont("Helvetica", 7)
        c.drawRightString(x0 - 10, y + 3, esquerda)
        c.drawString(x0 + 10 * passo + 18, y + 3, direita)
        for n in range(11):
            x = x0 + n * passo
            self.form.radio(
                name=nome, value=str(n), x=x, y=y, size=11, borderWidth=0.8,
                borderColor=VERDE, fillColor=white, textColor=VERDE,
                buttonStyle="circle", selected=False,
            )
            c.setFillColor(TINTA)
            c.drawCentredString(x + 5.5, y + 15, str(n))
        self.y -= 50

    def texto(self, paragrafo: str, tamanho: float = 8.5):
        c = self.c
        c.setFont("Helvetica", tamanho)
        c.setFillColor(TINTA)
        for linha in _quebrar(c, paragrafo, LARGURA, tamanho):
            c.drawString(M, self.y - tamanho, linha)
            self.y -= tamanho + 3.5
        self.y -= 4

    def assinatura(self):
        c = self.c
        self.y -= 30
        c.setStrokeColor(TINTA)
        c.setLineWidth(0.6)
        c.line(M, self.y, M + 300, self.y)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(CINZA)
        c.drawString(M, self.y - 10, "ASSINATURA DO(A) CLIENTE")
        c.drawString(M + 330, self.y + 22, "DATA")
        self._campo("data_assinatura", M + 330, self.y - 2, LARGURA - 330, 18)
        self.y -= 24

    def salvar(self):
        self._rodape()
        self.c.save()


def _slug(texto: str) -> str:
    trocas = str.maketrans("áàâãéêíóôõúüçÁÉÍÓÚÇ", "aaaaeeiooouucAEIOUC")
    return "".join(ch if ch.isalnum() else "_" for ch in texto.translate(trocas).lower())


def _quebrar(c, texto, largura, tamanho):
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if c.stringWidth(tentativa, "Helvetica", tamanho) <= largura:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    return linhas + [atual]


def main():
    f = Ficha(SAIDA)

    # -- pagina 1 ---------------------------------------------------------- #
    f.nova_pagina()
    f.cabecalho()

    f.secao(1, "Dados do cliente")
    f.linha([("Nome completo", "nome", 0.72), ("Data", "data", 0.28)])
    f.linha([("Data de nascimento", "nascimento", 0.25), ("Telefone / WhatsApp", "telefone", 0.35),
             ("E-mail", "email", 0.40)])
    f.linha([("Profissão", "profissao", 0.40), ("Contato de emergência (nome e telefone)",
                                                "emergencia", 0.60)])

    f.secao(2, "Motivo da procura")
    f.caixa("Queixa principal: o que incomoda e há quanto tempo", "queixa", 32)
    f.marcadores(["Relaxamento", "Alívio de dor", "Tensão muscular", "Retenção de líquido",
                  "Recuperação pós-treino", "Outro:"], "objetivo", colunas=3,
                 rotulo="Objetivo da sessão", extra={"Outro:": 0.6})
    f.escala("Intensidade da dor hoje", "dor", "sem dor", "pior dor")

    f.secao(3, "Histórico de saúde (marque o que se aplica)")
    f.marcadores(["Hipertensão", "Diabetes", "Problema cardíaco", "Trombose ou varizes",
                  "Câncer (atual ou em tratamento)", "Osteoporose", "Hérnia de disco",
                  "Fratura ou lesão recente", "Cirurgia recente", "Doença ou lesão de pele",
                  "Febre ou infecção atual", "Epilepsia", "Labirintite", "Marca-passo",
                  "Gestante — semanas:"], "saude", colunas=3,
                 extra={"Gestante — semanas:": 0.2})
    f.aviso("Itens marcados podem exigir liberação médica antes da sessão.")
    f.linha([("Medicamentos em uso", "medicamentos", 0.5),
             ("Alergias (óleos, cremes, essências)", "alergias", 0.5)])
    f.linha([("Cirurgias anteriores (qual e quando)", "cirurgias", 0.6),
             ("Faz acompanhamento médico? Com quem?", "acompanhamento", 0.4)])

    f.secao(4, "Avaliação do profissional")
    f.marcadores(["Liberação médica solicitada", "Liberação médica apresentada"], "liberacao",
                 colunas=2)
    f.linha([("Técnica indicada", "tecnica", 0.5), ("Frequência sugerida", "frequencia", 0.5)])
    f.caixa("Observações do profissional", "obs_profissional", 24)

    # -- pagina 2 ---------------------------------------------------------- #
    f.nova_pagina()

    f.secao(5, "Hábitos")
    f.linha([("Atividade física (qual e frequência)", "atividade", 0.5),
             ("Horas de sono por noite", "sono", 0.25), ("Água por dia", "agua", 0.25)])
    f.marcadores(["Sentado", "Em pé", "Misto", "Esforço físico"], "trabalho", colunas=4,
                 rotulo="Rotina de trabalho")
    f.escala("Nível de estresse", "estresse", "tranquilo", "muito alto")

    f.secao(6, "Regiões com dor ou tensão")
    f.marcadores(["Cabeça", "Cervical (pescoço)", "Ombros", "Braços", "Mãos e punhos",
                  "Região torácica", "Lombar", "Glúteos", "Quadril", "Coxas", "Joelhos",
                  "Panturrilhas", "Pés"], "regiao", colunas=4)

    f.secao(7, "Preferências para a sessão")
    f.marcadores(["Leve", "Média", "Firme"], "pressao", colunas=4, rotulo="Pressão preferida")
    f.linha([("Áreas que prefere não receber toque", "evitar", 1.0)])
    f.caixa("Observações", "observacoes", 38)

    f.secao(8, "Declaração e consentimento")
    f.texto("Declaro que as informações acima são verdadeiras e me comprometo a informar "
            "qualquer mudança no meu estado de saúde antes das próximas sessões. Estou "
            "ciente de que a massoterapia não substitui tratamento médico.")
    f.texto("Autorizo o uso destes dados, incluindo os dados de saúde, exclusivamente para o "
            "meu atendimento, conforme a Lei Geral de Proteção de Dados (Lei 13.709/2018). "
            "Posso pedir a correção ou a exclusão destes dados a qualquer momento.")
    f.marcadores(["Autorizo contato por WhatsApp para lembretes de sessão"], "autoriza",
                 colunas=1)
    f.assinatura()

    f.salvar()
    print(f"salvo em {SAIDA}")


if __name__ == "__main__":
    main()
