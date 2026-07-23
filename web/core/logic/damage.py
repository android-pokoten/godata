# ダメージ値計算
'''
input: attacker, defender > 辞書、species.csv の攻撃、防御ポケモンの行
        move > ダメージ計算を行うわざの move.csv の行
        iv_atk > 整数、攻撃側の攻撃個体値
        iv_def > 整数、防御側の防御個体値 
output: damage, mut > ダメージ値、ダメージ倍率(タイプ一致、タイプ相性) 
'''
def calc_damage(attacker, defender, move, iv_atk, iv_def):
    import math
    from core.type import TYPE_CHART

    power = move["power"]
    move_type = move["type"]

    # タイプ相性倍率
    mult = 1.0
    for t in [defender["type1"], defender["type2"]]:
        if t:
            mult *= TYPE_CHART.get(move_type, {}).get(t, 1.0)

    # STAB（タイプ一致）
    if move_type == attacker["type1"] or move_type == attacker["type2"]:
        mult *= 1.2

    # ダメージ計算
    damage = math.floor(0.5 * power * (iv_atk / iv_def) * mult) + 1
    return damage, mult
