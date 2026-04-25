import streamlit as st
import pandas as pd

from core.cpm import CPM
from core.type import TYPE_CHART, TYPE_JA
from core.param_calc import compute_cp_row, compute_scp_row, compute_hp_row
from core.loader import load_species, load_moves, load_individuals


individuals = load_individuals()
moves = load_moves()
species = load_species()
# CP,SCP,HP を追加
individuals["CP"] = individuals.apply(compute_cp_row, axis=1)
individuals["SCP"] = individuals.apply(compute_scp_row, axis=1)
individuals["HP"] = individuals.apply(compute_hp_row, axis=1)

# ポケモンのタイプ、世代を付与
individuals = individuals.merge(
    species[["species_id", "type1", "type2", "generation"]],
    on="species_id",
    how="left"
)

# 日本語タイプ列を追加
individuals["type1_ja"] = individuals["type1"].map(TYPE_JA)
individuals["type2_ja"] = individuals["type2"].map(TYPE_JA)

# fast_move のタイプを付与
individuals["fast_move"] = individuals["fast_move"].fillna("")
df_fast = individuals.merge(
    moves[["move_id", "type", "name_ja"]].rename(columns={"move_id": "fast_move", "type": "fast_type", "name_ja": "fast_ja"}),
    on="fast_move",
    how="left"
)
df_fast["fast_type_ja"] = df_fast["fast_type"].map(TYPE_JA)

# charge_move1 のタイプを付与
df_fast["charge_move1"] = df_fast["charge_move1"].fillna("")
df_charge1 = df_fast.merge(
    moves[["move_id", "type", "name_ja"]].rename(columns={"move_id": "charge_move1", "type": "charge1_type", "name_ja": "charge1_ja"}),
    on="charge_move1",
    how="left"
)
df_charge1["charge1_type_ja"] = df_charge1["charge1_type"].map(TYPE_JA)

# charge_move2 のタイプを付与
df_charge1["charge_move2"] = df_charge1["charge_move2"].fillna("")
individuals = df_charge1.merge(
    moves[["move_id", "type", "name_ja"]].rename(columns={"move_id": "charge_move2", "type": "charge2_type", "name_ja": "charge2_ja"}),
    on="charge_move2",
    how="left"
)
individuals["charge2_type_ja"] = individuals["charge2_type"].map(TYPE_JA)


# サブタブ表示
@st.fragment
def render_cup_filter():
    tabs = {
        "ジャングルカップ": render_jungle_filter,
        "でんきカップ": render_electro_filter,
        "ファンタジーカップ": render_fantasy_filter,
        "春カップ": render_spring_filter, 
        "カントーカップ": render_kanto_filter, 
    }

    tab_objects = st.tabs(list(tabs.keys()))

    for tab_obj, (name, func) in zip(tab_objects, tabs.items()):
        with tab_obj:
            func()


def cup_filter_common(target_types, banned_types, banned_sp):
    species = load_species()
    
    # 出場可能タイプが指定されている場合、タイプでフィルター
    # 空の場合は全タイプ対象としてフィルターをスキップ
    if len(target_types) > 0:
        species = species[
            species["type1"].isin(target_types) |
            species["type2"].isin(target_types)
        ]

    # 出場不可タイプが指定されている場合、タイプでフィルター
    species = species[
        ~species["type1"].isin(banned_types) |
        ~species["type2"].isin(banned_types)
    ]

    # 出場不可ポケモンが指定されている場合、ポケモン名でフィルター
    species = species[
        ~species["species_id"].isin(banned_sp)
    ]

    # individuals のリストをフィルターした結果を返す
    target_species_ids = species["species_id"].tolist()
    target_ivs = individuals[individuals["species_id"].isin(target_species_ids)]

    all_types = sorted(
        set(target_ivs["type1_ja"].dropna().unique()) |
        set(target_ivs["type2_ja"].dropna().unique())
    )
    all_move_types = sorted(
        set(target_ivs["fast_type_ja"].dropna()) |
        set(target_ivs["charge1_type_ja"].dropna()) |
        set(target_ivs["charge2_type_ja"].dropna())
    )

    return target_ivs, all_types, all_move_types

