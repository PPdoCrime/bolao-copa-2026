# Política de variância — congelada em 10/06/2026 (véspera da abertura)

Mudança de parâmetro durante a Copa SÓ por gatilho pré-definido (bug comprovado no motor
ou na rubrica). "Rodada ruim" NUNCA é gatilho. Log é post-mortem, não insumo de ajuste.

## Estado de ranking (consultar ANTES de cada palpite)

| Estado | Definição | Regra |
|---|---|---|
| LÍDER | 1º no ranking do grupo | Espelhar o palpite modal do pelotão (vender variância), SALVO quando o motor dá diferencial claramente positivo sem risco de invertido relevante |
| PELOTÃO | até ~30 pts do 1º | Padrão: palpite ótimo por EV; em fronteira (margem ≤ δ), desempatar DIVERGINDO do modal do pelotão |
| CAÇADOR | > ~30 pts atrás | Comprar variância: placar plausível-não-modal onde o pelotão não está, priorizando jogos com multiplicador (mata-mata) |

- Default da fase de grupos: VENDER variância (colher 5/6, não tomar -2).
- EV diferencial: desempate nos grupos; objetivo pleno no mata-mata SE estivermos atrás.
- Endgame de líder: a partir das quartas, liderança ≥ 40 pts → espelhar o palpite modal
  do 2º colocado (cobertura, match racing). Abaixo de 40 → política padrão.
- **Gatilho de virada p/ CAÇADOR (pré-comprometido 14/06, decisão do dono = disciplina agora):**
  não comprar variância no início só por rodada ruim. Reavaliar no FIM DA FASE DE GRUPOS
  (~27/06): se ainda no terço de baixo OU > ~20 pts do 1º → flipar auto_config.json p/
  CACADOR (caçar placar exato/10s, divergir forte), aproveitando os multiplicadores 2x/3x
  do mata-mata. Se dentro de ~1 vitória de jogo do pelotão de cima → seguir PELOTAO.
  Racional: só o 1º lugar importa (meio = último), então variância -EV é quase de graça
  QUANDO atrás e perto do fim; cedo, o edge por jogo compõe e a sorte do líder reverte.

## Desempate em fronteira (margem ≤ δ)
1. Aplicar a regra do estado de ranking (acima) contra o modal do pelotão.
2. Empate residual: maior P(exato); depois menor P(invertido) — espelha o desempate
   do ranking do bolão (1º mais completos, 2º menos invertidos).

### Emendas 12/06/2026-b (gatilho: red team externo — 2 bugs de motor + 3 erros de protocolo de calibração comprovados)
- **Bug corrigido (grade.decisao):** a fronteira agora compara margem/multiplicador ≤ δ —
  antes, o multiplicador 2x/3x ENCOLHIA a banda diferencial no mata-mata (gradiente oposto
  ao desta política). Teste de regressão adicionado.
- **Bug corrigido (odds.py):** clamps de favorito extremo (iguais ao treino) — sem eles,
  um Espanha x Haiti crashava a captura na janela T-60.
- **Parâmetros corrigidos: θ=0, ρ=1,10, δ=0,05.** Motivo (protocolo, não rodada ruim):
  θ=-0,05 foi calibrado em fechamento Pinnacle e empilha na MESMA direção do viés do devig
  proporcional sobre casas soft (instrumento de produção ≠ laboratório); ρ=1,18 não tem
  suporte fora de clubes (validação de seleções usa pipeline que conta empate 2x — inválida);
  tunado vs default era ruído (+0,022 com IC ±0,19, CV com ótimos na borda da grade).
- **Divergir do AGLOMERADO, não do argmax:** célula com share estimado ≥15% do pelotão
  conta como povoada (jogo 1 teve DUAS: 2x0=55% e 2x1=28%); se o candidato a divergência
  cair dentro do aglomerado, cravar o 1º por EV. Validar "argmax≈modal do pelotão" contra
  as distribuições reais do app por ≥5 jogos antes de confiar.
- **Jogos extremos (p_casa > 0,90):** cravar o 1º por EV sem divergência — é o estrato
  censurado de toda validação; não há evidência que pague divergir ali.
- **Gatilhos de emenda formalizados (lista fechada):** (i) bug comprovado no motor/rubrica;
  (ii) erro de protocolo de calibração comprovado; (iii) modelo de oponente falsificado por
  ≥2 distribuições reais do app; (iv) fonte de odds quebrada. "Rodada ruim" segue NÃO sendo.

