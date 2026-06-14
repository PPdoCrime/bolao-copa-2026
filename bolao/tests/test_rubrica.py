import pytest
from bolao.rubrica import pontos

# (palpite_casa, palpite_fora, resultado_casa, resultado_fora, pontos_esperados, descrição)
CASOS = [
    # — Exemplos oficiais do regulamento (Sistema de pontos do ranking.txt) —
    (2, 0, 2, 0, 10, "oficial: completo"),
    (0, 0, 0, 0, 10, "oficial: completo 0x0"),
    (3, 0, 2, 0, 6,  "oficial: intermediário (gols do visitante batem)"),
    (4, 1, 3, 0, 6,  "oficial: intermediário (saldo bate)"),
    (2, 1, 4, 0, 5,  "oficial: básico (só vencedor)"),
    (2, 2, 1, 1, 5,  "oficial: ARMADILHA — empate vs empate dá 5, NÃO 6"),
    (2, 0, 0, 2, -2, "oficial: invertido"),
    (3, 0, 1, 2, 0,  "oficial: nenhum"),
    (1, 0, 1, 1, 0,  "oficial: ARMADILHA — gols da casa batem mas é 0"),
    # — Armadilhas e fronteiras adicionais —
    (1, 1, 1, 1, 10, "empate exato"),
    (1, 1, 2, 2, 5,  "empate vs outro empate"),
    (0, 0, 1, 1, 5,  "0x0 vs 1x1"),
    (2, 1, 1, 2, -2, "invertido não óbvio"),
    (1, 0, 0, 1, -2, "invertido mínimo"),
    (0, 3, 3, 0, -2, "invertido visitante"),
    (2, 1, 2, 0, 6,  "intermediário: gols da casa batem"),
    (2, 1, 3, 2, 6,  "intermediário: saldo bate"),
    (3, 1, 1, 0, 5,  "básico: nada bate além do vencedor"),
    (0, 1, 1, 2, 6,  "intermediário visitante: saldo -1 bate"),
    (0, 2, 1, 4, 5,  "básico visitante"),
    (2, 2, 0, 1, 0,  "palpite empate, resultado visitante: 0 (não é invertido)"),
    (5, 0, 5, 0, 10, "completo placar alto"),
]

@pytest.mark.parametrize("ph,pa,rh,ra,esperado,desc", CASOS)
def test_pontos(ph, pa, rh, ra, esperado, desc):
    assert pontos((ph, pa), (rh, ra)) == esperado, desc
