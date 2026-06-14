"""Backtest: calibra theta (shade de λ), rho (inflador de empate) e delta (banda de
indiferença) maximizando pontos do bolão/jogo. Treino: clubes 2019/20–24/25 (football-data,
fechamento Pinnacle 1X2 + O/U 2.5). CV leave-one-season-out. Validação FINAL ÚNICA:
seleções (WorldCup2026.xlsx, 1X2). Compara: modal vs otimizador default vs tunado.

Resumível: CSVs por temporada/divisão, extrações parciais por temporada e o cache final
de λ ficam em bolao/dados/; se bolao/dados/_lambdas_cache.csv existir, download e
extração são pulados. Todo stdout é espelhado em bolao/backtest_report.md (append)."""
import datetime
import io
import itertools
import os

try:  # proxy corporativo intercepta TLS; usar certificados do Windows (CA do proxy)
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# O firewall corporativo faz MITM intermitente com raiz não confiada nem pelo Windows
# (truststore também falha). verify=False AQUI é aceitável: dataset público de placares,
# integridade conferida downstream (whitelist de colunas, ranges, bounds de extração).
# NÃO copiar este padrão para dados sensíveis.
VERIFY_TLS = False
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import numpy as np
import pandas as pd
import requests
from scipy.stats import poisson

from bolao.grade import MAX_GOLS
from bolao.lambdas import (prob_implicita_2, prob_implicita_1x2, total_de_ou25,
                           supremacia_de_1x2, lambdas_de_1x2)
from bolao.rubrica import pontos

import sys
if sys.stdout is not None:  # console cp1252 não imprime λ/θ/ρ/δ
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}  # sem UA o site dá 403

N = MAX_GOLS + 1
PASTA = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(PASTA, "dados")
CACHE_LAMBDAS = os.path.join(DADOS, "_lambdas_cache.csv")
REPORT = os.path.join(PASTA, "backtest_report.md")
TEMPORADAS = ["1920", "2021", "2122", "2223", "2324", "2425"]
DIVISOES = ["E0", "E1", "E2", "E3", "EC", "SC0", "SC1", "SC2", "SC3", "D1", "D2",
            "I1", "I2", "SP1", "SP2", "F1", "F2", "N1", "B1", "P1", "T1", "G1"]
COLS = ["FTHG", "FTAG", "PSCH", "PSCD", "PSCA", "PC>2.5", "PC<2.5"]
THETAS = [round(x, 3) for x in np.arange(-0.10, 0.101, 0.025)]
RHOS = [round(x, 2) for x in np.arange(1.00, 1.21, 0.02)]
DELTAS = [round(x, 2) for x in np.arange(0.05, 0.61, 0.05)]

PLACARES = [(h, a) for h in range(N) for a in range(N)]
MAT = np.array([[pontos(p, r) for r in PLACARES] for p in PLACARES], dtype=float)


def log(msg=""):
    """print + espelho incremental no report (sobrevive a interrupção)."""
    print(msg, flush=True)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")


def baixar_temporada(t):
    """Baixa (com cache por arquivo) e concatena as divisões de uma temporada."""
    frames = []
    for d in DIVISOES:
        fp = os.path.join(DADOS, f"{t}_{d}.csv")
        if not os.path.exists(fp):
            url = f"https://www.football-data.co.uk/mmz4281/{t}/{d}.csv"
            r = requests.get(url, timeout=30, verify=VERIFY_TLS, headers=UA)
            if r.status_code != 200 or len(r.content) < 500:
                log(f"pulei {t}/{d} (http {r.status_code})")
                continue
            with open(fp, "wb") as f:
                f.write(r.content)
        try:
            df = pd.read_csv(fp, encoding="latin-1", on_bad_lines="skip")
        except Exception as e:
            log(f"pulei {fp}: {e}")
            continue
        if all(c in df.columns for c in COLS):
            df = df[COLS].dropna().copy()
            odds_cols = ["PSCH", "PSCD", "PSCA", "PC>2.5", "PC<2.5"]
            df = df[(df[odds_cols] > 1.01).all(axis=1)]  # odd 0/lixo passa pelo dropna
            df["temporada"] = t
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=COLS + ["temporada"])
    base = pd.concat(frames, ignore_index=True)
    return base[(base["FTHG"] <= 20) & (base["FTAG"] <= 20)]


