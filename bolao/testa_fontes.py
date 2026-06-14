"""Sondagem das fontes de odds na rede corporativa. Roda uma vez, grava FONTES.md."""
import datetime
import pathlib
import sys
import io

try:  # proxy corporativo intercepta TLS; usar certificados do Windows (CA do proxy)
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import requests

_HERE = pathlib.Path(__file__).parent

# Force UTF-8 output on Windows consoles that default to cp1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FONTES = [
    ("Pinnacle BR",        "https://www.pinnacle.bet.br/"),
    ("OddsAgora (espelho OddsPortal)", "https://www.oddsagora.com.br/"),
    ("BetExplorer BR",     "https://www.betexplorer.com/br/"),
    ("football-data.co.uk", "https://www.football-data.co.uk/data.php"),
    ("eloratings.net TSV", "https://www.eloratings.net/World.tsv"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def sondar():
    dest = _HERE / "FONTES.md"
    if dest.exists() and "--force" not in sys.argv:
        print(f"AVISO: {dest} já existe e contém secção manual preenchida.")
        print("Use --force para sobrescrever. Abortando sem gravar.")
        return

    linhas = [f"# Fontes de odds — sondagem {datetime.date.today().isoformat()}", ""]
    for nome, url in FONTES:
        try:
            r = requests.get(url, headers=UA, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                status = f"OK http {r.status_code}, {len(r.content)//1024} KB, url final: {r.url}"
            else:
                status = f"AVISO http {r.status_code} (não utilizável), url final: {r.url}"
        except Exception as e:
            status = f"FALHOU: {type(e).__name__}: {e}"
        linhas.append(f"- **{nome}** -- {url} -> {status}")
    linhas += ["", "## Fonte primária do jogo a jogo", "(preencher à mão após inspecionar os resultados acima:",
               "1ª opção Pinnacle BR; senão OddsAgora; senão BetExplorer /br/.)"]
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print("\n".join(linhas))

if __name__ == "__main__":
    sondar()
