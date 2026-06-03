FROM python:3.12-slim

RUN apt update
RUN apt install -y python3-pip git
RUN pip install streamlit
WORKDIR /data
