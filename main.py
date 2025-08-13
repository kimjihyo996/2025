# 🎇✨ 별자리 럭키 랭킹 & 오늘의 할 일 추천 ✨🎇
# Streamlit app

import streamlit as st
import datetime as dt
import random
import hashlib
import requests
from functools import lru_cache

st.set_page_config(
    page_title="오늘의 별자리 운세",
    page_icon="✨",
    layout="wide",
)

# ---------- 스타일 ----------
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
* {font-family: 'Pretendard', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif}
.main-title{font-size:40px;font-weight:800;background:linear-gradient(90deg,#ff7af5,#ffd36e,#7af5ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{opacity:.85}
.badge{display:inline-block;padding:6px 12px;border-radius:999px;background:linear-gradient(90deg,#ffe680,#ffd1e8);font-weight:600}
.rank-card{border-radius:20px;padding:18px;background:linear-gradient(180deg,rgba(255,255,255,.7),rgba(255,255,255,.4));backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.4);
box-shadow:0 10px 28px rgba(0,0,0,.08)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.sign-pill{padding:6px 10px;border-radius:999px;background:#0000000d;border:1px solid #00000014}
.tip{border-left:6px solid #ffd36e;background:#fff9e6;padding:12px;border-radius:12px}
.emoji{font-size:22px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kpi{border-radius:16px;padding:14px;background:#ffffffd9;border:1px solid #00000010;text-align:center}
.kpi h3{margin:0;font-size:16px}
.kpi .val{font-size:28px;font-weight:800}
.celebs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.celebs .card{border-radius:16px;overflow:hidden;border:1px solid #00000012;background:#fff}
.celebs .card img{width:100%;height:160px;object-fit:cover}
.celebs .card .name{padding:8px 10px;font-weight:700;text-align:center}
.footer{opacity:.6;font-size:13px}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)

# ---------- 데이터 ----------
SIGNS = [
    ("양자리", "Aries", "♈"), ("황소자리", "Taurus", "♉"), ("쌍둥이자리", "Gemini", "♊"),
    ("게자리", "Cancer", "♋"), ("사자자리", "Leo", "♌"), ("처녀자리", "Virgo", "♍"),
    ("천칭자리", "Libra", "♎"), ("전갈자리", "Scorpio", "♏"), ("사수자리", "Sagittarius", "♐"),
    ("염소자리", "Capricorn", "♑"), ("물병자리", "Aquarius", "♒"), ("물고기자리", "Pisces", "♓"),
]

SIGN_KO = [s[0] for s in SIGNS]
SIGN_EN = {s[0]: s[1] for s in SIGNS}
SIGN_EMOJI = {s[0]: s[2] for s in SIGNS}

ELEMENT = {
    "양자리": "불", "사자자리": "불", "사수자리": "불",
    "황소자리": "흙", "처녀자리": "흙", "염소자리": "흙",
    "쌍둥이자리": "공기", "천칭자리": "공기", "물병자리": "공기",
    "게자리": "물", "전갈자리": "물", "물고기자리": "물",
}

SUGGESTIONS = {
    "불": ["🔥 에너지 폭발! 가벼운 달리기", "🎤 노래방에서 스트레스 시원하게", "🌶️ 매운 음식 도전"],
    "흙": ["🌿 산책하며 사진 찍기", "🍞 베이커리 신상 탐방", "🧹 책상 정리하고 새 출발"],
    "공기": ["🗣️ 친구에게 먼저 연락", "📚 카페에서 공부/독서", "🎧 새 플레이리스트 만들기"],
    "물": ["🛁 따뜻한 반신욕", "🍵 말차/허브티로 힐링", "🎨 감성 일기/드로잉"],
}

# (한국/글로벌) 유명인: 이름 -> 위키피디아 검색용 제목
CELEB_BY_SIGN = {
    "양자리": ["Lady Gaga", "Emma Watson", "오세훈 (가수)"],
    "황소자리": ["아이유", "David Beckham"],
    "쌍둥이자리": ["Angelina Jolie", "카니예 웨스트"],
    "게자리": ["Selena Gomez", "Ariana Grande"],
    "사자자리": ["Jennifer Lopez", "Barack Obama"],
    "처녀자리": ["정국", "Beyoncé"],
    "천칭자리": ["지민 (가수)", "Kim Kardashian"],
    "전갈자리": ["Leonardo DiCaprio", "Drake (래퍼)"],
    "사수자리": ["Taylor Swift", "진 (가수)"],
    "염소자리": ["뷔 (가수)", "제니 (가수)"],
    "물병자리": ["Harry Styles", "제이홉"],
    "물고기자리": ["SUGA", "Rihanna"],
}

# ---------- 함수 ----------

def seed_by_date(sign_ko: str, date: dt.date) -> random.Random:
    key = f"{date.isoformat()}::{sign_ko}::lucky"
    h = hashlib.sha256(key.encode()).hexdigest()
    seed_val = int(h[:16], 16)
    return random.Random(seed_val)

@lru_cache(maxsize=128)
def wiki_thumb(title: str):
    """위키피디아 썸네일 URL 가져오기 (없으면 None)"""
    try:
        url = f"https://{('ko' if any(ord(c) > 127 for c in title) else 'en')}.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(title)
        r = requests.get(url, timeout=6)
        if r.ok:
            data = r.json()
            thumb = data.get('thumbnail', {}).get('source')
            if thumb:
                return thumb
    except Exception:
        pass
    return None


def today_rank_all(date: dt.date):
    # 12자리 운세 점수 산출 (0~100)
    scores = []
    for sign in SIGN_KO:
        rng = seed_by_date(sign, date)
        score = rng.randint(55, 100)  # 대체로 좋은 하루 ✨
        scores.append((sign, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def detail_fortune(sign: str, date: dt.date):
    rng = seed_by_date(sign, date)
    def roll():
        return rng.randint(60, 99)
    love = roll(); money = roll(); study = roll(); health = roll()
    element = ELEMENT[sign]
    tips = random.sample(SUGGESTIONS[element], k=min(3, len(SUGGESTIONS[element])))
    lucky_color = rng.choice(["💜 보라", "💙 파랑", "💚 초록", "❤️ 빨강", "🧡 주황", "💛 노랑", "🖤 블랙", "🤍 화이트", "🤎 브라운"])
    lucky_item = rng.choice(["📸 필름카메라", "🎧 무선이어폰", "🍫 초콜릿", "🧴 핸드크림", "📒 노트", "💄 틴트", "🥤 아이스라떼", "📿 팔찌"])
    msg = rng.choice([
        "작은 씬스틸러가 되는 날!", "우연이 자주 겹치는 날 🔮", "집중력이 폭발하는 꿀컨디션!",
        "좋아하는 사람과 거리 좁히기 딱 좋은 타이밍 💘", "새 시도를 두려워하지 마세요 ✨",
    ])
    return {
        "love": love, "money": money, "study": study, "health": health,
        "tips": tips, "lucky_color": lucky_color, "lucky_item": lucky_item,
        "message": msg,
    }

# ---------- 헤더 ----------
col1, col2 = st.columns([1,1])
with col1:
    st.markdown("<div class='badge'>✨ 오늘의 포춘 ✨</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-title'>별자리 럭키 랭킹 & 해야 할 일 추천</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub'>이모지 잔뜩🎊 반짝이 팡팡🎉 오늘의 기분을 올려줄 포춘 피드 🔮</div>", unsafe_allow_html=True)
with col2:
    st.markdown("""<div style='text-align:right;font-size:52px'>🌈💫🌟✨</div>""", unsafe_allow_html=True)

# ---------- 입력 ----------
today = dt.date.today()
left, right = st.columns([1,2])
with left:
    sign = st.selectbox("내 별자리", options=SIGN_KO, index=0, help="양자리~물고기자리 순")
    st.write(f"선택한 별자리: {SIGN_EMOJI[sign]} **{sign}**")
with right:
    st.date_input("오늘 날짜", value=today, help="날짜별로 랭킹이 바뀌어요 ✨")

st.divider()

# ---------- 랭킹 영역 ----------
st.markdown("### 🏆 오늘의 별자리 랭킹")
rankings = today_rank_all(today)

# 상위 3 카드를 강조
top3_cols = st.columns(3)
for idx in range(3):
    s, sc = rankings[idx]
    with top3_cols[idx]:
        st.markdown(f"""
        <div class='rank-card'>
            <div style='font-size:18px;font-weight:800'>#{idx+1} {SIGN_EMOJI[s]} {s}</div>
            <div style='font-size:42px;font-weight:800'>{sc}점 ✨</div>
            <div class='sub'>오늘의 기운이 맥스치에 가까워요!</div>
        </div>
        """, unsafe_allow_html=True)

with st.expander("전체 랭킹 보기 🔽", expanded=False):
    grid_items = []
    for i, (s, sc) in enumerate(rankings, start=1):
        grid_items.append(f"<div class='sign-pill'>#{i} {SIGN_EMOJI[s]} <b>{s}</b> — <b>{sc}</b></div>")
    st.markdown(f"<div class='grid'>{''.join(grid_items)}</div>", unsafe_allow_html=True)

st.divider()

# ---------- 내 별자리 상세 ----------
st.markdown(f"## {SIGN_EMOJI[sign]} {sign} — 오늘의 디테일")
info = detail_fortune(sign, today)

# KPIs
st.markdown("<div class='kpis'>" +
            f"<div class='kpi'><h3>💘 사랑운</h3><div class='val'>{info['love']}%</div></div>"+
            f"<div class='kpi'><h3>💰 금전운</h3><div class='val'>{info['money']}%</div></div>"+
            f"<div class='kpi'><h3>📚 학업/일</h3><div class='val'>{info['study']}%</div></div>"+
            f"<div class='kpi'><h3>💪 건강</h3><div class='val'>{info['health']}%</div></div>"+
            "</div>", unsafe_allow_html=True)

st.markdown(f"<div class='tip'><span class='emoji'>💡</span> {info['message']}<br/>"
            f"<b>라키 컬러</b>: {info['lucky_color']} &nbsp;|&nbsp; <b>라키 아이템</b>: {info['lucky_item']}</div>",
            unsafe_allow_html=True)

# 추천 액션
st.markdown("### ✅ 오늘 하면 좋은 일 (추천)")
a = info['tips']
for t in a:
    st.markdown(f"- {t}")

st.divider()

# ---------- 유명인 카드 ----------
st.markdown(f"### 🌟 {sign}와(과) 같은 별자리 스타")

celeb_list = CELEB_BY_SIGN.get(sign, [])

def celeb_card(name: str):
    img = wiki_thumb(name)
    if img is None:
        # 기본 이모지 이미지
        st.markdown(f"<div class='card'><div style='height:160px;display:flex;align-items:center;justify-content:center;font-size:46px'>🎤</div><div class='name'>{name}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card'><img src='{img}'/><div class='name'>{name}</div></div>", unsafe_allow_html=True)

cards_col = st.columns(3)
for i, name in enumerate(celeb_list[:6]):
    with cards_col[i % 3]:
        celeb_card(name)

st.caption("이미지는 위키피디아 공개 썸네일을 사용합니다. (가끔 썸네일이 없을 수 있어요)")

# 축하 애니메이션
if rankings[0][0] == sign:
    st.balloons()
else:
    st.snow()

st.markdown("<div class='footer'>※ 이 앱은 오락용 컨텐츠입니다. 과학적 근거 X, 오늘 하루를 즐겁게 만드는 용도 💖</div>", unsafe_allow_html=True)
