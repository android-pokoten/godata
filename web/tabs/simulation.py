import streamlit as st
import pandas as pd

from core.simulator import simulate, list_move_damage_both
from core.loader import load_species, load_individuals, load_moves, load_opponents
from tabs.party_sim import render_3vs3_simulator

# バトルログのパス
battle_log_path = "data/battle_log.csv"

def render_simulator():
    # タブ切り替え
    tabs = {
        "1 vs 1": render_1vs1_simulator, 
        "マッチアップ": render_matchup, 
        "バトルログ登録": battle_log_tab,
        "バトルログ参照": battle_log_viewer_tab,
        "バトルログ分析": analyse_log_tab,
        "3 vs 3": render_3vs3_simulator,
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
        p1 = individuals[individuals["individual_id"] == p1_name].iloc[0]

    with col2:
        opponents = opponents.sort_values("individual_id")

        p2_name = st.selectbox(
            "ポケモン2（相手）",
            opponents["individual_id"].tolist(),
            key="sim_p2"
        )
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
                    "エネルギー": "{:.2f}"
                }),
                width="stretch"
            )

        # シミュレーション実行
        result = simulate(p1, p2, species, moves, shield1, shield2)

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
        st.markdown(result["logs"])


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
                result = simulate(ind, opp_row, species, moves, s_me, s_opp)

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

