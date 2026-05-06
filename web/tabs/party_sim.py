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

    def simulate_1vs1_simple_with_state(
        p1, p2,
        moves_df,
        hp1=None, hp2=None,
        e1=0, e2=0
    ):
        """
        p1, p2: 個体データ(dict)
        moves_df: moves.csv を DataFrame 化したもの
        hp1, hp2: 前の対面から引き継いだ HP（None の場合は満タン）
        e1, e2: 引き継ぎエネルギー
        """
        vslog = []

        # HP 初期化
        if hp1 is None:
            hp1 = p1["HP"]
        if hp2 is None:
            hp2 = p2["HP"]

        # 技データ取得
        f1 = moves_df.loc[p1["fast_move"]]
        f2 = moves_df.loc[p2["fast_move"]]

        c1 = moves_df.loc[p1["charge_move1"]]
        c1_ene = abs(c1["energy"])
        c2 = moves_df.loc[p2["charge_move1"]]
        c2_ene = abs(c2["energy"])

        # ターンは 0.5秒単位で進める
        # duration_ms を 500ms 単位に変換
        f1_cd = int(f1["turns"])
        f2_cd = int(f2["turns"])

        t1 = 0
        t2 = 0

        # 対面開始ログ
        vslog.append(f"{p1['individual_id']} vs {p2['individual_id']} 開始")
        print(f"p1: {f1["power"]}, {f1["energy"]}, {f1_cd}, {c1["energy"]}, {c1["power"]}, {c1_ene}")
        print(f"p2: {f2["power"]}, {f2["energy"]}, {f2_cd}, {c2["energy"]}, {c2["power"]}, {c2_ene}")

        while hp1 > 0 and hp2 > 0:

            print(f"{t1} / {e1}:{e2} / {hp1}:{hp2} / {c1_ene}:{c2_ene}")
            # --- p1 の行動 ---
            t1 += 1
            if t1 >= f1_cd:
                t1 = 0
                hp2 -= f1["power"]
                e1 += f1["energy"]
                print(f"P1のノーマルわざ > HP2:{hp2} E1:{e1}")

                # スペシャル発動
                if e1 >= c1_ene:
                    e1 -= c1_ene
                    hp2 -= c1["power"]
                    print(f"P1のスペシャルわざ > HP2:{hp2} E1:{e1}")

                if hp2 <= 0:
                    vslog.append(f"{p1['individual_id']} 勝利 HP: {hp1}, エネルギー: {e1}")
                    return "p1", hp1, 0, e1, 0, vslog

            # --- p2 の行動 ---
            t2 += 1
            if t2 >= f2_cd:
                t2 = 0
                hp1 -= f2["power"]
                e2 += f2["energy"]
                print(f"P2のノーマルわざ > HP1:{hp1} E2:{e2}")

                if e2 >= c2_ene:
                    e2 -= c2_ene
                    hp1 -= c2["power"]
                    print(f"P2のスペシャルわざ > HP1:{hp1} E2:{e2}")

                if hp1 <= 0:
                    vslog.append(f"{p2['individual_id']} 勝利 HP: {hp2}, エネルギー: {e2}")
                    return "p2", 0, hp2, 0, e2, vslog

        return ("p1" if hp1 > 0 else "p2"), hp1, hp2, e1, e2, vslog

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
            result, my_hp, opp_hp, my_e, opp_e, log1vs1 = simulate_1vs1_simple_with_state(
                my_team[my_idx],
                opp_team[opp_idx],
                moves_df,
                my_hp, opp_hp,
                my_e, opp_e
            )

            battle_log.extend(log1vs1)

            if result == "p1":
                # 相手が倒れた
                opp_idx += 1
                opp_hp = None
                opp_e = 0
            else:
                # 自分が倒れた
                my_idx += 1
                my_hp = None
                my_e = 0

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
