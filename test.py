import numpy as np
from PIL import Image, ImageOps
import streamlit as st

# ============ Pillow LANCZOS 호환 ============
try:
    RESAMPLE = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = Image.LANCZOS

# ============ Helper ============
def to_numpy(img: Image.Image) -> np.ndarray:
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)

def resize_for_analysis(img: Image.Image, max_side: int = 128) -> Image.Image:
    w, h = img.size
    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        return img.resize((int(w * scale), int(h * scale)), RESAMPLE)
    return img

def get_simple_palette(img: Image.Image, k: int = 5):
    small = resize_for_analysis(img, 128)
    arr = to_numpy(small).reshape(-1, 3)
    arr = (arr // 16) * 16
    uniq, counts = np.unique(arr, axis=0, return_counts=True)
    idx = np.argsort(-counts)[:k]
    return [tuple(map(int, uniq[i])) for i in idx]

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def color_swatches(colors):
    cols = st.columns(len(colors))
    for i, c in enumerate(colors):
        hexv = rgb_to_hex(c)
        with cols[i]:
            st.markdown(
                f"<div style='border-radius:12px;border:1px solid #ccc;height:80px;background:{hexv}'></div>",
                unsafe_allow_html=True,
            )
            st.caption(f"**{hexv.upper()}**")

# ============ 데이터 ============
BRANDS = {
    "street": ["Uniqlo U", "Diesel", "BAPE", "Carhartt WIP", "Off-White"],
    "minimal": ["Muji", "COS", "A.P.C.", "Jil Sander", "Lemaire"],
    "classic": ["Uniqlo", "Ralph Lauren", "Tommy Hilfiger", "Burberry"],
    "techwear": ["Nike ACG", "Stone Island", "ACRONYM"],
    "y2k": ["Bershka", "Diesel D logo", "Blumarine", "Miu Miu"],
}

OUTFITS = {
    "street": ["와이드 데님 + 그래픽 티셔츠", "카고팬츠 + 후드", "트랙팬츠 + 스니커즈"],
    "minimal": ["울 팬츠 + 니트", "와이드 치노 + 셔츠", "모노톤 자켓+팬츠 셋업"],
    "classic": ["옥스포드 셔츠 + 치노", "네이비 블레이저 + 그레이 팬츠", "니트 폴로 + 로퍼"],
    "techwear": ["방수 셸자켓 + 카고", "소프트셸 + 트레킹 슈즈"],
    "y2k": ["로우라이즈 데님 + 베이비 티", "트랙자켓 + 미니스커트"],
}

# ============ Streamlit UI ============
def main():
    st.set_page_config(page_title="AI 패션 코디네이터", page_icon="👗", layout="wide")
    st.markdown("<h1 style='text-align:center;'>👗 AI 패션 코디네이터</h1>", unsafe_allow_html=True)
    st.write("얼굴 사진을 업로드하면 대표 색상, 어울리는 브랜드, 코디 아이디어를 추천해드립니다.")

    style = st.sidebar.selectbox("스타일 선택", list(BRANDS.keys()), index=0)
    k_colors = st.sidebar.slider("대표 색상 개수", 3, 8, 5)

    uploaded = st.file_uploader("📸 얼굴 사진 업로드", type=["jpg","jpeg","png"])
    if not uploaded:
        st.info("사진을 올리면 분석이 시작돼요!")
        return

    img = Image.open(uploaded)
    img_preview = ImageOps.exif_transpose(img.copy())
    st.image(img_preview, caption="업로드한 이미지", use_container_width=True)

    # 팔레트 추출
    colors = get_simple_palette(img_preview, k=k_colors)
    st.subheader("🎨 대표 색상 팔레트")
    color_swatches(colors)

    # 브랜드 카드
    st.subheader("🏷️ 추천 브랜드")
    cols = st.columns(3)
    for i, b in enumerate(BRANDS[style]):
        with cols[i % 3]:
            st.markdown(
                f"<div style='border:1px solid #ddd;border-radius:15px;padding:15px;margin:5px;background:#fafafa;'><b>{b}</b><br><span style='color:#888;font-size:0.9em;'>스타일: {style}</span></div>",
                unsafe_allow_html=True,
            )

    # 코디 아이디어
    st.subheader("🧩 코디 아이디어")
    for s in OUTFITS[style]:
        st.markdown(f"- {s}")

    st.success("✨ 분석 완료! 사이드바 옵션을 바꿔보세요.")

if __name__ == "__main__":
    main()