# 絞り込み
def filter_type_common(label_id, target_ivs, all_types, all_move_types):
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_types = st.multiselect("タイプで絞り込み", all_types, key=f"ftype_{label_id}")

    with col2:
        selected_move_types = st.multiselect("わざタイプで絞り込み", all_move_types, key=f"fmtype_{label_id}")

    with col3:
        move_keyword = st.text_input("わざ名（部分一致）", key=f"fmove_{label_id}")

    # タイプフィルタ
    if selected_types:
        target_ivs = target_ivs[
            target_ivs["type1_ja"].isin(selected_types) |
            target_ivs["type2_ja"].isin(selected_types)
        ]

    # 技タイプフィルタ
    if selected_move_types:
        target_ivs = target_ivs[
            target_ivs["fast_type_ja"].isin(selected_move_types) |
            target_ivs["charge1_type_ja"].isin(selected_move_types) |
            target_ivs["charge2_type_ja"].isin(selected_move_types)
        ]

    # わざ名フィルタ
    if move_keyword:
        target_ivs = target_ivs[
            target_ivs["fast_ja"].str.contains(move_keyword, case=False, na=False) |
            target_ivs["charge1_ja"].str.contains(move_keyword, case=False, na=False) |
            target_ivs["charge2_ja"].str.contains(move_keyword, case=False, na=False)
        ]

    return target_ivs

# ジャングルカップ
def render_jungle_filter():
    st.header("ジャングルカップ出場可能ポケモン")

    st.markdown("""
    ### 🏞 ジャングルカップ出場条件

    - **CP1500 以下**
    - **使用可能タイプ：**
    - ノーマル / くさ / でんき / どく / じめん / ひこう / むし / あく
    - **使用禁止タイプ：**
    - (なし)
    - **使用不可**
    - (なし)
    """)

    # カップ対象タイプ
    target_types = ["normal", "grass", "electric", "poison", "ground", "flying", "bug", "dark"]

    # 出場不可タイプ
    banned_type = []

    # 使用不可
    banned_ids = []

    target_individuals, all_types, all_move_types = cup_filter_common(target_types, banned_type, banned_ids)

    st.subheader("出場可能な手持ち一覧")
    # フィルター
    ivs = filter_type_common("jungle", target_individuals, all_types, all_move_types)

    st.dataframe(ivs[[
        "individual_id", "iv_atk", "iv_def", "iv_sta", "level",
        "is_shadow", "is_purified", "CP", "SCP", "HP",
        "type1_ja", "type2_ja",
        "fast_ja", "fast_type_ja", "charge1_ja", "charge1_type_ja", "charge2_ja", "charge2_type_ja"
    ]].sort_values("individual_id"), width='stretch')

# でんきカップ
def render_electro_filter():
    st.header("でんきカップ出場可能ポケモン")

    st.markdown("""
    ### ⚡ でんきカップ出場条件

    - **CP1500 以下**
    - **使用可能タイプ：**
    - でんき
    - **使用禁止タイプ：**
    - (なし)
    - **使用不可**
    - マッギョ/エレザード/デンヂムシ/クワガノン
    """)

    # カップ対象タイプ
    target_types = ["electric"]

    # 出場不可タイプ
    banned_type = []

    # 使用不可
    banned_ids = ["stunfisk", "heliolisk", "charjabug", "vikavolt"]

    target_individuals, all_types, all_move_types = cup_filter_common(target_types, banned_type, banned_ids)

    st.subheader("出場可能な手持ち一覧")
    # フィルター
    ivs = filter_type_common("electro", target_individuals, all_types, all_move_types)

    st.dataframe(ivs[[
        "individual_id", "iv_atk", "iv_def", "iv_sta", "level",
        "is_shadow", "is_purified", "CP", "SCP", "HP",
        "type1_ja", "type2_ja",
        "fast_ja", "fast_type_ja", "charge1_ja", "charge1_type_ja", "charge2_ja", "charge2_type_ja"
    ]].sort_values("individual_id"), width='stretch')

