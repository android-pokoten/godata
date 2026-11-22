from core.header import render_header
import streamlit as st

render_header()

st.write("""
^



・Basic Data：基本的なデータ  
＞種族値データ  
＞わざデータ  
＞シーズンごとのわざ調整データ  
＞タイプ相性表  


・Pokemon Box：手持ちデータ  
＞手持ち一覧  
＞特殊カップ出場可能ポケモン抽出  
＞手持ちデータ修正機能  


・Register：手持ちデータ登録

・Detail：ポケモンの詳細データ

・Param Checker：CP計算、進化後のCP計算

・Simulation：バトル時の各種シミュレート  
＞1vs1の対戦シミュレーション  
＞特定のポケモンと手持ちのポケモンの相性確認  
＞手持ち3体のパーティの相性補完確認  
＞特定のポケモン同士のダメージ計算  


・Battle Log：対戦ログの入力、閲覧  
＞対戦ログの登録  
＞ログの閲覧、相手ポケモンの出現数の確認  
＞ログの傾向分析  

""")