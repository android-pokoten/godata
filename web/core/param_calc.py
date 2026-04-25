from core.cpm import CPM
from core.loader import load_species, load_moves, load_individuals

species = load_species()

# CP計算関数
def calc_cp(base_atk, base_def, base_sta, atk_iv, def_iv, sta_iv, level):
    cpm = CPM.get(level, None)
    if cpm is None:
        return None

    A = base_atk + atk_iv
    D = base_def + def_iv
    S = base_sta + sta_iv

    #print(f"{A} {D} {S} {level} {cpm}")
    cp = (A * (D ** 0.5) * (S ** 0.5) * (cpm ** 2)) / 10
    return max(10, int(cp))

# SCP計算関数
def calc_scp(base_atk, base_def, base_sta, atk_iv, def_iv, sta_iv, level):
    cpm = CPM.get(level, None)
    if cpm is None:
        return None

    A = (base_atk + atk_iv) * cpm
    D = (base_def + def_iv) * cpm
    HP = int((base_sta + sta_iv) * cpm)

    score = int(((A * D * HP) ** (2/3)) / 10)
    return score

# HP 計算
def calc_hp(base_sta, iv_sta, cpm):
    return max(10, int((base_sta + iv_sta) * cpm))

# 列ごとのCP計算
def compute_cp_row(row):    
    # 種族データ
    sp = species[species["species_id"] == row["species_id"]].iloc[0]

    #print(row["species_id"])
    return calc_cp(
        base_atk=sp["base_atk"],
        base_def=sp["base_def"],
        base_sta=sp["base_sta"],
        atk_iv=row["iv_atk"],
        def_iv=row["iv_def"],
        sta_iv=row["iv_sta"],
        level=row["level"]
    )

# 列ごとのSCP計算
def compute_scp_row(row):
    # 種族データ
    sp = species[species["species_id"] == row["species_id"]].iloc[0]

    return calc_scp(
        base_atk=sp["base_atk"],
        base_def=sp["base_def"],
        base_sta=sp["base_sta"],
        atk_iv=row["iv_atk"],
        def_iv=row["iv_def"],
        sta_iv=row["iv_sta"],
        level=row["level"]
    )

# 列ごとのHO計算
def compute_hp_row(row):
    # 種族データ
    sp = species[species["species_id"] == row["species_id"]].iloc[0]

    level = row["level"]

    cpm = CPM.get(level, None)
    if cpm is None:
        return None

    hp = int((sp["base_sta"] + row["iv_sta"]) * cpm)

    return max(10, hp)

# CPからレベルを逆算
def calc_level_from_cp(species_id, iv_atk, iv_def, iv_sta, target_cp):
    import math

    # 種族データ
    sp = species[species["species_id"] == species_id].iloc[0]

    atk_base = sp["base_atk"]
    def_base = sp["base_def"]
    sta_base = sp["base_sta"]

    best_level = 1.0
    best_diff = 999999

    for level, cpm in CPM.items():
        atk = (atk_base + iv_atk) * cpm
        defense = (def_base + iv_def) * cpm
        stamina = math.floor((sta_base + iv_sta) * cpm)

        cp = math.floor(atk * math.sqrt(defense) * math.sqrt(stamina) / 10)

        diff = abs(cp - target_cp)
        if diff < best_diff:
            best_diff = diff
            best_level = level

    return best_level

# CP1500に最も近いレベルを求める
def find_best_level_for_cp1500(base_atk, base_def, base_sta, iv_a, iv_d, iv_s):
    import math
    
    target_cp = 1500
    best_level = None
    best_cp = None
    best_diff = 99999

    for level, cpm in CPM.items():  # CPM はあなたのアプリにある dict
        atk = (base_atk + iv_a) * cpm
        defense = (base_def + iv_d) * cpm
        stamina = (base_sta + iv_s) * cpm

        cp = math.floor(atk * math.sqrt(defense) * math.sqrt(stamina) / 10)
        hp = calc_hp(base_sta, iv_s, cpm)

        if cp > target_cp:
            continue
            
        diff = abs(cp - target_cp)
        if diff < best_diff:
            best_diff = diff
            best_level = level
            best_cp = cp
            best_hp = hp

    return best_level, best_cp, best_hp

