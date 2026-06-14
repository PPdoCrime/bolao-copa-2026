

# Backtest θ/ρ/δ — run 2026-06-11 14:16:52



# Backtest θ/ρ/δ — run 2026-06-11 14:18:01



# Backtest θ/ρ/δ — run 2026-06-11 14:20:33

pulei 1920/E0 (http 403)
pulei 1920/E1 (http 403)
pulei 1920/E2 (http 403)
pulei 1920/E3 (http 403)
pulei 1920/EC (http 403)
pulei 1920/SC0 (http 403)
pulei 1920/SC1 (http 403)
pulei 1920/SC2 (http 403)
pulei 1920/SC3 (http 403)
pulei 1920/D1 (http 403)
pulei 1920/D2 (http 403)
pulei 1920/I1 (http 403)
pulei 1920/I2 (http 403)
pulei 1920/SP1 (http 403)
pulei 1920/SP2 (http 403)
pulei 1920/F1 (http 403)
pulei 1920/F2 (http 403)
pulei 1920/N1 (http 403)
pulei 1920/B1 (http 403)
pulei 1920/P1 (http 403)
pulei 1920/T1 (http 403)
pulei 1920/G1 (http 403)

## BLOQUEADO 11/06/2026 ~15h (rede corporativa)
Downloads de CSV do football-data.co.uk retornam 403 'Blocked site' (filtro corporativo; de manha funcionava).
Rodar de casa/hotspot: python -m bolao.backtest (resumivel: cache em bolao/dados/, report incremental aqui).
Ate la valem os defaults ja na planilha: theta=0, rho=1.10, delta=0.3.
Regra de adocao: so substituir defaults se ev_tunado >= ev_default na validacao de selecoes.


# Backtest θ/ρ/δ — run 2026-06-11 23:11:33

temporada 1920: 6891 jogos baixados; extraindo λ...
  ... 5000/6891 jogos extraídos
temporada 1920: 6891 jogos com λ extraído (parcial salvo)
temporada 2021: 7628 jogos baixados; extraindo λ...
  ... 5000/7628 jogos extraídos
temporada 2021: 7628 jogos com λ extraído (parcial salvo)
temporada 2122: 7817 jogos baixados; extraindo λ...
  ... 5000/7817 jogos extraídos
temporada 2122: 7817 jogos com λ extraído (parcial salvo)
temporada 2223: 7785 jogos baixados; extraindo λ...
  ... 5000/7785 jogos extraídos
temporada 2223: 7785 jogos com λ extraído (parcial salvo)
temporada 2324: 7766 jogos baixados; extraindo λ...
  ... 5000/7766 jogos extraídos
temporada 2324: 7766 jogos com λ extraído (parcial salvo)
temporada 2425: 7665 jogos baixados; extraindo λ...


# Backtest θ/ρ/δ — run 2026-06-11 23:16:23

temporada 1920: parcial em cache, 6891 jogos com λ
temporada 2021: parcial em cache, 7628 jogos com λ
temporada 2122: parcial em cache, 7817 jogos com λ
temporada 2223: parcial em cache, 7785 jogos com λ
temporada 2324: parcial em cache, 7766 jogos com λ
temporada 2425: 7663 jogos baixados; extraindo λ...
  ... 5000/7663 jogos extraídos
temporada 2425: 7663 jogos com λ extraído (parcial salvo)
base de treino: 45550 jogos com λ (cache salvo em C:\Users\PedroRamalho\python_corporativo\projetos\FirstProject\bolao\dados\_lambdas_cache.csv)

== Grade de pontos por (θ, ρ) na base de treino ==
grade computada: 99 combinações θxρ sobre 45550 jogos