# バトルログ記録
@st.fragment
def battle_log_tab():
    from datetime import datetime
    import os

    species = load_species()
    # 表示用のラベルを追加
    species["label"] = species["name_ja"] + " (" + species["species_id"] + ")"
    individuals = load_individuals()

    st.header("バトルログ記録")

    # --- 初期値の準備 ---
    default_season = 26
    default_cup = ""
    default_rank = 1
    default_my1 = None
    default_my2 = None
    default_my3 = None

    if os.path.exists(battle_log_path):
        try:
            df_log = pd.read_csv(battle_log_path)
            if len(df_log) > 0:
                last = df_log.iloc[-1]
                default_season = last.get("season", "")
                default_cup = last.get("cup", "")
                default_rank = last.get("rank", "")
                default_my1 = last.get("my1", None)
                default_my2 = last.get("my2", None)
                default_my3 = last.get("my3", None)
        except:
            pass  # 壊れたCSVでもアプリが落ちないように

    left, center, right = st.columns(3)

    with left:
        # --- シーズン（最終行を初期値に） ---
        season_list = list(range(20, 27))
        season = st.selectbox("シーズン", season_list, index=season_list.index(default_season))

    with center:
        # --- カップ名（最終行を初期値に） ---
        cup = st.text_input("カップ名", value=default_cup)

    with right:
        # --- ランク（最終行を初期値に） ---
        rank_list = list(range(1, 24))
        rank = st.selectbox("ランク", rank_list, index=rank_list.index(default_rank))

    st.write("### 自分の手持ち（3匹）")
    def idx(df, col, val):
        ret = df.index[df[col] == val][0] if val in df[col].values else 0
        # そのままだと Numpy.int64 になってしまうので、int に変換
        return ret.item()

    left, center, right = st.columns(3)
    with left:
        my1 = st.selectbox("1匹目", individuals["individual_id"], index=idx(individuals, "individual_id", default_my1))
    with center:
        my2 = st.selectbox("2匹目", individuals["individual_id"], index=idx(individuals, "individual_id", default_my2))
    with right:
        my3 = st.selectbox("3匹目", individuals["individual_id"], index=idx(individuals, "individual_id", default_my3))

    st.write("### 相手のポケモン（3匹）")
    left, center, right = st.columns(3)

    with left:
        opp1_input = st.text_input("相手1")
    with center:
        opp2_input = st.text_input("相手2")
    with right:
        opp3_input = st.text_input("相手3")

    choices = ["（不明）"] + species["label"].tolist()
    # selectbox の初期値推定
    def filter_choices(input_text):
        if not input_text:
            return ["（不明）"] + species["label"].tolist()
        hits = [label for label in species["label"] if input_text in label]
        if len(hits) == 0:
            return ["（不明）"] + species["label"].tolist()
        return ["（不明）"] + hits

    # --- 選択欄（補正用） ---
    opp1_choices = filter_choices(opp1_input)
    opp2_choices = filter_choices(opp2_input)
    opp3_choices = filter_choices(opp3_input)
        
    left, center, right = st.columns(3)

    with left:
        opp1_label = st.selectbox("相手1（選択）", opp1_choices)
    with center:
        opp2_label = st.selectbox("相手2（選択）", opp2_choices)
    with right:
        opp3_label = st.selectbox("相手3（選択）", opp3_choices)

    # --- 保存用 species_id 変換 ---
    def to_species_id(label):
        if label == "（不明）":
            return ""
        return species.loc[species["label"] == label, "species_id"].iloc[0]
    
    opp1 = to_species_id(opp1_label)
    opp2 = to_species_id(opp2_label)
    opp3 = to_species_id(opp3_label)

    # --- 勝敗 ---
    result = st.radio("結果", ["Win", "Lose", "Draw"], horizontal=True)

    # --- コメント（任意） ---
    comment = st.text_area("コメント（任意・100文字まで）", max_chars=100)
    # 改行を削除して1行にまとめる
    comment = "".join(comment.splitlines())

    # --- 保存処理 ---
    if st.button("ログを保存"):
        new_row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "season": season,
            "cup": cup,
            "rank": rank,
            "result": result,
            "my1": my1,
            "my2": my2,
            "my3": my3,
            "opp1": opp1,
            "opp2": opp2,
            "opp3": opp3,
            "comment": comment,
        }

        if os.path.exists(battle_log_path):
            df = pd.read_csv(battle_log_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_csv(battle_log_path, index=False)
        st.success("バトルログを保存しました！")


# バトルログ分析
@st.fragment
def analyse_log_tab():
    from datetime import datetime
    import os
    from core.season import SEASON_NAME

    st.header("バトルログ分析")

    # --- ログ読み込み ---
    try:
        df = pd.read_csv(battle_log_path)
    except:
        st.warning(f"{battle_log_path} がまだありません。バトルログを記録してください。")
        return

    if len(df) == 0:
        st.warning("バトルログが空です。")
        return

    # --- 勝敗を数値化（Win=1, Lose=0, Draw=0.5） ---
    def to_score(x):
        if x == "Win":
            return 1
        if x == "Lose":
            return 0
        return 0.5  # Draw

    df["score"] = df["result"].apply(to_score)

    st.subheader("シーズン別勝率")

    season_stats = (
        df.groupby("season")["score"]
        .agg(["count", "mean"])
        .rename(columns={"count": "試合数", "mean": "勝率"})
    )

    season_stats["勝率"] = (season_stats["勝率"] * 100).round(1).astype(str) + "%"
    # シーズン名を追加して並び替え
    season_stats["シーズン名"] = season_stats.index.map(SEASON_NAME)
    season_stats = season_stats[["シーズン名", "試合数", "勝率"]]

    st.table(season_stats)

    st.subheader("カップ別勝率")

    cup_stats = (
        df.groupby("cup")["score"]
        .agg(["count", "mean"])
        .rename(columns={"count": "試合数", "mean": "勝率"})
    )

    cup_stats["勝率"] = (cup_stats["勝率"] * 100).round(1).astype(str) + "%"

    st.table(cup_stats)

    st.subheader("自分のパーティ別勝率")

    # パーティをタプル化（順番も保持）
    df["party"] = df.apply(lambda x: (x["my1"], x["my2"], x["my3"]), axis=1)

    party_stats = (
        df.groupby("party")["score"]
        .agg(["count", "mean"])
        .rename(columns={"count": "試合数", "mean": "勝率"})
    )

    party_stats["勝率"] = (party_stats["勝率"] * 100).round(1).astype(str) + "%"

    st.table(party_stats.sort_values("勝率", ascending=False))

    st.subheader("ポケモン単体別勝率")

    # my1, my2, my3 を縦持ちに変換
    rows = []
    for _, row in df.iterrows():
        for p in ["my1", "my2", "my3"]:
            rows.append({"pokemon": row[p], "score": row["score"]})

    df_pokemon = pd.DataFrame(rows)

    pokemon_stats = (
        df_pokemon.groupby("pokemon")["score"]
        .agg(["count", "mean"])
        .rename(columns={"count": "試合数", "mean": "勝率"})
    )

    pokemon_stats["勝率"] = (pokemon_stats["勝率"] * 100).round(1).astype(str) + "%"

    st.table(pokemon_stats.sort_values("勝率", ascending=False))

# バトルログ参照
@st.fragment
def battle_log_viewer_tab():

    st.header("バトルログ閲覧")

    try:
        df = pd.read_csv(battle_log_path)
    except:
        st.warning(f"{battle_log_path} がありません。バトルログを記録してください。")
        return

    if len(df) == 0:
        st.warning("バトルログが空です。")
        return

    # --- フィルターUI ---
    st.subheader("フィルター")

    seasons = ["すべて"] + sorted(df["season"].dropna().unique().tolist())
    cups = ["すべて"] + sorted(df["cup"].dropna().unique().tolist())
    ranks = ["すべて"] + sorted(df["rank"].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        season_filter = st.selectbox("シーズン", seasons)
    with col2:
        cup_filter = st.selectbox("カップ", cups)
    with col3:
        rank_filter = st.selectbox("ランク", ranks)

    # --- フィルタリング ---
    df_filtered = df.copy()

    if season_filter != "すべて":
        df_filtered = df_filtered[df_filtered["season"] == season_filter]

    if cup_filter != "すべて":
        df_filtered = df_filtered[df_filtered["cup"] == cup_filter]

    if rank_filter != "すべて":
        df_filtered = df_filtered[df_filtered["rank"] == rank_filter]

    # --- 表示用整形 ---
    def format_team(row, prefix):
        return f"{row[prefix+'1']} / {row[prefix+'2']} / {row[prefix+'3']}"

    df_filtered["自分の構築"] = df_filtered.apply(lambda r: format_team(r, "my"), axis=1)
    df_filtered["相手の構築"] = df_filtered.apply(lambda r: format_team(r, "opp"), axis=1)

    display_cols = [
        "timestamp", "season", "cup", "rank",
        "自分の構築", "opp1", "opp2", "opp3",
        "result", "comment"
    ]

    st.subheader("バトルログ一覧")
    st.dataframe(
        df_filtered[display_cols],
        column_config={
            "opp1": "相手1",
            "opp2": "相手2",
            "opp3": "相手3",
        })

    left, center, right = st.columns(3)

    with left:
        st.subheader("勝率")

        total = len(df_filtered)
        wins = (df_filtered["result"] == "Win").sum()
        win_rates = wins / total * 100 if total > 0 else 0

        st.write(f"試合数: {total} / 勝率: {win_rates:.1f}%")

    with center:
        st.subheader("相手の初手ポケモン")

        # 初手ごとの出現数
        opp1_counts = df_filtered["opp1"].value_counts()

        # 初手ごとの出現割合
        opp1_rate = (opp1_counts / total * 100).round(1)

        # 初手ごとの勝率
        opp1_wins = df_filtered[df_filtered["result"] == "Win"]["opp1"].value_counts()
        opp1_winrate = (opp1_wins / opp1_counts * 100).fillna(0).round(1)

        df_opp1 = pd.DataFrame({
            "出現数": opp1_counts,
            "割合(%)": opp1_rate,
            "勝率(%)": opp1_winrate
        })

        st.dataframe(df_opp1)

    with right:
        st.subheader("相手の全ポケモン")

        # 3列を縦に並べる
        all_opps = pd.concat([
            df_filtered["opp1"],
            df_filtered["opp2"],
            df_filtered["opp3"]
        ])

        # 空欄は除外
        all_opps = all_opps[all_opps != ""]

        # ポケモンごとの出現数
        opp_counts = all_opps.value_counts()

        # ポケモンごとの出現割合
        opp_rate = (opp_counts / len(all_opps) * 100).round(1)

        # 勝ち数（勝った試合の opp1〜3 を縦に並べる）
        all_opps_win = pd.concat([
            df_filtered[df_filtered["result"] == "Win"]["opp1"],
            df_filtered[df_filtered["result"] == "Win"]["opp2"],
            df_filtered[df_filtered["result"] == "Win"]["opp3"]
        ])
        all_opps_win = all_opps_win[all_opps_win != ""]
        opp_wins = all_opps_win.value_counts()

        # 勝率
        opp_winrate = (opp_wins / opp_counts * 100).fillna(0).round(1)

        df_opp_all = pd.DataFrame({
            "出現数": opp_counts,
            "割合(%)": opp_rate,
            "勝率(%)": opp_winrate
        })

        st.dataframe(df_opp_all)