# PvPランク計算
def calc_pvp_rank(species_id, iv_atk, iv_def, iv_sta):
    import math

    # 種族データ
    sp = species[species["species_id"] == species_id].iloc[0]

    atk_base = sp["base_atk"]
    def_base = sp["base_def"]
    sta_base = sp["base_sta"]

    # 自分のステータス
    def calc_stats(iv_a, iv_d, iv_s, level):
        cpm = CPM[level]
        atk = (atk_base + iv_a) * cpm
        defense = (def_base + iv_d) * cpm
        stamina = math.floor((sta_base + iv_s) * cpm)
        return atk, defense, stamina

    # 自分の最大ステータス（1500/2500）
    def max_stats_for_cp(cap):
        best = 0
        for level in CPM.keys():
            atk, defense, stamina = calc_stats(iv_atk, iv_def, iv_sta, level)
            cp = math.floor(atk * math.sqrt(defense) * math.sqrt(stamina) / 10)
            if cp <= cap:
                score = atk * defense * stamina
                best = max(best, score)
        return best

    my_1500 = max_stats_for_cp(1500)
    my_2500 = max_stats_for_cp(2500)

    # 全 IV でランキング
    def rank_for_cap(cap, my_score):
        import numpy as np

        ivs = np.arange(16)
        A, D, S = np.meshgrid(ivs, ivs, ivs, indexing="ij")

        best_scp = np.zeros((16,16,16))

        for level, cpm in CPM.items():
            atk = (atk_base + A) * cpm
            defense = (def_base + D) * cpm
            stamina = np.floor((sta_base + S) * cpm)

            cp = np.floor(atk * np.sqrt(defense) * np.sqrt(stamina) / 10)

            scp = atk * defense * stamina

            mask = cp <= cap
            best_scp = np.maximum(best_scp, scp * mask)
        
        scores = best_scp.flatten()
        rank = np.sum(scores > my_score) + 1

        return rank

    rank_1500 = rank_for_cap(1500, my_1500)
    rank_2500 = rank_for_cap(2500, my_2500)

    return rank_1500, rank_2500

# テンプレ個体生成ロジック
def generate_template_individual(species_id, species_row):
    # PvP用テンプレIV（本当は種族ごとに違うが、まずは固定でOK）
    iv_a, iv_d, iv_s = 0, 15, 15

    # CP1500に最も近いレベルを計算
    best_level, best_cp, best_hp = find_best_level_for_cp1500(
        species_row["base_atk"],
        species_row["base_def"],
        species_row["base_sta"],
        iv_a, iv_d, iv_s
    )

    def choose_best_fast_move(fast_moves, moves_df):
        # fast_moves: ["vine_whip_fast", "razor_leaf_fast", ...]
        # moves_df: moves.csv を読み込んだ DataFrame

        best = None
        best_ept = -1

        for move_id in fast_moves:
            row = moves_df[moves_df["move_id"] == move_id].iloc[0]
            ept = row["energy"] / row["turns"]  # EPT = エネルギー / ターン

            if ept > best_ept:
                best_ept = ept
                best = move_id

        return best

    def choose_best_charge_moves(charge_moves, moves_df):
        # charge_moves: ["frenzy_plant", "sludge_bomb", ...]
        # moves_df: moves.csv

        rows = []
        for move_id in charge_moves:
            row = moves_df[moves_df["move_id"] == move_id].iloc[0]
            rows.append((move_id, row["energy"]))

        # エネルギーが小さい順にソート
        rows.sort(key=lambda x: x[1], reverse=True)

        # 1つ目と2つ目を返す（2つ未満なら空文字）
        move1 = rows[0][0] if len(rows) >= 1 else ""
        move2 = rows[1][0] if len(rows) >= 2 else ""

        return move1, move2

    moves = load_moves()

    # fast 技の選択
    fast_moves = species_row["fast_moves"].split(",")
    # レガシー fast 技
    elite_fast = []
    if isinstance(species_row["elitefast"], str) and species_row["elitefast"].strip():
        elite_fast = [m.strip() for m in species_row["elitefast"].split(",")]

    # 結合
    candidates = fast_moves + elite_fast

    fast = choose_best_fast_move(candidates, moves)

    # charge 技の選択
    charge_moves = species_row["charge_moves"].split(",")
    # レガシー charge 技
    elite_charge = []
    if isinstance(species_row["elitecharge"], str) and species_row["elitecharge"].strip():
        elite_charge = [m.strip() for m in species_row["elitecharge"].split(",")]

    # 結合
    candidates = charge_moves + elite_charge

    charge1, charge2 = choose_best_charge_moves(candidates, moves)

    return {
        "individual_id": species_row["name_ja"],
        "species_id": species_id,
        "iv_atk": iv_a,
        "iv_def": iv_d,
        "iv_sta": iv_s,
        "level": best_level,
        "fast_move": fast,
        "charge_move1": charge1,
        "charge_move2": charge2,
    }
