import random

from core.cpm import CPM
from core.type import TYPE_CHART

# ダメージ計算
def calc_damage(power, atk, deff, stab=1.0, eff=1.0):
    return max(1, int(0.5 * power * atk / deff * stab * eff) + 1)

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

# チャージわざ選択_高速場bb (エネルギーが軽い方を優先)
def choose_charge_move_sorted(energy, moves):
    for n in moves:
        if energy >= abs(n["energy"]):
            return n
    return None

# チャージわざ処理
def apply_charge(move, atk, deff, hp, shields, energy, stab=1.0, eff=1.0):
    # 1. エネルギー消費（チャージ技は energy が負）
    energy -= abs(move["energy"])

    # 2. シールド判定
    if shields > 0:
        shields -= 1
        # シールドで完全に防ぐのでダメージなし
        return hp, shields, energy, 0

    # 3. ダメージ計算（PvP 公式式）
    dmg = int(0.5 * move["power"] * atk / deff * stab * eff) + 1

    # 4. HP 更新
    hp -= dmg

    # 5. 更新後の状態を返す
    return hp, shields, energy, dmg

# 1vs1 シミュレーター
def simulate(p1, p2, species, moves,
        shield1=0, shield2=0,
        hp1=None, hp2=None,
        energy1=0, energy2=0
    ):
    logs = ""

    # 実数値計算
    atk1, def1, hpi1 = calc_stats_for_individual(p1, species)
    atk2, def2, hpi2 = calc_stats_for_individual(p2, species)

    # HP 初期化
    if hp1 is None:
        hp1 = hpi1
    if hp2 is None:
        hp2 = hpi2

    # 技データ (dict化)
    sp1 = species[species["species_id"] == p1["species_id"]].iloc[0] 
    sp2 = species[species["species_id"] == p2["species_id"]].iloc[0] 

    fm1 = moves.loc[p1["fast_move"]]
    fm1 = {
        "power": float(fm1["power"]),
        "energy": int(fm1["energy"]),
        "turns": int(fm1["turns"]),
        "name_ja": fm1["name_ja"],
    }
    fm2 = moves.loc[p2["fast_move"]]
    fm2 = {
        "power": float(fm2["power"]),
        "energy": int(fm2["energy"]),
        "turns": int(fm2["turns"]),
        "name_ja": fm2["name_ja"],
    }
    cm1_1 = moves.loc[p1["charge_move1"]]
    cm1_1 = {
        "power": float(cm1_1["power"]),
        "energy": int(cm1_1["energy"]),
        "name_ja": cm1_1["name_ja"],
        "e_dpe": effective_dpe(cm1_1, sp1, sp2),
    }
    cm1_2 = moves.loc[p1["charge_move2"]]
    cm1_2 = {
        "power": float(cm1_2["power"]),
        "energy": int(cm1_2["energy"]),
        "name_ja": cm1_2["name_ja"],
        "e_dpe": effective_dpe(cm1_2, sp1, sp2),
    }
    cm2_1 = moves.loc[p2["charge_move1"]]
    cm2_1 = {
        "power": float(cm2_1["power"]),
        "energy": int(cm2_1["energy"]),
        "name_ja": cm2_1["name_ja"],
        "e_dpe": effective_dpe(cm2_1, sp2, sp1),
    }
    cm2_2 = moves.loc[p2["charge_move2"]]
    cm2_2 = {
        "power": float(cm2_2["power"]),
        "energy": int(cm2_2["energy"]),
        "name_ja": cm2_2["name_ja"],
        "e_dpe": effective_dpe(cm2_2, sp2, sp1),
    }

    # チャージわざをエネルギー消費の少ない順に並べる
    charge_moves1 = sorted([cm1_1, cm1_2], key=lambda m: abs(m["energy"]))
    charge_moves2 = sorted([cm2_1, cm2_2], key=lambda m: abs(m["energy"]))

    # 状態
    energy1 = 0
    energy2 = 0
    turn = 0
    t1 = 0
    t2 = 0
    charge_cooldown1 = 0
    charge_cooldown2 = 0

    while hp1 > 0 and hp2 > 0:
        turn += 1
        logs += f"--- ターン {turn} ---\n\n"

        # チャージ技発動判定 (DPEも考慮する場合は上2行、エネルギー判定のみは下2行)
        move1 = choose_charge_move(energy1, cm1_1, cm1_2)
        move2 = choose_charge_move(energy2, cm2_1, cm2_2)
        #move1 = choose_charge_move_sorted(energy1, charge_moves1)
        #move2 = choose_charge_move_sorted(energy2, charge_moves2)

        # 両者が同時に撃てる → CMP タイ
        if move1 is not None and move2 is not None:
            if atk1 > atk2 or (atk1 == atk2 and random.choice([True, False])):
                logs += f"{p1['individual_id']} が {move1['name_ja']} を発動！ "
                hp2, shield2, energy1, dmg = apply_charge(move1, atk1, def2, hp2, shield2, energy1)
                logs += f"ダメージ{dmg} {p2['individual_id']} の HP {hp2}\n\n"
                charge_cooldown1 = 1
            else:
                logs += f"{p2['individual_id']} が {move2['name_ja']} を発動！ "
                hp1, shield1, energy2, dmg = apply_charge(move2, atk2, def1, hp1, shield1, energy2)
                logs += f"ダメージ{dmg} {p1['individual_id']} の HP {hp1}\n\n"
                charge_cooldown2 = 1

            # チャージわざを打ったターンは通常わざが発動しない
            continue

        # 片方だけ撃てる
        elif move1 is not None:
            logs += f"{p1['individual_id']} が {move1['name_ja']} を発動！ "
            hp2, shield2, energy1, dmg = apply_charge(move1, atk1, def2, hp2, shield2, energy1)
            logs += f"ダメージ{dmg} {p2['individual_id']} の HP {hp2}\n\n"
            charge_cooldown1 = 1
            continue

        elif move2 is not None:
            logs += f"{p2['individual_id']} が {move2['name_ja']} を発動！ "
            hp1, shield1, energy2, dmg = apply_charge(move2, atk2, def1, hp1, shield1, energy2)
            logs += f"ダメージ{dmg} {p1['individual_id']} の HP {hp1}\n\n"
            charge_cooldown2 = 1
            continue

        # 通常技処理
        if charge_cooldown1 == 0:
            t1 += 1
        else:
            charge_cooldown1 = 0

        if charge_cooldown2 == 0:
            t2 += 1
        else:
            charge_cooldown2 = 0

        if t1 >= fm1["turns"]:
            dmg = calc_damage(fm1["power"], atk1, def2)
            hp2 -= dmg
            energy1 += fm1["energy"]
            logs += f"{p1['individual_id']} の {fm1['name_ja']} → {dmg} ダメージ\n\n"
            t1 = 0

        if t2 >= fm2["turns"]:
            dmg = calc_damage(fm2["power"], atk2, def1)
            hp1 -= dmg
            energy2 += fm2["energy"]
            logs += f"{p2['individual_id']} の {fm2['name_ja']} → {dmg} ダメージ\n\n"
            t2 = 0

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
    }



# ダメージ値計算
def calc_damage2(attacker, defender, move, iv_atk, iv_def):
    import math

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

    # ダメージ計算（GO の標準式）
    damage = math.floor(0.5 * power * (iv_atk / iv_def) * mult) + 1
    return damage, mult

# わざごとにダメージ一覧
def list_move_damage_both(p1, p2, species, moves):
    import pandas as pd

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
        dmg, mult = calc_damage2(sp1, sp2, move, atk1, def2)
        rowsA.append({
            "技": move["name_ja"],
            "タイプ": move["type"],
            "威力": move["power"],
            "倍率": mult,
            "ダメージ": dmg,
            "エネルギー": move["energy"]
        })

    # --- B → A のダメージ ---
    for move in [fastB, chargeB1, chargeB2]:
        dmg, mult = calc_damage2(sp2, sp1, move, atk2, def1)
        rowsB.append({
            "技": move["name_ja"],
            "タイプ": move["type"],
            "威力": move["power"],
            "倍率": mult,
            "ダメージ": dmg,
            "エネルギー": move["energy"]
        })

    return pd.DataFrame(rowsA), pd.DataFrame(rowsB)

