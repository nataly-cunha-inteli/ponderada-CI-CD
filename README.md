# Pipeline CI/CD — Análise de Métricas

Atividade avaliativa de programação com o objetivo de construir, executar e metrificar através de pipelines de CI/CD no GitHub Actions.

## Estrutura do projeto

```
ponderada-CI-CD/
├── .github/workflows/ci.yml   ← pipeline do GitHub Actions
├── src/string_utils.py        ← funções utilitárias de string
├── tests/test_string_utils.py ← testes automatizados das funções de string, com pytest
├── scripts/
│   ├── processar_resultados.py ← chamado pelo CI para gerar test-meta.json
│   ├── coletar_metricas.py    ← coleta métricas via GitHub API → CSV
│   └── gerar_graficos.py      ← gera gráficos de análise
├── data/                      ← CSVs gerados
├── graphs/                    ← gráficos PNG gerados
└── RELATORIO.md           ← relatório do experimento
```

## Execução rápida dos testes locais

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Coleta de métricas (após execuções no GitHub Actions)

```bash
pip install -r requirements-scripts.txt
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx
export GITHUB_USUARIO=seu_usuario
python scripts/coletar_metricas.py
python scripts/gerar_graficos.py
```
