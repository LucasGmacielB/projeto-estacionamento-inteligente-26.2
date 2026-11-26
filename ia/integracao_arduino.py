
import os
import sys
import time
import re
from pathlib import Path

# CONFIGURACAO AUTOMATICA DO TCL/TK
python_dir = Path(sys.base_prefix)

tcl_dir = python_dir / "tcl" / "tcl8.6"
tk_dir = python_dir / "tcl" / "tk8.6"

if (tcl_dir / "init.tcl").exists():
    os.environ["TCL_LIBRARY"] = str(tcl_dir)

if (tk_dir / "tk.tcl").exists():
    os.environ["TK_LIBRARY"] = str(tk_dir)

import cv2
import serial
from serial.tools import list_ports

from popup_pagamento import abrir_popup_pagamento
from reconhecer_placa import reconhecer_placa

from estacionamento import (
    entrada_veiculo,
    consultar_saida,
    finalizar_saida
)


# CONFIGURACOES DO HARDWARE

PORTA_ARDUINO = "COM14"
VELOCIDADE = 9600
CAMERA_ID = 0


# CONFIGURACOES DO RECONHECIMENTO AUTOMATICO

CONFIANCA_MINIMA = 0.90
LEITURAS_NECESSARIAS = 5
INTERVALO_LEITURAS = 0.5
TEMPO_MAXIMO_RECONHECIMENTO = 30
TEMPO_PREPARACAO_CAMERA = 2

PERMITIR_CONFIRMACAO_MANUAL = True


def listar_portas():
    print("\nPortas seriais disponíveis:")

    for porta in list_ports.comports():
        print(f"  {porta.device} - {porta.description}")


def validar_placa(placa):
    placa = placa.strip().upper()

    # Formato antigo: ABC1234
    formato_antigo = r"[A-Z]{3}[0-9]{4}"

    # Formato Mercosul: ABC1D23
    formato_mercosul = r"[A-Z]{3}[0-9][A-Z][0-9]{2}"

    return bool(
        re.fullmatch(formato_antigo, placa)
        or re.fullmatch(formato_mercosul, placa)
    )


def confirmar_placa(placa_ia=None):
    if placa_ia:
        print(f"\nÚltima placa reconhecida: {placa_ia}")

    while True:
        resposta = input(
            "Digite a placa correta "
            "(ENTER para aceitar a sugestão / C para cancelar): "
        ).strip().upper()

        if resposta == "C":
            return None

        placa = resposta or placa_ia

        if placa and validar_placa(placa):
            return placa

        print("Formato de placa inválido.")


