
import cv2
from pathlib import Path
from processar_imagem import processar_placa

BASE = Path(__file__).resolve().parent
RESULTADOS = BASE / "resultados"
RESULTADOS.mkdir(exist_ok=True)

# Webcam externa
camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("Erro ao abrir a webcam.")
    exit()

print("Webcam iniciada!")
print("Posicione a placa dentro do retângulo.")
print("Pressione ESPAÇO para capturar.")
print("Pressione Q para sair.")

while True:
    sucesso, frame = camera.read()

    if not sucesso:
        print("Erro ao capturar imagem.")
        break

    altura, largura = frame.shape[:2]

    # Área central de captura
    x1 = int(largura * 0.15)
    x2 = int(largura * 0.85)
    y1 = int(altura * 0.35)
    y2 = int(altura * 0.65)

    visualizacao = frame.copy()

    cv2.rectangle(
        visualizacao,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    cv2.putText(
        visualizacao,
        "Posicione a placa aqui",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.imshow("Teste da Webcam", visualizacao)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord("q"):
        break

    if tecla == 32:
        placa = frame[y1:y2, x1:x2].copy()

        caracteres, binaria, candidatos = (
            processar_placa(placa)
        )

        print(
            f"\nCaracteres encontrados: {len(caracteres)}"
        )

        cv2.imwrite(
            str(RESULTADOS / "placa_capturada.png"),
            placa
        )

        cv2.imwrite(
            str(RESULTADOS / "placa_binaria.png"),
            binaria
        )

        # Exibe os caracteres identificados
        for i, caractere in enumerate(caracteres):
            cv2.imwrite(
                str(RESULTADOS / f"caractere_{i+1}.png"),
                caractere
            )

            cv2.imshow(
                f"Caractere {i+1}",
                caractere
            )

        if len(caracteres) == 7:
            print("Sete caracteres separados!")
        else:
            print(
                "A segmentação precisa de ajustes."
            )

camera.release()
cv2.destroyAllWindows()
