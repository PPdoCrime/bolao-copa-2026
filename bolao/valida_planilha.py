"""Valida a planilha contra o motor Python via Excel COM (requer Excel instalado).
3 cenários de odds justas geradas de λ conhecido: a planilha tem que recuperar λ
(tolerância = passo das tabelas de lookup) e o MESMO palpite ótimo do motor.
Empate de EV (|dif| < 0.05 entre o palpite do Excel e o top-1 do Python) conta como OK_TIE."""
import math
import os
import sys

import win32com.client

from bolao.grade import grade_probabilidades, achatar, decisao, ev_palpites
from bolao.lambdas import p_casa_vence, p_empate

CENARIOS = [  # (lam_casa, lam_fora) típicos: favorito médio, jogo parelho, favorito forte
    (1.8, 1.1), (1.35, 1.25), (2.4, 0.8),
]
THETA_DEFAULT, RHO_DEFAULT, DELTA_DEFAULT = 0.0, 1.10, 0.05  # red team 12/06 (ver Config)
XLSX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Bolao_Copa2026.xlsx")

def odds_justas(lh, la):
    lt, s = lh + la, lh - la
    p_h = p_casa_vence(lt, s); p_e = p_empate(lt, s); p_a = 1 - p_h - p_e
    p_over = 1 - math.exp(-lt) * (1 + lt + lt * lt / 2)
    return (1 / p_over, 1 / (1 - p_over), 1 / p_h, 1 / p_e, 1 / p_a)

def _abre_excel():
    # DispatchEx SEMPRE: Dispatch reusaria um Excel já aberto do usuário, e aí o
    # Visible=False esconderia a janela dele e o Quit() do finally fecharia as
    # planilhas dele com DisplayAlerts=False. Instância dedicada não tem esse risco.
    return win32com.client.DispatchEx("Excel.Application")

def _valida(xl):
    """Retorna nº de falhas. Excel já aberto; quem chama garante o Quit."""
    try:
        wb = xl.Workbooks.Open(XLSX)
    except Exception as e:  # lock (planilha aberta noutro Excel) etc.: NÃO forçar
        print(f"BLOCKED: Workbooks.Open falhou para {XLSX}: {e}")
        raise SystemExit(2)
    falhas = 0
    try:
        xl.CalculateFullRebuild()  # openpyxl não grava valores cacheados; força o cálculo
        val = wb.Worksheets("Validação").Range("F26").Value
        print(f"Validação rubrica (soma |dif|): {val}")
        if val != 0:
            falhas += 1
        ws = wb.Worksheets("Jogo")
        for lh, la in CENARIOS:
            o_over, o_under, o_h, o_d, o_a = odds_justas(lh, la)
            for celula, valor in [("B2", o_over), ("B3", o_under), ("B4", o_h),
                                  ("B5", o_d), ("B6", o_a), ("B7", 1), ("B8", 0), ("B9", 0)]:
                ws.Range(celula).Value = valor
            for r in range(2, 7):
                ws.Range(f"D{r}").Value = 0
            xl.CalculateFullRebuild()
            lh_xl, la_xl = ws.Range("B18").Value, ws.Range("B19").Value
            ev1_xl, palp_xl = ws.Range("Q2").Value, ws.Range("R2").Value
            if None in (lh_xl, la_xl, ev1_xl, palp_xl):
                falhas += 1
                print(f"λ({lh},{la}): célula vazia/erro no Excel: B18={lh_xl} B19={la_xl} "
                      f"Q2={ev1_xl} R2={palp_xl} -> FALHOU")
                continue
            # espelho do Excel: λ_final = λ_mercado*(1+θ); grade usa ρ da Config
            lh_t, la_t = lh * (1 + THETA_DEFAULT), la * (1 + THETA_DEFAULT)
            g = achatar(grade_probabilidades(lh_t, la_t, rho=RHO_DEFAULT), w=0.0)
            d = decisao(g, multiplicador=1, delta=DELTA_DEFAULT)
            ph, pa = d["top3"][0]["palpite"]
            # tolerância = 1 passo da tabela de lookup S (0,05) + arredondamento do passo T1 (0,01)
            ok_l = abs(lh_xl - lh_t) <= 0.06 and abs(la_xl - la_t) <= 0.06
            ok_p = palp_xl == f"{ph}x{pa}"
            ok_ev = abs(ev1_xl - d["top3"][0]["ev"]) <= 0.10
            if not ok_p:
                # Fronteira de EV: λ quantizado pode inverter palpites quase empatados.
                # Se NO PYTHON o EV do palpite do Excel está a <0.05 do top-1, é empate aceitável.
                try:
                    xh, xa = (int(t) for t in str(palp_xl).split("x"))
                    evs = dict(ev_palpites(g, multiplicador=1))
                    if abs(evs[(xh, xa)] - d["top3"][0]["ev"]) < 0.05:
                        ok_p = "TIE"
                except (ValueError, KeyError):
                    pass
            if ok_l and ok_p and ok_ev:
                status = "OK_TIE (EVs quase empatados)" if ok_p == "TIE" else "OK"
            else:
                status = "FALHOU"
                falhas += 1
            print(f"λ({lh},{la}): Excel λ=({lh_xl:.3f},{la_xl:.3f}) palpite={palp_xl} "
                  f"EV={ev1_xl:.3f} | Python palpite={ph}x{pa} EV={d['top3'][0]['ev']:.3f} -> {status}")
    finally:
        wb.Close(SaveChanges=False)
    return falhas

def main():
    if hasattr(sys.stdout, "reconfigure"):  # console cp1252 não imprime λ
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    xl = _abre_excel()
    try:
        xl.Visible = False; xl.DisplayAlerts = False
        falhas = _valida(xl)
    finally:
        xl.Quit()  # garante que o Excel.exe morre mesmo em exceção no meio
    print("VALIDAÇÃO GERAL:", "OK" if falhas == 0 else f"{falhas} FALHA(S)")
    raise SystemExit(0 if falhas == 0 else 1)

if __name__ == "__main__":
    main()
