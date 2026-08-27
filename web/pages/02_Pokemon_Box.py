import streamlit as st
import pandas as pd
import math

from tabs.cup_filter import render_cup_filter
from tabs.edit import render_editer

from core.header import render_header
from core.cpm import CPM
from core.type import TYPE_CHART, type_with_underline
from core.param_calc import compute_cp_row, compute_scp_row, compute_hp_row
from core.loader import load_species, load_moves, load_individuals

### メイン処理
def main():
    render_header()

    # タブ切り替え
    tabs = {
        "手持ち一覧": render_individuals_list,
        "特殊カップ": render_cup_filter,
        "手持ちデータ修正": render_iv_editor, 
    }

    tab_objects = st.tabs(list(tabs.keys()))

    for tab_obj, (name, func) in zip(tab_objects, tabs.items()):
        with tab_obj:
            func()

def calc_stats(species_row, iv_atk, iv_def, iv_sta, level):
    cpm = CPM[level]

    atk = (species_row["base_atk"] + iv_atk) * cpm
    defense = (species_row["base_def"] + iv_def) * cpm
    stamina = math.floor((species_row["base_sta"] + iv_sta) * cpm)

    return atk, defense, stamina

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

# 手持ちデータ修正
@st.fragment
def render_iv_editor():
    csv_files = {
        "個体データ (individuals.csv)": "data/individuals.csv",
    }

    render_editer(csv_files)
    

if __name__ == "__main__":
    main()
