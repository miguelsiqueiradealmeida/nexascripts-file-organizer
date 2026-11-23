
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import shutil
import csv
from datetime import datetime

# =====================================
# CONFIGURAÇÕES
# =====================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CATEGORIAS = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Documentos": [".pdf", ".docx", ".txt"],
    "Planilhas": [".csv", ".xlsx", ".xls"],
    "Vídeos": [".mp4", ".mov", ".avi"],
    "Áudio": [".mp3", ".wav"],
    "Códigos": [".py", ".js", ".html", ".css"]
}

pasta_selecionada = None
arquivos_encontrados = []

PASTA_LOGS = Path(__file__).parent / "logs"
ARQUIVO_HISTORICO = PASTA_LOGS / "historico.csv"


# =====================================
# HISTÓRICO
# =====================================

def registrar_historico(nome_arquivo, destino, resultado):
    PASTA_LOGS.mkdir(exist_ok=True)

    arquivo_novo = not ARQUIVO_HISTORICO.exists()

    with open(
        ARQUIVO_HISTORICO,
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:

        escritor = csv.writer(arquivo, delimiter=";")

        if arquivo_novo:
            escritor.writerow([
                "Data",
                "Arquivo",
                "Destino",
                "Resultado"
            ])

        escritor.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            nome_arquivo,
            destino,
            resultado
        ])


def visualizar_historico():
    if not ARQUIVO_HISTORICO.exists():
        messagebox.showinfo(
            "Histórico",
            "Ainda não existem registros."
        )
        return

    janela_historico = ctk.CTkToplevel(janela)
    janela_historico.title("NexaScripts | Histórico")
    janela_historico.geometry("750x500")
    janela_historico.transient(janela)

    ctk.CTkLabel(
        janela_historico,
        text="Histórico de operações",
        font=("Arial", 22, "bold")
    ).pack(pady=20)

    tabela = ctk.CTkTextbox(
        janela_historico,
        font=("Consolas", 12)
    )
    tabela.pack(
        padx=20,
        pady=10,
        fill="both",
        expand=True
    )

    try:
        with open(
            ARQUIVO_HISTORICO,
            "r",
            encoding="utf-8-sig"
        ) as arquivo:

            leitor = csv.reader(arquivo, delimiter=";")

            for linha in leitor:
                tabela.insert(
                    "end",
                    " | ".join(linha) + "\n"
                )

        tabela.configure(state="disabled")

    except OSError:
        janela_historico.destroy()
        messagebox.showerror(
            "Erro",
            "Não foi possível abrir o histórico."
        )


# =====================================
# IDENTIFICAR ARQUIVOS
# =====================================

def identificar_categoria(arquivo):
    extensao = arquivo.suffix.lower()

    for categoria, extensoes in CATEGORIAS.items():
        if extensao in extensoes:
            return categoria

    return "Outros"


def analisar_arquivos():
    global arquivos_encontrados

    arquivos_encontrados = []

    if not pasta_selecionada:
        return

    try:
        arquivos = [
            item for item in pasta_selecionada.iterdir()
            if item.is_file()
        ]

        for arquivo in arquivos:

            # Não organizar o próprio programa
            if arquivo.resolve() == Path(__file__).resolve():
                continue

            categoria = identificar_categoria(arquivo)
            destino = pasta_selecionada / categoria
            caminho_final = destino / arquivo.name

            arquivos_encontrados.append({
                "arquivo": arquivo,
                "categoria": categoria,
                "conflito": caminho_final.exists()
            })

    except OSError:
        messagebox.showerror(
            "Erro",
            "Não foi possível acessar essa pasta."
        )


# =====================================
# PRÉ-VISUALIZAÇÃO
# =====================================

def atualizar_previa():
    analisar_arquivos()

    for widget in lista_arquivos.winfo_children():
        widget.destroy()

    if not pasta_selecionada:
        total_label.configure(
            text="Selecione uma pasta"
        )
        return

    if not arquivos_encontrados:
        ctk.CTkLabel(
            lista_arquivos,
            text="Nenhum arquivo encontrado."
        ).pack(pady=20)

    organizaveis = sum(
        1 for item in arquivos_encontrados
        if not item["conflito"]
    )

    conflitos = sum(
        1 for item in arquivos_encontrados
        if item["conflito"]
    )

    for item in arquivos_encontrados:
        nome = item["arquivo"].name
        categoria = item["categoria"]

        if item["conflito"]:
            status = "Já existe - será ignorado"
            cor = "#F59E0B"
        else:
            status = f"Destino: {categoria}"
            cor = "#34D399"

        linha = ctk.CTkFrame(
            lista_arquivos,
            corner_radius=8
        )
        linha.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(
            linha,
            text=nome,
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            linha,
            text=status,
            text_color=cor,
            font=("Arial", 11)
        ).pack(anchor="w", padx=12, pady=(0, 8))

    total_label.configure(
        text=f"{len(arquivos_encontrados)} arquivos encontrados"
    )

    resumo_label.configure(
        text=f"Prontos para organizar: {organizaveis} | Conflitos: {conflitos}"
    )


# =====================================
# SELECIONAR PASTA
# =====================================

