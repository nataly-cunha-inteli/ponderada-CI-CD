# Pipeline CI/CD — Análise de Métricas

Atividade avaliativa de programação com o objetivo de construir, executar e metrificar através de pipelines de CI/CD no GitHub Actions.

## Estrutura do projeto

```
pondCICD/
├── .github/workflows/ci.yml   ← pipeline do GitHub Actions
├── src/string_utils.py        ← funções utilitárias de string
├── tests/test_string_utils.py ← testes automatizados com pytest
├── scripts/
│   ├── processar_resultados.py ← chamado pelo CI para gerar test-meta.json
│   ├── coletar_metricas.py    ← coleta métricas via GitHub API → CSV
│   └── gerar_graficos.py      ← gera os 4 gráficos de análise
├── data/                      ← CSVs gerados (ignorados pelo git)
├── graphs/                    ← gráficos PNG gerados (ignorados pelo git)
└── PASSO_A_PASSO.md           ← guia completo de reprodução do experimento
```

## Como reproduzir o experimento

Consulte o arquivo **PASSO_A_PASSO.md** para instruções detalhadas sobre:

1. Configuração do ambiente local
2. Sequência dos 12 commits com suas variações
3. Coleta de métricas via GitHub API
4. Geração dos gráficos

## Execução rápida dos testes locais

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Coleta de métricas (após as 12 execuções no GitHub Actions)

```bash
pip install -r requirements-scripts.txt
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx
export GITHUB_USUARIO=seu_usuario
python scripts/coletar_metricas.py
python scripts/gerar_graficos.py
```
