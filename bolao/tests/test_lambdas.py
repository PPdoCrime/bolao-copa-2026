import math

import pytest
from bolao.lambdas import (prob_implicita_2, prob_implicita_1x2, total_de_ou25,
                           p_casa_vence, supremacia_de_1x2, lambdas_de_1x2)

def _pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)

def _probs_exatas(lh, la, n=12):
    ph = sum(_pois(h, lh) * _pois(a, la) for h in range(n) for a in range(h))
    pe = sum(_pois(k, lh) * _pois(k, la) for k in range(n))
    return ph, pe, 1 - ph - pe

def test_margem_2vias_simetrica():
    assert prob_implicita_2(1.90, 1.90) == pytest.approx(0.5)

def test_margem_1x2_soma_1():
    p = prob_implicita_1x2(2.10, 3.30, 3.80)
    assert sum(p) == pytest.approx(1.0)

def test_roundtrip_total_ou25():
    lt = 2.9
    p_over = 1 - math.exp(-lt) * (1 + lt + lt * lt / 2)  # P(Pois(2.9) >= 3)
    assert total_de_ou25(p_over) == pytest.approx(2.9, abs=1e-6)

def test_roundtrip_supremacia():
    lh, la = 1.8, 1.1
    p_home, _, _ = _probs_exatas(lh, la)
    s = supremacia_de_1x2(lh + la, p_home)
    assert s == pytest.approx(0.7, abs=0.01)

def test_p_casa_vence_monotona_em_s():
    assert p_casa_vence(2.9, 0.9) > p_casa_vence(2.9, 0.0) > p_casa_vence(2.9, -0.9)

def test_lambdas_de_1x2_roundtrip():
    lh, la = 1.6, 1.3
    ph, pe, pa = _probs_exatas(lh, la)
    oh, od, oa = 1 / ph, 1 / pe, 1 / pa  # odds justas, sem margem
    lh2, la2 = lambdas_de_1x2(oh, od, oa)
    assert lh2 == pytest.approx(lh, abs=0.03)
    assert la2 == pytest.approx(la, abs=0.03)
