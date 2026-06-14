"""Grade de placares (Poisson independente + inflador de empate) e otimizador de EV
contra a rubrica do bolão. Espelho exato das fórmulas da planilha (valida_planilha.py confere)."""
import math

from bolao.rubrica import pontos

MAX_GOLS = 6  # grade 0..6 por lado; massa além disso é desprezível p/ λ de futebol

def _pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)

def grade_probabilidades(lam_casa, lam_fora, rho=1.10):
    """P(placar) 0..6 x 0..6. rho infla 0x0 e 1x1 (efeito Dixon-Coles como constante);
    renormaliza no final (também condiciona à grade truncada)."""
    g = [[_pois(h, lam_casa) * _pois(a, lam_fora) for a in range(MAX_GOLS + 1)]
         for h in range(MAX_GOLS + 1)]
    g[0][0] *= rho
    g[1][1] *= rho
    total = sum(sum(linha) for linha in g)
    return [[x / total for x in linha] for linha in g]

def achatar(g, w):
    """Flags do checklist alargam incerteza: blend com uniforme. P' = (1-w)P + w/49."""
    if not 0.0 <= w <= 1.0:
        raise ValueError(f"w fora de [0,1]: {w}")
    assert abs(sum(sum(l) for l in g) - 1.0) < 1e-6, "grade deve estar normalizada antes de achatar"
    n2 = (MAX_GOLS + 1) ** 2
    return [[(1 - w) * x + w / n2 for x in linha] for linha in g]

def ev_palpites(g, multiplicador=1):
    """[(palpite, EV)] para todos os 49 candidatos, ordenado por EV desc.
    O multiplicador de fase (1/2/3) escala tudo, inclusive o -2."""
    n = MAX_GOLS + 1
    evs = []
    for ph in range(n):
        for pa in range(n):
            ev = sum(g[rh][ra] * pontos((ph, pa), (rh, ra))
                     for rh in range(n) for ra in range(n)) * multiplicador
            evs.append(((ph, pa), ev))
    evs.sort(key=lambda x: -x[1])
    return evs

def celula_modal(g):
    """Argmax P da grade = modal previsto do pelotão (POLITICA.md emenda 12/06)."""
    n = MAX_GOLS + 1
    return max(((h, a) for h in range(n) for a in range(n)), key=lambda c: g[c[0]][c[1]])

def escolher_palpite(g, multiplicador=1, delta=0.05, estado="PELOTAO", p_extremo=None):
    """POLITICA.md em código — devolve o palpite FINAL (sem etapa manual):
    - sem fronteira -> 1º por EV;
    - fronteira em jogo extremo (p_extremo > 0.90) -> 1º por EV (emenda 12/06-b);
    - fronteira + LIDER -> colar na célula modal (vender variância);
    - fronteira + PELOTAO/CACADOR -> melhor EV da banda (EV1-EV <= delta, em unidades
      de fase 1x; CACADOR usa 2*delta) FORA do aglomerado;
      empate residual: maior P(exato), depois menor P(invertido);
      banda toda dentro do aglomerado -> 1º por EV (emenda 12/06-b).
    Aglomerado (emenda 12/06-e, 3 distribuições reais do app): célula MODAL da grade
    + 2x1 DO FAVORITO (placar-clichê de vitória: ≥15% do pelotão em 2 dos 3 jogos,
    13,8% no outro) — "top-2 por P" errava o 2º lugar real."""
    d = decisao(g, multiplicador, delta)
    evs = ev_palpites(g, multiplicador)
    n = MAX_GOLS + 1
    por_p = sorted(((h, a) for h in range(n) for a in range(n)),
                   key=lambda c: -g[c[0]][c[1]])
    p_casa_win = sum(g[h][a] for h in range(n) for a in range(n) if h > a)
    p_fora_win = sum(g[h][a] for h in range(n) for a in range(n) if a > h)
    cliche = (2, 1) if p_casa_win >= p_fora_win else (1, 2)
    aglomerado = [por_p[0]] + ([cliche] if cliche != por_p[0] else [])
    escolha, regra = evs[0][0], "EV: cravar o 1º"
    if d["fronteira"]:
        if p_extremo is not None and p_extremo > 0.90:
            regra = "FRONTEIRA em jogo extremo -> cravar o 1º por EV"
        elif estado == "LIDER":
            escolha, regra = por_p[0], "FRONTEIRA + LIDER -> colar no modal do pelotão"
        else:
            banda_delta = delta * (2 if estado == "CACADOR" else 1)
            ev1 = evs[0][1]
            banda = [(p, ev) for p, ev in evs if (ev1 - ev) / multiplicador <= banda_delta]
            fora = [(p, ev) for p, ev in banda if p not in aglomerado]
            if fora:
                def chave(item):
                    (ph, pa), ev = item
                    return (-ev, -g[ph][pa], 0.0 if ph == pa else g[pa][ph])
                escolha = min(fora, key=chave)[0]
                regra = ("FRONTEIRA + %s -> divergir do aglomerado %s" %
                         (estado, "/".join(f"{h}x{a}" for h, a in aglomerado)))
            else:
                regra = "FRONTEIRA mas banda toda no aglomerado -> cravar o 1º por EV"
    return {"palpite": escolha, "regra": regra, "decisao": d,
            "aglomerado": aglomerado, "modal": por_p[0]}

def decisao(g, multiplicador=1, delta=0.3):
    """Top-3 por EV com P(exato)/P(invertido), margem sobre o 2º e flag de fronteira
    (margem <= delta => desempate diferencial contra o pelotão, ver POLITICA.md).
    BUG FIX 12/06 (red team): a fronteira compara a margem em unidades de fase 1x —
    sem isso o multiplicador 2x/3x ENCOLHIA a banda diferencial no mata-mata,
    o gradiente oposto ao que a política manda."""
    evs = ev_palpites(g, multiplicador)
    top3 = []
    for (ph, pa), ev in evs[:3]:
        p_inv = 0.0 if ph == pa else g[pa][ph]
        top3.append({"palpite": (ph, pa), "ev": ev, "p_exato": g[ph][pa], "p_invertido": p_inv})
    margem = top3[0]["ev"] - top3[1]["ev"]
    return {"top3": top3, "margem": margem,
            "fronteira": bool(margem / multiplicador <= delta)}