def reconhecer_automaticamente():
    camera = cv2.VideoCapture(CAMERA_ID)

    if not camera.isOpened():
        print("ERRO: não foi possível abrir a webcam.")
        camera.release()
        return None

    print("\nWebcam aberta.")
    print("Posicione a placa no retângulo.")
    print("Reconhecimento automático iniciado.")
    print("Pressione Q para cancelar.")

    placa_anterior = None
    ultima_placa = None
    placa_validada = None

    confianca_atual = 0.0
    leituras_consecutivas = 0

    inicio = time.monotonic()
    ultima_leitura = inicio
    cancelado = False

    try:
        cv2.namedWindow(
            "Reconhecimento Automatico",
            cv2.WINDOW_NORMAL
        )

        cv2.resizeWindow(
            "Reconhecimento Automatico",
            900,
            600
        )

        while True:
            agora = time.monotonic()
            tempo_decorrido = agora - inicio

            if tempo_decorrido >= TEMPO_MAXIMO_RECONHECIMENTO:
                print("\nTempo máximo de reconhecimento atingido.")
                break

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

            # Retangulo de posicionamento
            cv2.rectangle(
                tela,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Aguarda a estabilizacao da camera
            if tempo_decorrido >= TEMPO_PREPARACAO_CAMERA:

                # Realiza reconhecimento em intervalos
                if agora - ultima_leitura >= INTERVALO_LEITURAS:

                    ultima_leitura = agora

                    imagem = frame[y1:y2, x1:x2].copy()

                    try:
                        resultado = reconhecer_placa(imagem)

                        if resultado["sucesso"]:

                            placa = resultado["placa"].strip().upper()

                            confianca = float(
                                resultado["confianca"]
                            )

                            ultima_placa = placa
                            confianca_atual = confianca

                            if (
                                confianca >= CONFIANCA_MINIMA
                                and validar_placa(placa)
                            ):

                                if placa == placa_anterior:
                                    leituras_consecutivas += 1

                                else:
                                    placa_anterior = placa
                                    leituras_consecutivas = 1

                                print(
                                    f"[IA] Placa: {placa} | "
                                    f"Confiança: {confianca:.2%} | "
                                    f"Validação: "
                                    f"{leituras_consecutivas}/"
                                    f"{LEITURAS_NECESSARIAS}"
                                )

                                if (
                                    leituras_consecutivas
                                    >= LEITURAS_NECESSARIAS
                                ):
                                    placa_validada = placa

                            else:
                                placa_anterior = None
                                leituras_consecutivas = 0

                                print(
                                    f"[IA] Leitura não validada: "
                                    f"{placa} | {confianca:.2%}"
                                )

                        else:
                            placa_anterior = None
                            leituras_consecutivas = 0

                    except Exception as erro:
                        placa_anterior = None
                        leituras_consecutivas = 0

                        print(f"[IA] Erro na leitura: {erro}")

            # INFORMACOES NA TELA

            tempo_restante = max(
                0,
                int(
                    TEMPO_MAXIMO_RECONHECIMENTO
                    - tempo_decorrido
                )
            )

            cv2.putText(
                tela,
                "RECONHECIMENTO AUTOMATICO",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                tela,
                f"Placa: {ultima_placa or 'Aguardando...'}",
                (15, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                tela,
                f"Confianca: {confianca_atual:.1%}",
                (15, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                tela,
                f"Validacao: {leituras_consecutivas}/"
                f"{LEITURAS_NECESSARIAS}",
                (15, altura - 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.putText(
                tela,
                f"Tempo: {tempo_restante}s | Q: cancelar",
                (15, altura - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "Reconhecimento Automatico",
                tela
            )

            tecla = cv2.waitKeyEx(1)

            if tecla in (ord("q"), ord("Q"), 27):
                print("Reconhecimento cancelado.")
                cancelado = True
                break

            if placa_validada:
                print("\nPLACA VALIDADA AUTOMATICAMENTE!")
                print(f"Placa: {placa_validada}")
                print(f"Confiança: {confianca_atual:.2%}")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    if cancelado:
        return None

    if placa_validada:
        return placa_validada

    # Alternativa manual em caso de falha
    if PERMITIR_CONFIRMACAO_MANUAL:
        print("\nNão foi possível validar automaticamente.")
        return confirmar_placa(ultima_placa)

    return None


def enviar_abertura(arduino, sentido):
    comando = f"ABRIR:{sentido}\n"

    arduino.write(comando.encode("utf-8"))
    arduino.flush()

    print(f"Comando enviado: {comando.strip()}")


def processar_entrada(arduino, placa):
    print("\n" + "=" * 40)
    print("REGISTRO AUTOMATICO DE ENTRADA")
    print("=" * 40)

    try:
        registro = entrada_veiculo(placa)

    except Exception as erro:
        print(f"Erro ao registrar entrada: {erro}")
        return

    print("\nENTRADA REGISTRADA COM SUCESSO!")
    print(f"Placa: {registro['placa']}")
    print(f"Horário: {registro['entrada']}")

    # Abertura automatica sem confirmacao manual
    try:
        enviar_abertura(arduino, "ENTRADA")

    except Exception as erro:
        print(f"Erro ao enviar comando: {erro}")
        print(
            "ATENÇÃO: entrada registrada no banco, "
            "mas abertura não confirmada."
        )


def processar_saida(arduino, placa):
    print("\n" + "=" * 40)
    print("REGISTRO AUTOMATICO DE SAIDA")
    print("=" * 40)

    try:
        consulta = consultar_saida(placa)

        # Exibe automaticamente o popup de pagamento
        metodo = abrir_popup_pagamento(consulta)

        if metodo is None:
            print("Pagamento cancelado.")
            print("Veículo permanece estacionado.")
            return

        # Mantem o valor exibido no popup
        registro = finalizar_saida(consulta)

    except Exception as erro:
        print(f"Erro ao processar saída: {erro}")
        return

    print("\n" + "=" * 40)
    print("PAGAMENTO SIMULADO CONFIRMADO")
    print("=" * 40)

    print(f"Placa: {registro['placa']}")
    print(f"Pagamento: {metodo.upper()}")
    print(f"Minutos cobrados: {consulta['minutos_cobrados']}")
    print(f"Valor: R$ {float(registro['valor']):.2f}")
    print(f"Status: {registro['status']}")

    # Abertura automatica apos pagamento
    try:
        enviar_abertura(arduino, "SAIDA")

    except Exception as erro:
        print(f"Erro ao enviar comando: {erro}")
        print(
            "ATENÇÃO: saída finalizada no banco, "
            "mas abertura não confirmada."
        )


def processar_veiculo(arduino, sentido):
    print("\n" + "=" * 40)
    print(f"VEÍCULO DETECTADO: {sentido}")
    print("=" * 40)

    # Reconhecimento sem interacao manual
    placa = reconhecer_automaticamente()

    if placa is None:
        print("Operação cancelada ou placa não identificada.")
        return

    print(f"\nPlaca identificada: {placa}")

    if sentido == "ENTRADA":
        processar_entrada(arduino, placa)

    elif sentido == "SAIDA":
        processar_saida(arduino, placa)


def main():
    listar_portas()

    print(
        f"\nConectando ao Arduino em "
        f"{PORTA_ARDUINO}..."
    )

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

    print("\n" + "=" * 40)
    print("ESTACIONAMENTO INTELIGENTE")
    print("MODO AUTOMATICO")
    print("=" * 40)

    print("Conectado ao Arduino!")
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

            # Ignora mensagens de debug
            if linha.startswith("#"):
                continue

            print(f"[ARDUINO] {linha}")

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

            elif linha.startswith("ERRO_SERVO:"):
                print("ATENÇÃO: falha na configuração do servo.")

            elif linha.startswith("CANCELA_ABERTA:"):
                sentido = linha.split(":", 1)[1]

                print(
                    f"Arduino informou abertura "
                    f"da cancela de {sentido}."
                )

            elif linha.startswith("CANCELA_FECHADA:"):
                sentido = linha.split(":", 1)[1]

                print(
                    f"Arduino informou fechamento "
                    f"da cancela de {sentido}."
                )

    except KeyboardInterrupt:
        print("\nIntegração encerrada.")

    except serial.SerialException as erro:
        print(f"\nErro na comunicação serial: {erro}")

    finally:
        arduino.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