### Emendas 12/06/2026-c (gatilho: automação total — esta política agora roda EM CÓDIGO, grade.escolher_palpite)
- **Resolução de fronteira codificada** (testes em tests/test_grade.py): sem fronteira →
  1º por EV; fronteira+LIDER → colar no modal da grade; fronteira+PELOTAO → melhor EV da
  banda (EV1−EV ≤ δ em unidades 1x) FORA do aglomerado; banda toda no aglomerado ou jogo
  extremo (max(p_casa,p_fora)>0,90) → 1º por EV; empate residual: maior P(exato), menor
  P(invertido).
- **Aglomerado operacional (emenda 12/06-e, gatilho iii com 3 distribuições reais):
  célula MODAL da grade + 2x1 DO FAVORITO** (1x2 se o favorito é o visitante). Evidência:
  células ≥15% reais foram {modal, 2x1-fav} no jogo 1 (2x0=55, 2x1=28) e jogo 3
  (1x0=27,6, 2x1=20,7); jogo 2 só o modal (1x1=48; 2x1=13,8 no limiar). A regra anterior
  (top-2 por P) previu {1x0,1x1} no jogo 3 e errou o 2º real (2x1). Modelo do pelotão
  (modal = argmax da grade): 3/3 acertos (55%, 48%, 27,6%) — VALIDADO; pelotão dispersa
  mais quanto mais parelho o jogo. Seguir conferindo a cada rodada.
- **CAÇADOR no automático = banda 2δ** (compra variância de forma pré-comprometida);
  divergência mais agressiva que isso é decisão manual.
- **Estado de ranking**: dados/auto_config.json (editar quando o ranking mudar; default
  PELOTAO). Tripwire de Elo roda automático (mando +100 só p/ MX/US/CA; resto neutro);
  disparo → conferir as odds no e-mail, NUNCA ajustar na mão.
- **Bug corrigido (tripwire, gatilho i):** We do Elo é score esperado (empate=1/2), não
  P(vitória); usar We direto inflava S_elo de favoritos → alarme falso crônico. Conversão
  p_win = We − p_emp/2. Jogos de anfitrião ainda podem disparar (Elo ama MX/US/CA com
  +100): disposição = conferir n de casas e range no e-mail; ok → mantido, registrar.
- **Rechecagem ~T-20 automática**: recaptura e só avisa se o palpite MUDOU — cobre a
  lista 2 (evento material pós-captura) na parte refletida pela linha; lesão que o
  mercado ainda não viu segue humana.
- **Disposição do tripwire automatizada (12/06-d)**: a "conferida" virou código
  (odds.captura_ok: n≥5 casas por mercado, dispersão ≤0,5, overround 1,005-1,18).
  Tripwire dispara + captura verificada = discordância Elo×mercado → MANTIDO no corpo,
  sem ⚠ no assunto. ⚠ [CONFERIR captura] no assunto só quando a PRÓPRIA captura falha
  nos checks (aí sim: conferir odds manualmente; em recheck suspeita, manter o anterior).

### Emendas 12/06/2026 (gatilho: contradição de regra + prior falsificado — post-mortem jogos 1-2)
- **Modal do pelotão (definição operacional):** sem dado ao vivo (app só mostra pós-lock),
  modal = célula de MAIOR PROBABILIDADE da nossa grade. Validado: jogo 1 (2x0 modal
  público ✓ 55%) e jogo 2 (1x1 célula modal da grade ✓ 48%). O pelotão é "apostador de
  placar mais provável". Sampling de IA externa: descontinuado.
- **Jogo parelho (|S| < 0,3):** risco de invertido é simétrico entre os candidatos e NÃO
  serve de desempate; vale só divergência do aglomerado + maior P(exato).

## Lista FECHADA de exceções que podem mover λ (teto ±10% por lado; tudo fora daqui NÃO move média — no máximo liga flag e achata a grade)
1. Escalação oficial confirma time reserva/misto em dead rubber E a linha capturada
   ainda não reagiu (captura anterior ao anúncio).
2. Evento material APÓS a captura da linha e ANTES do lock (lesão no aquecimento,
   expulsão pré-jogo, clima súbito severo) sem tempo de recapturar.
3. Tripwire de Elo disparou (>0,4 gol) e a inspeção confirma erro de LEITURA nosso →
   corrigir o input e recapturar. (Erro de leitura não é exceção de λ — está aqui para
   deixar explícito que a resposta é RECAPTURAR, nunca "ajustar na mão".)

## Rodada 3 da fase de grupos (kickoffs simultâneos, 24–27/06)
Triagem na véspera: jogos com risco real de rotação (classificados/eliminados) recebem
tratamento T-60 (no máximo 2 por janela); os demais travam a T-3h com captura única.
