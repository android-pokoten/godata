import streamlit as st
import pandas as pd

from core.simulator import simulate, list_move_damage_both
from core.loader import load_species, load_individuals, load_moves, load_opponents
from core.param_calc import generate_template_individual, compute_hp_row

@st.fragment
def render_3vs3_simulator():
    species = load_species()
    opponents = load_opponents()
    individuals = load_individuals()

    # HP 計算
    individuals["HP"] = individuals.apply(compute_hp_row, axis=1)
    opponents["HP"] = opponents.apply(compute_hp_row, axis=1)

    def parse_party_line(line):
        """
        1行の文字列をパースして
        [my1, my2, my3], [opp1, opp2, opp3]
        を返す
        """
        if not line:
            return ["", "", ""], ["", "", ""]

        # タブ or スペース or カンマで分割
        parts = [p.strip() for p in line.replace("/", " ").split() if p.strip()]

        # 6個なければエラー扱い
        if len(parts) != 6:
            return ["", "", ""], ["", "", ""]

        my = parts[:3]
        opp = parts[3:]
        return my, opp

    def generate_template(species_id):
        row = opponents[opponents["species_id"] == species_id]
        if len(row) > 0:
            r = row.iloc[0]
            # 処理しやすいように辞書形式に変換
            return r.to_dict()

        # opponents.csv にない場合、仮のテンプレ個体を生成する
        sp = species[species["species_id"] == species_id].iloc[0]
        row = generate_template_individual(sp["species_id"], sp)
        # 仮テンプレデータのindividual_idはポケモン名そのままにする
        row["individual_id"] = sp["name_ja"]
        return row

    def simulate_3vs3_simple(my_team, opp_team, moves_df):
        """
        my_team, opp_team: [p1, p2, p3] のテンプレ個体(dict)
        """

        my_idx = 0
        opp_idx = 0

        my_hp = None
        opp_hp = None
        my_e = 0
        opp_e = 0

        battle_log = []
        log1vs1 = ""

        while my_idx < 3 and opp_idx < 3:
            result = simulate(
                my_team[my_idx],
                opp_team[opp_idx],
                species,
                moves_df,
                0, 0,
                my_hp, opp_hp,
                my_e, opp_e
            ) 
            battle_log.append(f"{my_team[my_idx]["individual_id"]} vs {opp_team[opp_idx]["individual_id"]}")

            if result["winner"] == my_team[my_idx]["individual_id"]:
                # 相手が倒れた
                opp_idx += 1
                opp_hp = None
                opp_e = 0
                my_hp = result["hp1"]
                my_e = result["energy1"]
                battle_log.append(f"{result["winner"]} 勝利 HP: {result["hp1"]}, エネルギー: {result["energy1"]}")
            else:
                # 自分が倒れた
                my_idx += 1
                my_hp = None
                my_e = 0
                opp_hp = result["hp2"]
                opp_e = result["energy2"]
                battle_log.append(f"{result["winner"]} 勝利 HP: {result["hp2"]}, エネルギー: {result["energy2"]}")

        st.table(battle_log)
        return my_idx < 3  # True = 勝ち

    st.subheader("3vs3 パーティ入力（1行コピペ）")

    example = "フラージェス / カラマネロ / トリトドン\tgreninja\tglaceon\tmorpeko"

    line = st.text_input("パーティ1行入力", placeholder=example)

    my_names, opp_names = parse_party_line(line)

    col1, col2 = st.columns(2)

    with col1:
        st.write("### 自分のパーティ")
        my1 = st.text_input("自分1", placeholder=my_names[0])
        my2 = st.text_input("自分2", placeholder=my_names[1])
        my3 = st.text_input("自分3", placeholder=my_names[2])

    with col2:
        st.write("### 相手のパーティ")
        opp1 = st.text_input("相手1", placeholder=opp_names[0])
        opp2 = st.text_input("相手2", placeholder=opp_names[1])
        opp3 = st.text_input("相手3", placeholder=opp_names[2])

    if my_names[0] != "":
        my_team = []
        
        for name in my_names:
            indiv = individuals[individuals["individual_id"] == name].iloc[0]
            # 処理しやすいように辞書形式に変換
            my_team.append(indiv.to_dict())

    if opp_names[0] != "":
        opp_team = []

        for name in opp_names:
            indiv = generate_template(name)
            opp_team.append(indiv)

    if (my_names[0] != "") & (opp_names[0] != ""):
        moves = load_moves()
        moves = moves.set_index("move_id")
        result = simulate_3vs3_simple(my_team, opp_team, moves)

        if result:
            st.write(f"自分のパーティの勝利")
        else:
            st.write(f"相手のパーティの勝ち")
