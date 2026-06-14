"""Tripwire de Elo: converte ratings do eloratings.net em S_elo pra colar em Jogo!F5.

uso: python -m bolao.elo_s <time_casa> <time_fora> <lambda_total> [--neutro]
     python -m bolao.elo_s <time>                 (só consulta o rating)

Times: aceita código de 2 letras do eloratings.net (MX, BR, AR...) ou nome comum
(Mexico, Brasil, Argentina...). Bônus de mando = 100 pts de Elo; use --neutro em
jogo de campo neutro (México no Azteca = mando, NÃO neutro).
"""
import pathlib
import sys

from bolao.lambdas import supremacia_de_1x2

_TSV = pathlib.Path(__file__).parent / "dados" / "elo_world.tsv"

# nomes comuns -> código eloratings.net (lista focada em prováveis seleções da Copa)
NOMES = {
    "mexico": "MX", "méxico": "MX", "brasil": "BR", "brazil": "BR",
    "argentina": "AR", "espanha": "ES", "spain": "ES", "franca": "FR",
    "frança": "FR", "france": "FR", "inglaterra": "EN", "england": "EN",
    "portugal": "PT", "alemanha": "DE", "germany": "DE", "holanda": "NL",
    "netherlands": "NL", "italia": "IT", "itália": "IT", "italy": "IT",
    "belgica": "BE", "bélgica": "BE", "belgium": "BE", "croacia": "HR",
    "croácia": "HR", "croatia": "HR", "uruguai": "UY", "uruguay": "UY",
    "colombia": "CO", "colômbia": "CO", "equador": "EC", "ecuador": "EC",
    "eua": "US", "usa": "US", "estados unidos": "US", "canada": "CA",
    "canadá": "CA", "japao": "JP", "japão": "JP", "japan": "JP",
    "coreia": "KR", "korea": "KR", "marrocos": "MA", "morocco": "MA",
    "senegal": "SN", "gana": "GH", "ghana": "GH", "suica": "CH",
    "suíça": "CH", "switzerland": "CH", "austria": "AT", "áustria": "AT",
    "dinamarca": "DK", "denmark": "DK", "noruega": "NO", "norway": "NO",
    "australia": "AU", "austrália": "AU", "ira": "IR", "irã": "IR", "iran": "IR",
    "arabia saudita": "SA", "saudi": "SA", "catar": "QA", "qatar": "QA",
    "polonia": "PL", "polônia": "PL", "poland": "PL", "escocia": "SQ",
    "escócia": "SQ", "scotland": "SQ", "tunisia": "TN", "tunísia": "TN",
    "egito": "EG", "egypt": "EG", "argelia": "DZ", "argélia": "DZ", "algeria": "DZ",
    "costa do marfim": "CI", "ivory coast": "CI", "nigeria": "NG", "nigéria": "NG",
    "paraguai": "PY", "paraguay": "PY", "panama": "PA", "panamá": "PA",
    "costa rica": "CR", "honduras": "HN", "jamaica": "JM", "haiti": "HT",
    "nova zelandia": "NZ", "nova zelândia": "NZ", "new zealand": "NZ",
    "uzbequistao": "UZ", "uzbequistão": "UZ", "uzbekistan": "UZ",
    "jordania": "JO", "jordânia": "JO", "jordan": "JO", "cabo verde": "CV",
    "africa do sul": "ZA", "south africa": "ZA", "curacao": "CW", "curaçao": "CW",
    "tcheca": "CZ", "tchequia": "CZ", "republica tcheca": "CZ", "czech republic": "CZ",
    "czechia": "CZ", "south korea": "KR", "coreia do sul": "KR", "united states": "US",
    "cape verde": "CV", "saudi arabia": "SA", "arabia": "SA", "bosnia": "BA",
    "bosnia and herzegovina": "BA", "turquia": "TR", "turkey": "TR", "turkiye": "TR",
    "ukraine": "UA", "ucrania": "UA", "wales": "WA", "gales": "WA",
    "bosnia herzegovina": "BA", "cote d'ivoire": "CI", "côte d'ivoire": "CI",
    "sweden": "SE", "suecia": "SE", "suécia": "SE", "korea republic": "KR",
    "cape verde isl.": "CV", "cape verde isl": "CV", "dr congo": "CD",
    "rd congo": "CD", "iraq": "IQ", "iraque": "IQ",
}


def carregar():
    ratings = {}
    for linha in _TSV.read_text(encoding="utf-8").splitlines():
        campos = linha.split("\t")
        if len(campos) > 3 and campos[2].strip():
            try:
                ratings[campos[2].strip().upper()] = int(campos[3])
            except ValueError:
                continue
    return ratings


def resolver(nome, ratings):
    chave = nome.strip().lower()
    codigo = NOMES.get(chave, nome.strip().upper())
    if codigo in ratings:
        return codigo, ratings[codigo]
    candidatos = [c for c in ratings if chave.upper() in c]
    raise SystemExit(f"time '{nome}' não encontrado. Use código de 2 letras do "
                     f"eloratings.net. Parecidos: {candidatos[:10] or 'nenhum'}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if a != "--neutro"]
    neutro = "--neutro" in sys.argv
    ratings = carregar()
    if len(args) == 1:
        codigo, r = resolver(args[0], ratings)
        print(f"{codigo}: Elo {r}")
        return
    if len(args) != 3:
        print(__doc__)
        raise SystemExit(1)
    casa, fora, lam_total = args[0], args[1], float(args[2])
    cod_c, elo_c = resolver(casa, ratings)
    cod_f, elo_f = resolver(fora, ratings)
    bonus = 0 if neutro else 100
    dr = elo_c + bonus - elo_f
    we = 1 / (10 ** (-dr / 400) + 1)
    we = min(max(we, 0.03), 0.96)
    try:
        s_elo = supremacia_de_1x2(lam_total, we)
    except ValueError:
        print(f"{cod_c} (Elo {elo_c}) x {cod_f} (Elo {elo_f}): favorito extremo — "
              "tripwire não aplicável, deixe Jogo!F5 vazio.")
        return
    print(f"{cod_c} (Elo {elo_c}, mando +{bonus}) x {cod_f} (Elo {elo_f}) | "
          f"We={we:.3f} | λT={lam_total}")
    print(f"S_elo = {s_elo:.2f}  ->  Cole em Jogo!F5")


if __name__ == "__main__":
    main()
