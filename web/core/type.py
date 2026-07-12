TYPE_CHART = {
    "normal": {
        "rock": 0.625, "steel": 0.625, "ghost": 0.39
    },
    "fire": {
        "grass": 1.6, "ice": 1.6, "bug": 1.6, "steel": 1.6,
        "fire": 0.625, "water": 0.625, "rock": 0.625, "dragon": 0.625
    },
    "water": {
        "fire": 1.6, "ground": 1.6, "rock": 1.6,
        "water": 0.625, "grass": 0.625, "dragon": 0.625
    },
    "electric": {
        "water": 1.6, "flying": 1.6,
        "electric": 0.625, "grass": 0.625, "dragon": 0.625,
        "ground": 0.39
    },
    "grass": {
        "water": 1.6, "ground": 1.6, "rock": 1.6,
        "fire": 0.625, "grass": 0.625, "poison": 0.625,
        "flying": 0.625, "bug": 0.625, "dragon": 0.625, "steel": 0.625
    },
    "ice": {
        "grass": 1.6, "ground": 1.6, "flying": 1.6, "dragon": 1.6,
        "fire": 0.625, "water": 0.625, "ice": 0.625, "steel": 0.625
    },
    "fighting": {
        "normal": 1.6, "ice": 1.6, "rock": 1.6, "dark": 1.6, "steel": 1.6,
        "poison": 0.625, "flying": 0.625, "psychic": 0.625, "bug": 0.625, "fairy": 0.625,
        "ghost": 0.39
    },
    "poison": {
        "grass": 1.6, "fairy": 1.6,
        "poison": 0.625, "ground": 0.625, "rock": 0.625, "ghost": 0.625,
        "steel": 0.39
    },
    "ground": {
        "fire": 1.6, "electric": 1.6, "poison": 1.6, "rock": 1.6, "steel": 1.6,
        "grass": 0.625, "bug": 0.625,
        "flying": 0.39
    },
    "flying": {
        "grass": 1.6, "fighting": 1.6, "bug": 1.6,
        "electric": 0.625, "rock": 0.625, "steel": 0.625
    },
    "psychic": {
        "fighting": 1.6, "poison": 1.6,
        "psychic": 0.625, "steel": 0.625,
        "dark": 0.39
    },
    "bug": {
        "grass": 1.6, "psychic": 1.6, "dark": 1.6,
        "fire": 0.625, "fighting": 0.625, "poison": 0.625,
        "flying": 0.625, "ghost": 0.625, "steel": 0.625, "fairy": 0.625
    },
    "rock": {
        "fire": 1.6, "ice": 1.6, "flying": 1.6, "bug": 1.6,
        "fighting": 0.625, "ground": 0.625, "steel": 0.625
    },
    "ghost": {
        "psychic": 1.6, "ghost": 1.6,
        "dark": 0.625,
        "normal": 0.39
    },
    "dragon": {
        "dragon": 1.6,
        "steel": 0.625,
        "fairy": 0.39
    },
    "dark": {
        "psychic": 1.6, "ghost": 1.6,
        "fighting": 0.625, "dark": 0.625, "fairy": 0.625
    },
    "steel": {
        "ice": 1.6, "rock": 1.6, "fairy": 1.6,
        "fire": 0.625, "water": 0.625, "electric": 0.625, "steel": 0.625
    },
    "fairy": {
        "fighting": 1.6, "dragon": 1.6, "dark": 1.6,
        "fire": 0.625, "poison": 0.625, "steel": 0.625
    }
}

# タイプ表示順
TYPE_ORDER = [
    "normal", "fire", "water", "grass", "electric", "ice",
    "fighting", "poison", "ground", "flying", "psychic",
    "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"
]

# タイプ英和変換
TYPE_JA = {
    "normal": "ノーマル",
    "fire": "ほのお",
    "water": "みず",
    "grass": "くさ",
    "electric": "でんき",
    "ice": "こおり",
    "fighting": "かくとう",
    "poison": "どく",
    "ground": "じめん",
    "flying": "ひこう",
    "psychic": "エスパー",
    "bug": "むし",
    "rock": "いわ",
    "ghost": "ゴースト",
    "dragon": "ドラゴン",
    "dark": "あく",
    "steel": "はがね",
    "fairy": "フェアリー",
}

TYPE_EN = {v: k for k, v in TYPE_JA.items()}

# タイプ見出し色
TYPE_COLOR = {
    "normal":  "#A8A77A",
    "fire":    "#EE8130",
    "water":   "#6390F0",
    "electric":"#F7D02C",
    "grass":   "#7AC74C",
    "ice":     "#96D9D6",
    "fighting":"#C22E28",
    "poison":  "#A33EA1",
    "ground":  "#E2BF65",
    "flying":  "#A98FF3",
    "psychic": "#F95587",
    "bug":     "#A6B91A",
    "rock":    "#B6A136",
    "ghost":   "#735797",
    "dragon":  "#6F35FC",
    "dark":    "#705746",
    "steel":   "#B7B7CE",
    "fairy":   "#D685AD",
}

# 少し薄めのタイプ色
def lighten(hex_color, factor=0.3):
    """
    hex_color: "#A8A77A" のような HEX
    factor: 0〜1（白にどれだけ寄せるか）
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    '''
    # 白に寄せる
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    '''

    # 混ぜる色（白）
    R, G, B = 255, 255, 255

    r = int(r * (1-factor) + R * factor)
    g = int(g * (1-factor) + G * factor)
    b = int(b * (1-factor) + B * factor)

    return f"#{r:02X}{g:02X}{b:02X}"

TYPE_COLOR_LIGHT = {
    t: lighten(c, factor=0.8)
    for t, c in TYPE_COLOR.items()
}

# タイプ別の下線を引く
def type_with_underline(t):
    color = TYPE_COLOR[t]
    return f'''
        <span style="
            background: linear-gradient(
                to bottom,
                transparent 65%,
                {color} 85%,
                transparent 100%
            );
            padding: 0 2px;
        ">{TYPE_JA[t]}</span>
    '''
# タイプ名の日本語＞英語の逆引き
def ja_to_en_type(type_ja: str) -> str:
    return TYPE_EN.get(type_ja, type_ja)
