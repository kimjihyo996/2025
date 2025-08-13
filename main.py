# 🎇✨ 별자리 럭키 랭킹 & 오늘의 할 일 추천 — K‑Idol 에디션 ✨🎇
# Streamlit app — 더 화려하고, NCT / NCT WISH / RIIZE / 5세대 아이돌 매칭 지원

import streamlit as st
import datetime as dt
import random
import hashlib
import requests
from functools import lru_cache

st.set_page_config(
    page_title="오늘의 별자리 운세 — K‑Idol",
    page_icon="🌌",
    layout="wide",
)

# ---------- 스타일 ----------
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
* {font-family: 'Pretendard', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif}
body {background: radial-gradient(1200px 600px at 10% 0%, #ffe6ff 0%, #fff 40%),
                 radial-gradient(1000px 500px at 90% 10%, #e6f7ff 0%, #fff 40%),
                 linear-gradient(180deg,#ffffffcc,#ffffffef)}
.main-title{font-size:46px;font-weight:800;background:linear-gradient(90deg,#ff7af5,#ffd36e,#7af5ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{opacity:.9}
.badge{display:inline-block;padding:8px 14px;border-radius:999px;background:linear-gradient(90deg,#ffe680,#ffd1e8);font-weight:700}
.rank-card{bord
