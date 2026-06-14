"""Extração de gols esperados (λ) a partir de odds da linha afiada.
Operação (e planilha): O/U 2.5 dá o total λT; 1X2 dá a supremacia S; λ = (λT±S)/2.
Validação do backtest em seleções (só 1X2): lambdas_de_1x2 resolve (λT,S) das 2 probs.
Margem removida por normalização proporcional (suficiente; ver spec §7 sobre precisão)."""
import math

from scipy.optimize import brentq


def prob_implicita_2(odd_a, odd_b):
    ia, ib = 1 / odd_a, 1 / odd_b
    return ia / (ia + ib)


def prob_implicita_1x2(odd_h, odd_d, odd_a):
    ih, id_, ia = 1 / odd_h, 1 / odd_d, 1 / odd_a
    s = ih + id_ + ia
    return ih / s, id_ / s, ia / s


def total_de_ou25(p_over):
    """λT tal que P(Pois(λT) >= 3) = p_over."""
    f = lambda lt: 1 - math.exp(-lt) * (1 + lt + lt * lt / 2) - p_over
    return brentq(f, 0.05, 12.0)


def _pois(k, lam):
    # duplicado de grade.py de propósito: módulos independentes (decisão registrada em review)
    return math.exp(-lam) * lam ** k / math.factorial(k)


def p_casa_vence(lam_total, s, n=12):
    """P(casa vence) com Poisson independente, λh=(T+S)/2, λa=(T-S)/2 (sem rho:
    o viés sistemático é absorvido pela calibração de θ/ρ — idêntico em treino e operação)."""
    lh, la = (lam_total + s) / 2, (lam_total - s) / 2
    return sum(_pois(h, lh) * _pois(a, la) for h in range(n) for a in range(h))


def supremacia_de_1x2(lam_total, p_home):
    """S tal que p_casa_vence(lam_total, S) = p_home. Levanta ValueError (brentq) se
    p_home estiver fora do alcance do modelo (favorito extremo, p_home > ~0.98)."""
    eps = 0.02
    f = lambda s: p_casa_vence(lam_total, s) - p_home
    return brentq(f, -(lam_total - eps), lam_total - eps)


def p_empate(lam_total, s, n=12):
    lh, la = (lam_total + s) / 2, (lam_total - s) / 2
    return sum(_pois(k, lh) * _pois(k, la) for k in range(n))


def lambdas_de_1x2(odd_h, odd_d, odd_a):
    """(λh, λa) a partir só do 1X2: resolve λT por p_empate e S por p_home, alternando.
    Usado na validação em seleções (WorldCup2026.xlsx não tem O/U)."""
    p_h, p_d, _ = prob_implicita_1x2(odd_h, odd_d, odd_a)
    lt = 2.6  # chute inicial típico
    convergiu = False
    for _ in range(40):
        s = supremacia_de_1x2(lt, p_h)
        f = lambda t: p_empate(t, s) - p_d
        lt_novo = brentq(f, max(abs(s) + 0.04, 0.1), 12.0)
        if abs(lt_novo - lt) < 1e-7:
            lt = lt_novo
            convergiu = True
            break
        lt = lt_novo
    if not convergiu:
        import warnings
        warnings.warn(f"lambdas_de_1x2 não convergiu em 40 iterações (odds {odd_h}/{odd_d}/{odd_a})")
    s = supremacia_de_1x2(lt, p_h)
    return (lt + s) / 2, (lt - s) / 2
