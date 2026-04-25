import streamlit as st
import pandas as pd

from core.cpm import CPM
from core.param_calc import calc_cp, calc_scp, calc_hp
from core.loader import load_species, load_moves, load_individuals

@st.fragment
def render_max1500():
    st.header("CP1500 以下で使える最大レベル計算")
    
    species = load_species()
    individuals = load_individuals()

    results = []

    for _, row in individuals.iterrows():
        sp = species[species["species_id"] == row["species_id"]].iloc[0]

        base_atk = sp["base_atk"]
        base_def = sp["base_def"]
        base_sta = sp["base_sta"]

        iv_atk = row["iv_atk"]
        iv_def = row["iv_def"]
        iv_sta = row["iv_sta"]

        best_level = None
        best_cp = None
        best_hp = None

        # PL1〜50 を探索
        for level, cpm in CPM.items():
            cp = calc_cp(base_atk, base_def, base_sta, iv_atk, iv_def, iv_sta, level)
            if cp <= 1500:
                best_level = level
                best_cp = cp
                best_hp = calc_hp(base_sta, iv_sta, cpm)

        scp = calc_scp(base_atk, base_def, base_sta, iv_atk, iv_def, iv_sta, best_level)

        results.append({
            "individual_id": row["individual_id"],
            "species_id": row["species_id"],
            "nickname": row["nickname"],
            "IV": f"{iv_atk}/{iv_def}/{iv_sta}",
            "max_level_1500": best_level,
            "cp": best_cp,
            "scp": scp,
            "hp": best_hp,
        })

    st.dataframe(pd.DataFrame(results))
