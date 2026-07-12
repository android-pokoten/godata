import streamlit as st
import pandas as pd
import math

from tabs.register import render_register
from tabs.max_cp1500 import render_max1500

from core.cpm import CPM
from core.type import TYPE_CHART, type_with_underline
from core.param_calc import compute_cp_row, compute_scp_row, compute_hp_row
from core.loader import load_species, load_moves, load_individuals

from tabs.cup_filter import render_cup_filter
from tabs.edit import render_editer

def calc_stats(species_row, iv_atk, iv_def, iv_sta, level):
    cpm = CPM[level]

    atk = (species_row["base_atk"] + iv_atk) * cpm
    defense = (species_row["base_def"] + iv_def) * cpm
    stamina = math.floor((species_row["base_sta"] + iv_sta) * cpm)

    return atk, defense, stamina

# タイプ相性判定
def get_multiplier(move_type, target_types):
    mult = 1.0
    for t in target_types:
        mult *= TYPE_CHART.get(move_type, {}).get(t, 1.0)
    return mult

# サブタブ表示
@st.fragment
def render_individuals():
    # タブ切り替え
    tabs = {
        "手持ち一覧": render_individuals_list,
        "手持ち登録": render_register, 
        "CP1,500調整": render_max1500, 
        "対面評価": render_matchup_tab,
        "特殊カップ": render_cup_filter,
        "手持ちデータ修正": render_iv_editor, 
    }

    tab_objects = st.tabs(list(tabs.keys()))

    for tab_obj, (name, func) in zip(tab_objects, tabs.items()):
        with tab_obj:
            func()


# 手持ち一覧
def render_individuals_list():
    st.header("手持ち個体一覧")

    individuals = load_individuals()

    # CP 計算
    individuals["CP"] = individuals.apply(compute_cp_row, axis=1)

    # SCP計算
    individuals["SCP"] = individuals.apply(compute_scp_row, axis=1)

    # HP 計算
    individuals["HP"] = individuals.apply(compute_hp_row, axis=1)

    st.dataframe(individuals, width='stretch')

# 対面評価
def render_matchup_tab():
    st.subheader("対面評価（簡易版）")

    species = load_species()
    moves = load_moves()
    individuals = load_individuals()

    # -----------------------------
    # 相手ポケモン検索
    # -----------------------------
    query = st.text_input("相手ポケモン名で検索（部分一致）")

    if query:
        candidates = species[species["name_ja"].str.contains(query)]
    else:
        candidates = species

    if len(candidates) == 0:
        st.warning("該当するポケモンが見つかりませんでした。")
        st.stop()

    # name_ja(species_id) 形式で表示
    def fmt(sid):
        row = species.loc[species["species_id"] == sid].iloc[0]
        return f"{row['name_ja']} ({sid})"

    species_ids = candidates["species_id"].tolist()

    selected_sid = st.selectbox(
        "相手ポケモンを選択",
        species_ids,
        format_func=fmt
    )

    target = species[species["species_id"] == selected_sid].iloc[0]
    st.write(f"### 対象: {target['name_ja']} ({target['species_id']})")

    # タイプ色の下線を付ける
    target_types = [target['type1']]
    if not pd.isna(target['type2']):
        target_types.append(target['type2'])
    html = "タイプ: " + " / ".join(type_with_underline(t) for t in target_types)

    st.markdown(html, unsafe_allow_html=True)

    # 相手の技タイプ一覧（簡易版）
    target_fast = target["fast_moves"].split(",") if target["fast_moves"] else []
    target_charge = target["charge_moves"].split(",") if target["charge_moves"] else []

    target_move_types = set()

    for mid in target_fast + target_charge:
        if mid == "":
            continue
        m = moves[moves["move_id"] == mid].iloc[0]
        target_move_types.add(m["type"])

    html = "想定わざタイプ: " + ", ".join(type_with_underline(t) for t in target_move_types)

    st.markdown(html, unsafe_allow_html=True)

    # -----------------------------
    # 手持ち評価
    # -----------------------------
    results = []

    for _, row in individuals.iterrows():
        sp = species[species["species_id"] == row["species_id"]].iloc[0]

        # --- 技相性スコア ---
        score_moves = 0

        # 通常技
        fm_id = row["fast_move"]
        fm_id = str(fm_id).strip()
        if fm_id != "" and fm_id.lower() != "nan":
            fm = moves[moves["move_id"] == fm_id].iloc[0]
            fm_mult = get_multiplier(fm["type"], target_types)

            if fm_mult > 1.0:
                score_moves += 2
            elif fm_mult == 1.0:
                score_moves += 1

        # ゲージ技
        charge_mults = []

        for cm_id in [row["charge_move1"], row["charge_move2"]]:
            cm_id = str(cm_id).strip()
            if cm_id == "" or cm_id.lower() == "nan":
                continue
            cm = moves[moves["move_id"] == cm_id].iloc[0]
            charge_mults.append(get_multiplier(cm["type"], target_types))

        best_charge_mult = max(charge_mults) if charge_mults else 1.0

        if best_charge_mult > 1.0:
            score_moves += 2
        elif best_charge_mult == 1.0:
            score_moves += 1

        # --- 耐性スコア ---
        score_resist = 0
        for t in target_move_types:
            if TYPE_CHART.get(t, {}).get(sp["type1"], 1.0) < 1.0 or \
               TYPE_CHART.get(t, {}).get(sp["type2"], 1.0) < 1.0:
                score_resist += 1
                break

        # --- 実数値スコア ---
        atk, defense, stamina = calc_stats(
            sp,
            row["iv_atk"],
            row["iv_def"],
            row["iv_sta"],
            row["level"]
        )
        bulk = defense * stamina

        if bulk > 20000:
            score_bulk = 2
        elif bulk > 15000:
            score_bulk = 1
        else:
            score_bulk = 0

        total_score = score_moves + score_resist + score_bulk

        results.append({
            "name": sp["name_ja"],
            "nickname": row["nickname"],
            "level": row["level"],
            "fast_move": row["fast_move"],
            "charge1": row["charge_move1"],
            "charge2": row["charge_move2"],
            "bulk": bulk,
            "score": total_score,
            "(moves)": score_moves,
            "(resist)": score_resist,
            "(bulk)": score_bulk,
        })
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values("score", ascending=False)

        st.write("### 手持ちの中で有利な順ランキング")
        st.dataframe(df, width='stretch')

# 手持ちデータ修正
@st.fragment
def render_iv_editor():
    csv_files = {
        "個体データ (individuals.csv)": "data/individuals.csv",
    }

    render_editer(csv_files)
    