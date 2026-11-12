
import cv2
import numpy as np


def processar_placa(imagem):
    """
    Recebe uma imagem recortada da placa.
    Retorna os caracteres separados em ordem.
    """

    cinza = cv2.cvtColor(
        imagem,
        cv2.COLOR_BGR2GRAY
    )

    # Suaviza ruídos
    cinza = cv2.GaussianBlur(
        cinza, (3, 3), 0
    )

    # Caracteres escuros viram brancos
    _, binaria = cv2.threshold(
        cinza,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    contornos, _ = cv2.findContours(
        binaria,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    altura_placa, largura_placa = cinza.shape

    candidatos = []

    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)

        # Filtra elementos muito pequenos ou grandes
        if (
            h > altura_placa * 0.30
            and h < altura_placa * 0.95
            and w > largura_placa * 0.015
            and w < largura_placa * 0.20
        ):
            candidatos.append((x, y, w, h))

    # Ordena da esquerda para a direita
    candidatos.sort(key=lambda item: item[0])

    caracteres = []

    for x, y, w, h in candidatos:
        caractere = binaria[y:y+h, x:x+w]

        # Mantém proporção e adiciona margens
        tamanho = 20
        escala = min(
            tamanho / w,
            tamanho / h
        )

        novo_w = max(1, int(w * escala))
        novo_h = max(1, int(h * escala))

        caractere = cv2.resize(
            caractere,
            (novo_w, novo_h)
        )

        imagem_final = np.full(
            (32, 32),
            255,
            dtype=np.uint8
        )

        inicio_x = (32 - novo_w) // 2
        inicio_y = (32 - novo_h) // 2

        # Inverte o caractere: branco vira preto
        caractere = cv2.bitwise_not(caractere)
        # Reduz ligeiramente a espessura dos traços pretos
        kernel = np.ones((2, 2), np.uint8)

        caractere = cv2.dilate(
            caractere,
            kernel,
            iterations=1
        )

        imagem_final[
            inicio_y:inicio_y+novo_h,
            inicio_x:inicio_x+novo_w
        ] = caractere

        caracteres.append(imagem_final)

    return caracteres, binaria, candidatos
