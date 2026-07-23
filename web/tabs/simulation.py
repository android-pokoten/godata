import streamlit as st
import pandas as pd

from core.simulator import simulate, list_move_damage_both
from core.loader import load_species, load_individuals, load_moves, load_opponents
from tabs.party_sim import render_3vs3_simulator
from tabs.edit import render_editer

def render_simulator():
    # タブ切り替え
    tabs = {
        "1 vs 1": render_1vs1_simulator, 
        "マッチアップ": render_matchup, 
        "3 vs 3": render_3vs3_simulator,
        "相手用テンプレ個体編集": edit_opponet_tab,
        "パーティ検討": party_simulator,
    }

    tab_objects = st.tabs(list(tabs.keys()))

    for tab_obj, (name, func) in zip(tab_objects, tabs.items()):
        with tab_obj:
            func()


@st.fragment
def render_1vs1_simulator():
    st.header("1 vs 1 シミュレーター")

    species = load_species()
    individuals = load_individuals()
    moves = load_moves()
    moves = moves.set_index("move_id")
    opponents = load_opponents()

    # 個体選択
    st.subheader("対戦する個体を選択")

    col1, col2 = st.columns(2)

    with col1:
        # わざが登録されていないとシミュレーションできないので除外する
        valid = individuals[
            (individuals["fast_move"].notna()) & (individuals["fast_move"] != "") &
            (individuals["charge_move1"].notna()) & (individuals["charge_move1"] != "")
        ].sort_values("individual_id")

        p1_name = st.selectbox(
            "ポケモン1（自分）",
            valid["individual_id"].tolist(),
            key="sim_p1"
        )
        if p1_name:
            p1 = individuals[individuals["individual_id"] == p1_name].iloc[0]

    with col2:
        opponents = opponents.sort_values("individual_id")

        p2_name = st.selectbox(
            "ポケモン2（相手）",
            opponents["individual_id"].tolist(),
            key="sim_p2"
        )
        if p2_name:
            p2 = opponents[opponents["individual_id"] == p2_name].iloc[0]

    # シールド選択
    st.subheader("シールド数")
    col3, col4 = st.columns(2)

    with col3:
        shield1 = st.select_slider("自分のシールド", options=[0, 1, 2], value=2)

    with col4:
        shield2 = st.select_slider("相手のシールド", options=[0, 1, 2], value=2)

    # シミュレーション実行
    if st.button("シミュレーション開始"):

        # わざのダメージ一覧
        st.markdown("## 各わざのダメージ一覧")

        dfA, dfB = list_move_damage_both(p1, p2, species, moves)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f'### {p1["individual_id"]} → {p2["individual_id"]}')
            st.dataframe(
                dfA.style.format({
                    "倍率": "{:.2f}",
                    "ダメージ": "{:.2f}",
                    "威力": "{:.2f}",
                    "ターン数": "{:.2f}",
                    "エネルギー": "{:.2f}"
                }),
                width="stretch"
            )

        with col2:
            st.markdown(f'### {p2["individual_id"]} → {p1["individual_id"]}')
            st.dataframe(
                dfB.style.format({
                    "倍率": "{:.2f}",
                    "ダメージ": "{:.2f}",
                    "威力": "{:.2f}",
                    "ターン数": "{:.2f}",
                    "エネルギー": "{:.2f}"
                }),
                width="stretch"
            )

        # シミュレーション実行
        #result = simulate(p1, p2, species, moves, shield1, shield2)
        result = simulate(p1, p2, species, dfA, dfB, shield1, shield2)

        st.subheader("結果")

        st.write(f"**勝者：{result['winner']}**")
        st.write(f"ターン数：{result['turns']}")

        col5, col6 = st.columns(2)
        with col5:
            st.write(f"### {p1_name}")
            st.write(f"残りHP：{result['hp1']}")
            st.write(f"残りシールド：{result['shield1']}")

        with col6:
            st.write(f"### {p2_name}")
            st.write(f"残りHP：{result['hp2']}")
            st.write(f"残りシールド：{result['shield2']}")

        st.subheader("ログ (ターンごとの動き)")
        #st.markdown(result["logs"])
        
        df = pd.DataFrame(result["turn_logs"])
        df = df.rename(columns={
            "turn": "ターン",
            "p1_ene": "自エネ",
            "p1_move": p1_name,
            "p1_hp": "自HP",
            "p1_damage": "⇒ダメ",
            "p2_ene": "相エネ",
            "p2_move": p2_name,
            "p2_hp": "相HP",
            "p2_damage": "←ダメージ",
        })
        df = df[["自エネ", p1_name, "自HP", "⇒ダメ", "ターン", "←ダメージ", "相HP", p2_name, "相エネ"]]
        st.table(df)

