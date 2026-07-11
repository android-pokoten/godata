
# タイプ相性計算
'''
input: DataFrame、タイプ相性表
output: Styler、スタイル適用済みのタイプ相性表
'''
def style_type_relations(type_df):
    from core.type import TYPE_COLOR, TYPE_EN

    # ヘッダーセルにタイプごとの色付け
    def style_type_headers(df):
        # 列ヘッダーのスタイル
        col_styles = [
            {
                "selector": f"th.col_heading.level0.col{i}",
                "props": f"background-color: {TYPE_COLOR[TYPE_EN[col]]}; color: white; font-weight: bold;"
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

    # スタイル適用
    styled = (
        type_df
            .style.apply(highlight, axis=1)
            .set_table_styles(style_type_headers(type_df))  # ← 見出しだけ色付け
            .format("{:.2f}")  
    )

    return styled

# 攻撃タイプ相性一覧のスタイル
'''
input: DataFrame、タイプ相性表
output: styler、スタイル適用済みのタイプ相性表
'''
def style_attack_coverage_html(type_df):
    from core.type import TYPE_COLOR, TYPE_EN, TYPE_COLOR_LIGHT, ja_to_en_type
    
    def highlight(row):
        type_en = ja_to_en_type(row["相手のタイプ"])
        color = TYPE_COLOR_LIGHT.get(type_en, "#ffffff")

        return [f"background-color: {color};" for _ in row]

    # スタイル適用
    styled = (
        type_df
            .style.apply(highlight, axis=1)
    )

    return styled

# タイプ相性一覧のスタイル
'''
input: DataFrame、タイプ相性表
output: styler、スタイル適用済みのタイプ相性表
'''
def style_party_type_relations(type_df):
    from core.type import TYPE_COLOR, TYPE_EN, TYPE_COLOR_LIGHT, ja_to_en_type

    # ヘッダーセルにタイプごとの色付け
    def style_type_headers(df):
        col_styles = []
        # 列ヘッダーのスタイル
        for i, col in enumerate(df.columns):
            if col in TYPE_EN:
                props = f"background-color: {TYPE_COLOR[TYPE_EN[col]]}; color: white; font-weight: bold;"
            else:
                props = "background-color: #CCCCCC; color: black; font-weight: bold;"
            
            props += "writing-mode: vertical-rl; text-orientation: upright; padding: 6px 1px;"

            col_styles.append(
                {
                    "selector": f"th.col_heading.level0.col{i}",
                    "props": props
                }
            )
        return col_styles


    def highlight_sum_row(row):
        styles = []

        if row["NAME"] != "合計":
            # 合計以外の行の場合は 1 を中心に色付け
            for val in row:
                if isinstance(val, (int, float)):
                    if val >= 2.0:
                        styles.append("background-color: #ff9999")
                    elif val > 1.0:
                        styles.append("background-color: #ffcccc")
                    elif val == 1.0:
                        styles.append("background-color: #eeeeee; color: #eeeeee")
                    elif val > 0.39:
                        styles.append("background-color: #cce5ff")
                    else:
                        styles.append("background-color: #99ccff")
                else:
                    styles.append("")  # NAMEセル
        else:
            # 合計の行は 3 を中心に色付け
            for val in row:
                if isinstance(val, (int, float)):
                    if val >= 3.5:
                        styles.append("color: red; font-weight: bold;")
                    elif val <= 3:
                        styles.append("color: blue; font-weight: bold;")
                    else:
                        styles.append("")
                else:
                    styles.append("")  # NAMEセル
        return styles

    styled = (
        type_df.style
        .apply(highlight_sum_row, axis=1)
        .set_table_styles(style_type_headers(type_df))
        .format({
            col: "{:.2f}" for col in type_df.columns if col != "NAME"
        })  
    )

    return styled