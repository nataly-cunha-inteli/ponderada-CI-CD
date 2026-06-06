# -*- coding: utf-8 -*-
"""
Processa o arquivo XML gerado pelo pytest e cria test-meta.json.
Este script é chamado automaticamente pelo pipeline do GitHub Actions.
"""
import xml.etree.ElementTree as ET
import json
import os

ARQUIVO_XML = "test-results.xml"
ARQUIVO_META = "test-meta.json"

total = 0
falhas = 0

if os.path.exists(ARQUIVO_XML):
    tree = ET.parse(ARQUIVO_XML)
    root = tree.getroot()
    suite = root.find("testsuite") if root.tag != "testsuite" else root
    if suite is not None:
        total = int(suite.get("tests", 0))
        falhas = int(suite.get("failures", 0)) + int(suite.get("errors", 0))

meta = {"total_testes": total, "falhas_testes": falhas}

with open(ARQUIVO_META, "w", encoding="utf-8") as arquivo:
    json.dump(meta, arquivo, ensure_ascii=False)

print(f"Total de testes: {total} | Falhas: {falhas}")
