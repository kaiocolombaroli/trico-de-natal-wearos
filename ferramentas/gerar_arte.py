# -*- coding: utf-8 -*-
"""Gera toda a arte do mostrador "Tricô de Natal" (PNGs + prévias).

Uso:  python ferramentas/gerar_arte.py
Determinístico: sementes fixas. Requer Pillow e numpy.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageFilter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "watchface", "src", "main", "res", "drawable-nodpi")
PREVIA = os.path.join(RAIZ, "previa")

SS = 4          # supersampling
TELA = 450
CEL = 7         # célula do tecido
ORIGEM = 1      # deslocamento do tecido
GRADE = 64

# ---------------------------------------------------------------- paleta (lã)
def hexa(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


AZUL = hexa("1f4d63")
BRANCO = hexa("e9ece8")
VERMELHO = hexa("c8202b")
VERDE = hexa("2a9a3c")
VERDE_ESC = hexa("1d7a2e")
MARROM = hexa("6b3d22")
OURO = hexa("e8b33a")
PELE = hexa("f0b9a0")
FUNDO_LACO = tuple(int(c * 0.45) for c in AZUL)

LEGENDA = {
    "W": BRANCO, "R": VERMELHO, "G": VERDE, "D": VERDE_ESC, "B": MARROM,
    "Y": OURO, "S": PELE, "n": AZUL,
}

# ------------------------------------------------------- renderizador de ponto
_cache_tiles = {}


def _tile(rgb, s, variante):
    """Ponto de tricô em "V" (duas pernas), renderizado em SS x. Devolve (RGBA, padx, pady)."""
    chave = (rgb, s, variante)
    if chave in _cache_tiles:
        return _cache_tiles[chave]
    S = s * SS
    padx = max(2, S // 5)
    pady = max(3, S // 4)
    W, H = S + 2 * padx, S + 2 * pady
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    jit = (0.96, 1.0, 1.04)[variante]
    out = np.zeros((H, W, 4), dtype=np.float64)
    cy = pady + S / 2.0
    ang = math.radians(27)
    a, b = 0.26 * S, 0.60 * S
    for fx, sinal in ((0.28, +1), (0.72, -1)):  # esquerda "\", direita "/"
        cx = padx + fx * S
        dx, dy = xx - cx, yy - cy
        sn, cs = sinal * math.sin(ang), math.cos(ang)
        along = dx * sn + dy * cs
        across = dx * cs - dy * sn
        d = np.sqrt((across / a) ** 2 + (along / b) ** 2)
        dentro = d <= 1.0
        luz = 1.0 - d
        fator = (0.55 + 0.6 * luz) * jit
        for k in range(3):
            canal = np.clip(rgb[k] * fator, 0, 255)
            out[..., k][dentro] = canal[dentro]
        out[..., 3][dentro] = 255
    img = Image.fromarray(out.astype(np.uint8), "RGBA")
    _cache_tiles[chave] = (img, padx, pady)
    return _cache_tiles[chave]


def _tela_ss(larg, alt, margem, fundo):
    return Image.new("RGBA", ((larg + 2 * margem) * SS, (alt + 2 * margem) * SS), fundo)


def render_pontos(larg, alt, s, origem, pontos, fundo_gap=None, rng=None):
    """pontos: lista de (col, linha, rgb). Devolve RGBA larg x alt (já reduzida)."""
    margem = 8
    fundo = (fundo_gap + (255,)) if fundo_gap else (0, 0, 0, 0)
    tela = _tela_ss(larg, alt, margem, fundo)
    rng = rng or random.Random(1)
    for (c, r, rgb) in pontos:
        tile, px, py = _tile(rgb, s, rng.randrange(3))
        x = (margem + origem + s * c) * SS - px
        y = (margem + origem + s * r) * SS - py
        tela.alpha_composite(tile, (x, y))
    tela = tela.crop((margem * SS, margem * SS, (margem + larg) * SS, (margem + alt) * SS))
    return tela.resize((larg, alt), Image.LANCZOS)


# --------------------------------------------------------------------- sprites
ARVORE = [
    "....G....",
    "...GGG...",
    "..GGGGG..",
    "...GGG...",
    "..GGGGG..",
    ".GGGGGGG.",
    "..GGGGG..",
    ".GGGGGGG.",
    "GGGGGGGGG",
    "....B....",
]

# rena virada para a esquerda, em salto (13 x 11)
RENA = [
    "W...W...W....",
    ".W.W.W.W.....",
    "..W..W.......",
    "..WW.W.......",
    ".WWWW........",
    "WnWWWWWWWWW.W",
    ".WWWWWWWWWWWW",
    "..WWWWWWWWWW.",
    ".WW.WW...WW..",
    "WW..W.....WW.",
    "W..........WW",
]

# trenó com o Papai Noel (18 x 11)
TRENO = [
    "...............WW.",
    "..............RRRW",
    "............RRRRR.",
    "...........WWWWWW.",
    "...........SnSSS..",
    "...GG......WWWWW..",
    "..GGGG....WRRRRRRR",
    "Y..GGRRRRRRRRRRRRR",
    "YYRRRRRRRRRRRRRRRR",
    ".YYYYYYYYYYYYYYYY.",
    "..WWWWWWWWWWWWWW..",
]


def sprite_para_grade(grade, ocupado, linhas, col, lin, trocas=None, marcar=True):
    for j, linha in enumerate(linhas):
        for i, ch in enumerate(linha):
            if ch == ".":
                continue
            if trocas and (j, i) in trocas:
                ch = trocas[(j, i)]
            r, c = lin + j, col + i
            if 0 <= r < GRADE and 0 <= c < GRADE:
                grade[r][c] = LEGENDA[ch]
                if marcar:
                    ocupado[r][c] = True


def faixa(grade, ocupado, lin0):
    padrao = [".X..", "X.X.", ".X.."]
    for c in range(GRADE):
        for k, lin in enumerate(range(lin0, lin0 + 5)):
            if k in (0, 4):
                cor = BRANCO
            else:
                cor = BRANCO if padrao[k - 1][c % 4] == "X" else VERMELHO
            grade[lin][c] = cor
            ocupado[lin][c] = True


def montar_grade():
    grade = [[AZUL] * GRADE for _ in range(GRADE)]
    ocupado = [[False] * GRADE for _ in range(GRADE)]

    # árvores do topo (centros em 22, 32, 42; topo na linha 3)
    for cx, trocas in (
        (22, {(5, 3): "R", (7, 5): "Y"}),
        (32, {(0, 4): "Y", (4, 3): "R", (6, 5): "Y", (7, 2): "R", (8, 6): "R"}),
        (42, {(5, 5): "R", (7, 3): "Y"}),
    ):
        sprite_para_grade(grade, ocupado, ARVORE, cx - 4, 3, trocas)
    # estrela maior na árvore central
    for (r, c) in ((3, 31), (3, 33), (2, 32)):
        grade[r][c] = OURO
        ocupado[r][c] = True

    faixa(grade, ocupado, 14)
    faixa(grade, ocupado, 44)

    # cena
    sprite_para_grade(grade, ocupado, RENA, 5, 20)
    sprite_para_grade(grade, ocupado, RENA, 19, 20)
    sprite_para_grade(grade, ocupado, TRENO, 35, 20)
    # rédeas
    for c in range(17, 20):
        grade[24][c] = BRANCO
        ocupado[24][c] = True
    for c in range(31, 36):
        grade[25][c] = BRANCO
        ocupado[25][c] = True

    # árvores laterais
    sprite_para_grade(grade, ocupado, ARVORE, 3, 33, {(5, 3): "R", (7, 5): "Y"})
    sprite_para_grade(grade, ocupado, ARVORE, 52, 33, {(5, 5): "R", (7, 3): "Y"})
    return grade, ocupado


def neve(grade, ocupado):
    rng = random.Random(2024)
    reservado = [[False] * GRADE for _ in range(GRADE)]
    for r in range(32, 43):
        for c in range(13, 51):
            reservado[r][c] = True
    for r in range(50, 64):
        for c in range(16, 49):
            reservado[r][c] = True
    for r in range(GRADE):
        for c in range(GRADE):
            if ocupado[r][c]:
                for dr in (-2, -1, 0, 1, 2):
                    for dc in (-2, -1, 0, 1, 2):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < GRADE and 0 <= cc < GRADE:
                            reservado[rr][cc] = True

    def dentro_circulo(r, c):
        x = ORIGEM + CEL * c + CEL / 2
        y = ORIGEM + CEL * r + CEL / 2
        return math.hypot(x - 225, y - 225) < 225 - 10

    def livre(r, c):
        return (0 <= r < GRADE and 0 <= c < GRADE and not reservado[r][c]
                and grade[r][c] == AZUL and dentro_circulo(r, c))

    pontos = []
    flocos = []
    # flocos em cruz (+) primeiro
    tent = 0
    while len(flocos) < 4 and tent < 3000:
        tent += 1
        r, c = rng.randrange(1, 63), rng.randrange(1, 63)
        cel = [(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        if all(livre(*p) for p in cel) and all(
                math.hypot(r - f[0], c - f[1]) >= 8 for f in flocos):
            flocos.append((r, c))
            for p in cel:
                grade[p[0]][p[1]] = BRANCO
                reservado[p[0]][p[1]] = True
                pontos.append(p)
            for dr in (-2, -1, 0, 1, 2):
                for dc in (-2, -1, 0, 1, 2):
                    if 0 <= r + dr < GRADE and 0 <= c + dc < GRADE:
                        reservado[r + dr][c + dc] = True
    flocos_pts = list(pontos)
    cand = [(r, c) for r in range(GRADE) for c in range(GRADE)]
    rng.shuffle(cand)
    flakes = []
    for (r, c) in cand:
        if not livre(r, c):
            continue
        if any(math.hypot(r - a, c - b) < 3.0 for a, b in flakes + flocos_pts):
            continue
        # evita pingos colados nas faixas
        flakes.append((r, c))
        grade[r][c] = BRANCO
    return grade


def render_fundo():
    grade, ocupado = montar_grade()
    neve(grade, ocupado)
    pontos = [(c, r, grade[r][c]) for r in range(GRADE) for c in range(GRADE)]
    img = render_pontos(TELA, TELA, CEL, ORIGEM, pontos, fundo_gap=FUNDO_LACO,
                        rng=random.Random(11))
    arr = np.array(img.convert("RGB")).astype(np.int16)
    ruido = np.random.default_rng(5).integers(-5, 6, size=arr.shape[:2])[..., None]
    arr = np.clip(arr + ruido, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


# ------------------------------------------------------------------ fonte grande
GRANDE = {
    "0": ".XXXXX. XXXXXXX XX...XX XX...XX XX...XX XX...XX XX...XX XX...XX XX...XX XXXXXXX .XXXXX.",
    "1": "..XXX.. .XXXX.. XX.XX.. ...XX.. ...XX.. ...XX.. ...XX.. ...XX.. ...XX.. XXXXXXX XXXXXXX",
    "2": ".XXXXX. XXXXXXX XX...XX .....XX ....XXX ..XXXX. .XXX... XXX.... XX..... XXXXXXX XXXXXXX",
    "3": "XXXXXX. XXXXXXX .....XX .....XX ..XXXX. ..XXXX. .....XX .....XX .....XX XXXXXXX XXXXXX.",
    "4": "XX...XX XX...XX XX...XX XX...XX XX...XX XXXXXXX XXXXXXX .....XX .....XX .....XX .....XX",
    "5": "XXXXXXX XXXXXXX XX..... XX..... XXXXXX. XXXXXXX .....XX .....XX .....XX XXXXXXX XXXXXX.",
    "6": ".XXXXX. XXXXXXX XX..... XX..... XXXXXX. XXXXXXX XX...XX XX...XX XX...XX XXXXXXX .XXXXX.",
    "7": "XXXXXXX XXXXXXX .....XX ....XX. ...XX.. ..XX... ..XX... ..XX... ..XX... ..XX... ..XX...",
    "8": ".XXXXX. XXXXXXX XX...XX XX...XX .XXXXX. .XXXXX. XX...XX XX...XX XX...XX XXXXXXX .XXXXX.",
    "9": ".XXXXX. XXXXXXX XX...XX XX...XX XX...XX XXXXXXX .XXXXXX .....XX .....XX XXXXXXX .XXXXX.",
}
DOIS_PONTOS = ["...."] * 3 + ["XX"] * 2 + ["."] * 2 + ["XX"] * 2 + ["."] * 2


def render_glifo_grande(linhas, largura_cel):
    pts = []
    for r, linha in enumerate(linhas):
        for c, ch in enumerate(linha):
            if ch == "X":
                pts.append((c, r, BRANCO))
    larg = (largura_cel + 1) * CEL
    return render_pontos(larg, 11 * CEL, CEL, 0, pts, rng=random.Random(31 + largura_cel))


def gerar_fonte_grande():
    saida = {}
    for d, txt in GRANDE.items():
        saida["g_" + d] = render_glifo_grande(txt.split(), 7)
    linhas = [l[:2] for l in DOIS_PONTOS]
    saida["g_dois_pontos"] = render_glifo_grande(linhas, 2)
    return saida


# ------------------------------------------------------------------ fonte pequena
def seg(*partes):
    """partes: (linha_inicial, [linhas]) -> lista de 9 linhas."""
    larg = len(partes[0][1][0])
    g = ["." * larg for _ in range(9)]
    for ini, ls in partes:
        for k, l in enumerate(ls):
            g[ini + k] = l
    return g


PEQ = {
    "a": seg((2, [".XX.", "...X", ".XXX", "X..X", ".XXX"])),
    "á": seg((0, ["..X.", ".X.."]), (2, [".XX.", "...X", ".XXX", "X..X", ".XXX"])),
    "b": seg((0, ["X...", "X...", "XXX.", "X..X", "X..X", "X..X", "XXX."])),
    "ç": seg((2, [".XXX", "X...", "X...", "X...", ".XXX"]), (7, ["..X.", ".XX."])),
    "d": seg((0, ["...X", "...X", ".XXX", "X..X", "X..X", "X..X", ".XXX"])),
    "e": seg((2, [".XX.", "X..X", "XXXX", "X...", ".XXX"])),
    "g": seg((2, [".XXX", "X..X", "X..X", "X..X", ".XXX"]), (7, ["...X", ".XX."])),
    "i": seg((0, ["X"]), (2, ["X"] * 5)),
    "m": seg((2, ["XX.X.", "X.X.X", "X.X.X", "X.X.X", "X.X.X"])),
    "n": seg((2, ["XXX.", "X..X", "X..X", "X..X", "X..X"])),
    "o": seg((2, [".XX.", "X..X", "X..X", "X..X", ".XX."])),
    "q": seg((2, [".XXX", "X..X", "X..X", "X..X", ".XXX"]), (7, ["...X", "...X"])),
    "r": seg((2, ["X.XX", "XX..", "X...", "X...", "X..."])),
    "s": seg((2, [".XXX", "X...", ".XX.", "...X", "XXX."])),
    "t": seg((0, [".X.", ".X.", "XXX", ".X.", ".X.", ".X.", "..X"])),
    "u": seg((2, ["X..X", "X..X", "X..X", "X..X", ".XXX"])),
    "x": seg((2, ["X..X", "X..X", ".XX.", "X..X", "X..X"])),
    "0": seg((0, [".XX.", "X..X", "X..X", "X..X", "X..X", "X..X", ".XX."])),
    "1": seg((0, [".X..", "XX..", ".X..", ".X..", ".X..", ".X..", "XXX."])),
    "2": seg((0, [".XX.", "X..X", "...X", "..X.", ".X..", "X...", "XXXX"])),
    "3": seg((0, ["XXX.", "...X", "...X", ".XX.", "...X", "...X", "XXX."])),
    "4": seg((0, ["..X.", ".XX.", "X.X.", "X.X.", "XXXX", "..X.", "..X."])),
    "5": seg((0, ["XXXX", "X...", "XXX.", "...X", "...X", "X..X", ".XX."])),
    "6": seg((0, [".XX.", "X...", "X...", "XXX.", "X..X", "X..X", ".XX."])),
    "7": seg((0, ["XXXX", "...X", "..X.", "..X.", ".X..", ".X..", ".X.."])),
    "8": seg((0, [".XX.", "X..X", "X..X", ".XX.", "X..X", "X..X", ".XX."])),
    "9": seg((0, [".XX.", "X..X", "X..X", ".XXX", "...X", "...X", ".XX."])),
    "/": seg((0, ["...X", "...X", "..X.", "..X.", ".X..", ".X..", "X..."])),
}
NOMES_PEQ = {"á": "p_a_agudo", "ç": "p_c_cedilha", "/": "p_barra"}


def nome_peq(ch):
    return NOMES_PEQ.get(ch, "p_" + ch)


def render_glifo_pequeno(linhas):
    s = 4
    pts = [(c, r, BRANCO) for r, l in enumerate(linhas) for c, ch in enumerate(l) if ch == "X"]
    larg = (len(linhas[0]) + 1) * s
    img = render_pontos(larg, 9 * s, s, 0, pts, rng=random.Random(77 + len(linhas[0])))
    # sombra suave deslocada 1 px
    alfa = img.getchannel("A")
    sombra_a = Image.new("L", img.size, 0)
    sombra_a.paste(alfa, (1, 1))
    sombra_a = sombra_a.filter(ImageFilter.GaussianBlur(0.5)).point(lambda v: int(v * 0.65))
    sombra = Image.new("RGBA", img.size, (8, 22, 32, 0))
    sombra.putalpha(sombra_a)
    return Image.alpha_composite(sombra, img)


def gerar_fonte_pequena():
    return {nome_peq(ch): render_glifo_pequeno(l) for ch, l in PEQ.items()}


SEMANA = {
    "domingo": "dia_domingo", "segunda": "dia_segunda", "terça": "dia_terca",
    "quarta": "dia_quarta", "quinta": "dia_quinta", "sexta": "dia_sexta",
    "sábado": "dia_sabado",
}
# glifos pequenos que o mostrador realmente usa como fonte (data dd/mm)
USADOS_FONTE = set("0123456789/")


def gerar_dias_semana(pequenos):
    """Imagens pré-compostas dos dias da semana (glifos concatenados, sem a
    célula de espaço final). Altura 36."""
    saida = {}
    for palavra, nome in SEMANA.items():
        w = largura_texto(palavra, pequenos, nome_peq) - 4
        img = Image.new("RGBA", (w, 36), (0, 0, 0, 0))
        x = 0
        for ch in palavra:
            g = pequenos[nome_peq(ch)]
            img.alpha_composite(g, (x, 0))
            x += g.size[0]
        saida[nome] = img
    return saida


# --------------------------------------------------------------------- prévia
def largura_texto(texto, glifos, nomear):
    return sum(glifos[nomear(ch)].size[0] for ch in texto)


def desenhar_texto(canvas, texto, x, y, glifos, nomear, alfa=1.0):
    for ch in texto:
        g = glifos[nomear(ch)]
        if alfa < 1.0:
            g = g.copy()
            g.putalpha(g.getchannel("A").point(lambda v: int(v * alfa)))
        canvas.alpha_composite(g, (x, y))
        x += g.size[0]


def nome_grande(ch):
    return "g_dois_pontos" if ch == ":" else "g_" + ch


def mascara_circulo():
    m = Image.new("L", (TELA * SS, TELA * SS), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m).ellipse((0, 0, TELA * SS - 1, TELA * SS - 1), fill=255)
    return m.resize((TELA, TELA), Image.LANCZOS)


def compor(fundo, grandes, pequenos, dias, hora, semana, data, ambiente):
    if ambiente:
        canvas = Image.new("RGBA", (TELA, TELA), (0, 0, 0, 255))
    else:
        canvas = fundo.convert("RGBA")
    a_hora = 200 / 255.0 if ambiente else 1.0
    a_peq = 200 / 255.0 if ambiente else 1.0
    desenhar_texto(canvas, hora, 106, ORIGEM + CEL * 32, grandes, nome_grande, a_hora)
    img_dia = dias[SEMANA[semana]]
    if a_peq < 1.0:
        img_dia = img_dia.copy()
        img_dia.putalpha(img_dia.getchannel("A").point(lambda v: int(v * a_peq)))
    canvas.alpha_composite(img_dia, (225 - img_dia.size[0] // 2, 352))
    w = largura_texto(data, pequenos, nome_peq)
    desenhar_texto(canvas, data, (TELA - w) // 2, 392, pequenos, nome_peq, a_peq)
    canvas.putalpha(mascara_circulo())
    return canvas


def main():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(PREVIA, exist_ok=True)
    fundo = render_fundo()
    fundo.save(os.path.join(RES, "fundo.png"))
    grandes = gerar_fonte_grande()
    pequenos = gerar_fonte_pequena()
    dias = gerar_dias_semana(pequenos)
    usados = {nome_peq(ch): pequenos[nome_peq(ch)] for ch in USADOS_FONTE}
    for nome, img in {**grandes, **usados, **dias}.items():
        img.save(os.path.join(RES, nome + ".png"))
    normal = compor(fundo, grandes, pequenos, dias, "10:08", "sábado", "24/10", False)
    amb = compor(fundo, grandes, pequenos, dias, "10:08", "sábado", "24/10", True)
    normal.save(os.path.join(RES, "preview.png"))
    normal.save(os.path.join(PREVIA, "previa.png"))
    amb.save(os.path.join(PREVIA, "previa_ambiente.png"))
    # dimensões dos glifos, para conferir com o XML
    for nome, img in sorted({**grandes, **usados, **dias}.items()):
        print(nome, img.size)
    print("ok")


if __name__ == "__main__":
    main()
