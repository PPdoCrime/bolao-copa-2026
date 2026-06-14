"""Rubrica de pontos do bolão. Fonte: 'Sistema de pontos do ranking.txt' (regras fixas da plataforma).

Armadilha central: para palpite de empate, o acerto intermediário (6) é inalcançável —
o exemplo oficial '2x2 vs 1x1 = 5' prova que o saldo igual NÃO promove empate a 6.
"""

COMPLETO = 10
INTERMEDIARIO = 6
BASICO = 5
INVERTIDO = -2


def pontos(palpite: tuple, resultado: tuple) -> int:
    """Pontos do bolão para um palpite (casa, fora) contra um resultado (casa, fora)."""
    ph, pa = palpite
    rh, ra = resultado
    if (ph, pa) == (rh, ra):
        return COMPLETO
    sinal_p = (ph > pa) - (ph < pa)
    sinal_r = (rh > ra) - (rh < ra)
    if sinal_p == sinal_r:
        if sinal_p == 0:
            return BASICO
        # 6 pts exige, além do vencedor: gols de UM dos lados OU o saldo batendo
        if ph == rh or pa == ra or (ph - pa) == (rh - ra):
            return INTERMEDIARIO
        return BASICO
    if (ph, pa) == (ra, rh):
        return INVERTIDO
    return 0
