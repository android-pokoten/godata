

# コンテナイメージのビルド (Containerfile があるディレクトリで実行)
podman build -t godata .

# コンテナを起動して Streamlit の WebUI を起動する
podman run -it --rm -v .:/data -p 8501:8501 godata streamlit run web/gbl.py