def extrair_lambdas(base_t):
    """λ-total e supremacia por jogo (inversão das odds). Memoizado em (p_over, p_home)
    arredondados a 5 casas — odds repetem muito, inversão por brentq é o gargalo."""
    memo = {}
    lts, ss = [], []
    it = base_t.rename(columns={"PC>2.5": "PCo25", "PC<2.5": "PCu25"})
    for i, r in enumerate(it.itertuples(index=False)):
        if i and i % 5000 == 0:
            log(f"  ... {i}/{len(base_t)} jogos extraídos")
        p_over = prob_implicita_2(r.PCo25, r.PCu25)
        p_h, _, _ = prob_implicita_1x2(r.PSCH, r.PSCD, r.PSCA)
        chave = (round(min(max(p_over, 0.02), 0.98), 5), round(min(max(p_h, 0.02), 0.96), 5))
        if chave not in memo:
            try:
                lt = total_de_ou25(chave[0])
                s = supremacia_de_1x2(lt, chave[1])
            except ValueError:
                lt, s = np.nan, np.nan
            memo[chave] = (lt, s)
        lt, s = memo[chave]
        lts.append(lt)
        ss.append(s)
    return base_t.assign(lam_total=lts, suprem=ss).dropna(subset=["lam_total", "suprem"])


def construir_base():
    """Base de treino com λ extraído. Cache final + parciais por temporada (resumível)."""
    os.makedirs(DADOS, exist_ok=True)
    if os.path.exists(CACHE_LAMBDAS):
        base = pd.read_csv(CACHE_LAMBDAS, dtype={"temporada": str})
        log(f"cache de λ encontrado ({CACHE_LAMBDAS}): {len(base)} jogos — "
            "pulando download e extração")
        return base
    parciais = []
    for t in TEMPORADAS:
        pfp = os.path.join(DADOS, f"_lambdas_parcial_{t}.csv")
        if os.path.exists(pfp):
            p = pd.read_csv(pfp, dtype={"temporada": str})
            log(f"temporada {t}: parcial em cache, {len(p)} jogos com λ")
            parciais.append(p)
            continue
        bt = baixar_temporada(t)
        log(f"temporada {t}: {len(bt)} jogos baixados; extraindo λ...")
        bt = extrair_lambdas(bt)
        bt[["FTHG", "FTAG", "temporada", "lam_total", "suprem"]].to_csv(pfp, index=False)
        log(f"temporada {t}: {len(bt)} jogos com λ extraído (parcial salvo)")
        parciais.append(bt[["FTHG", "FTAG", "temporada", "lam_total", "suprem"]])
    base = pd.concat(parciais, ignore_index=True)
    base.to_csv(CACHE_LAMBDAS, index=False)
    log(f"base de treino: {len(base)} jogos com λ (cache salvo em {CACHE_LAMBDAS})")
    return base


def grades(lam_casa, lam_fora, rho):
    ph = poisson.pmf(np.arange(N)[None, :], lam_casa[:, None])
    pa = poisson.pmf(np.arange(N)[None, :], lam_fora[:, None])
    g = ph[:, :, None] * pa[:, None, :]
    g[:, 0, 0] *= rho
    g[:, 1, 1] *= rho
    g = g.reshape(len(lam_casa), N * N)
    return g / g.sum(axis=1, keepdims=True)


def pontos_por_jogo(base, theta, rho, escolha="ev"):
    lh = (base["lam_total"] + base["suprem"]).values / 2 * (1 + theta)
    la = (base["lam_total"] - base["suprem"]).values / 2 * (1 + theta)
    la = np.maximum(la, 0.05)
    g = grades(lh, la, rho)
    if escolha == "modal":
        pick = g.argmax(axis=1)
    else:
        pick = (g @ MAT.T).argmax(axis=1)
    res_idx = (base["FTHG"].clip(0, 6) * 7 + base["FTAG"].clip(0, 6)).astype(int).values
    return MAT[pick, res_idx]


