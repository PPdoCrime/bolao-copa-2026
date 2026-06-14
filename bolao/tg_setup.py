"""Pega seu chat_id do Telegram (pra cadastrar no secret TELEGRAM_CHAT_ID).

Passo: no Telegram, mande qualquer mensagem (ex.: "oi") pro seu bot. Depois rode:
    python -m bolao.tg_setup <TELEGRAM_TOKEN>
e ele imprime o chat_id. (Sem precisar ler JSON na mão.)"""
import sys

import requests


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    tok = sys.argv[1].strip()
    r = requests.get(f"https://api.telegram.org/bot{tok}/getUpdates", timeout=30)
    data = r.json()
    if not data.get("ok"):
        print(f"Token recusado pelo Telegram: {data}")
        raise SystemExit(1)
    achados = {}
    for upd in data.get("result", []):
        msg = upd.get("message") or upd.get("channel_post")
        if msg and "chat" in msg:
            c = msg["chat"]
            achados[c["id"]] = c.get("first_name") or c.get("title") or c.get("username", "")
    if not achados:
        print("Nenhuma mensagem vista ainda. Mande 'oi' pro seu bot no Telegram e rode de novo.")
        return
    for cid, nome in achados.items():
        print(f"TELEGRAM_CHAT_ID = {cid}   ({nome})")


if __name__ == "__main__":
    main()
