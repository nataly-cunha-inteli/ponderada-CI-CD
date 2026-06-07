# -*- coding: utf-8 -*-
"""
Gera os quatro graficos de analise do pipeline CI/CD.
Le data/metricas.csv e salva os graficos em graphs/.

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
COR_FALHA_TESTE = "#e74c3c"
COR_FALHA_LINT = "#e67e22"
COR_LINT = "#3498db"
COR_TEST = "#9b59b6"
COR_NAO_EXECUTADO = "#cccccc"


def configurar_estilo():
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False


def preparar_resumo_por_execucao(df):
    """Uma linha por execucao com status e metricas agregadas."""
    resumo = (
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
    resumo["numero"] = range(1, len(resumo) + 1)

    # Classifica o tipo de resultado para analise mais precisa
    def classificar(row):
        if row["status"] == "success":
            return "sucesso"
        if row["total_testes"] == 0:
            return "falha_lint"
        return "falha_teste"

    resumo["tipo"] = resumo.apply(classificar, axis=1)
    return resumo


# ── Grafico 1 ─────────────────────────────────────────────────────────────────

def grafico1_duracao_total(df):
    """Barras: duracao total do workflow por execucao, coloridas por tipo de resultado."""
    resumo = preparar_resumo_por_execucao(df)

    mapa_cores = {
        "sucesso": COR_SUCESSO,
        "falha_teste": COR_FALHA_TESTE,
        "falha_lint": COR_FALHA_LINT,
    }
    cores = [mapa_cores[t] for t in resumo["tipo"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    barras = ax.bar(
        resumo["numero"], resumo["duracao_workflow"],
        color=cores, edgecolor="white", linewidth=0.8,
    )

    for barra, dur in zip(barras, resumo["duracao_workflow"]):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 0.5,
            f"{dur:.0f}s",
            ha="center", va="bottom", fontsize=8, color="#333333",
        )

    ax.set_xlabel("Numero da Execucao", fontsize=12)
    ax.set_ylabel("Duracao Total (segundos)", fontsize=12)
    ax.set_title("Duracao Total do Pipeline por Execucao", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(resumo["numero"])

    legenda = [
        mpatches.Patch(color=COR_SUCESSO, label="Sucesso"),
        mpatches.Patch(color=COR_FALHA_TESTE, label="Falha de teste"),
        mpatches.Patch(color=COR_FALHA_LINT, label="Falha de lint"),
    ]
    ax.legend(handles=legenda, loc="upper left")

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico1_duracao_total.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Grafico 1 salvo: {caminho}")


# ── Grafico 2 ─────────────────────────────────────────────────────────────────

def grafico2_duracao_por_job(df):
    """Barras agrupadas: duracao de cada job por execucao.
    Barras cinzas indicam job que nao chegou a ser executado."""
    # Deduplicar: uma linha por (execucao, job)
    df_jobs = (
        df.groupby(["id_execucao", "nome_job"])
        .agg(duracao_job=("duracao_job", "first"), timestamp=("timestamp", "first"))
        .reset_index()
    )

    ordem = (
        df_jobs.groupby("id_execucao")["timestamp"]
        .first().reset_index()
        .sort_values("timestamp").reset_index(drop=True)
    )
    ordem["numero"] = range(1, len(ordem) + 1)
    df_jobs = df_jobs.merge(ordem[["id_execucao", "numero"]], on="id_execucao")

    pivot = df_jobs.pivot_table(
        index="numero", columns="nome_job", values="duracao_job", aggfunc="first"
    )

    # Identificar colunas e atribuir cores
    nomes_jobs = list(pivot.columns)
    paleta = [COR_LINT, COR_TEST, "#f39c12", "#1abc9c"]
    cores_jobs = {nome: paleta[i % len(paleta)] for i, nome in enumerate(nomes_jobs)}

    fig, ax = plt.subplots(figsize=(14, 5))
    n_jobs = len(nomes_jobs)
    largura = 0.8 / n_jobs
    indices = pivot.index.to_numpy()

    for i, nome in enumerate(nomes_jobs):
        valores = pivot[nome].to_numpy()
        posicoes = indices - 0.4 + largura * i + largura / 2

        # Barras normais onde o job rodou
        executou = ~pd.isna(valores)
        ax.bar(
            posicoes[executou], valores[executou],
            width=largura, color=cores_jobs[nome],
            edgecolor="white", linewidth=0.8, label=nome,
        )

        # Barras cinzas com hachura onde o job NAO rodou
        nao_executou = pd.isna(valores)
        if nao_executou.any():
            ax.bar(
                posicoes[nao_executou], [2] * nao_executou.sum(),
                width=largura, color=COR_NAO_EXECUTADO,
                edgecolor="white", linewidth=0.8,
                hatch="//", alpha=0.6,
            )

    ax.set_xlabel("Numero da Execucao", fontsize=12)
    ax.set_ylabel("Duracao do Job (segundos)", fontsize=12)
    ax.set_title(
        "Duracao por Job em Cada Execucao\n"
        "(barras cinzas com hachura = job nao executado)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xticks(indices)
    ax.legend(title="Job", loc="upper left")

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico2_duracao_por_job.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Grafico 2 salvo: {caminho}")


# ── Grafico 3 ─────────────────────────────────────────────────────────────────

def grafico3_taxa_sucesso(df):
    """Pizza com tres categorias: sucesso, falha de teste e falha de lint."""
    resumo = preparar_resumo_por_execucao(df)
    qtd_sucesso = (resumo["tipo"] == "sucesso").sum()
    qtd_falha_teste = (resumo["tipo"] == "falha_teste").sum()
    qtd_falha_lint = (resumo["tipo"] == "falha_lint").sum()

    valores = [qtd_sucesso, qtd_falha_lint, qtd_falha_teste]
    rotulos = [
        f"Sucesso\n({qtd_sucesso})",
        f"Falha de lint\n({qtd_falha_lint})",
        f"Falha de teste\n({qtd_falha_teste})",
    ]
    cores = [COR_SUCESSO, COR_FALHA_LINT, COR_FALHA_TESTE]

    # Remove fatias zeradas
    dados = [(v, r, c) for v, r, c in zip(valores, rotulos, cores) if v > 0]
    valores, rotulos, cores = zip(*dados)

    fig, ax = plt.subplots(figsize=(7, 7))
    _, textos, auto_textos = ax.pie(
        valores, labels=rotulos, autopct="%1.1f%%",
        colors=cores, startangle=90,
        explode=[0.04] * len(valores),
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for at in auto_textos:
        at.set_fontsize(12)
        at.set_fontweight("bold")

    ax.set_title(
        "Resultado das Execucoes por Tipo",
        fontsize=14, fontweight="bold", pad=15,
    )

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico3_taxa_sucesso.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Grafico 3 salvo: {caminho}")


# ── Grafico 4 ─────────────────────────────────────────────────────────────────

def grafico4_testes_vs_duracao(df):
    """Dispersao: quantidade de testes x duracao.
    Filtra execucoes sem testes (lint falhou antes de rodar testes)."""
    resumo = preparar_resumo_por_execucao(df)
    qtd_filtradas = (resumo["total_testes"] == 0).sum()
    resumo_filtrado = resumo[resumo["total_testes"] > 0].copy()

    mapa_cores = {
        "sucesso": COR_SUCESSO,
        "falha_teste": COR_FALHA_TESTE,
        "falha_lint": COR_FALHA_LINT,
    }
    cores = [mapa_cores[t] for t in resumo_filtrado["tipo"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        resumo_filtrado["total_testes"], resumo_filtrado["duracao_workflow"],
        c=cores, s=130, alpha=0.85, edgecolors="white", linewidths=1.2,
    )

    for _, linha in resumo_filtrado.iterrows():
        ax.annotate(
            f"#{int(linha['numero'])}",
            (linha["total_testes"], linha["duracao_workflow"]),
            textcoords="offset points", xytext=(6, 4),
            fontsize=9, color="#555555",
        )

    if qtd_filtradas > 0:
        ax.text(
            0.02, 0.04,
            f"{qtd_filtradas} execucao(oes) com lint falho excluidas (total_testes = 0)",
            transform=ax.transAxes, fontsize=9, color="#888888", style="italic",
        )

    ax.set_xlabel("Quantidade de Testes Executados", fontsize=12)
    ax.set_ylabel("Duracao Total do Workflow (segundos)", fontsize=12)
    ax.set_title(
        "Quantidade de Testes vs Duracao do Pipeline",
        fontsize=14, fontweight="bold", pad=15,
    )

    legenda = [
        mpatches.Patch(color=COR_SUCESSO, label="Sucesso"),
        mpatches.Patch(color=COR_FALHA_TESTE, label="Falha de teste"),
    ]
    ax.legend(handles=legenda, loc="upper left")

    plt.tight_layout()
    caminho = os.path.join(DIR_GRAFICOS, "grafico4_testes_vs_duracao.png")
    plt.savefig(caminho)
    plt.close()
    print(f"  Grafico 4 salvo: {caminho}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(DIR_GRAFICOS, exist_ok=True)
    configurar_estilo()

    print(f"Lendo dados de: {ARQUIVO_CSV}")
    df = pd.read_csv(ARQUIVO_CSV)
    print(f"Total de registros carregados: {len(df)}\n")

    print("Gerando graficos...")
    grafico1_duracao_total(df)
    grafico2_duracao_por_job(df)
    grafico3_taxa_sucesso(df)
    grafico4_testes_vs_duracao(df)

    print("\nTodos os graficos foram gerados com sucesso!")


if __name__ == "__main__":
    main()
