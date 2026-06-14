# Runbook por jogo (modo rápido ~10 min) — janela T-75 → T-15

## ⚙️ AUTOMÁTICO TOTAL (desde 12/06): tarefa "BolaoPalpite" roda a cada 20 min e envia
o PALPITE FINAL por e-mail a ~40 min do kickoff (bolao/auto_palpite.py). O robô aplica
o modelo INTEIRO: fase por data (grupos→27/06=1x; mata-mata=2x; final 19/07=3x), flag
de rodada 3 (24–27/06, achata a grade), tripwire de Elo (mando só MX/US/CA), estado de
ranking (dados/auto_config.json — EDITAR quando virar LIDER/CACADOR) e resolução de
FRONTEIRA pela POLITICA (divergir do aglomerado etc.). Você só: lê o e-mail → confere
os 2 itens humanos (lesão/clima pós-captura? jogo especial?) → TRAVA NO APP.
Requisitos: laptop LIGADO no horário + Outlook aberto/configurado. Sem e-mail a T-30 →
fluxo manual abaixo. Tripwire e captura se auto-verificam (n de casas, dispersão,
overround): assunto LIMPO = travar direto; assunto com [⚠ CONFERIR captura] = a captura
falhou nos checks → conferir as odds do corpo numa casa qualquer; se for recheck
suspeito, manter o palpite anterior. Gerenciar: `schtasks /Query /TN BolaoPalpite` |
log em dados/auto_palpite.log | testar: `python -m bolao.auto_palpite --simular
<time1> <time2>` (console, sem e-mail).

## Antes da rodada (1x por dia)
1. Modal do pelotão: AUTOMATIZADO — o Claude dispara 4-5 agentes frios com a pergunta
   de leigo na hora da decisão e conta o modal (validado no jogo 1: previu o aglomerado
   2x0/2x1 que deu 83% do grupo). Após cada lock, colar aqui a distribuição real do app
   → acumula no Log; quando o padrão "pelotão = placares óbvios de favorito" se confirmar
   em ~5 jogos, sampling só nos jogos parelhos.
2. Conferir estado de ranking no app do bolão → LIDER / PELOTAO / CACADOR.

## Por jogo
0. T-3h: captura-base (`python -m bolao.odds ...`) — se o site/jina cair na janela T-60,
   o palpite sai da base, não de improviso (red team 12/06).
1. T-75: escalações oficiais saem. Ver lineup (FlashScore/SofaScore). Anotar surpresas.
2. T-60→T-15: capturar odds + rodar o motor num comando (~10s, mediana SportyTrader):
   `python -m bolao.odds <time1> <time2> [--fase 2|3] [--flags N]`
   Sai: 5 odds, λs, célula modal (pelotão previsto), top-5 EV e a decisão.
   Fallback se o site/jina falhar: captura manual (bolao/FONTES.md) e colar na planilha.
3. Abrir bolao/Bolao_Copa2026.xlsx, aba Jogo: colar as 5 odds (B2:B6), fase (B7: 1
   grupo / 2 mata-mata / 3 final), flags (D2:D6), modal do pelotão (F2), estado (F3).
   Exceção de λ (B8/B9) SÓ se cair na lista fechada de POLITICA.md.
4. Tripwire: rodar `python -m bolao.elo_s <casa> <fora> <valor de B13>` (ver FONTES.md;
   `--neutro` se nenhum dos dois joga em casa) e colar o S_elo em F5. Se Q7 = "⚠ CONFERIR",
   reler as odds digitadas ANTES de qualquer coisa — a resposta é recapturar, nunca ajustar.
   A DISPOSIÇÃO do tripwire (ok / disparou+conferido+mantido / disparou+erro corrigido)
   entra OBRIGATORIAMENTE no racional do Log — sem registro, a regra vira enfeite.
   Pós-rodada: colar a distribuição do app no chat → validar o modelo do pelotão
   (argmax P da grade, POLITICA.md emenda 12/06) e registrar acerto/erro no Log.
5. Decisão (Q6): "OK: cravar o 1º" → palpite é R2. "FRONTEIRA" → aplicar POLITICA.md:
   LIDER cola no modal do pelotão; PELOTAO/CACADOR divergem do modal entre R2..R4;
   empate residual: maior P_exato (col L), depois menor P_invertido (col M).
6. Travar o palpite no app do bolão. Preencher a linha do Log (inclusive racional em
   1 frase). NÃO revisitar depois do kickoff.

## Jogo de abertura (11/06, HOJE) — checklist pré-preenchido
- Sede: Estádio Azteca, Cidade do México. México tem MANDO (não usar --neutro no elo_s).
- Flags: estreia=1 (pressão de abertura em casa). Altitude/clima do Azteca JÁ ESTÃO
  precificados na linha — flag clima só se evento súbito (tempestade no aquecimento).
- NÃO mover λ na mão: estreia NÃO está na lista fechada de exceções (POLITICA.md).
- Fase de grupos → B7=1, e default é VENDER variância (colher 5/6, não tomar -2).
- Lembrete do dry-run: odds parecidas com 1.95/3.40/4.20 dão FRONTEIRA entre 1x0 e 2x0
  — nesse caso o desempate é divergir do modal do pelotão (estado PELOTAO, todos zerados
  = início de Copa, vale ousadia controlada: escolher o placar do top-3 FORA do modal).

## Higiene operacional
- A planilha é regenerável (`python -m bolao.build_planilha`) mas isso APAGA Jogo+Log —
  copiar o Log antes, se houver histórico.
- Rodada 3 dos grupos (24–27/06, kickoffs simultâneos): triagem na véspera conforme
  POLITICA.md — até 2 jogos com tratamento T-60 (risco de rotação), resto trava a T-3h.
