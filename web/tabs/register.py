import streamlit as st
import pandas as pd

from core.type import type_with_underline
from core.loader import load_species, load_individuals, load_moves
from core.param_calc import calc_level_from_cp, calc_pvp_rank, find_best_level_for_cp1500, calc_cp

@st.fragment
def render_register():
    st.header("個体登録")

    species = load_species()
    moves = load_moves()

    # --- ポケモン検索 ---
    st.subheader("ポケモン検索")
    query = st.text_input("ポケモン名で検索（部分一致）")

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
    fast_move = st.selectbox("通常技", fast_df["name_ja"].tolist())
    fast_move_id = fast_df[fast_df["name_ja"] == fast_move].iloc[0]["move_id"]

    charge_list = sp["charge_moves"].split(",") if sp["charge_moves"] else []
    elite_charge_list = sp["elitecharge"].split(",") if sp["elitecharge"] else []
    charge_list += elite_charge_list
    charge_df = moves[moves["move_id"].isin(charge_list)]
    charge_moves_selected = st.multiselect(
        "ゲージ技（最大2つ）",
        charge_df["name_ja"].tolist(),
        max_selections=2
    )

    charge_move_ids = []
    for name in charge_moves_selected:
        charge_move_ids.append(charge_df[charge_df["name_ja"] == name].iloc[0]["move_id"])

    # --- 個体値 ---
    st.subheader("個体値")

    # 個体値選択用ボタン
    def iv_selector(label, default=15):
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.write(f"**{label}**")

        with col2:
            selected = st.session_state.get(f"iv_{label}", default)
            cols = st.columns(16)

            for i in range(16):
                key = f"{label}_{i}"
                # i が selected 以下ならオレンジ色
                css_class = "primary" if i <= selected else "secondary"

                if cols[i].button(
                    str(i),
                    key=key,
                    help=f"{label} = {i}",
                    type=css_class
                ):
                    st.session_state[f"iv_{label}"] = i
                    selected = i

        return selected

    col1, col2, col3 = st.columns(3)
    with col1:
        iv_atk = st.selectbox(
                "攻撃個体値",
                range(16)
            )

    with col2:
        iv_def =  st.selectbox(
                "防御個体値",
                range(16)
            )

    with col3:
        iv_sta = st.selectbox(
                "HP個体値",
                range(16)
            )

    # --- レベル ---
    st.subheader("レベル")
    level = st.slider("レベル", 1.0, 50.0, 40.0, step=0.5)

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

    # --- シャドウ/リトレーン ---
    st.subheader("状態")
    is_shadow = st.checkbox("シャドウ")
    is_purified = st.checkbox("リトレーン")

    # --- ニックネーム ---
    nickname = st.text_input("個体ID")

    # --- 登録行生成 ---
    if st.button("登録行を生成"):
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

        df = pd.DataFrame([row])
        st.subheader("CSV 追記用データ")
        st.dataframe(df)

        st.code(",".join(str(v) for v in row.values()), language="text")
