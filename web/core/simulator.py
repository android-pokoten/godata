import random

from core.cpm import CPM
from core.type import TYPE_CHART

# 種族値と個体値から実数値を計算
def calc_stats_for_individual(p, species): 
    sp = species[species["species_id"] == p["species_id"]].iloc[0] 
    cpm = CPM[p["level"]] 
    atk = (sp["base_atk"] + p["iv_atk"]) * cpm 
    deff = (sp["base_def"] + p["iv_def"]) * cpm 
    hp = int((sp["base_sta"] + p["iv_sta"]) * cpm) 
    return atk, deff, hp

def effective_dpe(move, attacker, defender):
    # move: 技データ（威力、タイプ、必要エネルギー）
    # attacker/defender: 種族データ or 個体データ

    power = move["power"]
    energy = move["energy"]
    move_type = move["type"]

    # タイプ相性倍率を計算
    mult = 1.0
    for t in [defender["type1"], defender["type2"]]:
        if t:
            mult *= TYPE_CHART.get(move_type, {}).get(t, 1.0)

    return (power * mult) / energy

# チャージわざ選択 (エネルギーが軽い方を優先)
def choose_charge_move(energy, m1, m2):
    available = []

    if energy >= abs(m1["energy"]):
        available.append(m1)
    if energy >= abs(m2["energy"]):
        available.append(m2)

    if not available:
        return None

    # エネルギーが軽い技を優先
    #available.sort(key=lambda m: abs(m["energy"]))
    #return available[0]
    # DPEが大きいわざを優先
    best = max(available, key=lambda m: abs(m["e_dpe"]))
    return best

# わざごとにダメージ一覧
def list_move_damage_both(p1, p2, species, moves):
    import pandas as pd

    from core.logic.damage import calc_damage

    # 実数値計算
    atk1, def1, hp1 = calc_stats_for_individual(p1, species)
    atk2, def2, hp2 = calc_stats_for_individual(p2, species)

    # 種族データ
    sp1 = species[species["species_id"] == p1["species_id"]].iloc[0] 
    sp2 = species[species["species_id"] == p2["species_id"]].iloc[0] 

    # わざデータ
    fastA       = moves.loc[p1["fast_move"]]
    chargeA1    = moves.loc[p1["charge_move1"]]
    chargeA2    = moves.loc[p1["charge_move2"]]
    fastB       = moves.loc[p2["fast_move"]]
    chargeB1    = moves.loc[p2["charge_move1"]]
    chargeB2    = moves.loc[p2["charge_move2"]]

    rowsA = []
    rowsB = []

    # --- A → B のダメージ ---
    for move in [fastA, chargeA1, chargeA2]:
        dmg, mult = calc_damage(sp1, sp2, move, atk1, def2)
        rowsA.append({
            "技": move["name_ja"],
            "タイプ": move["type"],
            "ターン数": move["turns"],
            "威力": move["power"],
            "倍率": mult,
            "ダメージ": dmg,
            "エネルギー": move["energy"]
        })

    # --- B → A のダメージ ---
    for move in [fastB, chargeB1, chargeB2]:
        dmg, mult = calc_damage(sp2, sp1, move, atk2, def1)
        rowsB.append({
            "技": move["name_ja"],
            "タイプ": move["type"],
            "ターン数": move["turns"],
            "威力": move["power"],
            "倍率": mult,
            "ダメージ": dmg,
            "エネルギー": move["energy"]
        })

    return pd.DataFrame(rowsA), pd.DataFrame(rowsB)

