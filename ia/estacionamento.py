
import math
from datetime import datetime, timezone

from banco import (
    registrar_entrada,
    buscar_veiculo,
    registrar_saida
)

VALOR_INICIAL = 15.00
VALOR_ADICIONAL = 5.00


def normalizar_placa(placa):
    placa = placa.strip().upper()

    if len(placa) != 7 or not placa.isalnum():
        raise ValueError("Placa inválida.")

    return placa



def calcular_cobranca(entrada, saida):
    segundos = max(
        0,
        (saida - entrada).total_seconds()
    )

    # Considera apenas minutos completos
    minutos = int(segundos // 60)

    # O primeiro minuto custa R$ 15,00
    minutos_cobrados = max(1, minutos)

    valor = (
        VALOR_INICIAL +
        (minutos_cobrados - 1) * VALOR_ADICIONAL
    )

    return {
        "minutos_cobrados": minutos_cobrados,
        "valor": round(valor, 2)
    }


def entrada_veiculo(placa):
    placa = normalizar_placa(placa)

    existente = buscar_veiculo(placa)

    if existente:
        raise ValueError(
            f"O veículo {placa} já está estacionado."
        )

    registro = registrar_entrada(placa)

    return registro


def consultar_saida(placa):
    placa = normalizar_placa(placa)

    registro = buscar_veiculo(placa)

    if not registro:
        raise ValueError(
            f"Não existe entrada ativa para {placa}."
        )

    entrada = datetime.fromisoformat(
        registro["entrada"].replace("Z", "+00:00")
    )

    saida = datetime.now(timezone.utc)

    cobranca = calcular_cobranca(entrada, saida)

    return {
        "registro": registro,
        "placa": placa,
        "entrada": entrada,
        "saida": saida,
        **cobranca
    }


def finalizar_saida(consulta):
    return registrar_saida(
        consulta["registro"]["id"],
        consulta["saida"].isoformat(),
        consulta["valor"]
    )
