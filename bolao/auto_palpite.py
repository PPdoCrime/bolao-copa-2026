"""Palpite automático COMPLETO: roda a cada 20 min (Agendador do Windows), detecta jogo
da Copa, captura odds (~T-40), roda o motor, APLICA A POLITICA (fase por data, flags
computáveis, tripwire de Elo, estado de ranking, resolução de fronteira) e envia o
palpite FINAL por e-mail (Outlook via COM — sem senha). Uma RECHECAGEM (~T-20) recaptura
e só manda novo e-mail se o palpite MUDOU (lesão/linha que andou — POLITICA lista 2).

uso manual: python -m bolao.auto_palpite                      (uma varredura)
            python -m bolao.auto_palpite --teste              (e-mail de teste e sai)
            python -m bolao.auto_palpite --digest             (e-mail com os jogos de hoje)
            python -m bolao.auto_palpite --simular t1 t2      (pipeline completo no
                                                               console, sem e-mail)

O que segue HUMANO (não dá pra automatizar): lesão/expulsão/clima súbito APÓS a captura
(POLITICA lista 2), confirmação de time reserva na escalação (rodada 3) e o LOCK no app.
Estado de ranking: editar dados/auto_config.json {"estado": "LIDER|PELOTAO|CACADOR"}.
Horários: lidos do JSON-LD (schema.org SportsEvent) do HTML cru do SportyTrader —
startDate vem em ISO COM fuso explícito (UTC), convertido p/ Brasília (UTC-3) de forma
exata. O horário do texto markdown NÃO tem fuso e oscila ±1h conforme qual servidor do
jina renderiza (foi o que mostrava 15:00 p/ jogo das 16:00); por isso não é mais usado."""
import datetime
import json
import os
import re
import sys
import warnings

# bootstrap: permite rodar por caminho de arquivo (Agendador) sem depender do cwd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings("ignore")
import requests

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from bolao.odds import (COMPETICAO, JINA, UA, achar_jogo, analisar, capturar,
                        captura_ok)

JANELA_MIN = (10, 55)     # 1º palpite: kickoff entre 10 e 55 min à frente (10 e não 25
                          # p/ que UMA falha transitória de captura ainda tenha retry)
JANELA_RECHECK = (4, 26)  # confirmação: recaptura e SÓ avisa se o palpite mudou
                          # (largura 22 > cadência 20: sem buraco mesmo se a grade
                          # da tarefa for re-registrada em outro minuto)
EMAIL = os.environ.get("BOLAO_EMAIL", "")  # só p/ Outlook local; na nuvem usa Telegram
TRIPWIRE_GOLS = 0.4       # = Config!tripwire_gols (política congelada)
FIM_GRUPOS = datetime.date(2026, 6, 27)
INICIO_RODADA3 = datetime.date(2026, 6, 24)
DATA_FINAL = datetime.date(2026, 7, 19)
ANFITRIOES = ("MX", "US", "CA")   # únicos com mando real; resto é campo neutro
PASTA = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(PASTA, "dados", "_palpites_enviados.json")
FIXCACHE = os.path.join(PASTA, "dados", "_fixtures_cache.json")
LOGFILE = os.path.join(PASTA, "dados", "auto_palpite.log")


def logar(msg):
    linha = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha)
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _do_cache(motivo):
    """Fallback de calendário: lê o cache em disco. Sem cache, propaga o erro."""
    if not os.path.exists(FIXCACHE):
        raise motivo if isinstance(motivo, BaseException) else RuntimeError(str(motivo))
    logar(f"listagem indisponível ({motivo}) — usando cache do calendário")
    with open(FIXCACHE, encoding="utf-8") as f:
        return sorted((datetime.datetime.fromisoformat(d), n, u) for d, n, u in json.load(f))