def _pontos_grid(base):
    """Pontos por jogo (base inteira) para cada (θ, ρ) da grade — calculado uma vez e
    reaproveitado no CV e no tuning final (resultado idêntico, ~7x menos contas)."""
    return {(t, r): pontos_por_jogo(base, t, r)
            for t, r in itertools.product(THETAS, RHOS)}


def cv_por_temporada(base, grid):
    melhor_por_fold = {}
    temporadas = base["temporada"].values
    for fold in TEMPORADAS:
        m = temporadas != fold
        if not (~m).any():
            log(f"fold {fold}: sem jogos, pulado")
            continue
        scores = {tr: pts[m].mean() for tr, pts in grid.items()}
        (t_, r_), _ = max(scores.items(), key=lambda kv: kv[1])
        fora = grid[(t_, r_)][~m].mean()
        melhor_por_fold[fold] = (t_, r_, fora)
        log(f"fold {fold}: θ*={t_} ρ*={r_} pts/jogo fora={fora:.4f}")
    return melhor_por_fold


def tunar_final(grid):
    scores = {tr: pts.mean() for tr, pts in grid.items()}
    return max(scores.items(), key=lambda kv: kv[1])


def calibrar_delta(base, theta, rho):
    lh = (base["lam_total"] + base["suprem"]).values / 2 * (1 + theta)
    la = np.maximum((base["lam_total"] - base["suprem"]).values / 2 * (1 + theta), 0.05)
    g = grades(lh, la, rho)
    ev = g @ MAT.T
    ordem = np.argsort(-ev, axis=1)
    p1, p2 = ordem[:, 0], ordem[:, 1]
    margem = ev[np.arange(len(ev)), p1] - ev[np.arange(len(ev)), p2]
    res_idx = (base["FTHG"].clip(0, 6) * 7 + base["FTAG"].clip(0, 6)).astype(int).values
    dif = MAT[p1, res_idx] - MAT[p2, res_idx]
    linhas = []
    for dlt in DELTAS:
        m = margem <= dlt
        linhas.append((dlt, int(m.sum()), float(dif[m].mean()) if m.any() else 0.0))
    return linhas


# ── Detecção de colunas no WorldCup2026.xlsx (nomes reais podem divergir do plano) ──
_BOOKIES = ["PSC", "PS", "PC", "Pinny", "P", "B365C", "B365", "AvgC", "Avg",
            "MaxC", "Max", "BbAv", "IW", "WH", "VC"]
TRIOS_CONHECIDOS = []
for _b in _BOOKIES:
    TRIOS_CONHECIDOS += [(f"{_b}H", f"{_b}D", f"{_b}A"), (f"{_b}-H", f"{_b}-D", f"{_b}-A"),
                         (f"H_{_b}", f"D_{_b}", f"A_{_b}"), (f"H-{_b}", f"D-{_b}", f"A-{_b}")]
GOLS_CONHECIDOS = [("HGFT", "AGFT"), ("FTHG", "FTAG"), ("HG", "AG"), ("Hgoal", "Agoal"),
                   ("HomeGoals", "AwayGoals"), ("GH", "GA"), ("HFT", "AFT"),
                   ("Home Goals", "Away Goals"), ("HS", "AS")]


def _norm_cols(df):
    return {str(c).strip().lower(): c for c in df.columns}


