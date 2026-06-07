# -*- coding: utf-8 -*-
"""
Coleta métricas de execuções do GitHub Actions via API e salva em data/metricas.csv.

Configuração necessária (variáveis de ambiente):
    GITHUB_TOKEN   — token de acesso pessoal do GitHub (com permissão repo/actions)
    GITHUB_USUARIO — nome do usuário ou organização do repositório
    GITHUB_REPO    — nome do repositório (padrão: ponderada-CI-CD)

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
REPO = os.environ.get("GITHUB_REPO", "ponderada-CI-CD")

DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_SAIDA = os.path.join(DIR_RAIZ, "data", "metricas.csv")

BASE_URL = f"https://api.github.com/repos/{USUARIO}/{REPO}"
CABECALHOS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Uma linha por etapa (step) de cada job de cada execucao
CAMPOS_CSV = [
    "id_execucao",
    "sha_commit",
    "mensagem_commit",
    "status",
    "duracao_workflow",
    "lead_time",
    "nome_job",
    "duracao_job",
    "nome_etapa",
    "duracao_etapa",
    "total_testes",
    "falhas_testes",
    "tempo_medio_testes",
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
    print("Buscando execucoes do workflow...")
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
        print(f"  Pagina {pagina}: {len(dados)} execucoes carregadas")
        pagina += 1
    print(f"Total de execucoes encontradas: {len(execucoes)}\n")
    return execucoes


def obter_jobs(id_execucao):
    """Retorna a lista de jobs (com etapas) de uma execução específica."""
    url = f"{BASE_URL}/actions/runs/{id_execucao}/jobs"
    resposta = requests.get(url, headers=CABECALHOS)
    resposta.raise_for_status()
    return resposta.json().get("jobs", [])


def baixar_meta_testes(id_execucao):
    """
    Baixa o artefato 'resultados-testes' e extrai as métricas de teste.
    Retorna (0, 0, 0.0) caso o artefato nao seja encontrado ou haja erro.
    """
    url = f"{BASE_URL}/actions/runs/{id_execucao}/artifacts"
    resposta = requests.get(url, headers=CABECALHOS)
    resposta.raise_for_status()
    artefatos = resposta.json().get("artifacts", [])

    for artefato in artefatos:
        if "resultados-testes" in artefato.get("name", ""):
            url_download = artefato["archive_download_url"]
            resposta_zip = requests.get(url_download, headers=CABECALHOS, allow_redirects=True)
            if resposta_zip.status_code != 200:
                print(f"  Aviso: nao foi possivel baixar artefato da execucao {id_execucao}")
                return 0, 0, 0.0
            try:
                with zipfile.ZipFile(io.BytesIO(resposta_zip.content)) as zf:
                    if "test-meta.json" in zf.namelist():
                        dados = json.loads(zf.read("test-meta.json").decode("utf-8"))
                        return (
                            dados.get("total_testes", 0),
                            dados.get("falhas_testes", 0),
                            dados.get("tempo_medio_testes", 0.0),
                        )
            except zipfile.BadZipFile:
                print(f"  Aviso: ZIP invalido para execucao {id_execucao}")

    return 0, 0, 0.0


# ── Função principal ──────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        print("ERRO: Defina a variavel de ambiente GITHUB_TOKEN antes de executar.")
        print("  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx")
        return

    if USUARIO == "SEU_USUARIO_AQUI":
        print("ERRO: Defina a variavel de ambiente GITHUB_USUARIO.")
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

        # duracao_workflow: tempo de execucao do runner (sem fila)
        duracao_workflow = calcular_duracao(
            execucao.get("run_started_at"),
            execucao.get("updated_at"),
        )

        # lead_time: tempo total desde o disparo ate o fim (inclui fila)
        lead_time = calcular_duracao(
            execucao.get("created_at"),
            execucao.get("updated_at"),
        )

        timestamp = execucao.get("created_at", "")

        print(f"Processando execucao #{id_exec} | {sha} | {status}")

        total_testes, falhas_testes, tempo_medio_testes = baixar_meta_testes(id_exec)
        jobs = obter_jobs(id_exec)

        # Fallback para execucoes sem tempo_medio_testes no artefato:
        # estima usando a duracao do step "Executar testes com pytest"
        if tempo_medio_testes == 0.0 and total_testes > 0:
            for job in jobs:
                for etapa in job.get("steps", []):
                    if "teste" in etapa.get("name", "").lower():
                        dur = calcular_duracao(etapa.get("started_at"), etapa.get("completed_at"))
                        if dur > 0:
                            tempo_medio_testes = round(dur / total_testes, 4)
                        break

        for job in jobs:
            duracao_job = calcular_duracao(job.get("started_at"), job.get("completed_at"))
            etapas = job.get("steps", [])

            if not etapas:
                # Job sem etapas detalhadas: registra uma linha com etapa vazia
                linhas.append({
                    "id_execucao": id_exec,
                    "sha_commit": sha,
                    "mensagem_commit": mensagem,
                    "status": status,
                    "duracao_workflow": round(duracao_workflow, 1),
                    "lead_time": round(lead_time, 1),
                    "nome_job": job["name"],
                    "duracao_job": round(duracao_job, 1),
                    "nome_etapa": "",
                    "duracao_etapa": "",
                    "total_testes": total_testes,
                    "falhas_testes": falhas_testes,
                    "tempo_medio_testes": tempo_medio_testes,
                    "timestamp": timestamp,
                })
            else:
                for etapa in etapas:
                    duracao_etapa = calcular_duracao(
                        etapa.get("started_at"),
                        etapa.get("completed_at"),
                    )
                    linhas.append({
                        "id_execucao": id_exec,
                        "sha_commit": sha,
                        "mensagem_commit": mensagem,
                        "status": status,
                        "duracao_workflow": round(duracao_workflow, 1),
                        "lead_time": round(lead_time, 1),
                        "nome_job": job["name"],
                        "duracao_job": round(duracao_job, 1),
                        "nome_etapa": etapa.get("name", ""),
                        "duracao_etapa": round(duracao_etapa, 1),
                        "total_testes": total_testes,
                        "falhas_testes": falhas_testes,
                        "tempo_medio_testes": tempo_medio_testes,
                        "timestamp": timestamp,
                    })

    with open(ARQUIVO_SAIDA, "w", newline="", encoding="utf-8") as arquivo_csv:
        escritor = csv.DictWriter(arquivo_csv, fieldnames=CAMPOS_CSV)
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"\nMetricas salvas em: {ARQUIVO_SAIDA}")
    print(f"Total de linhas geradas: {len(linhas)}")


if __name__ == "__main__":
    main()
