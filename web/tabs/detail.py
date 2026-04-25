import streamlit as st
import pandas as pd

from core.cpm import CPM
from core.type import TYPE_CHART, TYPE_ORDER, TYPE_JA, TYPE_COLOR, type_with_underline, ja_to_en_type
from core.param_calc import compute_cp_row, compute_scp_row, compute_hp_row, generate_template_individual
from core.loader import load_species, load_moves, load_individuals, load_opponents

# タイプ相性表
def render_type_relations(species_row):
    type1 = species_row["type1"]
    type2 = species_row["type2"]
    target_types = [t for t in [type1, type2] if t]

    row = {}

    for atk_type, chart in TYPE_CHART.items():
        mult = 1.0
        for t in target_types:
            mult *= chart.get(t, 1.0)

        row[atk_type] = mult

    # ヘッダーセルにタイプごとの色付け
    def style_type_headers(df):
        # 列ヘッダーのスタイル
        col_styles = [
            {
                "selector": f"th.col_heading.level0.col{i}",
                "props": f"background-color: {TYPE_COLOR[col]}; color: white; font-weight: bold;"
                "writing-mode: vertical-rl; "
                "text-orientation: upright; "
                "padding: 6px 1px;"
            }
            for i, col in enumerate(df.columns)
        ]

        return col_styles

    def highlight(row):
        styled = []
        for val in row:
            if val >= 2.0:
                styled.append("background-color: #ff9999")
            elif val > 1.0:
                styled.append("background-color: #ffcccc")
            elif val == 1.0:
                styled.append("background-color: #eeeeee; color: #eeeeee")
            elif val > 0.39:
                styled.append("background-color: #cce5ff")
            else:
                styled.append("background-color: #99ccff")
        return styled

    df = pd.DataFrame([row])

    df_jp = df.copy()
    df_jp.index = df_jp.index.map(TYPE_JA)
    df_jp.columns = df_jp.columns.map(TYPE_JA)

    styled = (
        df_jp
            .style.apply(highlight, axis=1)
            .set_table_styles(style_type_headers(df))  # ← 見出しだけ色付け
            .format("{:.2f}")  
    )

    # 色付きテーブル
    st.markdown("### タイプ相性まとめ")
    st.table(styled)