def _achar_trio(df):
    """Trio de odds 1X2: primeiro candidatos conhecidos, depois detecção genérica por
    radical comum (xH/xD/xA ou Hx/Dx/Ax) validada pelos valores (odds plausíveis)."""
    nc = _norm_cols(df)
    for trio in TRIOS_CONHECIDOS:
        chaves = [t.lower() for t in trio]
        if all(k in nc for k in chaves):
            cand = tuple(nc[k] for k in chaves)
            if _valida_odds(df, cand):
                return cand
    genericos = []
    for norm, orig in nc.items():
        if norm.endswith("h") and norm[:-1] + "d" in nc and norm[:-1] + "a" in nc:
            genericos.append((nc[norm], nc[norm[:-1] + "d"], nc[norm[:-1] + "a"]))
        if norm.startswith("h") and "d" + norm[1:] in nc and "a" + norm[1:] in nc:
            genericos.append((nc[norm], nc["d" + norm[1:]], nc["a" + norm[1:]]))
    genericos = [g for g in genericos if _valida_odds(df, g)]
    if not genericos:
        return None
    def prio(g):
        n = str(g[0]).lower()
        for i, tag in enumerate(["ps", "pin", "b365", "avg", "max"]):
            if tag in n:
                return i
        return 9
    return sorted(genericos, key=prio)[0]


def _valida_odds(df, trio):
    try:
        v = df[list(trio)].apply(pd.to_numeric, errors="coerce").dropna()
    except Exception:
        return False
    if len(v) < 10:
        return False
    if (v < 1.0).any().any():
        return False
    return 2.0 <= v.iloc[:, 1].median() <= 15.0  # odd de empate plausível


def _achar_gols(df):
    nc = _norm_cols(df)
    for par in GOLS_CONHECIDOS:
        chaves = [p.lower() for p in par]
        if all(k in nc for k in chaves):
            cand = tuple(nc[k] for k in chaves)
            if _valida_gols(df, cand):
                return cand
    genericos = []
    for norm, orig in nc.items():
        if "g" not in norm:
            continue
        if norm.startswith("h") and "a" + norm[1:] in nc:
            genericos.append((orig, nc["a" + norm[1:]]))
        if norm.endswith("h") and norm[:-1] + "a" in nc:
            genericos.append((orig, nc[norm[:-1] + "a"]))
    genericos = [g for g in genericos if _valida_gols(df, g)]
    return genericos[0] if genericos else None


def _valida_gols(df, par):
    try:
        v = df[list(par)].apply(pd.to_numeric, errors="coerce").dropna()
    except Exception:
        return False
    if len(v) < 10:
        return False
    inteiro = ((v % 1) == 0).all().all()
    return inteiro and (v >= 0).all().all() and (v <= 15).all().all() and v.median().max() <= 4


def carregar_selecoes():
    """Jogos de seleções do WorldCup2026.xlsx (download com cache local). Varre TODAS as
    abas e auto-detecta colunas de odds 1X2 e gols — os nomes do plano original
    (Pinny-H/HGFT) podem não existir; reporta o mapeamento usado por aba."""
    fp = os.path.join(DADOS, "WorldCup2026.xlsx")
    if not os.path.exists(fp):
        url = "https://www.football-data.co.uk/WorldCup2026.xlsx"
        log(f"baixando {url} ...")
        raw = requests.get(url, timeout=60, verify=VERIFY_TLS, headers=UA).content
        with open(fp, "wb") as f:
            f.write(raw)
    xl = pd.ExcelFile(fp)
    log(f"abas no xlsx: {xl.sheet_names}")
    frames = []
    for aba in xl.sheet_names:
        try:
            df = xl.parse(aba)
        except Exception as e:
            log(f"aba {aba}: falha ao ler ({e}), pulada")
            continue
        trio, gols = _achar_trio(df), _achar_gols(df)
        if trio is None or gols is None:
            log(f"aba {aba}: sem odds 1X2 + gols detectáveis, pulada. "
                f"Colunas: {list(df.columns)}")
            continue
        d = df[[*trio, *gols]].apply(pd.to_numeric, errors="coerce").dropna()
        if d.empty:
            log(f"aba {aba}: mapeamento {trio}+{gols} mas 0 linhas completas, pulada")
            continue
        d.columns = ["oh", "od", "oa", "gh", "ga"]
        log(f"aba {aba}: odds={trio} gols={gols} → {len(d)} jogos")
        frames.append(d)
    if not frames:
        raise RuntimeError("nenhuma aba do WorldCup2026.xlsx rendeu dados utilizáveis")
    return pd.concat(frames, ignore_index=True)


