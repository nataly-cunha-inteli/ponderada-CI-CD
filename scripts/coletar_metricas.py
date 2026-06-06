# -*- coding: utf-8 -*-
"""
Coleta métricas de execuções do GitHub Actions via API e salva em data/metricas.csv.

Configuração necessária (variáveis de ambiente):
    GITHUB_TOKEN   — token de acesso pessoal do GitHub (com permissão repo/actions)
    GITHUB_USUARIO — nome do usuário ou organização do repositório
    GITHUB_REPO    — nome do repositório (padrão: pondCICD)

Uso:
    export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx
    export GITHUB_USUARIO=seu_usuario
    python scripts/coletar_metricas.py
"""
import os
import io
import json
import csv
import zipfile
from datetime import datetime

import requests

# ── Configuração ──────────────────────────────────────────────────────────────
TOKEN = os.environ.get("GITHUB_TOKEN", "")
USUARIO = os.environ.get("GITHUB_USUARIO", "SEU_USUARIO_AQUI")
REPO = os.environ.get("GITHUB_REPO", "pondCICD")

DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_SAIDA = os.path.join(DIR_RAIZ, "data", "metricas.csv")

BASE_URL = f"https://api.github.com/repos/{USUARIO}/{REPO}"
CABECALHOS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

CAMPOS_CSV = [
    "id_execucao",
    "sha_commit",
    "mensagem_commit",
    "status",
    "duracao_workflow",
    "nome_job",
    "duracao_job",
    "total_testes",
    "falhas_testes",
    "timestamp",
]


# ── Funções auxiliares ────────────────────────────────────────────────────────

def calcular_duracao(inicio, fim):
    """Retorna a duração em segundos entre duas strings ISO 8601."""
    if not inicio or not fim:
        return 0.0
    formato = "%Y-%m-%dT%H:%M:%SZ"
    try:
        t_inicio = datetime.strptime(inicio, formato)
        t_fim = datetime.strptime(fim, formato)
        return max(0.0, (t_fim - t_inicio).total_seconds())
    except ValueError:
        return 0.0


def obter_execucoes():
    """Busca todas as execuções de workflow do repositório (com paginação)."""
    execucoes = []
    pagina = 1
    print("Buscando execuções do workflow...")
    while True:
        url = f"{BASE_URL}/actions/runs"
        resposta = requests.get(
            url,
            headers=CABECALHOS,
            params={"per_page": 100, "page": pagina},
        )
        resposta.raise_for_status()
        dados = resposta.json().get("workflow_runs", [])
        if not dados:
            break
        execucoes.extend(dados)
        print(f"  Página {pagina}: {len(dados)} execuções carregadas")
        pagina += 1
    print(f"Total de execuções encontradas: {len(execucoes)}\n")
    return execucoes


def obter_jobs(id_execucao):
    """Retorna a lista de jobs de uma execução específica."""
    url = f"{BASE_URL}/actions/runs/{id_execucao}/jobs"
    resposta = requests.get(url, headers=CABECALHOS)
    resposta.raise_for_status()
    return resposta.json().get("jobs", [])


def baixar_meta_testes(id_execucao):
    """
    Baixa o artefato 'resultados-testes' e extrai total_testes e falhas_testes.
    Retorna (0, 0) caso o artefato não seja encontrado ou haja erro.
    """
    url = f"{BASE_URL}/actions/runs/{id_execucao}/artifacts"
    resposta = requests.get(url, headers=CABECALHOS)
    resposta.raise_for_status()
    artefatos = resposta.json().get("artifacts", [])

    for artefato in artefatos:
        if "resultados-testes" in artefato.get("name", ""):
            url_download = artefato["archive_download_url"]
            # GitHub redireciona para armazenamento externo (S3); seguimos o redirect
            resposta_zip = requests.get(url_download, headers=CABECALHOS, allow_redirects=True)
            if resposta_zip.status_code != 200:
                print(f"  Aviso: não foi possível baixar artefato da execução {id_execucao}")
                return 0, 0
            try:
                with zipfile.ZipFile(io.BytesIO(resposta_zip.content)) as zf:
                    if "test-meta.json" in zf.namelist():
                        dados = json.loads(zf.read("test-meta.json").decode("utf-8"))
                        return dados.get("total_testes", 0), dados.get("falhas_testes", 0)
            except zipfile.BadZipFile:
                print(f"  Aviso: ZIP inválido para execução {id_execucao}")

    return 0, 0


# ── Função principal ──────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        print("ERRO: Defina a variável de ambiente GITHUB_TOKEN antes de executar.")
        print("  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx")
        return

    if USUARIO == "SEU_USUARIO_AQUI":
        print("ERRO: Defina a variável de ambiente GITHUB_USUARIO.")
        print("  export GITHUB_USUARIO=seu_usuario_github")
        return

    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)
    execucoes = obter_execucoes()

    linhas = []
    for execucao in execucoes:
        id_exec = execucao["id"]
        sha = execucao["head_sha"][:8]

        commit_info = execucao.get("head_commit") or {}
        mensagem = commit_info.get("message", "").split("\n")[0]

        status = execucao.get("conclusion") or execucao.get("status", "desconhecido")
        duracao_workflow = calcular_duracao(
            execucao.get("run_started_at"),
            execucao.get("updated_at"),
        )
        timestamp = execucao.get("created_at", "")

        print(f"Processando execução #{id_exec} | {sha} | {status}")

        total_testes, falhas_testes = baixar_meta_testes(id_exec)
        jobs = obter_jobs(id_exec)

        for job in jobs:
            duracao_job = calcular_duracao(job.get("started_at"), job.get("completed_at"))
            linhas.append({
                "id_execucao": id_exec,
                "sha_commit": sha,
                "mensagem_commit": mensagem,
                "status": status,
                "duracao_workflow": round(duracao_workflow, 1),
                "nome_job": job["name"],
                "duracao_job": round(duracao_job, 1),
                "total_testes": total_testes,
                "falhas_testes": falhas_testes,
                "timestamp": timestamp,
            })

    with open(ARQUIVO_SAIDA, "w", newline="", encoding="utf-8") as arquivo_csv:
        escritor = csv.DictWriter(arquivo_csv, fieldnames=CAMPOS_CSV)
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"\nMétricas salvas em: {ARQUIVO_SAIDA}")
    print(f"Total de linhas geradas: {len(linhas)}")


if __name__ == "__main__":
    main()
