
import time
from datetime import datetime
import cv2
import serial
from serial.tools import list_ports

from reconhecer_placa import reconhecer_placa
from estacionamento import (
    entrada_veiculo,
    consultar_saida,
    finalizar_saida
)

# CONFIGURAÇÕES
PORTA_ARDUINO = "COM14"
VELOCIDADE = 9600
CAMERA_ID = 0

# Mantemos a confirmação manual na demonstração
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


def confirmar_placa(placa_ia):
    print(f"\nPlaca reconhecida pela IA: {placa_ia}")

    while True:
        resposta = input(
            "Confirme a placa ou digite a correção "
            "(ENTER para aceitar / C para cancelar): "
        ).strip().upper()

        if resposta == "C":
            return None

        placa = resposta if resposta else placa_ia

        if len(placa) == 7 and placa.isalnum():
            return placa

        print("Placa inválida. Digite 7 letras/números.")


def confirmar(mensagem):
    if not MODO_TESTE:
        return False

    resposta = input(
        f"\n{mensagem} (s/n): "
    ).strip().lower()

    return resposta == "s"


def enviar_abertura(arduino, sentido):
    comando = f"ABRIR:{sentido}\n"

    arduino.write(comando.encode("utf-8"))
    arduino.flush()

    print(f"Comando enviado: {comando.strip()}")


def mostrar_cobranca(consulta):
    entrada = consulta["entrada"].astimezone()
    saida = consulta["saida"].astimezone()

    print("\n" + "=" * 40)
    print("RESUMO DO ESTACIONAMENTO")
    print("=" * 40)

    print(f"Placa: {consulta['placa']}")
    print(f"Entrada: {entrada:%d/%m/%Y %H:%M:%S}")
    print(f"Saída: {saida:%d/%m/%Y %H:%M:%S}")
    print(
        f"Minutos cobrados: "
        f"{consulta['minutos_cobrados']}"
    )
    print(f"Valor a pagar: R$ {consulta['valor']:.2f}")

    print("=" * 40)


def processar_entrada(arduino, placa):
    try:
        registro = entrada_veiculo(placa)

    except Exception as erro:
        print(f"Não foi possível registrar entrada: {erro}")
        return

    print("\nEntrada registrada no Supabase!")
    print(f"Placa: {registro['placa']}")
    print(f"Horário: {registro['entrada']}")

    if confirmar("Abrir cancela de ENTRADA?"):
        enviar_abertura(arduino, "ENTRADA")
    else:
        print(
            "Abertura cancelada. "
            "ATENÇÃO: a entrada já foi registrada no banco."
        )


def processar_saida(arduino, placa):
    try:
        consulta = consultar_saida(placa)

    except Exception as erro:
        print(f"Não foi possível consultar saída: {erro}")
        return

    mostrar_cobranca(consulta)

    if not confirmar(
        "Confirmar cobrança e liberar saída?"
    ):
        print("Saída cancelada. Registro continua ativo.")
        return

    try:
        # Atualiza a cobrança usando o horário atual.
        consulta = consultar_saida(placa)

        registro = finalizar_saida(consulta)

    except Exception as erro:
        print(f"Não foi possível finalizar saída: {erro}")
        return

    print("\nSaída registrada no Supabase!")
    print(f"Valor final: R$ {float(registro['valor']):.2f}")

    enviar_abertura(arduino, "SAIDA")


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

    placa = confirmar_placa(resultado["placa"])

    if placa is None:
        print("Operação cancelada.")
        return

    print(f"\nPlaca confirmada: {placa}")
    print(f"Confiança da IA: {resultado['confianca']}")

    if sentido == "ENTRADA":
        processar_entrada(arduino, placa)

    elif sentido == "SAIDA":
        processar_saida(arduino, placa)


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

    time.sleep(2)

    print("\nConectado ao Arduino!")
    print("Aguardando detecção de veículos...")
    print("CTRL+C para encerrar.\n")

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
