
import time
import cv2
import serial
from serial.tools import list_ports

from reconhecer_placa import reconhecer_placa

# CONFIGURAÇÕES
PORTA_ARDUINO = "COM14"
VELOCIDADE = 9600
CAMERA_ID = 0

# Modo de teste: exige confirmação manual
MODO_TESTE = True


def listar_portas():
    print("\nPortas seriais disponíveis:")

    for porta in list_ports.comports():
        print(f"  {porta.device} - {porta.description}")


def capturar_placa():
    camera = cv2.VideoCapture(CAMERA_ID)

    if not camera.isOpened():
        print("ERRO: não foi possível abrir a webcam.")
        return None

    print("\nWebcam aberta.")
    print("Posicione a placa no retângulo.")
    print("ESPAÇO: capturar | Q: cancelar")

    imagem = None

    try:
        cv2.namedWindow("Reconhecimento", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Reconhecimento", 900, 600)

        while True:
            ok, frame = camera.read()

            if not ok:
                print("Erro ao ler webcam.")
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

            cv2.putText(
                tela,
                "ESPACO: capturar | Q: cancelar",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.imshow("Reconhecimento", tela)

            tecla = cv2.waitKeyEx(30)

            if tecla in (ord("q"), ord("Q"), 27):
                print("Captura cancelada.")
                break

            if tecla == 32:
                imagem = frame[y1:y2, x1:x2].copy()
                print("Imagem capturada!")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    return imagem


def processar_veiculo(arduino, sentido):
    print(f"\n{'=' * 40}")
    print(f"VEÍCULO DETECTADO: {sentido}")
    print(f"{'=' * 40}")

    imagem = capturar_placa()

    if imagem is None:
        print("Nenhuma imagem capturada.")
        return

    try:
        resultado = reconhecer_placa(imagem)

    except Exception as erro:
        print(f"Erro no reconhecimento: {erro}")
        return

    print("\nRESULTADO DA IA:")
    print(resultado)

    if not resultado["sucesso"]:
        print("Reconhecimento não realizado.")
        return

    placa = resultado["placa"]

    print(f"\nPlaca reconhecida: {placa}")
    print(f"Confiança informada: {resultado['confianca']}")

    # Nesta etapa não existe autorização automática.
    # A abertura depende de confirmação manual.
    if MODO_TESTE:
        resposta = input(
            f"\nAbrir cancela de {sentido}? (s/n): "
        ).strip().lower()

        if resposta != "s":
            print("Abertura cancelada.")
            return
    else:
        print("Abertura automática desabilitada.")
        return

    comando = f"ABRIR:{sentido}\n"

    arduino.write(comando.encode("utf-8"))
    arduino.flush()

    print(f"Comando enviado: {comando.strip()}")


def main():
    listar_portas()

    print(f"\nConectando ao Arduino em {PORTA_ARDUINO}...")

    try:
        arduino = serial.Serial(
            PORTA_ARDUINO,
            VELOCIDADE,
            timeout=0.5
        )

    except serial.SerialException as erro:
        print(f"Erro ao conectar: {erro}")
        return

    # O Arduino Uno normalmente reinicia ao abrir a serial.
    time.sleep(2)

    print("\nConectado ao Arduino!")
    print("Aguardando detecção de veículos...")
    print("CTRL+C para encerrar.\n")

    # Evita processar repetidamente a mesma detecção
    # enquanto o sensor continua ocupado.
    sensores_ocupados = {
        "ENTRADA": False,
        "SAIDA": False
    }

    try:
        while True:
            linha = arduino.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if not linha:
                continue

            print(f"[ARDUINO] {linha}")

            if linha.startswith("#"):
                continue

            if linha.startswith("SENSOR_LIVRE:"):
                sentido = linha.split(":", 1)[1]

                if sentido in sensores_ocupados:
                    sensores_ocupados[sentido] = False

                continue

            if linha.startswith("CARRO_DETECTADO:"):
                sentido = linha.split(":", 1)[1]

                if sentido not in sensores_ocupados:
                    continue

                if sensores_ocupados[sentido]:
                    continue

                sensores_ocupados[sentido] = True

                processar_veiculo(arduino, sentido)

            elif linha.startswith("ERRO_SENSOR:"):
                print("ATENÇÃO: falha em um sensor.")

    except KeyboardInterrupt:
        print("\nIntegração encerrada.")

    finally:
        arduino.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
