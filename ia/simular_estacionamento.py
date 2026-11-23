
import cv2

from popup_pagamento import abrir_popup_pagamento
from reconhecer_placa import reconhecer_placa
from estacionamento import (
    entrada_veiculo,
    consultar_saida,
    finalizar_saida
)

CAMERA_ID = 0


def capturar_placa():
    camera = cv2.VideoCapture(CAMERA_ID)

    if not camera.isOpened():
        print("Erro ao abrir webcam.")
        return None

    imagem = None

    try:
        cv2.namedWindow("Simulador", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Simulador", 900, 600)

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

            cv2.putText(
                tela,
                "ESPACO: capturar | Q: cancelar",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.imshow("Simulador", tela)

            tecla = cv2.waitKeyEx(30)

            if tecla in (ord("q"), ord("Q"), 27):
                break

            if tecla == 32:
                imagem = frame[y1:y2, x1:x2].copy()
                print("Imagem capturada!")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    return imagem


def identificar_placa():
    imagem = capturar_placa()

    if imagem is None:
        print("Captura cancelada.")
        return None

    try:
        resultado = reconhecer_placa(imagem)
    except Exception as erro:
        print(f"Erro na IA: {erro}")
        return None

    if not resultado["sucesso"]:
        print("A IA não conseguiu reconhecer a placa.")
        return None

    print("\nRESULTADO DA CNN")
    print(f"Placa: {resultado['placa']}")
    print(f"Confiança: {resultado['confianca']}")

    while True:
        resposta = input(
            "\nENTER para confirmar, "
            "digite a placa correta ou C para cancelar: "
        ).strip().upper()

        if resposta == "C":
            return None

        placa = resposta or resultado["placa"]

        if len(placa) == 7 and placa.isalnum():
            return placa

        print("A placa deve conter 7 caracteres.")


def simular_entrada():
    print("\n=== SIMULAÇÃO DE ENTRADA ===")

    placa = identificar_placa()

    if placa is None:
        return

    try:
        registro = entrada_veiculo(placa)

        print("\nENTRADA REGISTRADA!")
        print(f"Placa: {registro['placa']}")
        print(f"Horário: {registro['entrada']}")
        print("Cancela de entrada: ABERTA (simulação)")

    except Exception as erro:
        print(f"Erro ao registrar entrada: {erro}")



def simular_saida():
    print("\n=== SIMULAÇÃO DE SAÍDA ===")

    placa = identificar_placa()

    if placa is None:
        return

    try:
        consulta = consultar_saida(placa)

        # Abre a interface de pagamento
        metodo = abrir_popup_pagamento(consulta)

        if metodo is None:
            print("Pagamento cancelado.")
            print("Veículo permanece estacionado.")
            return

        # Recalcula o valor no momento da confirmação
        consulta = consultar_saida(placa)

        registro = finalizar_saida(consulta)

        print("\n" + "=" * 40)
        print("PAGAMENTO SIMULADO COM SUCESSO!")
        print("=" * 40)

        print(f"Placa: {registro['placa']}")
        print(f"Forma de pagamento: {metodo.upper()}")
        print(f"Valor: R$ {float(registro['valor']):.2f}")
        print("Cancela de saída: ABERTA (simulação)")

    except Exception as erro:
        print(f"Erro ao registrar saída: {erro}")


def main():
    while True:
        print("\n" + "=" * 40)
        print("ESTACIONAMENTO INTELIGENTE")
        print("=" * 40)
        print("1 - Simular entrada")
        print("2 - Simular saída")
        print("0 - Encerrar")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            simular_entrada()

        elif opcao == "2":
            simular_saida()

        elif opcao == "0":
            print("Simulador encerrado.")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
