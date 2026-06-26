"""parse_render() tem que aguentar os DOIS layouts que o jina devolve (medido ao vivo
26/06): flat-com-bônus, flat-SEM-bônus (a célula de bônus some em vários jogos) e rich
(markdown com logo das casas). Fixtures reproduzem os três com as MESMAS cotas — então
as 5 medianas têm que sair idênticas nos três, independentemente do layout.

Cotas (5 casas): casa∈{1.95,2.00,2.05,2.10,2.20}→med 2.05; emp→3.25; fora→3.55;
under∈{1.48,1.50,1.52,1.55,1.60}→1.52; over→2.52. A seção Half Time / Under-Over 0.5
existe SÓ p/ testar o recorte (não pode vazar pras medianas)."""
import pytest
from bolao.odds import parse_render

# --- layout A: flat, cada cota numa linha, TODA linha com célula de bônus ---------
FLAT_COM_BONUS = """Full Time Result
BOOKMAKER
1
X
2
BONUS UP TO
2.00
3.20
3.50
€1000
2.10
3.30
3.60
$200
2.05
3.25
3.55
£150
1.95
3.15
3.45
€130
2.20
3.40
3.70
See the offer
Half Time Result
BOOKMAKER
1
X
2
BONUS UP TO
4.00
1.90
3.20
€100
4.10
1.95
3.25
$200
Under/Over 2.5 Goals
BOOKMAKER
-2.5
+2.5
BONUS UP TO
1.50
2.50
€1000
1.55
2.55
$200
1.52
2.52
£150
1.48
2.48
€130
1.60
2.60
See the offer
Under/Over 0.5 Goals
BOOKMAKER
-0.5
+0.5
BONUS UP TO
5.00
1.10
€100
"""

# --- layout A': flat SEM célula de bônus (croatia 26/06) — só um "See the offer" ---
FLAT_SEM_BONUS = """Full Time Result
BOOKMAKER
1
X
2
BONUS UP TO
2.00
3.20
3.50
2.10
3.30
3.60
2.05
3.25
3.55
See the offer
1.95
3.15
3.45
2.20
3.40
3.70
Half Time Result
BOOKMAKER
1
X
2
BONUS UP TO
4.00
1.90
3.20
4.10
1.95
3.25
Under/Over 2.5 Goals
BOOKMAKER
-2.5
+2.5
BONUS UP TO
1.50
2.50
1.55
2.55
1.52
2.52
See the offer
1.48
2.48
1.60
2.60
Under/Over 0.5 Goals
BOOKMAKER
-0.5
+0.5
BONUS UP TO
5.00
1.10
"""


# --- layout B: rich, markdown com logo das casas (colombia 26/06) -----------------
def _rich(book, *cotas):
    base = "https://static.sportytrader.com/icons/bookmakers"
    return (f"[![Image: {book}]({base}/30x30/{book}.webp)"
            f"![Image: {book}]({base}/100x45/{book}.webp) {' '.join(cotas)}]"
            f"(https://www.sportytrader.com/en/book/{book}/odds)")


RICH = (
    "Full Time Result\n\n Bookmaker 1 X 2 Bonus up to \n\n"
    + _rich("stake", "2.00", "3.20", "3.50")
    + _rich("1xbet", "2.10", "3.30", "3.60")
    + _rich("melbet", "2.05", "3.25", "3.55")
    + _rich("22bet", "1.95", "3.15", "3.45")
    + _rich("bet365", "2.20", "3.40", "3.70")
    + "\nHalf Time Result\n\n Bookmaker 1 X 2 Bonus up to \n\n"
    + _rich("stake", "4.00", "1.90", "3.20")
    + _rich("1xbet", "4.10", "1.95", "3.25")
    + "\nUnder/Over 2.5 Goals\n\n Bookmaker -2.5 +2.5 Bonus up to \n\n"
    + _rich("stake", "1.50", "2.50")
    + _rich("1xbet", "1.55", "2.55")
    + _rich("melbet", "1.52", "2.52")
    + _rich("22bet", "1.48", "2.48")
    + _rich("bet365", "1.60", "2.60")
    + "\nUnder/Over 0.5 Goals\n\n Bookmaker -0.5 +0.5 Bonus up to \n\n"
    + _rich("stake", "5.00", "1.10")
)


@pytest.mark.parametrize("render", [FLAT_COM_BONUS, FLAT_SEM_BONUS, RICH])
def test_medianas_identicas_nos_tres_layouts(render):
    odds, disp, qual = parse_render(render)
    assert odds["casa"] == pytest.approx(2.05)
    assert odds["empate"] == pytest.approx(3.25)
    assert odds["fora"] == pytest.approx(3.55)
    assert odds["under"] == pytest.approx(1.52)
    assert odds["over"] == pytest.approx(2.52)
    # 5 casas em cada mercado; Half Time / Under-Over 0.5 NÃO vazaram pra cá
    assert qual["n_1x2"] == 5
    assert qual["n_ou"] == 5


def test_secoes_ausentes_levanta():
    with pytest.raises(SystemExit):
        parse_render("página de erro sem odds nenhuma")


def test_poucas_casas_levanta():
    # só 2 casas no 1X2 (abaixo do piso de 3)
    ruim = ("Full Time Result\nBOOKMAKER\n1\nX\n2\nBONUS UP TO\n2.00\n3.20\n3.50\n"
            "2.10\n3.30\n3.60\nUnder/Over 2.5 Goals\nBOOKMAKER\n-2.5\n+2.5\n"
            "BONUS UP TO\n1.50\n2.50\n1.55\n2.55\n1.52\n2.52\nUnder/Over 0.5 Goals\n")
    with pytest.raises(SystemExit):
        parse_render(ruim)
