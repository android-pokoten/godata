
def render_header():
    import streamlit as st

    st.set_page_config(page_title="PokémonGO Data Viewer", layout="wide")

    # 上部余白を縮小
    st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
