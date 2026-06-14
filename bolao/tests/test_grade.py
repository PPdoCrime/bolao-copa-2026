import pytest
from bolao.grade import (grade_probabilidades, achatar, ev_palpites, decisao,
                         escolher_palpite, celula_modal, MAX_GOLS)

def grade_deterministica(h, a):
    """Grade fake com P=1 no placar (h,a)."""
    g = [[0.0] * (MAX_GOLS + 1) for _ in range(MAX_GOLS + 1)]
    g[h][a] = 1.0
    return g

def test_grade_soma_1():
    g = grade_probabilidades(1.8, 1.1, rho=1.10)
    assert abs(sum(sum(l) for l in g) - 1.0) < 1e-9

def test_rho_infla_empates_baixos():
    g1 = grade_probabilidades(1.5, 1.2, rho=1.0)
    g2 = grade_probabilidades(1.5, 1.2, rho=1.2)
    assert g2[0][0] / g1[0][0] > 1.05  # 0x0 sobe (mesmo após renormalizar)
    assert g2[1][1] / g1[1][1] > 1.05  # 1x1 sobe

def test_achatar_mistura_uniforme():
    g = grade_deterministica(1, 0)
    g2 = achatar(g, w=0.25)
    n = (MAX_GOLS + 1) ** 2
    assert abs(g2[1][0] - (0.75 + 0.25 / n)) < 1e-9
    assert abs(g2[0][0] - 0.25 / n) < 1e-9
    assert abs(sum(sum(l) for l in g2) - 1.0) < 1e-9

def test_ev_contra_grade_deterministica():
    # resultado certo = 1x0: EVs viram os próprios pontos da rubrica
    g = grade_deterministica(1, 0)
    ev = dict(((p, round(e, 9)) for p, e in ev_palpites(g, multiplicador=1)))
    assert ev[(1, 0)] == 10
    assert ev[(2, 0)] == 6   # gols do visitante batem
    assert ev[(2, 1)] == 6   # saldo bate
    assert ev[(3, 1)] == 5   # só vencedor
    assert ev[(0, 1)] == -2  # invertido
    assert ev[(1, 1)] == 0

def test_multiplicador_dobra_ev():
    g = grade_deterministica(1, 0)
    ev2 = dict(ev_palpites(g, multiplicador=2))
    assert ev2[(1, 0)] == 20
    assert ev2[(0, 1)] == -4

def test_fronteira_invariante_ao_multiplicador():
    # regressão do bug do red team 12/06: a banda diferencial não pode encolher no mata-mata
    g = grade_probabilidades(1.3, 1.2, rho=1.10)
    d1 = decisao(g, multiplicador=1, delta=0.3)
    d3 = decisao(g, multiplicador=3, delta=0.3)
    assert d1["fronteira"] == d3["fronteira"]
    assert d3["margem"] == pytest.approx(3 * d1["margem"])

def grade_dupla():
    """P=0.5 em 1x0 e 0.5 em 2x0: EV(1x0)=EV(2x0)=8.0 (empate exato -> fronteira),
    aglomerado = {modal 1x0, cliche 2x1}; 2x0 fica FORA dele com EV 8.0."""
    g = [[0.0] * (MAX_GOLS + 1) for _ in range(MAX_GOLS + 1)]
    g[1][0] = 0.5
    g[2][0] = 0.5
    return g

def grade_cliche():
    """P=0.5 em 1x0 e 0.5 em 2x1: EV(1x0)=EV(2x1)=8.0 e a banda estreita coincide
    EXATAMENTE com o aglomerado {modal 1x0, cliche 2x1}; proximo EV fora: 2x0=6.0."""
    g = [[0.0] * (MAX_GOLS + 1) for _ in range(MAX_GOLS + 1)]
    g[1][0] = 0.5
    g[2][1] = 0.5
    return g

def test_escolher_sem_fronteira_crava_o_primeiro():
    g = grade_deterministica(1, 0)
    r = escolher_palpite(g, multiplicador=1, delta=0.05, estado="PELOTAO")
    assert r["palpite"] == (1, 0) and r["regra"].startswith("EV")

def test_escolher_fronteira_lider_cola_no_modal():
    r = escolher_palpite(grade_dupla(), delta=0.5, estado="LIDER")
    assert r["palpite"] == celula_modal(grade_dupla()) == (1, 0)
    assert "LIDER" in r["regra"]

def test_escolher_fronteira_pelotao_diverge_do_aglomerado():
    # aglomerado = {1x0 modal, 2x1 cliche do favorito}; melhor EV fora = 2x0 (8.0)
    r = escolher_palpite(grade_dupla(), delta=0.5, estado="PELOTAO")
    assert r["aglomerado"] == [(1, 0), (2, 1)]
    assert r["palpite"] == (2, 0) and "divergir" in r["regra"]

def test_escolher_banda_toda_no_aglomerado_crava_o_primeiro():
    # banda delta=0.5 = {1x0, 2x1} (EV 8.0) == aglomerado -> crava o 1º
    r = escolher_palpite(grade_cliche(), delta=0.5, estado="PELOTAO")
    assert r["palpite"] == (1, 0) and "aglomerado" in r["regra"]

def test_escolher_jogo_extremo_nao_diverge():
    r = escolher_palpite(grade_dupla(), delta=2.5, estado="PELOTAO", p_extremo=0.93)
    assert r["palpite"] == (1, 0) and "extremo" in r["regra"]

def test_escolher_cacador_banda_dobrada():
    # delta=1.25: banda do PELOTAO = so o aglomerado (crava 1º); CACADOR (2x) alcanca
    # EV>=5.5 e diverge pro melhor fora do aglomerado: 2x0 (6.0)
    rp = escolher_palpite(grade_cliche(), delta=1.25, estado="PELOTAO")
    rc = escolher_palpite(grade_cliche(), delta=1.25, estado="CACADOR")
    assert rp["palpite"] == (1, 0)
    assert rc["palpite"] == (2, 0)

def test_escolher_visitante_favorito_cliche_invertido():
    g = [[0.0] * (MAX_GOLS + 1) for _ in range(MAX_GOLS + 1)]
    g[0][1] = 0.5
    g[0][2] = 0.5
    r = escolher_palpite(g, delta=0.5, estado="PELOTAO")
    assert r["aglomerado"] == [(0, 1), (1, 2)]

def test_decisao_estrutura_e_fronteira():
    g = grade_probabilidades(1.8, 1.1, rho=1.10)
    d = decisao(g, multiplicador=1, delta=0.3)
    assert len(d["top3"]) == 3
    assert d["top3"][0]["ev"] >= d["top3"][1]["ev"] >= d["top3"][2]["ev"]
    assert d["margem"] == pytest.approx(d["top3"][0]["ev"] - d["top3"][1]["ev"])
    assert isinstance(d["fronteira"], bool)
    top = d["top3"][0]
    assert set(top) == {"palpite", "ev", "p_exato", "p_invertido"}
