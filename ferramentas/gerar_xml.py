"""Gera watchface/src/main/res/raw/watchface.xml.

Uso:  python ferramentas/gerar_xml.py
Hora e data são montadas com PartImage escolhidos por <Condition> (sem BitmapFont/PartText,
que o relógio ignora). Slots na grade do tecido. O dia da semana (pt-BR) é fixo abaixo.
"""
import pathlib

SAIDA = pathlib.Path(__file__).resolve().parent.parent / "watchface/src/main/res/raw/watchface.xml"

DIAS = [  # (nome, expressão, x, largura, recurso)
    ("dom", "[DAY_OF_WEEK] == 1", 161, 128, "dia_domingo"),
    ("seg", "[DAY_OF_WEEK] == 2", 157, 136, "dia_segunda"),
    ("ter", "[DAY_OF_WEEK] == 3", 179, 92, "dia_terca"),
    ("qua", "[DAY_OF_WEEK] == 4", 169, 112, "dia_quarta"),
    ("qui", "[DAY_OF_WEEK] == 5", 175, 100, "dia_quinta"),
    ("sex", "[DAY_OF_WEEK] == 6", 179, 92, "dia_sexta"),
]
SABADO = (167, 116, "dia_sabado")


def slot(nome, x, y, w, h, expr, prefixo, ndig):
    """Grupo com um dígito escolhido por Condition: expr(d) -> expressão booleana."""
    o = [f'        <Group name="{nome}" x="{x}" y="{y}" width="{w}" height="{h}">',
         "            <Condition>", "                <Expressions>"]
    for d in range(ndig - 1):
        o.append(f'                    <Expression name="d{d}"><![CDATA[{expr(d)}]]></Expression>')
    o.append("                </Expressions>")
    for d in range(ndig - 1):
        o.append(f'                <Compare expression="d{d}">')
        o.append(f'                    <PartImage x="0" y="0" width="{w}" height="{h}"><Image resource="{prefixo}{d}" /></PartImage>')
        o.append("                </Compare>")
    o.append("                <Default>")
    o.append(f'                    <PartImage x="0" y="0" width="{w}" height="{h}"><Image resource="{prefixo}{ndig - 1}" /></PartImage>')
    o.append("                </Default>")
    o.append("            </Condition>")
    o.append("        </Group>")
    return o


def imagem(nome, x, y, w, h, res):
    return [f'        <Group name="{nome}" x="{x}" y="{y}" width="{w}" height="{h}">',
            f'            <PartImage x="0" y="0" width="{w}" height="{h}"><Image resource="{res}" /></PartImage>',
            "        </Group>"]


def main():
    o = ['<?xml version="1.0" encoding="utf-8"?>',
         '<WatchFace width="450" height="450">',
         '    <Metadata key="CLOCK_TYPE" value="DIGITAL" />',
         '    <Metadata key="PREVIEW_TIME" value="10:08:32" />', "",
         '    <Scene backgroundColor="#ff000000">',
         "        <!-- Tecido de tricô (apagado no modo ambiente) -->",
         '        <Group name="fundo" x="0" y="0" width="450" height="450">',
         '            <PartImage x="0" y="0" width="450" height="450">',
         '                <Image resource="fundo" />',
         '                <Variant mode="AMBIENT" target="alpha" value="0" />',
         "            </PartImage>", "        </Group>", "",
         "        <!-- Hora HH:mm: 4 dígitos + dois pontos = 4*56 + 21 = 245 px, na grade do tecido -->",
         '        <Group name="hora" x="0" y="0" width="450" height="450">']
    h = 77
    sl = []
    sl += slot("h_dezena", 106, 225, 56, h, lambda d: f"floor([HOUR_0_23] / 10) == {d}", "g_", 3)
    sl += slot("h_unidade", 162, 225, 56, h, lambda d: f"[HOUR_0_23] % 10 == {d}", "g_", 10)
    sl += imagem("dois_pontos", 218, 225, 21, h, "g_dois_pontos")
    sl += slot("m_dezena", 239, 225, 56, h, lambda d: f"floor([MINUTE] / 10) == {d}", "g_", 10)
    sl += slot("m_unidade", 295, 225, 56, h, lambda d: f"[MINUTE] % 10 == {d}", "g_", 10)
    o += ["    " + l for l in sl]
    o += ['            <Variant mode="AMBIENT" target="alpha" value="200" />', "        </Group>", "",
          "        <!-- Dia da semana em pt-BR, independente do idioma do relógio -->",
          '        <Group name="dia_semana" x="0" y="0" width="450" height="450">',
          "            <Condition>", "                <Expressions>"]
    for n, e, *_ in DIAS:
        o.append(f'                    <Expression name="{n}"><![CDATA[{e}]]></Expression>')
    o.append("                </Expressions>")
    for n, e, x, w, r in DIAS:
        o += [f'                <Compare expression="{n}">',
              f'                    <PartImage x="{x}" y="352" width="{w}" height="36"><Image resource="{r}" /></PartImage>',
              "                </Compare>"]
    x, w, r = SABADO
    o += ["                <Default>",
          f'                    <PartImage x="{x}" y="352" width="{w}" height="36"><Image resource="{r}" /></PartImage>',
          "                </Default>", "            </Condition>",
          '            <Variant mode="AMBIENT" target="alpha" value="200" />', "        </Group>", "",
          "        <!-- Data dd/mm: 5 glifos de 20 px centrados (x = 175..275) -->",
          '        <Group name="data" x="0" y="0" width="450" height="450">']
    sl = []
    sl += slot("d_dezena", 175, 392, 20, 36, lambda d: f"floor([DAY] / 10) == {d}", "p_", 4)
    sl += slot("d_unidade", 195, 392, 20, 36, lambda d: f"[DAY] % 10 == {d}", "p_", 10)
    sl += imagem("barra", 215, 392, 20, 36, "p_barra")
    sl += slot("mes_dezena", 235, 392, 20, 36, lambda d: f"floor([MONTH] / 10) == {d}", "p_", 2)
    sl += slot("mes_unidade", 255, 392, 20, 36, lambda d: f"[MONTH] % 10 == {d}", "p_", 10)
    o += ["    " + l for l in sl]
    o += ['            <Variant mode="AMBIENT" target="alpha" value="200" />', "        </Group>",
          "    </Scene>", "</WatchFace>", ""]
    SAIDA.write_text("\n".join(o), encoding="utf-8")


main()
