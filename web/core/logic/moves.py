# ノーマルわざの一覧を作る
'''
input: sp > 辞書、species.csv データの1行
output: > DataFrame、わざ一覧データ
'''
def calc_fastmove_list(sp):
    from core.type import TYPE_JA
    from core.loader import load_moves

    moves_df = load_moves()

    # ノーマルわざのリストを作る
    fast_list = sp["fast_moves"].split(",") if sp["fast_moves"] else [] 
    # 限定ノーマルわざのリストを作る
    elite_fast_list = sp["elitefast"].split(",") if sp["elitefast"] else []
    # 限定わざを含むノーマルわざ全リストを作る
    fast_list += elite_fast_list

    # ノーマルわざ全リストから、わざデータのリストを作る
    fast_move_list = moves_df[moves_df["move_id"].isin(fast_list)].copy()

    # タイプ一致倍率の stab 列を追加
    fast_move_list["stab"] = fast_move_list["type"].apply(
        lambda t: 1.2 if t in [sp["type1"], sp["type2"]] else 1.0
    )
    # タイプ一致判定用の 一致 列を追加
    fast_move_list["一致"] = fast_move_list["stab"].apply(lambda x: "⭐" if x > 1.0 else "")
    # 倍率適用後の実際のダメージ値の power_stab 列を追加
    fast_move_list["power_stab"] = (fast_move_list["power"] * fast_move_list["stab"]).round(1)
    # ターンごとのダメージ値の dpt 列を追加
    fast_move_list["dpt"] = fast_move_list["power_stab"] / fast_move_list["turns"]
    # ターンごとのエネルギー値の ept 列を追加
    fast_move_list["ept"] = fast_move_list["energy"] / fast_move_list["turns"]
    # わざの日本語名の name_ja 列を追加
    fast_move_list["name_ja"] = fast_move_list.apply(
        lambda row: row["name_ja"] + "＊" if row["move_id"] in elite_fast_list else row["name_ja"],
        axis=1
    )
    # わざのタイプの type 列を日本語名にする
    fast_move_list["type"] = fast_move_list["type"].apply(lambda x: TYPE_JA.get(x, x))

    return fast_move_list


# チャージわざの一覧を作る
'''
input: sp > 辞書、species.csv データの1行
output: > DataFrame、わざ一覧データ
'''
def calc_chargemove_list(sp):
    from core.type import TYPE_JA
    from core.loader import load_moves

    moves_df = load_moves()

    # チャージわざのリストを作る
    charge_list = sp["charge_moves"].split(",") if sp["charge_moves"] else []
    # 限定チャージわざのリストを作る
    elite_charge_list = sp["elitecharge"].split(",") if sp["elitecharge"] else []
    # 限定わざを含むチャージわざ全リストを作る
    charge_list += elite_charge_list

    # チャージわざ全リストから、わざデータのリストを作る
    charge_moves = moves_df[moves_df["move_id"].isin(charge_list)].copy()

    # タイプ一致倍率の stab 列を追加
    charge_moves["stab"] = charge_moves["type"].apply(
        lambda t: 1.2 if t in [sp["type1"], sp["type2"]] else 1.0
    )
    # タイプ一致判定用の 一致 列を追加
    charge_moves["一致"] = charge_moves["stab"].apply(lambda x: "⭐" if x > 1.0 else "")
    # 倍率適用後の実際のダメージ値の power_stab 列を追加
    charge_moves["power_stab"] = (charge_moves["power"] * charge_moves["stab"]).round(1)
    # エネルギーごとのダメージ値の dpe 列を追加
    charge_moves["dpe"] = (charge_moves["power_stab"] / charge_moves["energy"].abs()).round(1)
    # わざの日本語名の name_ja 列を追加
    charge_moves["name_ja"] = charge_moves.apply(
        lambda row: row["name_ja"] + "＊" if row["move_id"] in elite_charge_list else row["name_ja"],
        axis=1
    )
    # わざのタイプの type 列を日本語名にする
    charge_moves["type"] = charge_moves["type"].apply(lambda x: TYPE_JA.get(x, x))

    return charge_moves

    # チャージわざ選択ロジック
def choose_charge_move(energy, m1, m2):
    available = []

    if energy >= abs(m1["エネルギー"]):
        available.append(m1)
    if energy >= abs(m2["エネルギー"]):
        available.append(m2)

    if not available:
        return None

    # エネルギーが軽い技を優先
    #available.sort(key=lambda m: abs(m["エネルギー"]))
    # 打てるわざのうちダメージが大きいわざを優先
    available.sort(key=lambda m: abs(m["ダメージ"]), reverse=True)
    # DPEが大きいわざを優先
    #best = max(available, key=lambda m: abs(m["e_dpe"]))
    return available[0]

# チャージわざ処理
def apply_charge(move, energy, hp, shields):
    # 1. エネルギー消費（チャージ技は energy が負）
    energy -= abs(move["エネルギー"])

    # 2. シールド判定
    if shields > 0:
        shields -= 1
        # シールドで完全に防ぐのでダメージなし
        return hp, shields, energy, 0

    # 3. ダメージ計算（PvP 公式式）
    #dmg = int(0.5 * move["power"] * atk / deff * stab * eff) + 1

    # 4. HP 更新
    hp -= move["ダメージ"]

    # 5. 更新後の状態を返す
    return hp, shields, energy, move["ダメージ"]
