
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError(
        "Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env"
    )

supabase = create_client(url, key)


def registrar_entrada(placa):
    placa = placa.strip().upper()

    resultado = (
        supabase.table("estacionamentos")
        .insert({"placa": placa})
        .execute()
    )

    return resultado.data[0]


def buscar_veiculo(placa):
    placa = placa.strip().upper()

    resultado = (
        supabase.table("estacionamentos")
        .select("*")
        .eq("placa", placa)
        .eq("status", "ativo")
        .limit(1)
        .execute()
    )

    return resultado.data[0] if resultado.data else None


def listar_veiculos_ativos():
    resultado = (
        supabase.table("estacionamentos")
        .select("*")
        .eq("status", "ativo")
        .order("entrada", desc=True)
        .execute()
    )

    return resultado.data


def registrar_saida(id_registro, horario_saida, valor):
    resultado = (
        supabase.table("estacionamentos")
        .update({
            "saida": horario_saida,
            "valor": valor,
            "status": "finalizado"
        })
        .eq("id", id_registro)
        .eq("status", "ativo")
        .execute()
    )

    if not resultado.data:
        raise ValueError(
            "Registro ativo não encontrado para finalizar."
        )

    return resultado.data[0]