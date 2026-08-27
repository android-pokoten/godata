import streamlit as st
import pandas as pd
from urllib.parse import unquote

from core.header import render_header
from core.type import type_with_underline
from core.loader import load_species, load_individuals, load_moves
from core.param_calc import calc_level_from_cp, calc_pvp_rank, find_best_level_for_cp1500, calc_cp

from core.logic.utils import save_new_individual, update_individual

### メイン処理
def main():
    render_header()

    render_register()

@st.fragment
def render_register():
    species = load_species()
    moves = load_moves()
    individuals = load_individuals()

    st.header("個体登録")
    # species=[str] でポケモンから登録する
    # ivid=[str] で個体データの編集
    # 指定しない場合は新規登録

    params = st.query_params
    sp_id = params.get("species", None)
    iv_id = params.get("ivid", None)

    if sp_id:
        # ポケモンから登録の場合
        row = species[species["species_id"] == sp_id]
        if not row.empty:
            data = row.iloc[0]
            initial_query = data["species_id"]
            iv_data = None
    elif iv_id:
        # 個体から登録の場合
        # URLエンコードされているので、デコードする
        iv_id = unquote(iv_id)
        iv_row = individuals[individuals["individual_id"] == iv_id]
        if not iv_row.empty:
            iv_data = iv_row.iloc[0]
            # 個体のデータを準備
            initial_query = iv_data["species_id"]
            #iv_fast_move_ja = moves[moves["move_id"] == iv_data["fast_move"]].iloc[0]["name_ja"] if iv_data["fast_move"] else ""
            try:
                iv_fast_move_ja = moves[moves["move_id"] == iv_data["fast_move"]].iloc[0]["name_ja"]
            except IndexError:
                iv_fast_move_ja = ""
            iv_charge_move_ja = []
            try:
                iv_charge_move_ja.append(moves[moves["move_id"] == iv_data["charge_move1"]].iloc[0]["name_ja"])
                iv_charge_move_ja.append(moves[moves["move_id"] == iv_data["charge_move2"]].iloc[0]["name_ja"])
            except IndexError:
                pass

            row = species[species["species_id"] == initial_query]
    else:
        data = None
        initial_query = None
        iv_data = None

    # --- ポケモン検索 ---
    st.subheader("ポケモン検索")
    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input(
            "ポケモン名で検索（部分一致）",
            value=initial_query
        )

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
            format_func=lambda sid: name_map[sid]
        )

    sp = species[species["species_id"] == species_name].iloc[0]

    # タイプ色の下線を付ける
    types = [sp['type1']]
    if not pd.isna(sp['type2']):
        types.append(sp['type2'])
    html = "**タイプ**: " + " / ".join(type_with_underline(t) for t in types)

    st.markdown(html, unsafe_allow_html=True)

    # --- 技選択 ---
    st.subheader("技選択")

    fast_list = sp["fast_moves"].split(",") if sp["fast_moves"] else []
    elite_fast_list = sp["elitefast"].split(",") if sp["elitefast"] else []
    fast_list += elite_fast_list
    fast_df = moves[moves["move_id"].isin(fast_list)]
    fast_names = fast_df["name_ja"].tolist()
    # 編集モードの時は個体のわざを選択状態にする
    if iv_data is not None:
        try:
            fast_index = fast_names.index(iv_fast_move_ja)
        except ValueError:
            fast_index = 0
    else:
        fast_index = 0

    fast_move = st.selectbox(
        "通常技",
        fast_names,
        index=fast_index
        )
    fast_move_id = fast_df[fast_df["name_ja"] == fast_move].iloc[0]["move_id"]

    charge_list = sp["charge_moves"].split(",") if sp["charge_moves"] else []
    elite_charge_list = sp["elitecharge"].split(",") if sp["elitecharge"] else []
    charge_list += elite_charge_list
    charge_df = moves[moves["move_id"].isin(charge_list)]
    charge_moves_selected = st.multiselect(
        "ゲージ技（最大2つ）",
        charge_df["name_ja"].tolist(),
        max_selections=2,
        default=iv_charge_move_ja if iv_data is not None else []
    )

    charge_move_ids = []
    for name in charge_moves_selected:
        charge_move_ids.append(charge_df[charge_df["name_ja"] == name].iloc[0]["move_id"])

    # --- シャドウ/リトレーン ---
    st.subheader("状態")
    is_shadow = st.checkbox(
        "シャドウ",
        key="is_shadow_regist",
        value=iv_data["is_shadow"] if iv_data is not None else False
        )
    is_purified = st.checkbox(
        "リトレーン",
        key="is_purify_regist",
        value=iv_data["is_purified"] if iv_data is not None else False
        )

    # --- 個体値 ---
    st.subheader("個体値")

    col1, col2, col3 = st.columns(3)
    with col1:
        iv_atk = st.selectbox(
                "攻撃個体値",
                range(16),
                index=int(iv_data["iv_atk"] if iv_data is not None else 0)
            )

    with col2:
        iv_def =  st.selectbox(
                "防御個体値",
                range(16),
                index=int(iv_data["iv_def"] if iv_data is not None else 0)
            )

    with col3:
        iv_sta = st.selectbox(
                "HP個体値",
                range(16),
                index=int(iv_data["iv_sta"] if iv_data is not None else 0)
            )

    # --- レベル ---
    st.subheader("レベル")
    level = st.slider(
        "レベル",
        1.0,
        50.0,
        value=iv_data["level"] if iv_data is not None else 40.0,
        step=0.5,
        )

    # --- CPからレベルを計算 ---
    cp_input = st.number_input("CP (レベル逆算する場合)", min_value=0, max_value=6000, value=0)
    if cp_input > 0:
        level = calc_level_from_cp(sp["species_id"], iv_atk, iv_def, iv_sta, cp_input)
        st.write(f"推定レベル: **{level}**")

    # --- 個体値からCP1500に最も近いレベルを求める
    if st.button("CP1500 に最も近いレベルを計算"):
        base_atk = sp["base_atk"]
        base_def = sp["base_def"]
        base_sta = sp["base_sta"]

        best_level, best_cp, best_hp = find_best_level_for_cp1500(
            base_atk, base_def, base_sta,
            iv_atk, iv_def, iv_sta
        )
        st.success(F"最適レベル: {best_level} / CP: {best_cp}")

    # --- ニックネーム ---
    nickname = st.text_input(
        "個体ID",
        value=iv_data["individual_id"] if iv_data is not None else ""
        )

    # --- 保存処理 ---
    if 'reg_confirm_update' not in st.session_state:
        st.session_state["reg_confirm_update"] = False

    if st.button("登録行生成", key="update_button"):
        row = {
            "individual_id": nickname,
            "species_id": sp["species_id"],
            "nickname": "",
            "iv_atk": iv_atk,
            "iv_def": iv_def,
            "iv_sta": iv_sta,
            "level": level,
            "fast_move": fast_move_id,
            "charge_move1": charge_move_ids[0] if len(charge_move_ids) > 0 else "",
            "charge_move2": charge_move_ids[1] if len(charge_move_ids) > 1 else "",
            "is_shadow": is_shadow,
            "is_purified": is_purified,
        }

        st.session_state.reg_confirm_update = row

        st.code(",".join(str(v) for v in row.values()), language="text")

    if st.button("個体を保存", key="save_button"):
        if not st.session_state.get("reg_confirm_update", False):
            # 登録業を生成していない場合は登録しない
            st.warning("最初に登録行を生成してください")
        elif len(nickname) < 1:
            # 個体IDはIDとして使用するため、空欄の場合は登録しない
            st.warning("個体IDを入力してください")
        else:
            row = st.session_state.get("reg_confirm_update", False)
            if iv_data is None:
                save_new_individual(row)
            else:
                update_individual(nickname, row)

            st.session_state["reg_confirm_update"] = False
            st.success("保存しました")

if __name__ == "__main__":
    main()