def fixtures():
    """[(kickoff_brt, 'Home - Away', url)] do JSON-LD (schema.org SportsEvent) do HTML
    cru do SportyTrader. startDate vem em ISO COM fuso explícito → conversão p/ Brasília
    (UTC-3) exata e imune ao drift de fuso do render (o horário do markdown não tem fuso
    e oscilava ±1h conforme o servidor do jina). Sucesso grava cache; falha de rede (ou
    JSON-LD ausente) cai no cache — sem isso, um soluço da rede na varredura certa =
    jogo perdido em silêncio."""
    try:
        txt = requests.get(JINA + COMPETICAO, timeout=90, verify=False,
                           headers={**UA, "X-Return-Format": "html"}).text
    except Exception as e:
        return _do_cache(e)
    brt = datetime.timezone(datetime.timedelta(hours=-3))
    jogos = []

    def _coletar(o):
        if isinstance(o, dict):
            if o.get("@type") == "SportsEvent":
                start, url = o.get("startDate"), o.get("url")
                home = (o.get("homeTeam") or {}).get("name")
                away = (o.get("awayTeam") or {}).get("name")
                if start and url and home and away:
                    dt = datetime.datetime.fromisoformat(start)
                    if dt.tzinfo is None:                 # sem fuso no ISO: assume UTC
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                    dt = dt.astimezone(brt).replace(tzinfo=None)  # naive em horário BRT
                    jogos.append((dt, f"{home} - {away}", url))
            for v in o.values():
                _coletar(v)
        elif isinstance(o, list):
            for v in o:
                _coletar(v)

    for bloco in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", txt, re.S):
        try:
            _coletar(json.loads(bloco.strip()))
        except ValueError:
            continue
    jogos = sorted(set(jogos))
    if jogos:
        os.makedirs(os.path.dirname(FIXCACHE), exist_ok=True)
        with open(FIXCACHE, "w", encoding="utf-8") as f:
            json.dump([(dt.isoformat(), n, u) for dt, n, u in jogos], f)
        return jogos
    return _do_cache("JSON-LD vazio (schema mudou?)")  # fetch ok mas sem eventos


def contexto(dt):
    """(fase, nflags, avisos) derivados da DATA do jogo — antes era manual.
    -3h: jogo após a meia-noite BRT pertence ao matchday anterior (senão um jogo de
    grupo 00:30 de 28/06 viraria fase=2: multiplicador muda a fronteira e some a flag)."""
    d = (dt - datetime.timedelta(hours=3)).date()
    fase = 1 if d <= FIM_GRUPOS else (3 if d >= DATA_FINAL else 2)
    flags, avisos = 0, []
    if INICIO_RODADA3 <= d <= FIM_GRUPOS:
        flags += 1
        avisos.append("RODADA 3 — flag dead-rubber LIGADA (grade achatada). Risco de "
                      "time reserva: ver escalação a T-75; exceção de λ só manual "
                      "(POLITICA lista 1).")
    if fase >= 2:
        avisos.append(f"MATA-MATA (EV x{fase}): vale o placar do FIM DA PRORROGAÇÃO; "
                      "pênaltis NÃO contam. ATENÇÃO: grade ainda é de 90' — NÃO travar "
                      "sem o motor 120' (Task 12); até lá, conferir manual.")
    return fase, flags, avisos


def tripwire(nome, lt, s_mercado, p_emp):
    """S_elo vs S do mercado (>0,4 gol = conferir a captura, nunca ajustar na mão).
    Mando só pros anfitriões; resto da Copa é campo neutro. Elo do TSV local (estático;
    drift de dias é irrelevante pro limiar de 0,4).
    BUG FIX 12/06 (red team interno): We do Elo é SCORE ESPERADO (empate vale 1/2),
    não P(vitória) — usar We direto inflava S_elo de todo favorito e o tripwire viraria
    alarme falso crônico (fadiga -> erro real passa batido). Conversão: p_win = We - p_emp/2."""
    try:
        from bolao.elo_s import carregar, resolver
        from bolao.lambdas import supremacia_de_1x2
        casa, fora = [t.strip() for t in nome.split(" - ", 1)]
        ratings = carregar()
        cod_c, elo_c = resolver(casa, ratings)
        cod_f, elo_f = resolver(fora, ratings)
        # anfitrião joga em casa MESMO listado como visitante (ex.: Czechia x Mexico
        # é no México) — só o mando administrativo da esquerda errava o sinal do dr
        bonus_c = 100 if cod_c in ANFITRIOES else 0
        bonus_f = 100 if cod_f in ANFITRIOES else 0
        we = 1 / (10 ** (-(elo_c + bonus_c - elo_f - bonus_f) / 400) + 1)
        p_win = min(max(we - p_emp / 2, 0.03), 0.96)
        s_elo = supremacia_de_1x2(lt, p_win)
        gap = abs(s_elo - s_mercado)
        ok = gap <= TRIPWIRE_GOLS
        return ok, (f"tripwire Elo [{cod_c} {elo_c}{'+' + str(bonus_c) if bonus_c else ''} x "
                    f"{cod_f} {elo_f}{'+' + str(bonus_f) if bonus_f else ''}]: "
                    f"S_elo={s_elo:.2f} vs S_mercado={s_mercado:.2f} "
                    f"(gap {gap:.2f}) -> " + ("ok" if ok else "⚠ CONFERIR captura"))
    except (Exception, SystemExit) as e:
        return True, f"tripwire indisponível ({type(e).__name__}: {e})"