@st.fragment
def render_matchup():
    st.header("マッチアップ一覧")

    win = "o"
    lose = "*"

    species = load_species()
    individuals = load_individuals()
    moves = load_moves()
    moves = moves.set_index("move_id")
    opponents = load_opponents()

    # opponents.csv が空の場合は処理をせず抜ける
    if opponents.empty:
        st.warning("対戦相手の登録がありません。")
        return

    # opponents.csv から 1 行選ぶ
    # name_ja を付与してソート
    df_opp2 = opponents.merge(
        species[["species_id", "name_ja"]],
        on="species_id",
        how="left"
    ).sort_values("name_ja")

    selected_opp_id = st.selectbox(
        "対戦相手（opponents.csv）を選択",
        df_opp2.index,
        format_func=lambda idx: f"{df_opp2.loc[idx, 'individual_id']}"
    )

    opp_row = df_opp2.loc[selected_opp_id]

    # individuals.csv の全個体をループ
    valid_ind = individuals[
        (individuals["fast_move"].notna()) & (individuals["fast_move"] != "") &
        (individuals["charge_move1"].notna()) & (individuals["charge_move1"] != "")
    ].sort_values("individual_id")

    # 各個体について 5 パターンのシールド差で simulate()
    def run_matchups(opp_row, valid_ind):
        results = []

        for _, ind in valid_ind.iterrows():
            ind_id = ind["individual_id"]
            my_moves, opp_moves = list_move_damage_both(ind, opp_row, species, moves)

            # 5パターン
            patterns = [
                ("自分+2", 2, 0),
                ("自分+1", 1, 0),
                ("0-0",   0, 0),
                ("相手+1", 0, 1),
                ("相手+2", 0, 2),
            ]

            row_result = {"individual_id": ind_id}

            for label, s_me, s_opp in patterns:
                result = simulate(ind, opp_row, species, my_moves, opp_moves, s_me, s_opp)

                row_result[label] = win if result["hp1"] > result["hp2"] else lose

            results.append(row_result)

        return pd.DataFrame(results)

    # DataFrame にまとめて表示
    if st.button("相性一覧を計算する"):
        df_result = run_matchups(opp_row, valid_ind)
        
        # 勝ち数が多い順にソート
        cols = ["自分+2", "自分+1", "0-0", "相手+1", "相手+2"]
        df_result["win_count"] = (df_result[cols] == win).sum(axis=1)
        df_result = df_result.sort_values("win_count", ascending=False)

        df_result = df_result[
            ["individual_id", "win_count", "自分+2", "自分+1", "0-0", "相手+1", "相手+2"]
        ]

        def highlight_win(row):
            styles = []
            for col, val in row.items():
                if val == win:
                    styles.append("background-color: #a0c8ff;")
                else:
                    styles.append("")
            return styles

        st.dataframe(df_result.style.apply(highlight_win))

# テンプレ個体修正
@st.fragment
def edit_opponet_tab():
    csv_files = {
        "対戦相手データ (opponents.csv)": "data/opponents.csv",
    }

    render_editer(csv_files)


# パーティ検討
@st.fragment
def party_simulator():
    from core.logic.type_matchup import calc_party_type_relations, calc_party_attacktype_coverage
    from core.style.type_matchup_style import style_type_relations, style_attack_coverage_html, style_party_type_relations
    import pandas as pd

    species = load_species()
    moves = load_moves()
    # 表示用のラベルを追加
    species["label"] = species["name_ja"] + " (" + species["species_id"] + ")"
    individuals = load_individuals()

    st.header("パーティ検討")

    st.write("### 自分の手持ち（3匹）")
    def idx(df, col, val=None):
        try:
            return int(df.index[df[col] == val][0])
        except Exception:
            return 0

    left, center, right = st.columns(3)
    with left:
        my1 = st.selectbox("1匹目", individuals["individual_id"], index=idx(individuals, "individual_id"))
    with center:
        my2 = st.selectbox("2匹目", individuals["individual_id"], index=idx(individuals, "individual_id"))
    with right:
        my3 = st.selectbox("3匹目", individuals["individual_id"], index=idx(individuals, "individual_id"))

    if st.button("相性補完確認"):
        type_df = calc_party_type_relations(my1, my2, my3, species, individuals)
        styled_type_df = style_party_type_relations(type_df)

        st.table(styled_type_df)
        #styled_type_df = style_type_relations(type_df)
        #st.table(styled_type_df)

        attack_df = calc_party_attacktype_coverage(my1, my2, my3, individuals, moves)
        styled_attach_df = style_attack_coverage_html(attack_df)

        st.table(styled_attach_df)
