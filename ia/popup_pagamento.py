
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def abrir_popup_pagamento(consulta):
    """
    Exibe a cobrança e retorna a forma de pagamento
    escolhida ou None se o usuário cancelar.
    """

    resultado = {"metodo": None}

    # Primeiro cria a janela
    janela = ctk.CTk()

    # Depois cria a variável vinculada à janela
    metodo = ctk.StringVar(master=janela, value="pix")

    janela.title("Estacionamento Inteligente - Pagamento")
    janela.geometry("460x620")
    janela.resizable(False, False)

    def fechar_janela():
        janela.withdraw()
        janela.quit()


    def confirmar():
        resultado["metodo"] = metodo.get()
        fechar_janela()


    def cancelar():
        resultado["metodo"] = None
        fechar_janela()

    janela.protocol("WM_DELETE_WINDOW", cancelar)

    container = ctk.CTkFrame(
        janela,
        corner_radius=18,
        fg_color="#1E293B"
    )
    container.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    ctk.CTkLabel(
        container,
        text="PAGAMENTO",
        font=("Arial", 23, "bold")
    ).pack(pady=(25, 5))

    ctk.CTkLabel(
        container,
        text="Estacionamento Inteligente",
        font=("Arial", 14),
        text_color="#94A3B8"
    ).pack(pady=(0, 20))

    dados = ctk.CTkFrame(
        container,
        fg_color="#334155",
        corner_radius=12
    )
    dados.pack(fill="x", padx=20, pady=5)

    def adicionar_dado(rotulo, valor):
        linha = ctk.CTkFrame(
            dados,
            fg_color="transparent"
        )
        linha.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(
            linha,
            text=rotulo,
            text_color="#CBD5E1"
        ).pack(side="left")

        ctk.CTkLabel(
            linha,
            text=str(valor),
            font=("Arial", 13, "bold")
        ).pack(side="right")

    adicionar_dado("Placa", consulta["placa"])
    adicionar_dado(
        "Entrada",
        consulta["entrada"].astimezone().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )
    adicionar_dado(
        "Permanência cobrada",
        f"{consulta['minutos_cobrados']} min"
    )

    ctk.CTkLabel(
        container,
        text="TOTAL A PAGAR",
        font=("Arial", 13),
        text_color="#94A3B8"
    ).pack(pady=(20, 3))

    ctk.CTkLabel(
        container,
        text=f"R$ {consulta['valor']:.2f}".replace(".", ","),
        font=("Arial", 36, "bold"),
        text_color="#34D399"
    ).pack(pady=(0, 20))

    ctk.CTkLabel(
        container,
        text="Selecione a forma de pagamento",
        font=("Arial", 14, "bold")
    ).pack(pady=(0, 10))

    opcoes = ctk.CTkFrame(
        container,
        fg_color="transparent"
    )
    opcoes.pack(fill="x", padx=25)

    for texto, valor in [
        ("Cartão de Crédito", "credito"),
        ("Cartão de Débito", "debito"),
        ("Pix", "pix")
    ]:
        ctk.CTkRadioButton(
            opcoes,
            text=texto,
            variable=metodo,
            value=valor,
            font=("Arial", 14)
        ).pack(anchor="w", pady=7)

    ctk.CTkButton(
        container,
        text="Confirmar pagamento (simulado)",
        command=confirmar,
        height=44,
        corner_radius=10,
        fg_color="#059669",
        hover_color="#047857",
        font=("Arial", 14, "bold")
    ).pack(fill="x", padx=25, pady=(20, 8))

    ctk.CTkButton(
        container,
        text="Cancelar",
        command=cancelar,
        height=36,
        fg_color="transparent",
        border_width=1,
        border_color="#64748B"
    ).pack(fill="x", padx=25)

    janela.mainloop()

    return resultado["metodo"]
