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
.rank-card{border-radius:22px;padding:20px;background:linear-gradient(180deg,rgba(255,255,255,.85),rgba(255,255,255,.55));backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.5);
box-shadow:0 16px 34px rgba(0,0,0,.08)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}
.sign-pill{padding:8px 12px;border-radius:999px;background:#0000000d;border:1px solid #00000014}
.tip{border-left:6px solid #ffd36e;background:#fff9e6;padding:14px;border-radius:12px}
.emoji{font-size:22px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kpi{border-radius:16px;padding:16px;background:#ffffffd9;border:1px solid #00000010;text-align:center}
.kpi h3{margin:0;font-size:16px}
.kpi .val{font-size:30px;font-weight:800}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.card{border-radius:18px;overflow:hidden;border:1px solid #00000012;background:#fff}
.card img{width:100%;height:180px;object-fit:cover}
.card .name{padding:10px 12px;font-weight:800;text-align:center}
.card .meta{padding:0 12px 12px 12px;text-align:center;color:#666;font-size:13px}
.footer{opacity:.6;font-size:13px}
.marquee{white-space:nowrap;overflow:hidden}
.marquee span{display:inline-block;padding-left:100%;animation:scroll 18s linear infinite}
@keyframes scroll{0%{transform:translateX(0)}100%{transform:translateX(-100%)}}
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
    "불": ["🔥 에너지 폭발! 하이킥 산책", "🎤 노래방에서 리즈곡 부르기", "🌶️ 매운 음식 도전"],
    "흙": ["🌿 초록 카페에서 사진찍기", "🍞 동네 베이커리 신상 투어", "🧹 책상 정리하고 새 시작"],
    "공기": ["🗣️ 먼저 안부 보내기", "📚 도서관에서 1시간 집중", "🎧 새 플레이리스트 만들기"],
    "물": ["🛁 따뜻한 반신욕", "🍵 말차/허브티로 힐링", "🎨 감성 일기/드로잉"],
}

# (글로벌) 유명인 예시 — 기본 카드용
CELEB_BY_SIGN = {
    "양자리": ["Lady Gaga", "Emma Watson"],
    "황소자리": ["아이유", "David Beckham"],
    "쌍둥이자리": ["Angelina Jolie", "Kanye West"],
    "게자리": ["Selena Gomez", "Ariana Grande"],
    "사자자리": ["Jennifer Lopez", "Barack Obama"],
    "처녀자리": ["정국", "Zendaya"],
    "천칭자리": ["지민 (가수)", "Kim Kardashian"],
    "전갈자리": ["Leonardo DiCaprio", "Drake (래퍼)"],
    "사수자리": ["Taylor Swift", "진 (가수)"],
    "염소자리": ["뷔 (가수)", "제니 (가수)"],
    "물병자리": ["Harry Styles", "제이홉"],
    "물고기자리": ["SUGA", "Rihanna"],
}

# ▼▼ K‑Idol 프리셋 (검증 필요시 사용자 입력으로 보완 가능) ▼▼
# 간편 매칭을 위한 샘플: 이름, 그룹, 별자리, 위키 제목
IDOLS = [
    # RIIZE
    {"name": "SHOTARO", "group": "RIIZE", "sign": "사수자리", "wiki": "Shotaro (singer)"},
    {"name": "SUNGCHAN", "group": "RIIZE", "sign": "처녀자리", "wiki": "Sungchan"},
    {"name": "SOHEE", "group": "RIIZE", "sign": "전갈자리", "wiki": "Sohee (singer)"},
    {"name": "WONBIN", "group": "RIIZE", "sign": "물고기자리", "wiki": "Wonbin (singer)"},
    {"name": "EUNSEOK", "group": "RIIZE", "sign": "물고기자리", "wiki": "Eunseok"},
    {"name": "ANTON", "group": "RIIZE", "sign": "양자리", "wiki": "Anton (singer)"},
    # NCT (일부)
    {"name": "TAEYONG", "group": "NCT", "sign": "게자리", "wiki": "Taeyong"},
    {"name": "MARK", "group": "NCT", "sign": "사자자리", "wiki": "Mark Lee (singer)"},
    {"name": "JAEHYUN", "group": "NCT", "sign": "물병자리", "wiki": "Jaehyun"},
    {"name": "HAECHAN", "group": "NCT", "sign": "쌍둥이자리", "wiki": "Haechan"},
    {"name": "TEN", "group": "NCT", "sign": "물고기자리", "wiki": "Ten (singer)"},
    {"name": "JISUNG", "group": "NCT", "sign": "물병자리", "wiki": "Jisung (singer, born 2002)"},
    # 5세대 예시
    {"name": "ILLIT WONHEE", "group": "ILLIT", "sign": "쌍둥이자리", "wiki": "Wonhee"},
    {"name": "ILLIT MINJU", "group": "ILLIT", "sign": "물병자리", "wiki": "Minju (singer, born 2004)"},
    {"name": "TWS SHINYU", "group": "TWS", "sign": "물고기자리", "wiki": "Shinyu"},
    {"name": "TWS DOHOON", "group": "TWS", "sign": "사수자리", "wiki": "Dohoon"},
    {"name": "BABYMONSTER AHYEON", "group": "BABYMONSTER", "sign": "물고기자리", "wiki": "Ahyeon"},
]

GROUPS = sorted(list({i["group"] for i in IDOLS}))

# ---------- 유틸 ----------

def seed_by_date(sign_ko: str, date: dt.date) -> random.Random:
    key = f"{date.isoformat()}::{sign_ko}::lucky"
    h = hashlib.sha256(key.encode()).hexdigest()
    seed_val = int(h[:16], 16)
    return random.Random(seed_val)

@lru_cache(maxsize=256)
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
    scores = []
    for sign in SIGN_KO:
        rng = seed_by_date(sign, date)
        score = rng.randint(55, 100)
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
    vibe = rng.choice(["하이틴 무드🌈", "스포티 에너지💥", "러블리 감성💖", "시크&모던🖤", "내추럴 힐링🍃"])
    msg = rng.choice([
        "작은 씬스틸러가 되는 날!", "우연이 자주 겹치는 날 🔮", "집중력이 폭발하는 꿀컨디션!",
        "좋아하는 사람과 거리 좁히기 딱 좋은 타이밍 💘", "새 시도를 두려워하지 마세요 ✨",
    ])
    return {
        "love": love, "money": money, "study": study, "health": health,
        "tips": tips, "lucky_color": lucky_color, "lucky_item": lucky_item,
        "vibe": vibe, "message": msg,
    }

# ---------- 헤더 ----------
col1, col2 = st.columns([1,1])
with col1:
    st.markdown("<div class='badge'>✨ 오늘의 포춘 ✨</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-title'>별자리 럭키 랭킹 & K‑Idol 매칭</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub'>이모지 잔뜩🎊 반짝이 팡팡🎉 오늘 기분 올려줄 포춘 피드 🔮</div>", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class='marquee'><span>🌌 NCT · NCT WISH · RIIZE · 5세대 아이돌 매칭 업데이트! 🌠🌠🌠</span></div>""", unsafe_allow_html=True)

# ---------- 입력 ----------
today = dt.date.today()
left, right = st.columns([1,2])
with left:
    sign = st.selectbox("내 별자리", options=SIGN_KO, index=0, help="양자리~물고기자리 순")
    st.write(f"선택한 별자리: {SIGN_EMOJI[sign]} **{sign}**")
with right:
    st.date_input("오늘 날짜", value=today, help="날짜별로 랭킹이 바뀌어요 ✨")

# 그룹 필터
st.divider()
st.markdown("### 🧭 K‑Idol 그룹 필터")
g1, g2 = st.columns([2,3])
with g1:
    use_filter = st.toggle("특정 그룹만 보기", value=True)
with g2:
    selected_groups = st.multiselect("그룹 선택", options=["NCT","NCT WISH","RIIZE","ILLIT","TWS","BABYMONSTER"], default=["NCT","RIIZE"])

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
            <div style='font-size:44px;font-weight:800'>{sc}점 ✨</div>
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
            f"<b>라키 컬러</b>: {info['lucky_color']} &nbsp;|&nbsp; <b>라키 아이템</b>: {info['lucky_item']} &nbsp;|&nbsp; <b>오늘 무드</b>: {info['vibe']}</div>",
            unsafe_allow_html=True)

# 추천 액션
st.markdown("### ✅ 오늘 하면 좋은 일 (추천)")
for t in info['tips']:
    st.markdown(f"- {t}")

st.divider()

# ---------- 같은 별자리 스타 (기본) ----------
st.markdown(f"### 🌟 {sign}와(과) 같은 별자리 — 유명인")

def celeb_card(title: str, subtitle: str = ""):
    img = wiki_thumb(title)
    if img is None:
        st.markdown(f"<div class='card'><div style='height:180px;display:flex;align-items:center;justify-content:center;font-size:46px'>🎤</div><div class='name'>{title}</div><div class='meta'>{subtitle}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card'><img src='{img}'/><div class='name'>{title}</div><div class='meta'>{subtitle}</div></div>", unsafe_allow_html=True)

cards_col = st.columns(3)
for i, name in enumerate(CELEB_BY_SIGN.get(sign, [])[:6]):
    with cards_col[i % 3]:
        celeb_card(name)

# ---------- 같은 별자리 — K‑Idol 매칭 ----------
st.markdown(f"### 💚 {sign}와(과) 같은 별자리 — K‑Idol")

filtered = [i for i in IDOLS if i["sign"] == sign]
if use_filter and selected_groups:
    filtered = [i for i in filtered if i["group"] in selected_groups]

if not filtered:
    st.info("선택한 조건에 맞는 아이돌 카드가 아직 없어요. 사이드바에서 직접 추가해보세요! ✍️")
else:
    st.markdown("<div class='cards'>", unsafe_allow_html=True)
    for idol in filtered:
        title = idol.get("wiki") or idol["name"]
        img = wiki_thumb(title)
        if img is None:
            st.markdown(f"<div class='card'><div style='height:180px;display:flex;align-items:center;justify-content:center;font-size:46px'>⭐</div><div class='name'>{idol['name']} ({idol['group']})</div><div class='meta'>{idol['sign']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='card'><img src='{img}'/><div class='name'>{idol['name']} ({idol['group']})</div><div class='meta'>{idol['sign']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("이미지는 위키피디아 공개 썸네일을 사용합니다. 일부 인물/페이지는 썸네일이 없을 수 있어요.")

# ---------- 사이드바: 커스텀 아이돌 추가 ----------
st.sidebar.header("🧩 커스텀 아이돌 추가")
with st.sidebar.form("add_idol"):
    name = st.text_input("이름(필수)")
    group = st.text_input("그룹/설명", value="NCT WISH")
    bday = st.date_input("생일 (별자리 자동 계산)", value=dt.date(2004,1,1))
    wiki_title = st.text_input("위키 제목(선택)", help="이미지 자동 불러오기용. 없으면 이름으로 시도")
    submitted = st.form_submit_button("추가")

    def sign_from_bday(d: dt.date):
        m, d_ = d.month, d.day
        # 서양 12궁 기준
        if (m==3 and d_>=21) or (m==4 and d_<=19): return "양자리"
        if (m==4 and d_>=20) or (m==5 and d_<=20): return "황소자리"
        if (m==5 and d_>=21) or (m==6 and d_<=21): return "쌍둥이자리"
        if (m==6 and d_>=22) or (m==7 and d_<=22): return "게자리"
        if (m==7 and d_>=23) or (m==8 and d_<=22): return "사자자리"
        if (m==8 and d_>=23) or (m==9 and d_<=22): return "처녀자리"
        if (m==9 and d_>=23) or (m==10 and d_<=22): return "천칭자리"
        if (m==10 and d_>=23) or (m==11 and d_<=22): return "전갈자리"
        if (m==11 and d_>=23) or (m==12 and d_<=21): return "사수자리"
        if (m==12 and d_>=22) or (m==1 and d_<=19): return "염소자리"
        if (m==1 and d_>=20) or (m==2 and d_<=18): return "물병자리"
        return "물고기자리"

    if submitted:
        if name.strip():
            IDOLS.append({
                "name": name.strip(),
                "group": group.strip() or "K‑Idol",
                "sign": sign_from_bday(bday),
                "wiki": wiki_title.strip() or name.strip(),
            })
            st.success(f"추가 완료! {name} — {sign_from_bday(bday)}")
        else:
            st.warning("이름은 필수에요 ✨")

# 축하 애니메이션
if rankings[0][0] == sign:
    st.balloons()
else:
    st.snow()

st.markdown("<div class='footer'>※ 이 앱은 오락용 컨텐츠입니다. 과학적 근거 X, 오늘 하루를 즐겁게 만드는 용도 💖<br/>K‑Idol 프리셋은 참고용으로 일부 오차가 있을 수 있습니다. 정확한 생일/별자리는 직접 추가 기능을 이용해 주세요.</div>", unsafe_allow_html=True)
