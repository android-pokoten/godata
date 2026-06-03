import streamlit as st
import pandas as pd
import subprocess
import re

from core.loader import load_species, load_moves, load_individuals, load_opponents

# シーズンごとのコミットIDリスト
SEASON_COMMITS = {
    "S26 -> S27": "6012742ffe4b0e0024ec8340785e299f1f72bdea",
}

def parse_move_changes(diff_text):
    """
    diff から変更された技の変更内容を抽出する
    """
    def to_int(x):
        try:
            return int(float(x))
        except:
            return None

    moves_df = load_moves()
    changes = {}

    for line in diff_text.split("\n"):
        if not (line.startswith("+") or line.startswith("-")):
            continue

        cols = line[1:].split(",")
        if len(cols) < 4:
            continue

        move_id = cols[0].strip()
        power = cols[4].strip()
        energy = cols[5].strip()
        move_type = cols[2].strip()

        if move_id not in changes:
            changes[move_id] = {"before": None, "after": None}

        if line.startswith("-"):
            changes[move_id]["before"] = (power, energy, move_type)
        else:
            changes[move_id]["after"] = (power, energy, move_type)

    # 差分だけに絞る
    diff_list = []
    for move, data in changes.items():
        before = data["before"]
        after = data["after"]

        if before and after and before != after:
            # 変更内容をスコア化
            score = 0
            # 威力差分
            score += (to_int(after[0]) - to_int(before[0]))
            # エネルギー差分（重み2倍）
            score += (to_int(after[1]) - to_int(before[1])) * 2

            # 変更内容を説明分にする
            desc = []

            if before[0] != after[0]:
                desc.append(f"威力 {before[0]}→{after[0]}")

            if before[1] != after[1]:
                desc.append(f"エネルギー {before[1]}→{after[1]}")

            desc_txt = " / ".join(desc)

            diff_list.append({
                "move": move,
                "move_name_ja": moves_df[moves_df["move_id"] == move]["name_ja"].iloc[0],
                "power_before": before[0],
                "power_after": after[0],
                "energy_before": before[1],
                "energy_after": after[1],
                "score": score,
                "desc": desc_txt,
            })

    return pd.DataFrame(diff_list)

def parse_species_move_changes(diff_text):
    """
    species.csv の diff から fast_moves / charge_moves の追加・削除を抽出する
    """
    before = {}
    after = {}

    # fast_moves="xxx,yyy"
    fast_re = re.compile(r'"([^"]*)",\s*"([^"]*)"')

    for line in diff_text.split("\n"):
        if not (line.startswith("+") or line.startswith("-")):
            continue

        # CSV の最初の列（species_id）だけ split で取る
        # それ以降は正規表現で抽出する
        species_id = line[1:].split(",", 1)[0].strip()

        # fast_moves と charge_moves を抽出
        m = fast_re.search(line)
        if not m:
            continue

        fast_moves_raw = m.group(1)
        charge_moves_raw = m.group(2)

        fast_moves = [x.strip() for x in fast_moves_raw.split(",") if x.strip()]
        charge_moves = [x.strip() for x in charge_moves_raw.split(",") if x.strip()]

        moves = fast_moves + charge_moves

        if line.startswith("-"):
            before[species_id] = moves
        else:
            after[species_id] = moves

    # 差分を比較
    added = {}
    removed = {}

    for sid in before:
        if sid not in after:
            continue

        b = set(before[sid])
        a = set(after[sid])

        add = list(a - b)
        rem = list(b - a)

        if add:
            added[sid] = add
        if rem:
            removed[sid] = rem

    return added, removed

def find_pokemon_using_moves(species_df, move_list):
    """
    species.csv から、指定された技を覚えるポケモン一覧を返す
    """
    results = []

    for _, mc in move_list.iterrows():
        move = mc["move"]

        affected = species_df[
            species_df["fast_moves"].str.contains(move)
            | species_df["charge_moves"].str.contains(move)
            | species_df["elitefast"].str.contains(move)
            | species_df["elitecharge"].str.contains(move)
        ]

        for _, row in affected.iterrows():
            results.append({
                "species_id": row["species_id"],
                "name_ja": row["name_ja"],
                "move_name_ja": mc["move_name_ja"],
                "desc": mc["desc"],
                "score": mc["score"],
            })

    return pd.DataFrame(results)

def build_added_moves(species_df, added_moves_dict):
    moves_df = load_moves()
    rows = []

    for sid, moves in added_moves_dict.items():
        sp = species_df[species_df["species_id"] == sid]
        if sp.empty:
            print(f"{sid} が存在しません")
            continue

        row = sp.iloc[0]

        for move in moves:
            move_name_ja = moves_df[moves_df["move_id"] == move]["name_ja"].iloc[0]
            rows.append({
                "species_id": sid,
                "name_ja": row["name_ja"],
                "move_name_ja": move_name_ja,
                "desc": "わざ追加",
                "score": 50,   # 技追加は大強化扱い
            })

    return pd.DataFrame(rows)

# Git の差分を取得
def get_git_diff(commit, filename):
    try:
        diff = subprocess.check_output(
            ["git", "diff", f"{commit}^", commit, "--", filename],            text=True,
            stderr=subprocess.STDOUT
        )
        return diff
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output}"

@st.fragment
# シーズンごとのわざ調整
def render_season_effect():
    st.header("シーズン調整（コミット差分）")

    # コミット選択
    selected_label = st.selectbox("対象コミットを選択", list(SEASON_COMMITS.keys()))
    commit_id = SEASON_COMMITS[selected_label]
    
    st.write(f"対象コミット: `{commit_id}`")

    # diff を取得
    diff_moves = get_git_diff(commit_id, "data/moves.csv")

    # 変更された技を抽出
    changed_moves_df = parse_move_changes(diff_moves)
    with st.expander("変更された技"):
        st.table(changed_moves_df)

    st.subheader("影響を受けるポケモン一覧")
    # --- 技フィルター UI ---
    all_moves = ["すべて", "わざ追加"] + sorted(changed_moves_df["move_name_ja"].unique())
    selected_move = st.selectbox("技で絞り込み", all_moves)

    # --- フィルタ処理 ---
    if selected_move != "すべて":
        filtered_df = changed_moves_df[changed_moves_df["move_name_ja"] == selected_move]
    else:
        filtered_df = changed_moves_df

    # species.csv を読み込み
    species_df = load_species()

    # わざを覚えるポケモンを逆引き
    affected_df = find_pokemon_using_moves(species_df, filtered_df)

    # わざ追加ポケモンを一覧に追加
    # species.csv の diff を取得
    diff_species = get_git_diff(commit_id, "data/species.csv")

    # わざ追加・削除を抽出
    added_moves, removed_moves = parse_species_move_changes(diff_species)

    # わざ追加影響ポケモン一覧
    added_df = build_added_moves(species_df, added_moves)

    # 一覧をフィルター
    if selected_move == "すべて":
        filtered_df = pd.concat([affected_df, added_df])

    elif selected_move == "わざ追加":
        filtered_df = added_df

    else:
        filtered_df = affected_df[affected_df["move_name_ja"] == selected_move]

    # --- わざを覚えるポケモンフィルター UI ---
    all_species = ["すべて"] + sorted(filtered_df["name_ja"].unique())
    selected_sp = st.selectbox("ポケモンで絞り込み", all_species)

    # --- フィルタ処理 ---
    if selected_sp != "すべて":
        filtered_species = filtered_df[filtered_df["name_ja"] == selected_sp]
    else:
        filtered_species = filtered_df

    st.dataframe(filtered_species)
