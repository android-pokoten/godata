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

# わざごとにダメージ一覧
def list_move_damage_both_sp(p1, p2, species, moves):
    import pandas as pd
    import streamlit as st

    from core.logic.damage import calc_damage
    from core.simulator import calc_stats_for_individual

    # 実数値計算
    atk1, def1, hp1 = calc_stats_for_individual(p1, species)
    atk2, def2, hp2 = calc_stats_for_individual(p2, species)

    # 種族データ
    sp1 = species[species["species_id"] == p1["species_id"]].iloc[0] 
    sp2 = species[species["species_id"] == p2["species_id"]].iloc[0] 
    # 計算用に攻撃と防御の種族値をセット
    sp1["iv_atk"] = atk1
    sp1["iv_def"] = def1
    sp2["iv_atk"] = atk2
    sp2["iv_def"] = def2

    # moves の index を move_id にセット
    moves = moves.set_index("move_id")

    spRows = []

    for spA, spB in [(sp1, sp2), (sp2, sp1)]:
        # わざ一覧を列挙
        move_list = spA["fast_moves"].split(",") if spA["fast_moves"] else []
        move_list += spA["elitefast"].split(",") if spA["elitefast"] else []
        move_list += spA["charge_moves"].split(",") if spA["charge_moves"] else []
        move_list += spA["elitecharge"].split(",") if spA["elitecharge"] else []

        rowsA = []

        # --- A → B のダメージ ---
        for move in move_list:
            #st.write(f"{moves.index}")
            move_data = moves.loc[move]

            dmg, mult = calc_damage(spA, spB, move_data, spA["iv_atk"], spB["iv_def"])
            rowsA.append({
                "技": move_data["name_ja"],
                "タイプ": move_data["type"],
                "ターン数": move_data["turns"],
                "威力": move_data["power"],
                "倍率": mult,
                "ダメージ": dmg,
                "エネルギー": move_data["energy"]
            })

        spRows.append(rowsA)

    return pd.DataFrame(spRows[0]), pd.DataFrame(spRows[1])