== CV por temporada (estabilidade) ==
fold 1920: θ*=-0.05 ρ*=1.2 pts/jogo fora=3.1979
fold 2021: θ*=-0.05 ρ*=1.2 pts/jogo fora=3.2575
fold 2122: θ*=-0.1 ρ*=1.02 pts/jogo fora=3.2908
fold 2223: θ*=-0.05 ρ*=1.18 pts/jogo fora=3.3344
fold 2324: θ*=-0.05 ρ*=1.18 pts/jogo fora=3.3003
fold 2425: θ*=-0.05 ρ*=1.18 pts/jogo fora=3.3063

== Tuning final em toda a base ==
θ*=-0.05 ρ*=1.18 pts/jogo treino=3.2921

== Curva de delta (banda de indiferença) ==
δ=0.05: 26200 jogos na banda, perda real média de trocar p/ 2º = +0.0336
δ=0.1: 40634 jogos na banda, perda real média de trocar p/ 2º = +0.0510
δ=0.15: 45083 jogos na banda, perda real média de trocar p/ 2º = +0.0527
δ=0.2: 45474 jogos na banda, perda real média de trocar p/ 2º = +0.0531
δ=0.25: 45514 jogos na banda, perda real média de trocar p/ 2º = +0.0529
δ=0.3: 45539 jogos na banda, perda real média de trocar p/ 2º = +0.0526
δ=0.35: 45542 jogos na banda, perda real média de trocar p/ 2º = +0.0527
δ=0.4: 45545 jogos na banda, perda real média de trocar p/ 2º = +0.0524
δ=0.45: 45547 jogos na banda, perda real média de trocar p/ 2º = +0.0524
δ=0.5: 45550 jogos na banda, perda real média de trocar p/ 2º = +0.0526
δ=0.55: 45550 jogos na banda, perda real média de trocar p/ 2º = +0.0526
δ=0.6: 45550 jogos na banda, perda real média de trocar p/ 2º = +0.0526
δ* sugerido (maior δ com |perda| < 0.05): 0.05

== VALIDAÇÃO FINAL (seleções, uma única vez) ==
baixando https://www.football-data.co.uk/WorldCup2026.xlsx ...
abas no xlsx: ['WorldCup2026Qualifiers', 'WorldCup2022', 'WorldCup2018', 'WorldCup2014']
aba WorldCup2026Qualifiers: odds=('H_Avg', 'D_Avg', 'A_Avg') gols=('HG', 'AG') → 888 jogos
aba WorldCup2022: odds=('H-Avg', 'D-Avg', 'A-Avg') gols=('HGFT', 'AGFT') → 64 jogos
aba WorldCup2018: odds=('Pinny-H', 'Pinny-D', 'Pinny-A') gols=('HGFT', 'AGFT') → 64 jogos
aba WorldCup2014: odds=('Pinny-H', 'Pinny-D', 'Pinny-A') gols=('HGFT', 'AGFT') → 64 jogos
validação seleções: 727 jogos (353 pulados por odds extremas)
modal: 3.5763 pts/jogo | vs modal: dif média 0.0000 IC95 [0.0000, 0.0000]
ev_default: 3.4704 pts/jogo | vs modal: dif média -0.1059 IC95 [-0.2559, 0.0372]
ev_tunado: 3.4924 pts/jogo | vs modal: dif média -0.0839 IC95 [-0.2710, 0.1032]

== RECOMENDAÇÃO (não aplicada — regra de decisão) ==
ev_tunado (3.4924) >= ev_default (3.4704) nas seleções: RECOMENDO atualizar Config para B2=θ*=-0.05, B3=ρ*=1.18, B4=δ*=0.05 e re-rodar valida_planilha.

runtime total: 0:00:20.038817
cache de λ encontrado (C:\Users\PedroRamalho\python_corporativo\projetos\FirstProject\bolao\dados\_lambdas_cache.csv): 45550 jogos — pulando download e extração
cache de λ encontrado (C:\Users\PedroRamalho\python_corporativo\projetos\FirstProject\bolao\dados\_lambdas_cache.csv): 45550 jogos — pulando download e extração
