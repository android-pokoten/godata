# タイプ別の下線を引く
'''
input: type1 > 文字列、タイプ名(fire, walter など)
output: > 文字列、下線を引くインラインスタイルシート
'''
def type_with_underline(t):
    from core.type import TYPE_JA, TYPE_COLOR

    color = TYPE_COLOR[t]
    return f'''
        <span style="
            background: linear-gradient(
                to bottom,
                transparent 65%,
                {color} 85%,
                transparent 100%
            );
            padding: 0 2px;
        ">{TYPE_JA[t]}</span>
    '''

# 限定わざにハイライトを追加
'''
input: row > DataFrameの行
output: > 文字列、限定わざのハイライトを描写するインラインスタイルシート
'''
def highlight_legacy(row):
    from core.type import TYPE_COLOR, ja_to_en_type

    styles = []
    for col, val in row.items():
        if col == "type":
            styles.append(f"background: linear-gradient(to bottom, transparent 65%,  {TYPE_COLOR[ja_to_en_type(val)]} 85%, transparent 100%);")
        elif col == "name_ja" and "＊" in val:
                styles.append(f"background: linear-gradient(to left, transparent 98%,  red 99%, transparent 100%);")
        else:
            styles.append("")
    return styles

# タイプ一致のわざをハイライトする
'''
input: row > DataFrameの行
output: > 文字列、タイプ一致わざのハイライトを描写するインラインスタイルシート
'''
def highlight_stab(row):
    return ['background-color: #fff3cd' if row["一致"] == "⭐" else '' for _ in row]

# スペシャルわざのゲージを表示
def render_charge_gauge(energy, turn, cost, fast_type, charge_type):
    from core.type import TYPE_COLOR

    energy = abs(int(float(energy)))
    turn = abs(int(float(turn)))
    cost = abs(int(float(cost)))

    fast_times = ((cost +  energy - 1) // energy)
    total_turn = fast_times * turn
    
    blocks = []
    for i in range(1, total_turn + 1):
        blocks.append('■')
        if i % turn == 0:
            blocks.append('|')
        else:
            blocks.append(' ')
        
    guage = "".join(blocks)

    return f'<span style="color: {TYPE_COLOR[fast_type]};">{guage}</span><span style="color: {TYPE_COLOR[charge_type]};">[{total_turn} turns/ {fast_times} times]</span>'

# わざのタイプを色分け
def draw_types(move_type, move_name, tooltip):
    from core.type import TYPE_COLOR, TYPE_JA

    return f'(<span title="{tooltip}" style="background: linear-gradient(to bottom, transparent 65%,  {TYPE_COLOR[move_type]} 85%, transparent 100%);">{TYPE_JA[move_type]}</span>) {move_name}'