def escolher_pasta():
    global pasta_selecionada

    pasta = filedialog.askdirectory()

    if not pasta:
        return

    pasta_selecionada = Path(pasta)

    caminho_label.configure(
        text=str(pasta_selecionada)
    )

    atualizar_previa()


# =====================================
# ORGANIZAR ARQUIVOS
# =====================================

def organizar_arquivos():

    if not pasta_selecionada:
        messagebox.showwarning(
            "Atenção",
            "Selecione uma pasta primeiro."
        )
        return

    atualizar_previa()

    organizaveis = [
        item for item in arquivos_encontrados
        if not item["conflito"]
    ]

    if not organizaveis:
        messagebox.showinfo(
            "Aviso",
            "Não existem arquivos para organizar."
        )
        return

    confirmar = messagebox.askyesno(
        "Confirmar organização",
        f"{len(organizaveis)} arquivos serão movidos.\n\n"
        "Deseja continuar?"
    )

    if not confirmar:
        return

    organizados = 0
    conflitos = 0
    erros = 0

    for item in arquivos_encontrados:

        arquivo = item["arquivo"]
        categoria = item["categoria"]
        destino = pasta_selecionada / categoria
        caminho_final = destino / arquivo.name

        if caminho_final.exists():
            registrar_historico(
                arquivo.name,
                str(destino),
                "Conflito - arquivo já existe"
            )
            conflitos += 1
            continue

        try:
            destino.mkdir(exist_ok=True)

            shutil.move(
                str(arquivo),
                str(caminho_final)
            )

            registrar_historico(
                arquivo.name,
                str(destino),
                "Sucesso"
            )

            organizados += 1

        except OSError as erro:
            registrar_historico(
                arquivo.name,
                str(destino),
                f"Erro: {erro}"
            )
            erros += 1

    atualizar_previa()

    messagebox.showinfo(
        "Organização concluída",
        f"Organizados: {organizados}\n"
        f"Conflitos: {conflitos}\n"
        f"Erros: {erros}"
    )


# =====================================
# INTERFACE
# =====================================

janela = ctk.CTk()

janela.title("NexaScripts | File Organizer")
janela.geometry("760x760")
janela.minsize(650, 650)

# CABEÇALHO

ctk.CTkLabel(
    janela,
    text="NexaScripts",
    font=("Arial", 32, "bold")
).pack(pady=(25, 0))

ctk.CTkLabel(
    janela,
    text="FILE ORGANIZER  •  ORGANIZAÇÃO INTELIGENTE",
    text_color="#8B9BB4",
    font=("Arial", 12)
).pack(pady=(5, 20))


# PAINEL DA PASTA

painel = ctk.CTkFrame(
    janela,
    corner_radius=15
)
painel.pack(fill="x", padx=30, pady=5)

ctk.CTkLabel(
    painel,
    text="Pasta selecionada",
    font=("Arial", 16, "bold")
).pack(anchor="w", padx=20, pady=(15, 5))

caminho_label = ctk.CTkLabel(
    painel,
    text="Nenhuma pasta selecionada",
    text_color="#9CAAC0",
    wraplength=650
)
caminho_label.pack(anchor="w", padx=20, pady=5)

ctk.CTkButton(
    painel,
    text="Selecionar pasta",
    command=escolher_pasta,
    height=38
).pack(anchor="w", padx=20, pady=(8, 18))


# RESUMO

total_label = ctk.CTkLabel(
    janela,
    text="0 arquivos encontrados",
    font=("Arial", 17, "bold")
)
total_label.pack(pady=(15, 5))

resumo_label = ctk.CTkLabel(
    janela,
    text="Prontos para organizar: 0 | Conflitos: 0",
    text_color="#9CAAC0"
)
resumo_label.pack(pady=(0, 12))


# PRÉ-VISUALIZAÇÃO

ctk.CTkLabel(
    janela,
    text="PRÉ-VISUALIZAÇÃO DOS ARQUIVOS",
    font=("Arial", 13, "bold"),
    text_color="#8B9BB4"
).pack(anchor="w", padx=35, pady=(5, 8))

lista_arquivos = ctk.CTkScrollableFrame(
    janela,
    corner_radius=12
)
lista_arquivos.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=5
)


# BOTÕES

botoes = ctk.CTkFrame(
    janela,
    fg_color="transparent"
)
botoes.pack(pady=15)

ctk.CTkButton(
    botoes,
    text="ORGANIZAR ARQUIVOS",
    command=organizar_arquivos,
    height=48,
    width=230,
    corner_radius=12,
    font=("Arial", 13, "bold"),
    fg_color="#2563EB",
    hover_color="#1D4ED8"
).pack(side="left", padx=6)

ctk.CTkButton(
    botoes,
    text="VER HISTÓRICO",
    command=visualizar_historico,
    height=48,
    width=180,
    corner_radius=12,
    font=("Arial", 13, "bold"),
    fg_color="#374151",
    hover_color="#4B5563"
).pack(side="left", padx=6)


# RODAPÉ

ctk.CTkLabel(
    janela,
    text="NexaScripts • File Organizer v4.0",
    text_color="#64748B",
    font=("Arial", 10)
).pack(pady=(0, 12))


janela.mainloop()