def validar_selecoes(theta, rho):
    sel = carregar_selecoes()
    lams, manter, pulados = [], [], 0
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for r in sel.itertuples():
            try:
                lams.append(lambdas_de_1x2(r.oh, r.od, r.oa))
                manter.append(True)
            except Exception:  # odds extremas (ex.: 1.01) estouram o brentq
                pulados += 1
                manter.append(False)
    sel = sel[manter].copy()
    log(f"validação seleções: {len(sel)} jogos ({pulados} pulados por odds extremas)")
    sel["lam_total"] = [a + b for a, b in lams]
    sel["suprem"] = [a - b for a, b in lams]
    sel["FTHG"], sel["FTAG"] = sel["gh"], sel["ga"]
    sel["temporada"] = "sel"
    resultados = {}
    for nome, (t, r, esc) in {"modal": (0.0, 1.0, "modal"),
                              "ev_default": (0.0, 1.10, "ev"),
                              "ev_tunado": (theta, rho, "ev")}.items():
        pts = pontos_por_jogo(sel, t, r, escolha=esc)
        resultados[nome] = (pts.mean(), pts)
    base_pts = resultados["modal"][1]
    for nome, (media, pts) in resultados.items():
        dif = pts - base_pts
        boots = [np.random.default_rng(i).choice(dif, len(dif)).mean() for i in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        log(f"{nome}: {media:.4f} pts/jogo | vs modal: dif média {dif.mean():.4f} "
            f"IC95 [{lo:.4f}, {hi:.4f}]")
    return resultados


def main():
    inicio = datetime.datetime.now()
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(f"\n\n# Backtest θ/ρ/δ — run {inicio:%Y-%m-%d %H:%M:%S}\n\n")
    base = construir_base()
    log("\n== Grade de pontos por (θ, ρ) na base de treino ==")
    grid = _pontos_grid(base)
    log(f"grade computada: {len(grid)} combinações θxρ sobre {len(base)} jogos")
    log("\n== CV por temporada (estabilidade) ==")
    cv_por_temporada(base, grid)
    log("\n== Tuning final em toda a base ==")
    (theta, rho), score = tunar_final(grid)
    log(f"θ*={theta} ρ*={rho} pts/jogo treino={score:.4f}")
    log("\n== Curva de delta (banda de indiferença) ==")
    delta_estrela = None
    for dlt, nb, perda in calibrar_delta(base, theta, rho):
        log(f"δ={dlt}: {nb} jogos na banda, perda real média de trocar p/ 2º = {perda:+.4f}")
        if abs(perda) < 0.05:
            delta_estrela = dlt
    log(f"δ* sugerido (maior δ com |perda| < 0.05): {delta_estrela}")
    log("\n== VALIDAÇÃO FINAL (seleções, uma única vez) ==")
    resultados = validar_selecoes(theta, rho)
    m_def, m_tun = resultados["ev_default"][0], resultados["ev_tunado"][0]
    log("\n== RECOMENDAÇÃO (não aplicada — regra de decisão) ==")
    if m_tun >= m_def:
        log(f"ev_tunado ({m_tun:.4f}) >= ev_default ({m_def:.4f}) nas seleções: "
            f"RECOMENDO atualizar Config para B2=θ*={theta}, B3=ρ*={rho}, "
            f"B4=δ*={delta_estrela} e re-rodar valida_planilha.")
    else:
        log(f"ev_tunado ({m_tun:.4f}) < ev_default ({m_def:.4f}) nas seleções: "
            f"RECOMENDO MANTER os defaults da Config (θ=0, ρ=1.10, δ=0.3).")
    log(f"\nruntime total: {datetime.datetime.now() - inicio}")


if __name__ == "__main__":
    main()
