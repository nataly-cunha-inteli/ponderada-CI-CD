# -*- coding: utf-8 -*-
"""Utilitários para manipulação de strings.

Primeiro script de função simples apenas para servir de utilitário para testar a pipeline de CI/CD.
"""


def reverter(texto):
    """Retorna o texto na ordem invertida."""
    return texto[::-1]


def eh_palindromo(texto):
    """Verifica se o texto é um palíndromo (ignora maiúsculas e espaços)."""
    limpo = texto.lower().replace(" ", "")
    return limpo == limpo[::-1]


def contar_vogais(texto):
    """Conta o número de vogais no texto (incluindo acentuadas)."""
    vogais = "aeiouáéíóúâêîôûãõ"
    return sum(1 for caractere in texto.lower() if caractere in vogais)


def capitalizar_palavras(texto):
    """Capitaliza a primeira letra de cada palavra."""
    return texto.title()


def contar_palavras(texto):
    """Conta o número de palavras no texto."""
    if not texto.strip():
        return 0
    return len(texto.split())


def remover_duplicatas(lista):
    """Remove elementos duplicados de uma lista mantendo a ordem original."""
    vistos = set()
    resultado = []
    for item in lista:
        if item not in vistos:
            vistos.add(item)
            resultado.append(item)
    return resultado


def eh_anagrama(texto1, texto2):
    """Verifica se dois textos são anagramas entre si."""
    normalizar = lambda t: sorted(t.lower().replace(" ", ""))  # noqa: E731
    return normalizar(texto1) == normalizar(texto2)


def truncar(texto, limite, sufixo="..."):
    """Trunca o texto ao limite de caracteres, adicionando sufixo se necessário."""
    if len(texto) <= limite:
        return texto
    return texto[:limite] + sufixo