def montar(dt, nome, odds, disp, relatorio, info, avisos, msg_trip):
    ph, pa = info["palpite"]
    extras = "".join(f"⚠ {a}\n" for a in avisos)
    corpo = (f"{nome} — kickoff {dt:%d/%m %H:%M} (Brasília, estimado)\n\n"
             f"PALPITE FINAL: {ph} x {pa}   [{info['regra']} | estado={info['estado']}]\n"
             f"{msg_trip}\n\n"
             f"odds (medianas): Over2.5={odds['over']:.2f} Under2.5={odds['under']:.2f} "
             f"Casa={odds['casa']:.2f} Empate={odds['empate']:.2f} Fora={odds['fora']:.2f}\n"
             f"[{disp}]\n\n{relatorio}\n\n{extras}"
             "Lesão/expulsão/clima que o MERCADO viu já está na linha (e a rechecagem "
             "~T-20 reenvia se o palpite mudar). Só te segura: você sabe de algo que o "
             "mercado NÃO sabe, ou 'jogo especial'? Senão, TRAVAR NO APP.")
    return corpo


def _enviar_outlook(assunto, corpo):
    import win32com.client
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = EMAIL
    mail.Subject = assunto
    mail.Body = corpo
    mail.Send()


def _enviar_telegram(assunto, corpo):
    tok = os.environ["TELEGRAM_TOKEN"]
    chat = os.environ["TELEGRAM_CHAT_ID"]
    texto = f"{assunto}\n\n{corpo}"[:4096]  # limite do Telegram
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      data={"chat_id": chat, "text": texto}, timeout=30)
    r.raise_for_status()


def enviar_email(assunto, corpo):
    """Dispatcher (mantém o nome p/ não mexer nos call sites): Telegram quando
    TELEGRAM_TOKEN está no ambiente (nuvem/GitHub Actions), senão Outlook COM (local)."""
    if os.environ.get("TELEGRAM_TOKEN"):
        _enviar_telegram(assunto, corpo)
    else:
        _enviar_outlook(assunto, corpo)


def carregar_estado():
    """{url: {'palpite': '2x0', 'rechecado': bool}} (migra o formato antigo = lista).
    JSON corrompido NÃO pode matar a varredura pra sempre: e-mail duplicado é melhor
    que silêncio permanente com heartbeat verde (digest não passa por aqui)."""
    try:
        if os.path.exists(ESTADO):
            with open(ESTADO, encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, list):
                return {u: {"palpite": "?", "rechecado": True} for u in dados}
            return dados
    except (OSError, ValueError) as e:
        logar(f"estado corrompido ({type(e).__name__}) — recomeçando vazio")
    return {}


def salvar_estado(feitos):
    os.makedirs(os.path.dirname(ESTADO), exist_ok=True)
    tmp = ESTADO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(feitos, f)
    os.replace(tmp, ESTADO)  # atômico: kill no meio do write não trunca o estado


def diagnostico(nome, info, qual):
    """A 'conferida' do tripwire, automática: se o S discrepa do Elo MAS a captura
    passa nos checks (n de casas, dispersão, overround), é discordância genuína
    Elo x mercado -> disposição MANTIDO, sem ⚠ no assunto. ⚠ só quando a própria
    captura está estranha — que é o caso que pede olho humano."""
    ok_trip, msg_trip = tripwire(nome, info["lt"], info["s"], info["p_emp"])
    cap_ok, checks = captura_ok(qual)
    if not ok_trip:
        msg_trip += ("\n  -> captura AUTO-VERIFICADA (casas/dispersão/overround ok): "
                     "discordância genuína Elo x mercado; o mercado manda — MANTIDO."
                     if cap_ok else
                     "\n  -> e a captura TAMBÉM falhou na verificação: conferir antes de travar!")
    if not cap_ok:
        ruins = [k for k, v in checks.items() if not v]
        msg_trip += f"\n⚠ captura suspeita (falhou: {', '.join(ruins)})"
    suspeito = (not cap_ok) or (not info["lt_ok"])
    return suspeito, ok_trip, msg_trip


def processar_jogo(dt, nome, url, enviar=True):
    """Captura+motor+política+tripwire+e-mail. Devolve 'PHxPA' p/ guardar no estado."""
    odds, disp, qual = capturar(url)
    fase, flags, avisos = contexto(dt)
    relatorio, info = analisar(odds, fase=fase, nflags=flags)
    suspeito, ok_trip, msg_trip = diagnostico(nome, info, qual)
    corpo = montar(dt, nome, odds, disp, relatorio, info, avisos, msg_trip)
    ph, pa = info["palpite"]
    ko = "  [⚠ MATA-MATA 120' — NÃO travar sem conferir]" if fase >= 2 else ""
    assunto = (f"⚽ Palpite: {nome} → {ph}x{pa}{ko}"
               + ("  [⚠ CONFERIR captura]" if suspeito else ""))
    if enviar:
        enviar_email(assunto, corpo)
        logar(f"enviado: {nome} → {ph}x{pa} | {info['regra']} | "
              f"tripwire {'ok' if ok_trip else 'DISPAROU+mantido'} | suspeito={suspeito}")
    else:
        print(assunto + "\n\n" + corpo)
    return f"{ph}x{pa}"


