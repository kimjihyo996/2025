import numpy as np
from PIL import Image, ImageOps
import streamlit as st
from sklearn.cluster import KMeans

# =========================
# Pillow LANCZOS 호환 처리
# =========================
try:
    RESAMPLE = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = Image.LANCZOS

# =========================
# Helper Functions
# =========================
def to_numpy(img: Image.Image) -> np.ndarray:
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)

def resize_for_analysis(img: Image.Image, max_side: int = 512) -> Image.Image:
    w, h = img.size
    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        return img.resize((int(w * scale), int(h * scale)), RESAMPLE)
    return img

def get_dominant_colors(img: Image.Image, k: int = 5):
    """대표 색상 K개 뽑기"""
    small = resize_for_analysis(img, 256)
    arr = to_numpy(small).reshape(-1, 3).astype(np.float32)

    if arr.shape[0] > 50000:  # 속도 위해 샘플링
        idx = np.random.choice(arr.shape[0], 50000, replace=False)
        arr = arr[idx]

    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(arr)
    centers = np.clip(km.cluster_centers_.astype(int), 0, 255)
    return [tuple(map(int, c)) for c in centers]

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def color_swatches(colors):
    cols = st.columns(len(colors))
    for i, c in enumerate(colors):
        hexv = rgb_to_hex(c)
        with cols[i]:
            st.markdown(
                f"<div style='border-radius:12px;border:1px solid #eee;height:60px;background:{hexv}'></div>",
                unsafe_allow_html=True,
            )
            st.caption(hexv.upper())

# =========================
# 브랜드 & 코디 규칙
# =========================
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

# =========================
# Streamlit App
# =========================
def main():
    st.set_page_config(page_title="AI 패션 코디네이터", page_icon="👗", layout="wide")
    st.title("👗 AI 패션 코디네이터")
    st.caption("얼굴 사진을 업로드하면 어울릴만한 브랜드와 코디를 추천합니다!")

    style = st.sidebar.selectbox("스타일 선택", list(BRANDS.keys()), index=0)
    k_colors = st.sidebar.slider("대표 색상 개수", 3, 8, 5)

    uploaded = st.file_uploader("얼굴 사진을 업로드하세요", type=["jpg","jpeg","png"])
    if uploaded is None:
        st.info("사진을 업로드하면 분석이 시작됩니다.")
        return

    img = Image.open(uploaded)
    img_preview = ImageOps.exif_transpose(img.copy())
    st.image(img_preview, caption="업로드한 이미지", use_column_width=True)

    # 대표 색상 뽑기
    colors = get_dominant_colors(img_preview, k=k_colors)
    st.subheader("🎨 대표 색상 팔레트")
    color_swatches(colors)

    # 브랜드 추천
    st.subheader("🏷️ 추천 브랜드")
    st.write(", ".join(BRANDS[style]))

    # 코디 아이디어
    st.subheader("🧩 코디 아이디어")
    for s in OUTFITS[style]:
        st.markdown(f"- {s}")

if __name__ == "__main__":
    main()
streamlit>=1.35.0
Pillow>=9.0.0
numpy>=1.23.0
scikit-learn>=1.2.0


