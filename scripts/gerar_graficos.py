# -*- coding: utf-8 -*-
"""
Gera os quatro gráficos de análise do pipeline CI/CD.
Lê data/metricas.csv e salva os gráficos em graphs/.

Uso:
    python scripts/gerar_graficos.py
"""
import os

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_CSV = os.path.join(DIR_RAIZ, "data", "metricas.csv")
DIR_GRAFICOS = os.path.join(DIR_RAIZ, "graphs")

COR_SUCESSO = "#2ecc71"
COR_FALHA = "#e74c3c"
COR_LINT = "#3498db"
COR_TEST = "#9b59b6"


def configurar_estilo():
    """Aplica configurações globais de estilo aos gráficos."""
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False


def preparar_resumo_por_execucao(df):
    """Agrega o DataFrame para uma linha por execução (workflow)."""
    return (
        df.groupby("id_execucao")
        .agg(
            duracao_workflow=("duracao_workflow", "first"),
            status=("status", "first"),
            total_testes=("total_testes", "first"),
            falhas_testes=("falhas_testes", "first"),
            timestamp=("timestamp", "first"),
        )
        .reset_index()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def grafico1_duracao_total(df):
    """Gráfico de barras: duração total do workflow por execução."""
    resumo = preparar_resumo_por_execucao(df)
    resumo["numero"] = range(1, len(resumo) + 1)
    cores = [COR_SUCESSO if s == "success" else COR_FALHA for s in resumo["status"]]

    fig, ax = plt.subplots(figsize=(13, 5))
    barras = ax.bar(resumo["numero"], resumo["duracao_workflow"], color=cores, edgecolor="white", linewidth=0.8)

    for barra, duracao in zip(barras, resumo["duracao_workflow"]):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 1,
            f"{duracao:.0f}s",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#333333",
        )

    ax.set_xlabel("Número da Execução", fontsize=12)
    ax.set_ylabel("Duração Total (segundos)", fontsize=12)
    ax.set_title("Duração Total do Pipeline por Execução", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(resumo["numero"])

    legenda = [
        mpatches.Patch(color=COR_SUCESSO, label="Sucesso"),
        mpatches.Patch(color=COR_FALHA, label="Falha"),
    ]
    ax.legend(handles=legenda, loc="upper right")

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico1_duracao_total.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Gráfico 1 salvo: {caminho}")


def grafico2_duracao_por_job(df):
    """Gráfico de barras agrupadas: duração de cada job por execução."""
    # Cria número sequencial por ordem de execução
    ordem = (
        df.groupby("id_execucao")["timestamp"]
        .first()
        .reset_index()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    ordem["numero"] = range(1, len(ordem) + 1)
    df = df.merge(ordem[["id_execucao", "numero"]], on="id_execucao")

    pivot = df.pivot_table(index="numero", columns="nome_job", values="duracao_job", aggfunc="first")

    ax = pivot.plot(kind="bar", figsize=(13, 5), color=[COR_LINT, COR_TEST], edgecolor="white", linewidth=0.8)
    ax.set_xlabel("Número da Execução", fontsize=12)
    ax.set_ylabel("Duração do Job (segundos)", fontsize=12)
    ax.set_title("Duração por Job em Cada Execução", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticklabels(pivot.index, rotation=0)
    ax.legend(title="Job", loc="upper right")

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico2_duracao_por_job.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Gráfico 2 salvo: {caminho}")


def grafico3_taxa_sucesso(df):
    """Gráfico de pizza: proporção de execuções com sucesso e com falha."""
    resumo = preparar_resumo_por_execucao(df)
    qtd_sucesso = (resumo["status"] == "success").sum()
    qtd_falha = (resumo["status"] != "success").sum()

    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, textos, auto_textos = ax.pie(
        [qtd_sucesso, qtd_falha],
        labels=[f"Sucesso\n({qtd_sucesso})", f"Falha\n({qtd_falha})"],
        autopct="%1.1f%%",
        colors=[COR_SUCESSO, COR_FALHA],
        startangle=90,
        explode=(0.04, 0.04),
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for texto_auto in auto_textos:
        texto_auto.set_fontsize(13)
        texto_auto.set_fontweight("bold")

    ax.set_title("Taxa de Sucesso vs Falha nas Execuções", fontsize=14, fontweight="bold", pad=15)

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico3_taxa_sucesso.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Gráfico 3 salvo: {caminho}")


def grafico4_testes_vs_duracao(df):
    """Gráfico de dispersão: quantidade de testes versus duração do pipeline."""
    resumo = preparar_resumo_por_execucao(df)
    resumo["numero"] = range(1, len(resumo) + 1)
    cores = [COR_SUCESSO if s == "success" else COR_FALHA for s in resumo["status"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        resumo["total_testes"],
        resumo["duracao_workflow"],
        c=cores,
        s=130,
        alpha=0.85,
        edgecolors="white",
        linewidths=1.2,
    )

    for _, linha in resumo.iterrows():
        ax.annotate(
            f"#{int(linha['numero'])}",
            (linha["total_testes"], linha["duracao_workflow"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=9,
            color="#555555",
        )

    ax.set_xlabel("Quantidade de Testes Executados", fontsize=12)
    ax.set_ylabel("Duração Total do Workflow (segundos)", fontsize=12)
    ax.set_title("Quantidade de Testes vs Duração do Pipeline", fontsize=14, fontweight="bold", pad=15)

    legenda = [
        mpatches.Patch(color=COR_SUCESSO, label="Sucesso"),
        mpatches.Patch(color=COR_FALHA, label="Falha"),
    ]
    ax.legend(handles=legenda, loc="upper left")

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico4_testes_vs_duracao.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Gráfico 4 salvo: {caminho}")


def main():
    os.makedirs(DIR_GRAFICOS, exist_ok=True)
    configurar_estilo()

    print(f"Lendo dados de: {ARQUIVO_CSV}")
    df = pd.read_csv(ARQUIVO_CSV)
    print(f"Total de registros carregados: {len(df)}\n")

    print("Gerando gráficos...")
    grafico1_duracao_total(df)
    grafico2_duracao_por_job(df)
    grafico3_taxa_sucesso(df)
    grafico4_testes_vs_duracao(df)

    print("\nTodos os gráficos foram gerados com sucesso!")


if __name__ == "__main__":
    main()