def rechecar(dt, nome, url, antigo):
    """2ª passada (~T-20): recaptura e SÓ manda e-mail se o palpite MUDOU (lesão no
    aquecimento, linha que andou). Cobre a 'lista 2' da POLITICA sem inundar a caixa."""
    odds, disp, qual = capturar(url)
    fase, flags, avisos = contexto(dt)
    relatorio, info = analisar(odds, fase=fase, nflags=flags)
    ph, pa = info["palpite"]
    novo = f"{ph}x{pa}"
    if novo != antigo:
        suspeito, ok_trip, msg_trip = diagnostico(nome, info, qual)
        corpo = (("⚠ CAPTURA SUSPEITA nesta recheck — se não conferir as odds abaixo, "
                  f"MANTENHA o palpite anterior ({antigo}).\n\n" if suspeito else
                  "RECHECAGEM (~T-20): a linha andou e o palpite MUDOU — use ESTE.\n\n")
                 + montar(dt, nome, odds, disp, relatorio, info, avisos, msg_trip))
        ko = "  [MATA-MATA 120']" if fase >= 2 else ""
        enviar_email(f"⚠ MUDOU: {nome} → {novo} (era {antigo}){ko}"
                     + ("  [⚠ CONFERIR captura]" if suspeito else ""), corpo)
        logar(f"recheck: {nome} MUDOU {antigo} → {novo} | suspeito={suspeito}")
    else:
        logar(f"recheck: {nome} confirmado ({antigo})")
    return novo


def main():
    if "--teste" in sys.argv:
        enviar_email("⚽ Bolão: teste do palpite automático",
                     "Funcionou. Eu verifico os jogos perto do kickoff e mando o palpite "
                     "FINAL aqui (POLITICA aplicada por código).")
        logar("mensagem de teste enviada")
        return
    if "--simular" in sys.argv:
        i = sys.argv.index("--simular")
        t1, t2 = sys.argv[i + 1], sys.argv[i + 2]
        url = achar_jogo(t1, t2)
        dt = next((d for d, _, u in fixtures() if u == url), datetime.datetime.now())
        processar_jogo(dt, f"{t1} - {t2}", url, enviar=False)
        return
    try:
        jogos = fixtures()
    except (Exception, SystemExit) as e:
        logar(f"FALHA na varredura (sem cache): {type(e).__name__}: {e}")
        return
    agora = datetime.datetime.now()
    if "--digest" in sys.argv:
        de_hoje = [(dt, n) for dt, n, _ in jogos if dt.date() == agora.date()]
        corpo = "\n".join(f"{dt:%H:%M} (Brasília, estimado) — {n}" for dt, n in de_hoje) \
                or "Sem jogos hoje na listagem."
        enviar_email(f"⚽ Bolão: {len(de_hoje)} jogo(s) hoje", corpo)
        logar(f"digest enviado ({len(de_hoje)} jogos)")
        return
    feitos = carregar_estado()
    mexeu = False
    for dt, nome, url in jogos:
        mins = (dt - agora).total_seconds() / 60
        try:
            if url not in feitos and JANELA_MIN[0] <= mins <= JANELA_MIN[1]:
                palpite = processar_jogo(dt, nome, url)
                feitos[url] = {"palpite": palpite, "rechecado": False}
                salvar_estado(feitos)  # já: morrer no jogo seguinte não re-envia este
                mexeu = True
            elif (url in feitos and not feitos[url].get("rechecado")
                  and JANELA_RECHECK[0] <= mins <= JANELA_RECHECK[1]):
                feitos[url]["palpite"] = rechecar(dt, nome, url, feitos[url]["palpite"])
                feitos[url]["rechecado"] = True
                salvar_estado(feitos)
                mexeu = True
        except (Exception, SystemExit) as e:  # capturar usa SystemExit
            logar(f"FALHA {nome}: {type(e).__name__}: {e}")
            if url not in feitos:  # recheck que falha não vira spam: palpite já foi
                try:
                    enviar_email(f"⚠ Bolão: falha no palpite automático de {nome}",
                                 f"{type(e).__name__}: {e}\nCapturar manual: "
                                 f"python -m bolao.odds ... (RUNBOOK_JOGO.md)")
                except Exception:
                    pass
    if not mexeu:
        logar(f"varredura: nada na janela ({len(jogos)} jogos no calendário)")


if __name__ == "__main__":
    main()
