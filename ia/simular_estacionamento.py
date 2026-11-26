
from integracao_arduino import reconhecer_automaticamente

from estacionamento import (
    entrada_veiculo,
    consultar_saida,
    finalizar_saida
)

from popup_pagamento import abrir_popup_pagamento


def simular_entrada():
    print("\n" + "=" * 40)
    print("SIMULACAO DE ENTRADA")
    print("=" * 40)

    print("[SIMULACAO] CARRO_DETECTADO:ENTRADA")

    placa = reconhecer_automaticamente()

    if placa is None:
        print("Operação cancelada.")
        return

    try:
        registro = entrada_veiculo(placa)

        print("\nENTRADA REGISTRADA COM SUCESSO!")
        print(f"Placa: {registro['placa']}")
        print(f"Horário: {registro['entrada']}")

        print("[SIMULACAO] ABRIR:ENTRADA")
        print("[SIMULACAO] CANCELA_ABERTA:ENTRADA")

    except Exception as erro:
        print(f"Erro ao registrar entrada: {erro}")


def simular_saida():
    print("\n" + "=" * 40)
    print("SIMULACAO DE SAIDA")
    print("=" * 40)

    print("[SIMULACAO] CARRO_DETECTADO:SAIDA")

    placa = reconhecer_automaticamente()

    if placa is None:
        print("Operação cancelada.")
        return

    try:
        consulta = consultar_saida(placa)

        metodo = abrir_popup_pagamento(consulta)

        if metodo is None:
            print("Pagamento cancelado.")
            print("Veículo permanece estacionado.")
            return

        registro = finalizar_saida(consulta)

        print("\nPAGAMENTO SIMULADO CONFIRMADO!")
        print(f"Placa: {registro['placa']}")
        print(f"Pagamento: {metodo.upper()}")
        print(f"Minutos: {consulta['minutos_cobrados']}")
        print(f"Valor: R$ {float(registro['valor']):.2f}")
        print(f"Status: {registro['status']}")

        print("[SIMULACAO] ABRIR:SAIDA")
        print("[SIMULACAO] CANCELA_ABERTA:SAIDA")

    except Exception as erro:
        print(f"Erro ao processar saída: {erro}")


def main():
    while True:
        print("\n" + "=" * 40)
        print("ESTACIONAMENTO INTELIGENTE")
        print("SIMULADOR AUTOMATICO")
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
            print("Simulação encerrada.")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
