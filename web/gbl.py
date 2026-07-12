import streamlit as st

from tabs.datum import render_datum
from tabs.iv import render_individuals
from tabs.detail import render_detail
from tabs.iv_checker import render_iv_checker
from tabs.simulation import render_simulator
from tabs.battle_log import render_battlelog

st.set_page_config(page_title="Pokémon Data Viewer", layout="wide")

st.title("Pokémon GO Data Viewer")

# タブ切り替え
tabs = {
    "基本データ": render_datum, # 種族値、わざデータ
    "手持ち": render_individuals,  # 手持ちデータ
    "ポケモン詳細": render_detail,  # ポケモン詳細データ
    "個体値チェッカー": render_iv_checker,  # CPからポケモンレベルを計算する
    "VS SIM": render_simulator, # 1vs1 シミュレーター
    "対戦ログ": render_battlelog, # 1vs1 シミュレーター
}

tab_objects = st.tabs(list(tabs.keys()))

for tab_obj, (name, func) in zip(tab_objects, tabs.items()):
    with tab_obj:
        func()
