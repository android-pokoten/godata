import streamlit as st
import pandas as pd
import numpy as np

from core.header import render_header
from core.type import ja_to_en_type
from core.loader import load_species, load_opponents
from core.param_calc import generate_template_individual

from core.logic.type_matchup import calc_type_relations
from core.logic.moves import calc_fastmove_list, calc_chargemove_list
from core.logic.stats import calc_indivisuals_stats, load_notes, save_note
from core.style.type_matchup_style import style_type_relations
from core.style.stats_style import type_with_underline, highlight_legacy, highlight_stab, render_charge_gauge, draw_types

### メイン処理
def main():
    render_header()

    render_detail()

@st.fragment
def render_detail():
    st.header("ポケモン詳細")

    species = load_species()

    # 検索欄
    query = st.text_input(
        "ポケモン名で検索（日本語・英語どちらでも）",
        value=initial_query
    )
    
    # 絞り込み
    if query:
        filtered = species[
            species["name_ja"].str.contains(query, case=False) |
            species["species_id"].str.contains(query, case=False)
        ]
    else:
        filtered = species

    if len(filtered) == 0:
        st.warning("該当するポケモンがありません")
        st.stop()

    # species_id を選択
    species_ids = filtered["species_id"].tolist()

    # 事前に辞書を作る
    name_map = {
        row["species_id"]: f"{row['name_ja']} ({row['species_id']})"
        for _, row in species.iterrows()
    }

    selected = st.selectbox(
        "リージョン、フォルムなどを選択",
        species_ids,
        format_func=lambda sid: name_map[sid]
    )

    # 種族データ
    sp = species[species["species_id"] == selected].iloc[0]

    # タイプ色の下線を付ける
    html1 = f"**タイプ1:** {type_with_underline(sp['type1'])}"
    if not pd.isna(sp['type2']):
        html2 = f"**タイプ2:** {type_with_underline(sp['type2'])}"
    else:
        html2 = f"**タイプ2:**"

    #st.subheader("基本データ")
    with st.expander("基本データ"):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**種族 ID:** {sp['species_id']}")
            st.write(f"**名前:** {sp['name_ja']}")
            st.markdown(html1, unsafe_allow_html=True)
            st.markdown(html2, unsafe_allow_html=True)

        with col2:
            st.write(f"**図鑑番号:** {int(sp['dex']):04d}")
            st.write(f"**攻撃種族値:** {sp['base_atk']}")
            st.write(f"**防御種族値:** {sp['base_def']}")
            st.write(f"**ＨＰ種族値:** {sp['base_sta']}")

        st.subheader("進化")
        col1, col2 = st.columns(2)

        with col1:
            st.write("進化前＜＜")
            if sp["evolves_from"]:
                st.code(f'{species[species["species_id"] == sp["evolves_from"].lower()].iloc[0]["name_ja"]}')

        with col2:
            st.write("＞＞進化先")
            if sp["evolves_to"]:
                next_forms = sp["evolves_to"].split(",")
                for evo in next_forms:
                    evo = species[species["species_id"] == evo.strip().lower()].iloc[0]["name_ja"]
                    st.code(f"{evo}")

    # タイプ相性
    st.markdown("### タイプ相性まとめ")
    type_df = calc_type_relations(sp["type1"], sp["type2"])
    styled_type_df = style_type_relations(type_df)
    st.table(styled_type_df)

    # 技データ
    st.subheader("わざ")

    # わざリストを作成
    fast_move_list = calc_fastmove_list(sp)
    charge_moves = calc_chargemove_list(sp)

    st.write("### ノーマルわざ")
    cols = ["power_stab", "energy", "turns", "dpt", "ept"]
    for c in cols:
        fast_move_list[c] = fast_move_list[c].map(lambda x: f"{x: .1f}")
    
    st.table(fast_move_list[[
        "move_id",
        "name_ja",
        "type",
        "power_stab",
        "energy",
        "turns",
        "dpt",
        "ept",
        "一致",
        ]].style.apply(lambda row: highlight_legacy(row), axis=1)
        .apply(highlight_stab, axis=1)
        )

    st.write("### スペシャルわざ")
    cols = ["power_stab", "energy", "dpe"]
    for c in cols:
        charge_moves[c] = charge_moves[c].map(lambda x: f"{x: .1f}")
    
    st.table(charge_moves[[
        "move_id",
        "name_ja",
        "type",
        "power_stab",
        "energy",
        "dpe",
        "一致",
        ]].style.apply(lambda row: highlight_legacy(row), axis=1)
        .apply(highlight_stab, axis=1)
        )

    st.markdown("わざ名の＊はコミュニティデイなどで覚えるわざ")

    # 個体データ
    st.subheader("手持ち個体一覧")

    indiv = calc_indivisuals_stats(selected, fast_move_list, charge_moves)
    # 手持ちが居ない場合は処理をスキップ
    if not indiv is None:
        NUM_COLS = 3
        cols = st.columns(NUM_COLS)

        for i, (_, row) in enumerate(indiv.iterrows()):
            col = cols[i % NUM_COLS]

            with col:
                st.write(f"{row["individual_id"]}")
                st.write(f"CP: **{row["CP"]}** / SCP: **{row["SCP"]}**")
                st.write(f"HP: **{row["HP"]}**")
                st.write(f"個体値: **{row["iv_atk"]}** / **{row["iv_def"]}** / **{row["iv_sta"]}**")

                # わざ未登録のデータがある場合はわざデータ処理をスキップ
                if not pd.isna(row["fast_move_ja"]):
                    # ノーマルわざ
                    st.markdown(draw_types(
                        ja_to_en_type(row["fast_move_type"]), 
                        row["fast_move_ja"], 
                        row["fast_move_text"]
                        ), unsafe_allow_html=True
                    )
                    # チャージわざ1
                    st.markdown(draw_types(
                        ja_to_en_type(row["charge_move1_type"]), 
                        row["charge_move1_ja"], 
                        row["charge_move1_text"]), unsafe_allow_html=True
                    )
                    st.markdown(render_charge_gauge(
                        row["fast_energy"], 
                        row["fast_turns"],
                        row["charge1_energy"], 
                        ja_to_en_type(row["fast_move_type"]), 
                        ja_to_en_type(row["charge_move1_type"])), unsafe_allow_html=True
                    )
                    # チャージわざ2
                    st.markdown(draw_types(
                        ja_to_en_type(row["charge_move2_type"]), 
                        row["charge_move2_ja"], 
                        row["charge_move2_text"]), unsafe_allow_html=True
                    )
                    st.markdown(render_charge_gauge(
                        row["fast_energy"], 
                        row["fast_turns"],
                        row["charge2_energy"], 
                        ja_to_en_type(row["fast_move_type"]), 
                        ja_to_en_type(row["charge_move2_type"])), unsafe_allow_html=True
                    )

                # 既存メモを取得
                sid = row["individual_id"]
                memo_text = load_notes(sid)

                # メモ入力欄
                memo = st.text_area("メモ（100文字まで）", memo_text, max_chars=100, key=f"{sid}_txt")

                # メモ保存ボタン
                if st.button("メモを保存", key=f"{sid}_but"):
                    save_note(sid, memo)
                    st.success("保存しました！")


    # テンプレ個体データ
    opponents = load_opponents()
    oppos = opponents[opponents["species_id"] == selected].copy()

    if len(oppos) == 0:
        if st.button("このポケモンのテンプレ個体を生成"):
            #sp = species_row  # detailタブで選択中のポケモン

            row = generate_template_individual(sp["species_id"], sp)

            st.code(",".join(str(v) for v in row.values()), language="text")
    else:
        st.subheader("テンプレ個体")
        st.table(oppos[[
            "individual_id", "fast_move", "charge_move1", "charge_move2",
            "iv_atk", "iv_def", "iv_sta", "level"
        ]], width='stretch')


if __name__ == "__main__":
    main()
