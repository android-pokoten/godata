import streamlit as st
import pandas as pd

from core.loader import load_species, load_moves, load_individuals, load_opponents
from tabs.season_effect import render_season_effect
from tabs.edit import render_editer

@st.fragment
def render_datum():
    # タブ切り替え
    tabs = {
        "種族値": render_species, 
        "わざ": render_moves, 
        "シーズン調整一覧": render_season_effect,
        "タイプ相性表": render_typechart,
    }

    tab_objects = st.tabs(list(tabs.keys()))

    for tab_obj, (name, func) in zip(tab_objects, tabs.items()):
        with tab_obj:
            func()

# 種族値一覧
def render_species():
    st.header("種族値データ")

    species = load_species()

    st.dataframe(species)

# わざ一覧
def render_moves():
    st.header("わざデータ")

    moves = load_moves()

    # 数値に変換
    for col in ["power", "energy", "turns"]:
        moves[col] = pd.to_numeric(moves[col], errors="coerce")

    # DPT, EPT を追加
    fast_mask = moves["category"] == "fast"
    moves.loc[fast_mask, "dpt"] = moves.loc[fast_mask, "power"] / moves.loc[fast_mask, "turns"]
    moves.loc[fast_mask, "ept"] = moves.loc[fast_mask, "energy"] / moves.loc[fast_mask, "turns"]

    # DPE を追加
    fast_mask = moves["category"] == "charge"
    moves.loc[fast_mask, "dpe"] = (moves.loc[fast_mask, "power"] / moves.loc[fast_mask, "energy"].abs()).round(1)

    st.subheader("フィルター")
    sp_ene_filter = st.selectbox("スペシャルわざのエネルギー", ["-", -35, -40, -45, -50, -55])
    
    df_filtered = moves.copy()

    if sp_ene_filter != "-":
        df_filtered = df_filtered[(df_filtered["energy"] == sp_ene_filter) & (df_filtered["category"] == "charge")]

    st.dataframe(df_filtered, width='stretch')

# タイプ相性表
def render_typechart():
    from core.type import TYPE_CHART, TYPE_ORDER, TYPE_JA, TYPE_COLOR

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

        # 行ヘッダーのスタイル
        row_styles = [
            {
                "selector": f"th.row_heading.level0.row{i}",
                "props": f"background-color: {TYPE_COLOR[idx]}; color: white; font-weight: bold;"
            }
            for i, idx in enumerate(df.index)
        ]

        return col_styles + row_styles

    # タイプチャートをDataframeに変換
    def type_chart_to_df(TYPE_CHART):
        # 行：攻撃側タイプ、列：防御側タイプ
        df = pd.DataFrame.from_dict(TYPE_CHART, orient="index")
        df = df.fillna(1.0)  # 未定義は等倍扱い

        # 行、列を並び替え
        df = df.reindex(TYPE_ORDER)
        df = df[TYPE_ORDER]

        return df

    # 表に色付け
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

    df_chart = type_chart_to_df(TYPE_CHART)

    # 表記用にタイプ名を日本語に置き換え(セル色は英語名のままで処理する)
    df_jp = df_chart.copy()
    df_jp.index = df_jp.index.map(TYPE_JA)
    df_jp.columns = df_jp.columns.map(TYPE_JA)

    styled = (
        df_jp
            .style.apply(highlight, axis=1)
            .set_table_styles(style_type_headers(df_chart))  # ← 見出しだけ色付け
            .format("{:.2f}")  
    )

    # 色付きテーブル
    st.markdown("### タイプ相性表")
    st.table(styled)
