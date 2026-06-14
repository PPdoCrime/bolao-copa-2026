# Fontes de odds — sondagem 2026-06-11

- **Pinnacle BR** -- https://www.pinnacle.bet.br/ -> OK http 200, 5 KB, url final: https://pinnacle.bet.br/
- **OddsAgora (espelho OddsPortal)** -- https://www.oddsagora.com.br/ -> OK http 200, 95 KB, url final: https://www.oddsagora.com.br/
- **BetExplorer BR** -- https://www.betexplorer.com/br/ -> OK http 200, 467 KB, url final: https://www.betexplorer.com/br/
- **football-data.co.uk** -- https://www.football-data.co.uk/data.php -> OK http 200, 51 KB, url final: https://www.football-data.co.uk/data.php
- **eloratings.net TSV** -- https://www.eloratings.net/World.tsv -> OK http 200, 29 KB, url final: https://www.eloratings.net/World.tsv

## Fonte primária do jogo a jogo

**Escolha: Pinnacle BR** — foi a 1ª na ordem de preferência e retornou HTTP 200 (5 KB, redirect para https://pinnacle.bet.br/).

### Como achar o jogo de abertura da Copa 2026 (11/06, México)

1. Acesse https://pinnacle.bet.br/
2. No menu de esportes, selecione "Futebol" → "Copa do Mundo 2026" (ou busca por "World Cup 2026").
3. Procure o jogo do dia 11/06: **México vs (adversário do Grupo A)** — jogo de abertura, Estádio Azteca, Cidade do México (MetLife/NY é a FINAL, não a abertura).
4. As odds aparecerão no formato europeu (decimal). Anote as **5 odds**: Over 2.5, Under 2.5, vitória México, empate, derrota México (na ordem das células Jogo!B2:B6).
5. Se a página da Copa não estiver disponível ainda (mercado fecha tarde), use como fallback:
   - OddsAgora: https://www.oddsagora.com.br/ — buscar "Copa do Mundo" → jogo de abertura
   - BetExplorer: https://www.betexplorer.com/br/ → Futebol → Copa do Mundo FIFA 2026

### Fallback total (se todos os sites bloquearem no dia)
Abrir manualmente no navegador qualquer casa de aposta acessível e registrar as odds Avg/médias do jogo de abertura diretamente.

## Tripwire Elo (S_elo)

Antes de travar o palpite, calcule o S_elo de conferência:

```
C:\Users\PedroRamalho\python_corporativo\venv\Scripts\python.exe -m bolao.elo_s <casa> <fora> <lambda_total>
```

- `<lambda_total>` = valor de Jogo!B13 após colar as odds. Times por nome comum ou código de 2 letras (MX, BR...). Consulta avulsa: `python -m bolao.elo_s Mexico`.
- Bônus de mando = 100 pts de Elo, automático; use `--neutro` quando NENHUM dos dois joga em casa (maioria dos jogos nos EUA/Canadá é neutra; México/EUA/Canadá jogando em casa NÃO é neutro — México no Azteca = mando).
- Cole o `S_elo` impresso em **Jogo!F5**. Q7 avisa se |S_mercado − S_elo| > 0,4 gol → conferir digitação das odds, NUNCA "ajustar na mão" (POLITICA.md).
- Ressalva conhecida: o We do Elo conta empate como meio acerto (≠ prob. de vitória pura), então o S_elo carrega viés pequeno — irrelevante pro propósito de tripwire com gatilho de 0,4.
- Ratings em `bolao/dados/elo_world.tsv` (snapshot 11/06). Pra atualizar durante a Copa: rebaixar o World.tsv (URL na sondagem acima).