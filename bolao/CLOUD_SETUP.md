# Bolão na nuvem — GitHub Actions + Telegram (notebook pode estar desligado)

O motor roda na nuvem do GitHub a cada 15 min, captura odds, aplica a POLITICA e manda
o **palpite final no Telegram**. Zero token (Python puro). Você lê no celular e trava no
app. **Eu já deixei o repositório montado e commitado** na pasta `projetos\bolao-cloud\`
(SÓ o bolão — nada da Charles River). Você faz só o que depende das suas contas.

## ⚠️ NUNCA suba a pasta FirstProject pro GitHub
Ela tem material confidencial da firma (dashboard de fundos, API BTG, slides). Use a pasta
**`bolao-cloud`** que eu preparei — ela tem só o código do bolão, seguro pra publicar.

## 1. Criar o bot do Telegram (2 min)
1. No Telegram, fale com **@BotFather** → `/newbot` → dê um nome → ele te dá um **TOKEN**
   (ex.: `8123456789:AAH...`). Guarde.
2. Procure o seu bot pelo @username e mande "oi" pra ele.
3. Pegue o **chat_id** rodando (no venv, dentro de `bolao-cloud`):
   ```
   python -m bolao.tg_setup <SEU_TOKEN>
   ```
   Ele imprime `TELEGRAM_CHAT_ID = ...`. (Pronto, sem ler JSON na mão.)

## 2. Criar o repositório e dar push
1. No GitHub, **New repository** → nome à vontade → pode ser **Privado** (recomendado p/
   contexto de trabalho) ou Público. Crie VAZIO (sem README).
2. No terminal, dentro de `projetos\bolao-cloud` (já está com git init + commit feitos):
   ```
   git remote add origin https://github.com/<voce>/<repo>.git
   git push -u origin main
   ```
   (No 1º push o Git abre o login do GitHub no navegador — é só autorizar.)

> **Privado x Público:** privado é mais discreto, mas o free tem 2000 min/mês de Actions.
> Em */15 min isso pode estourar no fim do mês. Se for privado, troque no
> `.github/workflows/palpite.yml` o cron pra `*/30 * * * *` (cabe folgado). Público =
> ilimitado, deixa */15. O código não tem nada sensível (já tirei seu e-mail dele).

## 3. Cadastrar os segredos
Repo → **Settings → Secrets and variables → Actions → New repository secret**:
- `TELEGRAM_TOKEN` = o token do BotFather
- `TELEGRAM_CHAT_ID` = o número do passo 1.3

## 4. Permissão de escrita pra Action (dedup)
**Settings → Actions → General → Workflow permissions → "Read and write permissions"** → Save.

## 5. Testar
Aba **Actions** → habilite os workflows → **Bolao palpite** → **Run workflow** → no campo
`flag` escreva `--teste` → Run. Em ~1 min chega uma mensagem no Telegram. Chegou = no ar.

## Manutenção (rara)
- **Virar CACADOR** (gatilho do fim dos grupos, ~27/06): edite
  `bolao/dados/auto_config.json` → `{"estado": "CACADOR"}` → `git commit -am x; git push`.
- **Prova de vida**: o **digest** chega ~09:00 todo dia com os jogos. Não chegou = quebrou
  (veja a aba Actions; cada run verde = ok).
- **Fuso**: horários são estimados (OFFSET_HORAS=1). Palpite muito fora de ~T-40 → ajuste
  `OFFSET_HORAS` em `bolao/auto_palpite.py`.
- **Mata-mata (28/06+)**: grade ainda é 90' (Task 12) — e-mail de KO avisa pra conferir.

## O que continua HUMANO
Lesão/clima que o mercado ainda não viu, "jogo especial", e o **LOCK no app**. Só isso.
