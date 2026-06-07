# -*- coding: utf-8 -*-
"""
Testes automatizados para o módulo string_utils.
"""
import string_utils
import time


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


def test_remover_duplicatas_lista():
    assert string_utils.remover_duplicatas([1, 2, 2, 3, 1]) == [1, 2, 3]


def test_remover_duplicatas_sem_duplicatas():
    assert string_utils.remover_duplicatas([1, 2, 3]) == [1, 2, 3]


def test_eh_anagrama_verdadeiro():
    assert string_utils.eh_anagrama("listen", "silent") is True


def test_eh_anagrama_falso():
    assert string_utils.eh_anagrama("hello", "world") is False


def test_truncar_texto_longo():
    assert string_utils.truncar("Olá, mundo!", 5) == "Olá, ..."


def test_truncar_texto_curto():
    assert string_utils.truncar("Olá", 10) == "Olá"


def test_contar_vogais_texto_vazio():
    assert string_utils.contar_vogais("") == 0


def test_operacao_lenta():
    time.sleep(3)
    assert string_utils.reverter("lento") == "otnel"


def test_reverter_numero_como_string():
    assert string_utils.reverter("12345") == "54321"


def test_eh_palindromo_com_espacos():
    frase = "amanaplanacanalpanama"
    assert string_utils.eh_palindromo(frase) is True


def test_contar_vogais_so_vogais():
    assert string_utils.contar_vogais("aeiou") == 5


def test_contar_vogais_so_consoantes():
    assert string_utils.contar_vogais("bcdfg") == 0


def test_capitalizar_palavras_uma_letra():
    assert string_utils.capitalizar_palavras("a") == "A"


def test_contar_palavras_multiplos_espacos():
    assert string_utils.contar_palavras("a  b  c") == 3


def test_remover_duplicatas_lista_vazia():
    assert string_utils.remover_duplicatas([]) == []


def test_eh_anagrama_maiusculas():
    assert string_utils.eh_anagrama("Listen", "Silent") is True


def test_truncar_sufixo_vazio():
    assert string_utils.truncar("hello world", 5, "") == "hello"


def test_truncar_tamanho_exato():
    assert string_utils.truncar("hello", 5) == "hello"
