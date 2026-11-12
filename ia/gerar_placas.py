
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
import string

BASE = Path(__file__).resolve().parent
SAIDA = BASE / "placas_coleta"
SAIDA.mkdir(exist_ok=True)

random.seed(42)

LETRAS = string.ascii_uppercase
NUMEROS = string.digits

# Fontes disponíveis no Windows
FONTES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/bahnschrift.ttf",
]

def carregar_fonte(tamanho):
    for caminho in FONTES:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)

    raise FileNotFoundError("Nenhuma fonte encontrada.")


def gerar_combinacoes(quantidade=100):
    placas = set()

    while len(placas) < quantidade:
        placa = (
            "".join(random.choices(LETRAS, k=3))
            + random.choice(NUMEROS)
            + random.choice(LETRAS)
            + "".join(random.choices(NUMEROS, k=2))
        )

        placas.add(placa)

    return sorted(placas)


def criar_imagem(placa, numero):
    largura, altura = 640, 180

    imagem = Image.new(
        "RGB",
        (largura, altura),
        "white"
    )

    desenho = ImageDraw.Draw(imagem)

    # Faixa azul
    desenho.rectangle(
        (0, 0, largura, 45),
        fill="#1454A1"
    )

    fonte_topo = carregar_fonte(24)
    fonte_placa = carregar_fonte(100)

    desenho.text(
        (largura // 2, 22),
        "BRASIL",
        fill="white",
        font=fonte_topo,
        anchor="mm"
    )

    desenho.text(
        (largura // 2, 112),
        placa,
        fill="black",
        font=fonte_placa,
        anchor="mm"
    )

    desenho.rectangle(
        (2, 2, largura - 3, altura - 3),
        outline="black",
        width=3
    )

    caminho = SAIDA / f"placa_{numero:03d}_{placa}.png"
    imagem.save(caminho)


placas = gerar_combinacoes(100)

for i, placa in enumerate(placas, start=1):
    criar_imagem(placa, i)

(SAIDA / "lista_placas.txt").write_text(
    "\n".join(placas),
    encoding="utf-8"
)

print(f"{len(placas)} placas geradas!")
print(f"Arquivos salvos em: {SAIDA}")

from collections import Counter

contagem = Counter("".join(placas))

print("\nQuantidade de ocorrências por caractere:")

for caractere in LETRAS + NUMEROS:
    print(f"{caractere}: {contagem[caractere]}")