@st.fragment
def render_detail():
    st.header("ポケモン詳細")

    species = load_species()
    moves = load_moves()
    individuals = load_individuals()

    # 検索欄
    query = st.text_input("ポケモン名で検索（日本語・英語どちらでも）")
    
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

    st.subheader("基本データ")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**種族 ID:** {sp['species_id']}")
        st.write(f"**名前:** {sp['name_ja']}")
        st.markdown(html1, unsafe_allow_html=True)
        st.markdown(html2, unsafe_allow_html=True)

    with col2:
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
    render_type_relations(sp)

    # 技データ
    st.subheader("わざ")

    fast_list = sp["fast_moves"].split(",") if sp["fast_moves"] else [] 
    elite_fast_list = sp["elitefast"].split(",") if sp["elitefast"] else []
    fast_list += elite_fast_list
    fast_move_list = moves[moves["move_id"].isin(fast_list)].copy()
    fast_move_list["stab"] = fast_move_list["type"].apply(
        lambda t: 1.2 if t in [sp["type1"], sp["type2"]] else 1.0
    )
    fast_move_list["一致"] = fast_move_list["stab"].apply(lambda x: "⭐" if x > 1.0 else "")
    fast_move_list["power_stab"] = (fast_move_list["power"] * fast_move_list["stab"]).round(1)
    fast_move_list["dpt"] = fast_move_list["power_stab"] / fast_move_list["turns"]
    fast_move_list["ept"] = fast_move_list["energy"] / fast_move_list["turns"]
    fast_move_list["name_ja"] = fast_move_list.apply(
        lambda row: row["name_ja"] + "＊" if row["move_id"] in elite_fast_list else row["name_ja"],
        axis=1
    )
    fast_move_list["type"] = fast_move_list["type"].apply(lambda x: TYPE_JA.get(x, x))

    charge_list = sp["charge_moves"].split(",") if sp["charge_moves"] else []
    elite_charge_list = sp["elitecharge"].split(",") if sp["elitecharge"] else []
    charge_list += elite_charge_list
    charge_moves = moves[moves["move_id"].isin(charge_list)].copy()
    charge_moves["stab"] = charge_moves["type"].apply(
        lambda t: 1.2 if t in [sp["type1"], sp["type2"]] else 1.0
    )
    charge_moves["一致"] = charge_moves["stab"].apply(lambda x: "⭐" if x > 1.0 else "")
    charge_moves["power_stab"] = (charge_moves["power"] * charge_moves["stab"]).round(1)
    charge_moves["dpe"] = (charge_moves["power_stab"] / charge_moves["energy"].abs()).round(1)
    charge_moves["name_ja"] = charge_moves.apply(
        lambda row: row["name_ja"] + "＊" if row["move_id"] in elite_charge_list else row["name_ja"],
        axis=1
    )
    charge_moves["type"] = charge_moves["type"].apply(lambda x: TYPE_JA.get(x, x))

    def highlight_legacy(row):
        styles = []
        for col, val in row.items():
            if col == "type":
                styles.append(f"background: linear-gradient(to bottom, transparent 65%,  {TYPE_COLOR[ja_to_en_type(val)]} 85%, transparent 100%);")
            elif col == "name_ja" and "＊" in val:
                 styles.append(f"background: linear-gradient(to left, transparent 98%,  red 99%, transparent 100%);")
            else:
                styles.append("")
        return styles

    def highlight_stab(row):
        return ['background-color: #fff3cd' if row["一致"] == "⭐" else '' for _ in row]

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

    # 選択された species_id の個体を抽出
    indiv = individuals[individuals["species_id"] == selected].copy()

    # 個体のCP, SCP, HP を計算
    if not indiv.empty:
        indiv["CP"] = indiv.apply(compute_cp_row, axis=1)
        indiv["SCP"] = indiv.apply(compute_scp_row, axis=1)
        indiv["HP"] = indiv.apply(compute_hp_row, axis=1)

        # fast_move の日本語名を結合
        indiv = indiv.merge(
            moves[["move_id", "name_ja"]].rename(columns={"name_ja": "fast_move_ja"}),
            how="left",
            left_on="fast_move",
            right_on="move_id"
        ).drop(columns=["move_id"])
        
        # charge_move1 の日本語名
        indiv = indiv.merge(
            moves[["move_id", "name_ja"]].rename(columns={"name_ja": "charge_move1_ja"}),
            how="left",
            left_on="charge_move1",
            right_on="move_id"
        ).drop(columns=["move_id"])
        
        # charge_move2 の日本語名
        indiv = indiv.merge(
            moves[["move_id", "name_ja"]].rename(columns={"name_ja": "charge_move2_ja"}),
            how="left",
            left_on="charge_move2",
            right_on="move_id"
        ).drop(columns=["move_id"])

        # 最速ターン計算
        def compute_turns(row, special_col):
            fast_id = sp["fast_moves"].split(",")[0] # 代表の速技（1つ目）
            fast = moves[moves["move_id"] == fast_id].iloc[0]
            
            charge_id = row[special_col]
            if pd.isna(charge_id):
                return None
                
            charge = moves[moves["move_id"] == charge_id].iloc[0]
            
            ept = fast["energy"] / fast["turns"]
            need = abs(charge["energy"])
            
            return int((need + ept - 1) // ept)

        indiv["special1_turns"] = indiv.apply(lambda r: compute_turns(r, "charge_move1"), axis=1)
        indiv["special2_turns"] = indiv.apply(lambda r: compute_turns(r, "charge_move2"), axis=1)

        st.table(indiv[[
            "individual_id", "CP", "SCP", "HP", "fast_move_ja", 
            "charge_move1_ja", "special1_turns", "charge_move2_ja", "special2_turns",
            "iv_atk", "iv_def", "iv_sta", "level"
        ]])

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


