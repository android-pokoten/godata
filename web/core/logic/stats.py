NOTE_PATH = "data/notes.csv"

# 手持ち個体の詳細データ作る
'''
input: selected_iv > 文字列、対象の species_id
output: > DataFrame、必要データを付与した個体のデータ(0～複数)
'''
def calc_indivisuals_stats(selected_iv, fast_move_list, charge_move_list):
    from core.loader import load_moves, load_individuals
    from core.param_calc import compute_cp_row, compute_scp_row, compute_hp_row

    moves = load_moves()

    # 選択された species_id の個体を抽出
    individuals = load_individuals()
    indiv = individuals[individuals["species_id"] == selected_iv].copy()

    # 個体のCP, SCP, HP を計算
    if not indiv.empty:
        indiv["CP"] = indiv.apply(compute_cp_row, axis=1)
        indiv["SCP"] = indiv.apply(compute_scp_row, axis=1)
        indiv["HP"] = indiv.apply(compute_hp_row, axis=1)

        # fast_move の日本語名を結合
        indiv = indiv.merge(
            fast_move_list[["move_id", "name_ja", "type", "power_stab", "energy", "turns", "dpt", "ept"]].rename(columns={"name_ja": "fast_move_ja", "type": "fast_move_type", "power_stab": "fast_power_stab", "energy": "fast_energy", "turns": "fast_turns"}),
            how="left",
            left_on="fast_move",
            right_on="move_id"
        ).drop(columns=["move_id"])
        
        # charge_move1 の日本語名
        indiv = indiv.merge(
            charge_move_list[["move_id", "name_ja", "type", "power_stab", "energy", "dpe"]].rename(columns={"name_ja": "charge_move1_ja", "type": "charge_move1_type", "power_stab": "charge1_power_stab", "energy": "charge1_energy", "dpe": "charge1_dpe"}),
            how="left",
            left_on="charge_move1",
            right_on="move_id"
        ).drop(columns=["move_id"])
        
        # charge_move2 の日本語名
        indiv = indiv.merge(
            charge_move_list[["move_id", "name_ja", "type", "power_stab", "energy", "dpe"]].rename(columns={"name_ja": "charge_move2_ja", "type": "charge_move2_type", "power_stab": "charge2_power_stab", "energy": "charge2_energy", "dpe": "charge2_dpe"}),
            how="left",
            left_on="charge_move2",
            right_on="move_id"
        ).drop(columns=["move_id"])

        def make_fastmove_tooltip(row):
            return f"ダメージ: {row["fast_power_stab"]} / エネルギー: {row["fast_energy"]} / DPT: {row["dpt"]} / EPT: {row["ept"]}"
        def make_charge1move_tooltip(row):
            return f"ダメージ: {row["charge1_power_stab"]} / エネルギー: {row["charge1_energy"]} / DPE: {row["charge1_dpe"]}"
        def make_charge2move_tooltip(row):
            return f"ダメージ: {row["charge2_power_stab"]} / エネルギー: {row["charge2_energy"]} / DPE: {row["charge2_dpe"]}"

        indiv["fast_move_text"] = indiv.apply(make_fastmove_tooltip, axis=1)
        indiv["charge_move1_text"] = indiv.apply(make_charge1move_tooltip, axis=1)
        indiv["charge_move2_text"] = indiv.apply(make_charge2move_tooltip, axis=1)

        return indiv
    else:
        return None

# メモを読み込んで内容を返す
'''
input: selected_iv > 文字列、対象の individual_id
output: > 文字列、メモのテキスト
'''
def load_notes(selected_iv):
    import os
    import pandas as pd

    # メモファイルが存在しない場合は空を返す
    if not os.path.exists(NOTE_PATH):
        return ""

    df = pd.read_csv(NOTE_PATH)
    existing = df[df["individual_id"] == selected_iv]
    return existing["memo"].iloc[0] if not existing.empty else ""

# メモを書き込む
'''
input: selected_iv, memo > 文字列, 文字列、対象の individual_id, 書き込むテキスト
output: > 文字列、メモのテキスト
'''
def save_note(individual_id, memo):
    import os
    import pandas as pd

    if not os.path.exists(NOTE_PATH):
        notes = pd.DataFrame(columns=["individual_id", "memo"])
    else:
        notes = pd.read_csv(NOTE_PATH)

    # 既存のメモを更新 or 新規追加
    notes = notes[notes["individual_id"] != individual_id]
    notes = pd.concat([
        notes,
        pd.DataFrame([{"individual_id": individual_id, "memo": memo}])
    ])

    notes.to_csv(NOTE_PATH, index=False)
