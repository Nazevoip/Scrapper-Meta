"""Gera as imagens da pagina de vendas a partir dos PDFs das fichas.

    python oferta/kit-massoterapia/gerar_imagens.py

Precisa do `pdftoppm` (poppler) e do Pillow. Rode depois de `gerar_fichas.py`.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).parent
FICHAS = AQUI / "fichas"
ASSETS = AQUI / "pagina" / "assets"

PLUM = (116, 52, 79)
PLUM_ESCURO = (88, 37, 59)
ROSA = (245, 232, 237)
OURO = (212, 167, 91)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTE_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def renderizar(pdf: Path, dpi: int = 150) -> list[Image.Image]:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), f"{tmp}/p"], check=True)
        return [Image.open(p).convert("RGB") for p in sorted(Path(tmp).glob("p-*.png"))]


def com_sombra(img: Image.Image, angulo: float, raio: int = 16, opacidade: int = 80) -> Image.Image:
    """Gira a imagem e devolve RGBA com sombra suave, em canvas com folga."""
    folga = raio * 3
    base = Image.new("RGBA", (img.width + folga * 2, img.height + folga * 2), (0, 0, 0, 0))
    sombra = Image.new("L", base.size, 0)
    ImageDraw.Draw(sombra).rectangle(
        (folga, folga + raio // 2, folga + img.width, folga + img.height + raio // 2), fill=opacidade)
    sombra = sombra.filter(ImageFilter.GaussianBlur(raio))
    base.paste((60, 25, 40, 255), mask=sombra)
    base.paste(img.convert("RGBA"), (folga, folga))
    return base.rotate(angulo, resample=Image.BICUBIC, expand=True)


def celular(paginas: list[Image.Image], altura: int) -> Image.Image:
    """Moldura simples de celular com as paginas uma embaixo da outra."""
    gap = 24
    doc = Image.new("RGB", (paginas[0].width, sum(p.height for p in paginas) + gap * (len(paginas) - 1)),
                    (225, 214, 219))
    y = 0
    for p in paginas:
        doc.paste(p, (0, y))
        y += p.height + gap
    largura = int(altura * 0.49)
    borda, raio = int(altura * 0.025), int(altura * 0.075)
    tel = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(tel)
    d.rounded_rectangle((0, 0, largura - 1, altura - 1), raio, fill=(34, 28, 31, 255))
    tela_w, tela_h = largura - 2 * borda, altura - 2 * borda
    tela = doc.resize((tela_w, int(doc.height * tela_w / doc.width)), Image.LANCZOS).crop((0, 0, tela_w, tela_h))
    mascara = Image.new("L", (tela_w, tela_h), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, tela_w - 1, tela_h - 1), raio - borda, fill=255)
    tel.paste(tela, (borda, borda), mascara)
    d.rounded_rectangle((largura // 2 - largura // 8, borda + 6, largura // 2 + largura // 8,
                         borda + 6 + altura // 60), altura // 120, fill=(34, 28, 31, 255))
    return tel


def mockup(paginas: list[Image.Image], tamanho: tuple[int, int]) -> Image.Image:
    """Leque de fichas com um celular na frente, fundo transparente."""
    W, H = tamanho
    canvas = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    alt = int(H * 0.62)
    escala = alt / paginas[0].height
    folhas = [p.resize((int(p.width * escala), alt), Image.LANCZOS) for p in paginas]

    # (indice da folha, angulo, x relativo ao centro, y relativo ao topo)
    leque = [(3, 9, -0.40, 0.10), (2, 4, -0.24, 0.04), (1, -4, 0.10, 0.06), (0, -1, -0.10, 0.17)]
    for i, ang, dx, dy in leque:
        img = com_sombra(folhas[i], ang)
        canvas.alpha_composite(img, (int(W / 2 + dx * W - img.width / 2 + folhas[i].width / 2),
                                     int(dy * H)))
    tel = com_sombra(celular([paginas[0], paginas[1]], int(H * 0.6)), -3, raio=14, opacidade=110)
    canvas.alpha_composite(tel, (int(W * 0.66), H - tel.height - int(H * 0.01)))
    return canvas


def capa_bonus(titulo: str, subtitulo: str, icone: str, caminho: Path, lado: int = 640):
    """Capa quadrada simples para os bonus."""
    img = Image.new("RGB", (lado, lado), PLUM)
    d = ImageDraw.Draw(img)
    for y in range(lado):  # degrade vertical
        t = y / lado
        cor = tuple(int(PLUM[k] * (1 - t) + PLUM_ESCURO[k] * t) for k in range(3))
        d.line([(0, y), (lado, y)], fill=cor)
    d.rounded_rectangle((40, 40, lado - 40, lado - 40), 36, outline=OURO, width=3)
    d.ellipse((lado / 2 - 80, 110, lado / 2 + 80, 270), fill=ROSA)
    f_ic = ImageFont.truetype(FONTE, 84)
    d.text((lado / 2, 190), icone, font=f_ic, fill=PLUM, anchor="mm")
    f_tit = ImageFont.truetype(FONTE, 42)
    y = 330
    for linha in titulo.split("\n"):
        d.text((lado / 2, y), linha, font=f_tit, fill="white", anchor="mm")
        y += 54
    f_sub = ImageFont.truetype(FONTE_REG, 24)
    d.text((lado / 2, y + 22), subtitulo, font=f_sub, fill=OURO, anchor="mm")
    img.save(caminho, quality=88, method=6)


def main():
    (ASSETS / "fichas").mkdir(parents=True, exist_ok=True)
    (ASSETS / "bonuses").mkdir(exist_ok=True)

    anamnese = renderizar(FICHAS / "ficha-anamnese.pdf")
    evolucao, = renderizar(FICHAS / "evolucao-acompanhamento.pdf")
    pacotes, = renderizar(FICHAS / "controle-sessoes-pacotes.pdf")
    fechamento, = renderizar(FICHAS / "fechamento-mensal.pdf")

    leque = [anamnese[0], evolucao, pacotes, fechamento]
    mockup(leque, (1400, 933)).save(ASSETS / "hero-mockup-transparent.webp", quality=88, method=6)
    mockup(leque, (1280, 853)).save(ASSETS / "mockup.webp", quality=88, method=6)

    esteira = {
        "anamnese-1": anamnese[0], "fechamento-mensal": fechamento,
        "evolucao-acompanhamento": evolucao, "controle-sessoes-pacotes": pacotes,
        "anamnese-2": anamnese[1],
    }
    for nome, pagina in esteira.items():
        pagina.resize((1100, 1556), Image.LANCZOS).save(
            ASSETS / "fichas" / f"{nome}.webp", quality=86, method=6)

    capa_bonus("Pack de Mimos\npara Clientes", "fidelidade · presente · indicação", "♥",
               ASSETS / "bonuses" / "pack-mimos-clientes.webp")
    capa_bonus("Kit Agenda Cheia\nno WhatsApp", "50 respostas prontas", "✉",
               ASSETS / "bonuses" / "agenda-whatsapp.webp")
    capa_bonus("Calculadora de\nPreço & Lucro", "sessões e pacotes", "%",
               ASSETS / "bonuses" / "calculadora.webp")
    print(f"imagens salvas em {ASSETS}")


if __name__ == "__main__":
    main()