# ファンタジーカップ
def render_fantasy_filter():
    st.header("ファンタジーカップ出場可能ポケモン")

    st.markdown("""
    ### 🧚 ファンタジーカップ出場条件

    - **CP1500 以下**
    - **使用可能タイプ：**
    - はがね / フェアリー / ドラゴン
    - **使用禁止タイプ：**
    - (なし)
    - **使用不可**
    - (なし)
    """)

    # カップ対象タイプ
    target_types = ["steel", "fairy", "dragon"]

    # 出場不可タイプ
    banned_type = []

    # 使用不可
    banned_ids = []

    target_individuals, all_types, all_move_types = cup_filter_common(target_types, banned_type, banned_ids)

    st.subheader("出場可能な手持ち一覧")
    # フィルター
    ivs = filter_type_common("fantasy", target_individuals, all_types, all_move_types)

    st.dataframe(ivs[[
        "individual_id", "iv_atk", "iv_def", "iv_sta", "level",
        "is_shadow", "is_purified", "CP", "SCP", "HP",
        "type1_ja", "type2_ja",
        "fast_ja", "fast_type_ja", "charge1_ja", "charge1_type_ja", "charge2_ja", "charge2_type_ja"
    ]].sort_values("individual_id"), width='stretch')

# 春カップ
def render_spring_filter():
    st.header("春カップ出場可能ポケモン")

    st.markdown("""
    ### 春カップ出場条件

    - **CP1500 以下**
    - **使用可能タイプ：**
    - みず / くさ / フェアリー
    - **使用禁止タイプ：**
    - (なし)
    - **使用不可**
    - ワタッコ / ロズレイド / ドヒドイデ
    """)

    # カップ対象タイプ
    target_types = ["water", "fairy", "grass"]

    # 出場不可タイプ
    banned_type = []

    # 使用不可
    banned_ids = ["jumpluff", "roserade", "toxapex"]

    target_individuals, all_types, all_move_types = cup_filter_common(target_types, banned_type, banned_ids)

    st.subheader("出場可能な手持ち一覧")
    # フィルター
    ivs = filter_type_common("spring", target_individuals, all_types, all_move_types)

    st.dataframe(ivs[[
        "individual_id", "iv_atk", "iv_def", "iv_sta", "level",
        "is_shadow", "is_purified", "CP", "SCP", "HP",
        "type1_ja", "type2_ja",
        "fast_ja", "fast_type_ja", "charge1_ja", "charge1_type_ja", "charge2_ja", "charge2_type_ja"
    ]].sort_values("individual_id"), width='stretch')


# カントーカップ
def render_kanto_filter():
    st.header("カントーカップ出場可能ポケモン")

    st.markdown("""
    ### カントーカップ出場条件

    - **CP1500 以下**
    - 図鑑番号：001 から 151 のポケモンが参加可能
    - **使用可能タイプ：**
    - すべて
    - **使用禁止タイプ：**
    - (なし)
    - **使用不可**
    - (なし)
    """)

    # カップ対象タイプ
    target_types = []

    # 出場不可タイプ
    banned_type = []

    # 使用不可
    banned_ids = []

    target_individuals, all_types, all_move_types = cup_filter_common(target_types, banned_type, banned_ids)

    # カントーカップ（第1世代）
    target_individuals = target_individuals[target_individuals["generation"] == 1]

    st.subheader("出場可能な手持ち一覧")
    # フィルター
    ivs = filter_type_common("kanto", target_individuals, all_types, all_move_types)

    st.dataframe(ivs[[
        "individual_id", "iv_atk", "iv_def", "iv_sta", "level",
        "is_shadow", "is_purified", "CP", "SCP", "HP",
        "type1_ja", "type2_ja",
        "fast_ja", "fast_type_ja", "charge1_ja", "charge1_type_ja", "charge2_ja", "charge2_type_ja", "generation"
    ]].sort_values("individual_id"), width='stretch')
