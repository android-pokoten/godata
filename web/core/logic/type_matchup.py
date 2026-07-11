
# タイプ相性計算
'''
input: type1, type2 > 文字列、タイプ名(fire, walter など)
output: > DataFrame、タイプ相性一覧のDataFrame
'''
def calc_type_relations(type1, type2):
    import pandas as pd

    from core.type import TYPE_CHART, TYPE_JA

    target_types = [t for t in [type1, type2] if t]

    row = {}

    # タイプ別の倍率計算
    for atk_type, chart in TYPE_CHART.items():
        mult = 1.0
        for t in target_types:
            mult *= chart.get(t, 1.0)

        row[atk_type] = mult

    df_jp = pd.DataFrame([row])

    # タイプ名を日本語表記に置き換え
    df_jp.index = df_jp.index.map(TYPE_JA)
    df_jp.columns = df_jp.columns.map(TYPE_JA)

    return df_jp

# パーティのタイプ相性計算
'''
input: my1, my2, my3 > 文字列、手持ち3匹のindivisual_id
output: > DataFrame、タイプ相性一覧のDataFrame
'''
def calc_party_type_relations(my1, my2, my3, species, individuals):
    import pandas as pd

    my_ivs = [my1, my2, my3]
    type_df = pd.DataFrame()

    for my in my_ivs:
        iv = individuals[individuals["individual_id"] == my].iloc[0]
        sp = species[species["species_id"] == iv["species_id"]].iloc[0]
        df = calc_type_relations(sp["type1"], sp["type2"])
        df["NAME"] = my
        type_df = pd.concat([type_df, df], axis=0)

    # NAME を一番左にする
    cols = ["NAME"] + [c for c in type_df.columns if c != "NAME"]
    type_df = type_df[cols]

    # 合計値の行を追加
    sum_row = type_df.drop(columns=["NAME"]).sum()
    sum_row["NAME"] = "合計"
    df_sum = pd.concat([type_df, sum_row.to_frame().T], ignore_index=True)

    return df_sum

# パーティの攻撃タイプ相性計算
'''
input: my1, my2, my3 > 文字列、手持ち3匹のindivisual_id
output: > DataFrame、タイプ相性一覧のDataFrame
'''
def calc_party_attacktype_coverage(my1, my2, my3, individuals, moves):
    import pandas as pd
    from core.type import TYPE_CHART, TYPE_JA

    # 一覧を作る
    my_ivs = [my1, my2, my3]
    type_df = pd.DataFrame()

    for my in my_ivs:
        iv = individuals[individuals["individual_id"] == my].iloc[0]
        charge_move_1_id = iv["charge_move1"]
        charge_move_2_id = iv["charge_move2"]

        charge_move_1 = moves[moves["move_id"] == charge_move_1_id].iloc[0]
        charge_move_2 = moves[moves["move_id"] == charge_move_2_id].iloc[0]

        row = {
            "name_ja": iv["individual_id"],
            "charge_move_1_type": charge_move_1["type"],
            "charge_move_2_type": charge_move_2["type"],
            "charge_move_1_ja": charge_move_1["name_ja"],
            "charge_move_2_ja": charge_move_2["name_ja"],
        }
        type_df = pd.concat([type_df, pd.DataFrame([row])], axis=0)


    # 全タイプ（日本語表記）
    all_types = list(TYPE_CHART.keys())
    all_types_ja = [TYPE_JA[t] for t in all_types]

    # 結果を格納する dict
    coverage = {TYPE_JA[t]: [] for t in all_types}

    # 3体の処理
    for _, row in type_df.iterrows():
        pname = row["name_ja"]

        # チャージわざを2つまで取得
        charge_moves = []
        if pd.notna(row["charge_move_1_type"]):
            charge_moves.append((row["charge_move_1_type"], row["charge_move_1_ja"]))
        if pd.notna(row["charge_move_2_type"]):
            charge_moves.append((row["charge_move_2_type"], row["charge_move_2_ja"]))

        # 各チャージわざがどのタイプに抜群か判定
        for move_type, move_name in charge_moves:
            chart = TYPE_CHART.get(move_type, {})

            for def_type, mult in chart.items():
                if mult > 1.0:  # ばつぐん判定
                    coverage[TYPE_JA[def_type]].append(
                        f"{move_name}（{pname}）"
                    )

    # DataFrame に変換
    df = pd.DataFrame({
        "相手のタイプ": list(coverage.keys()),
        "ばつぐんを取れるわざ": [", ".join(v) if v else "" for v in coverage.values()]
    })

    return df
