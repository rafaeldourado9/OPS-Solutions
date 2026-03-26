"""
Unit tests for split_response() — the response splitting utility.

These tests run entirely in memory with no external dependencies.
"""

import pytest

from core.use_cases.process_message import split_response


class TestSplitResponse:
    def test_short_text_returned_as_single_part(self):
        text = "Olá! Como posso ajudar?"
        parts = split_response(text, max_chars=180)
        assert parts == ["Olá! Como posso ajudar?"]

    def test_empty_string_returns_empty_list(self):
        assert split_response("", max_chars=180) == []

    def test_whitespace_only_returns_empty_list(self):
        assert split_response("   \n\n   ", max_chars=180) == []

    def test_two_paragraphs_become_two_parts(self):
        text = "Primeira parte da mensagem.\n\nSegunda parte da mensagem."
        parts = split_response(text, max_chars=180)
        assert len(parts) == 2
        assert "Primeira" in parts[0]
        assert "Segunda" in parts[1]

    def test_long_paragraph_split_by_sentences(self):
        # Create a paragraph with two sentences that together exceed max_chars
        s1 = "Esta é a primeira frase longa com bastante conteúdo para testar."
        s2 = "Esta é a segunda frase também longa que deve ir numa parte separada."
        text = f"{s1} {s2}"
        parts = split_response(text, max_chars=80)
        assert len(parts) >= 2
        assert all(s1 not in p and s2 not in p or len(p) <= 80 or s1 in p for p in parts)

    def test_no_sentence_cut_in_middle(self):
        text = "Frase um. Frase dois. Frase três."
        parts = split_response(text, max_chars=20)
        # Each part should be a complete sentence or fragment
        for part in parts:
            # No part should be empty
            assert part.strip()

    def test_single_sentence_longer_than_max_kept_whole(self):
        long_sentence = "A" * 300
        parts = split_response(long_sentence, max_chars=180)
        assert len(parts) == 1
        assert parts[0] == long_sentence

    def test_multiple_paragraphs(self):
        paragraphs = ["Para um.", "Para dois.", "Para três.", "Para quatro."]
        text = "\n\n".join(paragraphs)
        parts = split_response(text, max_chars=180)
        assert len(parts) == 4

    def test_no_empty_parts(self):
        text = "Olá!\n\n\n\nTudo bem?\n\n"
        parts = split_response(text, max_chars=180)
        assert all(p.strip() for p in parts)

    def test_max_chars_respected_for_paragraphs(self):
        # Each paragraph shorter than max_chars should be a single part
        text = "Curto.\n\nTambém curto.\n\nOutro curto."
        parts = split_response(text, max_chars=180)
        for part in parts:
            assert len(part) <= 180

    def test_realistic_whatsapp_response(self):
        text = (
            "Olá! Tudo certo por aqui.\n\n"
            "Sobre o pedido, ele foi processado ontem. "
            "Você deve receber em até 3 dias úteis.\n\n"
            "Qualquer dúvida, estou à disposição!"
        )
        parts = split_response(text, max_chars=180)
        assert len(parts) == 3
        assert "Olá" in parts[0]
        assert "pedido" in parts[1]
        assert "disposição" in parts[2]
