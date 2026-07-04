import streamlit as st
import pandas as pd

from core.type import type_with_underline
from core.loader import load_species, load_individuals, load_moves
from core.param_calc import calc_level_from_cp, calc_pvp_rank, find_best_level_for_cp1500, calc_cp

@st.fragment
def render_iv_checker():
    st.header("個体値チェッカー")
    
    # CSS 定義
    st.markdown("""
    <style>
    .iv-wrapper {
        position: relative;
        display: inline-block;
        margin: 2px;
    }
    .iv-btn {
        position: absolute;
        top: 0;
        left: 0;
        width: 32px;
        height: 32px;
        opacity: 0;
        z-index: 2;
    }
    .iv-label {
        width: 32px;
        height: 32px;
        border-radius: 4px;
        border: 1px solid #aaa;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #eee;
        z-index: 1;
    }
    .iv-selected {
        background-color: #ffcc80;
        border-color: #cc6600;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    species = load_species()
    moves = load_moves()

    # --- ポケモン検索 ---
    st.subheader("ポケモン検索")
    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input("ポケモン名で検索（部分一致）", key="ivcheck")

        if query:
            candidates = species[
                species["name_ja"].str.contains(query, case=False) |
                species["species_id"].str.contains(query, case=False)
            ]

        else:
            candidates = species

        if len(candidates) == 0:
            st.warning("該当するポケモンがありません")
            st.stop()

        species_ids = candidates["species_id"].tolist()

        # 事前に辞書を作る
        name_map = {
            row["species_id"]: f"{row['name_ja']} ({row['species_id']})"
            for _, row in species.iterrows()
        }

    with col2:
        species_name = st.selectbox(
            "ポケモンを選択",
            species_ids,
            format_func=lambda sid: name_map[sid],
            key="ivchecksel"
        )

        sp = species[species["species_id"] == species_name].iloc[0]

        # タイプ色の下線を付ける
        types = [sp['type1']]
        if not pd.isna(sp['type2']):
            types.append(sp['type2'])
        html = "**タイプ**: " + " / ".join(type_with_underline(t) for t in types)

        st.markdown(html, unsafe_allow_html=True)

    # --- シャドウ/リトレーン ---
    st.subheader("状態")
    is_shadow = st.checkbox("シャドウ", key="shadow_c")
    is_purified = st.checkbox("リトレーン", key="purify_c")

    # --- 個体値 ---
    st.subheader("個体値")

    # 個体値選択用ボタン
    def iv_selector(label, default=15):
        st.write(f"**{label}**")

        # スライダー本体
        value = st.slider(
            label,
            min_value=0,
            max_value=15,
            value=default,
            step=1,
            label_visibility="collapsed"
        )

        # 目盛り表示（CSSで横並び）
        ticks = "".join([f"<span style='margin-right:8px'>{i}</span>" for i in range(16)])
        st.markdown(f"<div style='display:flex; justify-content:space-between; width:100%'>{ticks}</div>", unsafe_allow_html=True)

        return value

    iv_atk = iv_selector("攻撃 IV")
    iv_def = iv_selector("防御 IV")
    iv_sta = iv_selector("HP IV")

    cp_input = st.number_input("表示されている CP", min_value=0, max_value=6000, value=0)
    if cp_input > 0:
        level = calc_level_from_cp(sp["species_id"], iv_atk, iv_def, iv_sta, cp_input, is_shadow)
        st.write(f"推定レベル: **{level}**")
    else:
        level = 0

    rank_1500, rank_2500 = calc_pvp_rank(sp["species_id"], iv_atk, iv_def, iv_sta)
    st.success(f"スーパーリーグランク: **{rank_1500}位**")

    # 進化先がある場合は進化後のCPを計算して表示する
    def write_evo_cp(base_sp):
        if base_sp["evolves_to"]:
            next_forms = base_sp["evolves_to"].split(",")
            for evo in next_forms:
                evo_sp = species[species["species_id"] == evo.strip().lower()].iloc[0]
                evo_atk = evo_sp["base_atk"]
                evo_def = evo_sp["base_def"]
                evo_sta = evo_sp["base_sta"]
                if level > 0:
                    evo_cp = calc_cp(evo_atk, evo_def, evo_sta, iv_atk, iv_def, iv_sta, level)
                else:
                    evo_cp = "-"

                evo_best_level, evo_best_cp, evo_best_hp = find_best_level_for_cp1500(
                    evo_atk, evo_def, evo_sta,
                    iv_atk, iv_def, iv_sta, is_shadow
                )
                evo_rank_1500, evo_rank_2500 = calc_pvp_rank(evo.strip().lower(), iv_atk, iv_def, iv_sta)
                st.success(f'{evo_sp["name_ja"]} に進化した場合の推定CP: **{evo_cp}** / スーパーリーグ用 CP {evo_best_cp} / LV {evo_best_level} ({evo_rank_1500}位)')

    # 進化後のCPを表示
    write_evo_cp(sp)
    
    # 2進化先のCPも表示
    if sp["evolves_to"]:
        next_evo_forms = sp["evolves_to"].split(",")
        for evo in next_evo_forms:
            evo_sps = species[species["species_id"] == evo.strip().lower()].iloc[0]
            write_evo_cp(evo_sps)