# 1vs1 シミュレーター
# p1 = 自分
# p2 = 相手
def simulate(p1, p2, species, p1_moves, p2_moves,
        shield1=0, shield2=0,
        hp1=None, hp2=None,
        energy1=0, energy2=0
    ):
    from core.logic.moves import choose_charge_move, apply_charge

    logs = ""

    # 実数値計算
    atk1, def1, hpi1 = calc_stats_for_individual(p1, species)
    atk2, def2, hpi2 = calc_stats_for_individual(p2, species)

    # チャージわざをエネルギー消費の少ない順に並べる
    charge_moves1 = sorted([p1_moves.iloc[1], p1_moves.iloc[2]], key=lambda m: abs(m["エネルギー"]))
    charge_moves2 = sorted([p2_moves.iloc[1], p2_moves.iloc[2]], key=lambda m: abs(m["エネルギー"]))

    # 状態変数初期化
    # HP (パーティシミュレーションの場合はバトル開始時を引数で渡す)
    if hp1 is None:
        hp1 = hpi1
    if hp2 is None:
        hp2 = hpi2
    turn = 0
    t1 = 0
    t2 = 0
    charge_cooldown1 = 0
    charge_cooldown2 = 0

    turn_logs = []

    while hp1 > 0 and hp2 > 0:
        # ログに残す用の行動
        p1_move = ""
        p2_move = ""
        dmg1 = ""
        dmg2 = ""

        turn += 1
        logs += f"--- ターン {turn} ---\n\n"

        # チャージ技発動判定 (DPEも考慮する場合は上2行、エネルギー判定のみは下2行)
        move1 = choose_charge_move(energy1, p1_moves.iloc[1], p1_moves.iloc[2])
        move2 = choose_charge_move(energy2, p2_moves.iloc[1], p2_moves.iloc[2])
        #move1 = choose_charge_move_sorted(energy1, charge_moves1)
        #move2 = choose_charge_move_sorted(energy2, charge_moves2)

        # 両者が同時に撃てる → CMP タイ
        if move1 is not None and move2 is not None:
            if atk1 > atk2 or (atk1 == atk2 and random.choice([True, False])):
                p1_move = move1['技']
                logs += f"{p1['individual_id']} が {p1_move} を発動！ "
                hp2, shield2, energy1, dmg1 = apply_charge(move1, energy1, hp2, shield2)
                logs += f"ダメージ{dmg1} {p2['individual_id']} の HP {hp2}\n\n"
                charge_cooldown1 = 1
            else:
                p2_move = move2['技']
                logs += f"{p2['individual_id']} が {p2_move} を発動！ "
                hp1, shield1, energy2, dmg2 = apply_charge(move2, energy2, hp1, shield1)
                logs += f"ダメージ{dmg2} {p1['individual_id']} の HP {hp1}\n\n"
                charge_cooldown2 = 1

        # 片方だけ撃てる
        elif move1 is not None:
            p1_move = move1['技']
            logs += f"{p1['individual_id']} が {p1_move} を発動！ "
            hp2, shield2, energy1, dmg1 = apply_charge(move1, energy1, hp2, shield2)
            logs += f"ダメージ{dmg1} {p2['individual_id']} の HP {hp2}\n\n"
            charge_cooldown1 = 1

        elif move2 is not None:
            p2_move = move2['技']
            logs += f"{p2['individual_id']} が {p2_move} を発動！ "
            hp1, shield1, energy2, dmg2 = apply_charge(move2, energy2, hp1, shield1)
            logs += f"ダメージ{dmg2} {p1['individual_id']} の HP {hp1}\n\n"
            charge_cooldown2 = 1

        # チャージわざを打ったターンはノーマルわざを発動しない
        if p1_move == "" and p2_move == "":
            # 通常技処理
            if charge_cooldown1 == 0:
                t1 += 1
            else:
                charge_cooldown1 = 0

            if charge_cooldown2 == 0:
                t2 += 1
            else:
                charge_cooldown2 = 0

            if t1 >= p1_moves.iloc[0]["ターン数"]:
                p1_move = p1_moves.iloc[0]['技']
                dmg1 = p1_moves.iloc[0]["ダメージ"]
                hp2 -= dmg1
                energy1 += p1_moves.iloc[0]["エネルギー"]
                logs += f"{p1['individual_id']} の {p1_move} → {dmg1} ダメージ\n\n"
                t1 = 0

            if t2 >= p2_moves.iloc[0]["ターン数"]:
                p2_move = p2_moves.iloc[0]['技']
                dmg2 = p2_moves.iloc[0]["ダメージ"]
                hp1 -= dmg2
                energy2 += p2_moves.iloc[0]["エネルギー"]
                logs += f"{p2['individual_id']} の {p2_move} → {dmg2} ダメージ\n\n"
                t2 = 0

        turn_logs.append(
            {
                "turn": turn,
                "p1_ene": energy1,
                "p1_move": p1_move,
                "p1_hp": hp1,
                "p1_damage": dmg1,
                "p2_ene": energy2,
                "p2_move": p2_move,
                "p2_hp": hp2,
                "p2_damage": dmg2,
            }
        )

    return {
        "winner": p1["individual_id"] if hp1 > 0 else p2["individual_id"],
        "hp1": hp1,
        "hp2": hp2,
        "shield1": shield1,
        "shield2": shield2,
        "energy1": energy1,
        "energy2": energy2,
        "turns": turn,
        "logs": logs,
        "turn_logs": turn_logs,
    }
