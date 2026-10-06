"""Gera o Kit Massoterapia Organizada editavel (PPTX para importar no Canva).

Cada pagina e desenhada algumas vezes num documento de rascunho ate o conteudo
encostar no limite inferior da folha; so a versao final vai para o arquivo.
"""
import sys

from base import Doc
import estilo_a

MODULOS = [estilo_a]
try:
    import estilo_b
    MODULOS.append(estilo_b)
except ImportError:
    pass

INICIO = 135  # onde o conteudo comeca, mais ou menos, em todas as paginas


def ajustar(mod, fn):
    v = 1.0
    for _ in range(6):
        mod.ESC["v"], mod.ESC["t"] = v, min(1.2, 1 + (v - 1) * 0.35)
        fim, limite = fn(Doc())
        if abs(fim - limite) < 3:
            break
        v = max(0.8, min(2.2, v * (limite - INICIO) / (fim - INICIO)))
    return v


saida = sys.argv[1] if len(sys.argv) > 1 else "kit.pptx"
doc = Doc()
total = 0
for mod in MODULOS:
    for fn in mod.PAGINAS:
        v = ajustar(mod, fn)
        mod.ESC["v"], mod.ESC["t"] = v, min(1.2, 1 + (v - 1) * 0.35)
        fim, limite = fn(doc)
        total += 1
        print(f"{total:2d} {fn.__name__:22s} espaco x{v:.2f}  fim {fim:.0f} / limite {limite:.0f}")
doc.salvar(saida)
print("ok", total, "paginas ->", saida)
