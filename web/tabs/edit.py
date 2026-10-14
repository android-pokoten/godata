import streamlit as st
import pandas as pd
import os
from pathlib import Path

CSV_FILES = {
    #"個体データ (individuals.csv)": "data/individuals.csv",
    #"対戦相手データ (opponents.csv)": "data/opponents.csv",
    "種族データ (species.csv)": "data/species.csv",
    "技データ (moves.csv)": "data/moves.csv",
    #"対戦ログ(battle_log.csv)": "data/battle_log.csv",
}

def render_editer(csv_files=CSV_FILES):
    st.header("CSV 編集ツール")

    col1, col2 = st.columns(2)

    with col1:
        # ① 編集する CSV を選択
        selected_label = st.selectbox("編集する CSV を選択", list(csv_files.keys()))
        selected_path = csv_files[selected_label]

        # ② CSV 読み込み
        if os.path.exists(selected_path):
            df = pd.read_csv(selected_path)
        else:
            st.warning("ファイルが存在しません")
            st.stop()

    with col2:
        # インポート
        uploaded_file = st.file_uploader(
            "CSVインポート",
            type=["csv"]
        )
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            st.success(f"{len(df)} 件のデータを読み込みました")

    st.write(f"**{selected_label} を編集**")

    # ③ DataFrame を編集可能にする
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        width="stretch"
    )

    col1, col2 = st.columns(2)

    with col1:
        # ④ 保存ボタン
        if st.button("保存", key=f"{selected_path}"):
            edited_df.to_csv(selected_path, index=False)
            st.success("保存しました！")

    with col2:
        # エクスポート
        csv_data = edited_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="CSV エクスポート",
            data=csv_data,
            file_name=Path(csv_files[selected_label]).name,
            mime="text/csv"
            )
