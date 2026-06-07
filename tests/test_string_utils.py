# -*- coding: utf-8 -*-
"""
Testes automatizados para o módulo string_utils.
"""
import string_utils


def test_reverter_texto_simples():
    assert string_utils.reverter("hello") == "olleh"


def test_reverter_texto_vazio():
    assert string_utils.reverter("") == ""


def test_eh_palindromo_verdadeiro():
    assert string_utils.eh_palindromo("arara") is True


def test_eh_palindromo_falso():
    assert string_utils.eh_palindromo("python") is False


def test_contar_vogais():
    assert string_utils.contar_vogais("hello world") == 3


def test_capitalizar_palavras():
    assert string_utils.capitalizar_palavras("olá mundo") == "Olá Mundo"


def test_contar_palavras_normal():
    assert string_utils.contar_palavras("uma frase simples") == 3


def test_contar_palavras_vazio():
    assert string_utils.contar_palavras("") == 0
