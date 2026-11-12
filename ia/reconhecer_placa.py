
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf

from processar_imagem import processar_placa

BASE = Path(__file__).resolve().parent

modelo = tf.keras.models.load_model(
    BASE / "modelos" / "placas_cnn.keras"
)

classes = (
    BASE / "modelos" / "classes.txt"
).read_text(encoding="utf-8").splitlines()


def reconhecer_placa(imagem):
    caracteres, _, _ = processar_placa(imagem)

    if len(caracteres) != 7:
        return {
            "sucesso": False,
            "placa": None,
            "confianca": None,
            "erro": "SEGMENTACAO_INVALIDA"
        }

    # Prepara os sete caracteres para a CNN
    entrada = np.array(
        caracteres,
        dtype=np.float32
    ).reshape(-1, 32, 32, 1)

    previsoes = modelo.predict(
        entrada,
        verbose=0
    )

    placa = ""
    confiancas = []

    for i, previsao in enumerate(previsoes):
        indice = int(np.argmax(previsao))

        placa += classes[indice]
        confiancas.append(float(previsao[indice]))

        melhores = np.argsort(previsao)[-3:][::-1]

        print(f"\nCaractere {i + 1}:")
        for j in melhores:
            print(
                f"  {classes[j]}: {previsao[j] * 100:.2f}%"
            )

    return {
        "sucesso": True,
        "placa": placa,
        "confianca": round(min(confiancas), 4),
        "erro": None
    }


if __name__ == "__main__":
    imagem = cv2.imread(
        str(BASE / "resultados" / "placa_capturada.png")
    )

    if imagem is None:
        print("Imagem não encontrada.")
    else:
        resultado = reconhecer_placa(imagem)
        print("\nResultado da IA:")
        print(resultado)
