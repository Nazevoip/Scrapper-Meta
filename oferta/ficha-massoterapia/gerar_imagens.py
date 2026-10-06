"""Gera as imagens da pagina de vendas a partir do PDF da ficha.

    python oferta/ficha-massoterapia/gerar_imagens.py

Precisa do `pdftoppm` (poppler) e do Pillow.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

AQUI = Path(__file__).parent
PDF = AQUI / "ficha-anamnese-massoterapia.pdf"
ASSETS = AQUI / "pagina" / "assets"


def renderizar(dpi: int = 150) -> list[Image.Image]:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(PDF), f"{tmp}/p"], check=True)
        return [Image.open(p).convert("RGB") for p in sorted(Path(tmp).glob("p-*.png"))]


def com_sombra(img: Image.Image, angulo: float, raio: int = 18, opacidade: int = 90) -> Image.Image:
    """Gira a imagem e devolve RGBA com sombra suave, em canvas com folga."""
    folga = raio * 3
    base = Image.new("RGBA", (img.width + folga * 2, img.height + folga * 2), (0, 0, 0, 0))
    sombra = Image.new("L", base.size, 0)
    ImageDraw.Draw(sombra).rectangle(
        (folga, folga + raio // 2, folga + img.width, folga + img.height + raio // 2), fill=opacidade)
    sombra = sombra.filter(ImageFilter.GaussianBlur(raio))
    base.paste((20, 40, 35, 255), mask=sombra)
    base.paste(img.convert("RGBA"), (folga, folga))
    return base.rotate(angulo, resample=Image.BICUBIC, expand=True)


def celular(paginas: list[Image.Image], altura: int) -> Image.Image:
    """Moldura simples de celular com as paginas da ficha uma embaixo da outra."""
    gap = 24
    pagina = Image.new("RGB", (paginas[0].width, sum(p.height for p in paginas) + gap * (len(paginas) - 1)),
                       (210, 218, 215))
    y = 0
    for p in paginas:
        pagina.paste(p, (0, y))
        y += p.height + gap
    largura = int(altura * 0.49)
    borda, raio = int(altura * 0.025), int(altura * 0.075)
    tel = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(tel)
    d.rounded_rectangle((0, 0, largura - 1, altura - 1), raio, fill=(28, 34, 32, 255))
    tela_w, tela_h = largura - 2 * borda, altura - 2 * borda
    escala = tela_w / pagina.width
    tela = pagina.resize((tela_w, int(pagina.height * escala)), Image.LANCZOS).crop((0, 0, tela_w, tela_h))
    mascara = Image.new("L", (tela_w, tela_h), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, tela_w - 1, tela_h - 1), raio - borda, fill=255)
    tel.paste(tela, (borda, borda), mascara)
    d.rounded_rectangle((largura // 2 - largura // 8, borda + 6, largura // 2 + largura // 8,
                         borda + 6 + altura // 60), altura // 120, fill=(28, 34, 32, 255))
    return tel


def mockup(p1: Image.Image, p2: Image.Image, tamanho: tuple[int, int]) -> Image.Image:
    W, H = tamanho
    canvas = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    alt = int(H * 0.74)
    escala = alt / p1.height
    a = p1.resize((int(p1.width * escala), alt), Image.LANCZOS)
    b = p2.resize((int(p2.width * escala), alt), Image.LANCZOS)

    tras = com_sombra(b, 7)
    frente = com_sombra(a, -3)
    tel = com_sombra(celular([p1, p2], int(H * 0.56)), -2, raio=14, opacidade=110)

    cx = W // 2
    canvas.alpha_composite(tras, (cx - tras.width + int(W * 0.06), (H - tras.height) // 2))
    canvas.alpha_composite(frente, (cx - int(W * 0.12), (H - frente.height) // 2 + int(H * 0.02)))
    canvas.alpha_composite(tel, (cx + int(W * 0.19), H - tel.height - int(H * 0.01)))
    return canvas


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "fichas").mkdir(exist_ok=True)
    p1, p2 = renderizar()

    mockup(p1, p2, (1400, 933)).save(ASSETS / "hero-mockup.webp", quality=88, method=6)
    mockup(p1, p2, (1280, 853)).save(ASSETS / "mockup.webp", quality=88, method=6)
    for i, p in enumerate((p1, p2), 1):
        p.resize((566 * 2, 800 * 2), Image.LANCZOS).save(
            ASSETS / "fichas" / f"pagina-{i}.webp", quality=86, method=6)
    print(f"imagens salvas em {ASSETS}")


if __name__ == "__main__":
    main()
