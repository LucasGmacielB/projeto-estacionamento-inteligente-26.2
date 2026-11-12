
from pathlib import Path
from datetime import datetime
import csv
import cv2
import numpy as np

from processar_imagem import processar_placa

BASE = Path(__file__).resolve().parent
SAIDA = BASE / "dataset_real"
SAIDA.mkdir(exist_ok=True)

CAMERA_ID = 1

# Cria pastas para todas as classes
for caractere in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    (SAIDA / caractere).mkdir(exist_ok=True)


def montar_previa(caracteres):
    """Monta uma imagem com os 7 caracteres lado a lado."""
    blocos = []

    for i, caractere in enumerate(caracteres):
        ampliado = cv2.resize(
            caractere,
            (96, 96),
            interpolation=cv2.INTER_NEAREST
        )

        bloco = cv2.cvtColor(
            ampliado,
            cv2.COLOR_GRAY2BGR
        )

        cv2.putText(
            bloco,
            str(i + 1),
            (5, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1
        )

        blocos.append(bloco)

    return np.hstack(blocos)


def salvar_coleta(placa, caracteres):
    identificador = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    registros = []

    for posicao, (rotulo, imagem) in enumerate(
        zip(placa, caracteres), start=1
    ):
        nome = (
            f"{identificador}_"
            f"{placa}_pos{posicao}.png"
        )

        destino = SAIDA / rotulo / nome

        if not cv2.imwrite(str(destino), imagem):
            raise IOError(f"Erro ao salvar {destino}")

        registros.append([
            identificador,
            placa,
            posicao,
            rotulo,
            str(destino.relative_to(BASE))
        ])

    # Guarda a origem de cada imagem para separar
    # treino e teste por captura, sem misturá-los.
    arquivo_csv = SAIDA / "coletas.csv"
    novo = not arquivo_csv.exists()

    with open(
        arquivo_csv,
        "a",
        newline="",
        encoding="utf-8"
    ) as arquivo:
        escritor = csv.writer(arquivo)

        if novo:
            escritor.writerow([
                "captura_id",
                "placa",
                "posicao",
                "rotulo",
                "arquivo"
            ])

        escritor.writerows(registros)

    print(f"\nColeta salva: {placa}")


def main():
    camera = cv2.VideoCapture(CAMERA_ID)

    if not camera.isOpened():
        print("Não foi possível abrir a webcam.")
        return

    print("\n=== COLETA DE DATASET ===")
    print("Digite a placa exibida no celular.")
    print("ESPAÇO: capturar | Q: sair")

    try:
        while True:
            placa = input(
                "\nPlaca que será exibida (ou SAIR): "
            ).strip().upper()

            if placa == "SAIR":
                break

            if (
                len(placa) != 7
                or not placa.isalnum()
                or not placa.isascii()
            ):
                print("Informe 7 letras/números ASCII.")
                continue

            print(f"Posicione a placa {placa} na webcam.")
            cv2.namedWindow("Coleta", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Coleta", 900, 600)

            while True:
                ok, frame = camera.read()

                if not ok:
                    print("Erro ao capturar imagem.")
                    break

                altura, largura = frame.shape[:2]

                x1 = int(largura * 0.15)
                x2 = int(largura * 0.85)
                y1 = int(altura * 0.35)
                y2 = int(altura * 0.65)

                tela = frame.copy()

                cv2.rectangle(
                    tela,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.imshow("Coleta", tela)

                # Aguarda a janela processar eventos
                tecla = cv2.waitKeyEx(30)

                # Q ou ESC: sair da captura
                if tecla in (ord("q"), ord("Q"), 27):
                    print("Captura cancelada.")
                    break

                # ESPAÇO: capturar imagem
                if tecla != 32:
                    continue

                print("Espaço detectado! Capturando imagem...")

                recorte = frame[y1:y2, x1:x2].copy()

                caracteres, _, _ = processar_placa(
                    recorte
                )

                if len(caracteres) != 7:
                    print(
                        f"Encontrados {len(caracteres)} "
                        "caracteres. Tente novamente."
                    )
                    continue

                previa = montar_previa(caracteres)

                cv2.imshow("Conferir caracteres", previa)

                print(
                    "\nConfira a janela com os caracteres."
                )
                print(
                    "Pressione S na janela para salvar."
                )
                print(
                    "Pressione qualquer outra tecla "
                    "para descartar."
                )

                confirmacao = cv2.waitKey(0) & 0xFF
                cv2.destroyWindow("Conferir caracteres")

                if confirmacao == ord("s"):
                    salvar_coleta(placa, caracteres)
                    break

                print("Captura descartada.")

            cv2.destroyWindow("Coleta")

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
