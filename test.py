# Create a Streamlit app (app.py), requirements.txt, and README.md for the user.
import os, textwrap, json, pathlib

base = "/mnt/data/ai-fashion-coordinator"
os.makedirs(base, exist_ok=True)

app_py = r"""
import io
import base64
from typing import List, Tuple, Dict
import numpy as np
from PIL import Image, ImageOps
import streamlit as st
from sklearn.cluster import KMeans

# =========================
# Helpers
# =========================

def to_numpy(img: Image.Image) -> np.ndarray:
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)

def resize_for_analysis(img: Image.Image, max_side: int = 512) -> Image.Image:
    w, h = img.size
    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img

def get_dominant_colors(img: Image.Image, k: int = 5) -> List[Tuple[int, int, int]]:
    """Return k dominant colors (RGB tuples) from image using KMeans."""
    small = resize_for_analysis(img, 256)
    arr = to_numpy(small).reshape(-1, 3).astype(np.float32)
    # Light blur via random sampling for speed
    if arr.shape[0] > 50000:
        idx = np.random.choice(arr.shape[0], 50000, replace=False)
        arr = arr[idx]
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    km.fit(arr)
    centers = np.clip(km.cluster_centers_.astype(int), 0, 255)
    # Sort by perceived luminance to get a nice order
    def luminance(c): return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]
    centers_list = [tuple(map(int, c)) for c in centers]
    centers_list.sort(key=luminance, reverse=True)
    return centers_list

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % rgb

def central_patch(img: Image.Image, size_ratio: float = 0.3) -> Image.Image:
    """Crop a central square patch (~face region proxy)."""
    w, h = img.size
    s = int(min(w, h) * size_ratio)
    cx, cy = w // 2, h // 2
    left = max(cx - s // 2, 0)
    upper = max(cy - s // 2, 0)
    right = min(left + s, w)
    lower = min(upper + s, h)
    return img.crop((left, upper, right, lower))

def estimate_undertone(img: Image.Image) -> Dict[str, float]:
    """
    Very lightweight skin/undertone guess using central patch average.
    Returns {'warm_score': x, 'cool_score': y, 'neutral_score': z}
    """
    patch = central_patch(resize_for_analysis(img, 256), 0.4)
    arr = to_numpy(patch).astype(np.float32) / 255.0
    # focus on low-saturation, mid-lightness pixels to approximate skin
    # convert to HSL-ish via simple approach
    r, g, b = arr[...,0], arr[...,1], arr[...,2]
    cmax = arr.max(axis=-1)
    cmin = arr.min(axis=-1)
    delta = cmax - cmin
    light = (cmax + cmin) / 2.0
    sat = np.where(delta == 0, 0, delta / (1 - np.abs(2*light - 1) + 1e-6))
    mask = (sat < 0.35) & (light > 0.2) & (light < 0.85)
    if mask.sum() < 100:
        # fallback to full patch
        mask = np.ones_like(light, dtype=bool)
    mean_rgb = np.array([r[mask].mean(), g[mask].mean(), b[mask].mean()])
    # Warm if R is notably higher than B and slightly higher than G
    warm_score = float(np.clip((mean_rgb[0] - mean_rgb[2]) * 2 + (mean_rgb[0] - mean_rgb[1]), -1, 1))
    # Cool if B is higher than R and G
    cool_score = float(np.clip((mean_rgb[2] - mean_rgb[0]) * 2 + (mean_rgb[2] - mean_rgb[1]), -1, 1))
    # Neutral otherwise
    neutral_score = float(1 - abs(warm_score) - abs(cool_score))
    return {
        "warm_score": warm_score,
        "cool_score": cool_score,
        "neutral_score": neutral_score
    }

def classify_season(undertone: Dict[str, float], brightness_hint: float) -> str:
    """
    Map undertone + brightness to one of seasonal palettes (Spring/Warm, Summer/Cool, Autumn/Warm Deep, Winter/Cool Deep).
    brightness_hint in [0,1].
    """
    warm = undertone["warm_score"]
    cool = undertone["cool_score"]
    if warm > cool:
        if brightness_hint > 0.55:
            return "Spring (Warm & Bright)"
        else:
            return "Autumn (Warm & Deep)"
    else:
        if brightness_hint > 0.55:
            return "Summer (Cool & Soft)"
        else:
            return "Winter (Cool & Deep)"

def image_brightness(img: Image.Image) -> float:
    arr = to_numpy(resize_for_analysis(img, 256)).astype(np.float32) / 255.0
    # perceived luminance
    lum = 0.2126*arr[...,0] + 0.7152*arr[...,1] + 0.0722*arr[...,2]
    return float(lum.mean())

# =========================
# Brand Knowledge (simple rules)
# =========================

BRANDS = {
    "street": {
        "low": ["Uniqlo U", "GU", "Nike", "Adidas", "New Balance", "Stüssy"],
        "mid": ["Carhartt WIP", "C.P. Company", "A.P.C.", "Diesel", "BAPE"],
        "high": ["Off-White", "Palm Angels", "AMBUSH", "Maison Mihara", "Undercover"]
    },
    "minimal": {
        "low": ["Muji", "COS (sale)", "Zara (minimal line)", "H&M Studio"],
        "mid": ["COS", "A.P.C.", "Our Legacy", "Studio Nicholson"],
        "high": ["Lemaire", "Jil Sander", "The Row", "Maison Margiela (line 10)"]
    },
    "classic": {
        "low": ["Uniqlo", "Mango", "Spao (tailored)", "Arket"],
        "mid": ["Ralph Lauren", "Tommy Hilfiger", "Brooks Brothers", "A.P.C."],
        "high": ["AMI Paris", "Burberry", "Acne Studios", "Paul Smith"]
    },
    "avant": {
        "low": ["COS (sculptural)", "Zara SRPLS"],
        "mid": ["Issey Miyake Pleats", "Needles", "Kapital"],
        "high": ["Comme des Garçons", "Rick Owens", "Yohji Yamamoto", "Undercover"]
    },
    "techwear": {
        "low": ["Uniqlo (Blocktech)", "Decathlon Quechua", "Nike ACG (sale)"],
        "mid": ["And Wander", "Snow Peak", "Goldwin", "Stone Island Shadow"],
        "high": ["ACRONYM", "Veilance", "GORE-TEX Pro lines"]
    },
    "y2k": {
        "low": ["Bershka", "H&M", "Forever 21"],
        "mid": ["Diesel (D logo)", "GCDS", "Mschf (apparel)", "Ksubi"],
        "high": ["Blumarine", "Miu Miu", "Marine Serre"]
    }
}

PALETTE_HINTS = {
    "Spring (Warm & Bright)": ["ivory", "camel", "coral", "mint", "warm navy"],
    "Autumn (Warm & Deep)": ["tan", "olive", "rust", "mustard", "chocolate"],
    "Summer (Cool & Soft)": ["cool gray", "dusty rose", "lavender", "sage", "soft navy"],
    "Winter (Cool & Deep)": ["black", "optic white", "charcoal", "cobalt", "crimson"]
}

def filter_brands(style: str, budget: str, season: str, gender: str) -> List[str]:
    """Combine by style + budget, then lightly re-rank by palette-season match."""
    base = BRANDS.get(style, {}).get(budget, [])
    # very light re-weighting: winter/summer -> brands known for crisp neutrals; autumn/spring -> earthy/warm houses
    weight = []
    for b in base:
        w = 0
        if season.startswith("Winter") or season.startswith("Summer"):
            if b in ["COS", "A.P.C.", "Studio Nicholson", "Jil Sander", "The Row", "Acne Studios", "Arket", "Uniqlo", "Muji"]:
                w += 1
        if season.startswith("Autumn") or season.startswith("Spring"):
            if b in ["Diesel", "Kapital", "Needles", "Ralph Lauren", "Paul Smith", "Burberry", "C.P. Company"]:
                w += 1
        # light gender expression bias (purely heuristic, optional)
        if gender == "Feminine" and b in ["AMI Paris", "Miu Miu", "Blumarine", "Pleats Please", "Acne Studios"]:
            w += 0.5
        if gender == "Masculine" and b in ["Stone Island Shadow", "ACRONYM", "Carhartt WIP", "C.P. Company"]:
            w += 0.5
        weight.append((w, b))
    weight.sort(reverse=True)
    return [b for _, b in weight]

def color_swatches(colors: List[Tuple[int,int,int]]):
    cols = st.columns(len(colors))
    for i, c in enumerate(colors):
        hexv = rgb_to_hex(c)
        with cols[i]:
            st.markdown(f"<div style='border-radius:12px;border:1px solid #eee;height:60px;background:{hexv}'></div>", unsafe_allow_html=True)
            st.caption(hexv.upper())

def suggest_outfits(style: str, season: str) -> List[str]:
    if style == "street":
        return [
            "Loose fit denim + graphic tee + chunky sneakers",
            "Cargo pants + hoodie + cap",
            "Track pants + zip-up + retro runners"
        ]
    if style == "minimal":
        return [
            "Straight wool trousers + fine knit + leather loafers",
            "Wide chinos + boxy shirt + clean sneakers",
            "Monochrome set-up (jacket+pants) + plain tee"
        ]
    if style == "classic":
        return [
            "Oxford shirt + chino + penny loafers",
            "Navy blazer + grey trousers + white shirt",
            "Knit polo + tailored shorts + derbies"
        ]
    if style == "avant":
        return [
            "Asymmetric top + wide trousers + platform boots",
            "Textured pleats set + minimalist sneakers",
            "Deconstructed shirt + flared pants"
        ]
    if style == "techwear":
        return [
            "Waterproof shell + tapered cargos + trail shoes",
            "Softshell jacket + utility shorts + mid boots",
            "3L shell + articulated pants + crossbody"
        ]
    if style == "y2k":
        return [
            "Low-rise denim + baby tee + platform sneakers",
            "Shiny track jacket + mini skirt + boots",
            "Logo tee + flared jeans + baguette bag"
        ]
    return []

def explain_reasoning(undertone: Dict[str, float], season: str, brightness: float, dom_colors: List[Tuple[int,int,int]]) -> str:
    hexes = ", ".join(rgb_to_hex(c).upper() for c in dom_colors[:3])
    return (
        f"중앙 영역 평균 색을 기반으로 **{season}** 팔레트를 추정했어요. "
        f"이미지 평균 밝기는 {brightness:.2f}이며, 대표 색(상위 3개)은 {hexes} 입니다. "
        "이 팔레트를 바탕으로 피부톤과 대비가 잘 맞는 브랜드/무드를 우선 추천했어요. "
        "※ 참고: 얼굴 인식 없이 중앙 패치로 추정하는 간단 모델이라 조명에 영향을 받습니다."
    )

def header_ui():
    st.markdown(
        """
        <style>
        .big-title { font-size: 2rem; font-weight: 800; }
        .subtitle { color: #666; }
        .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#f1f5f9; margin-right:6px; font-size:0.85rem;}
        .card { border:1px solid #eee; border-radius:18px; padding:16px; background:white; }
        </style>
        """, unsafe_allow_html=True
    )
    st.markdown("<div class='big-title'>👗 AI 패션 코디네이터</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>얼굴 사진을 업로드하면 어울리는 브랜드와 코디를 추천해줘요.</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

def sidebar_ui():
    st.sidebar.header("⚙️ 옵션")
    style = st.sidebar.selectbox("스타일", ["street", "minimal", "classic", "avant", "techwear", "y2k"], index=0)
    budget = st.sidebar.selectbox("예산", ["low", "mid", "high"], index=1)
    gender = st.sidebar.selectbox("젠더 무드", ["Androgynous", "Masculine", "Feminine"], index=0)
    k_colors = st.sidebar.slider("팔레트 색상 개수", 3, 8, 5)
    return style, budget, gender, k_colors

# =========================
# App
# =========================
def main():
    st.set_page_config(page_title="AI Fashion Coordinator", page_icon="👗", layout="wide")
    header_ui()
    style, budget, gender, k_colors = sidebar_ui()

    uploaded = st.file_uploader("얼굴 사진을 업로드하세요 (JPG/PNG)", type=["jpg","jpeg","png"])
    if uploaded is None:
        st.info("샘플 이미지가 없어요. 사진을 업로드하면 분석을 시작합니다.")
        st.stop()

    img = Image.open(uploaded)
    img_preview = ImageOps.exif_transpose(img.copy())
    st.image(img_preview, caption="업로드한 이미지", use_column_width=True)

    # Analysis
    brightness = image_brightness(img_preview)
    colors = get_dominant_colors(img_preview, k=k_colors)
    undertone = estimate_undertone(img_preview)
    season = classify_season(undertone, brightness)

    st.subheader("🎨 대표 색상")
    color_swatches(colors)
    st.caption(f"평균 밝기 추정: {brightness:.2f} / 언더톤(warm={undertone['warm_score']:.2f}, cool={undertone['cool_score']:.2f}) → **{season}**")

    # Recommendations
    st.subheader("🏷️ 추천 브랜드")
    brands = filter_brands(style, budget, season, gender)
    if not brands:
        st.write("해당 옵션에 맞는 브랜드 데이터가 부족해요. 다른 조합을 시도해보세요.")
    else:
        cols = st.columns(3)
        for i, b in enumerate(brands[:9]):
            with cols[i % 3]:
                st.markdown(f"<div class='card'><b>{b}</b><br><span class='pill'>{style}</span><span class='pill'>{budget}</span><span class='pill'>{season.split()[0]}</span></div>", unsafe_allow_html=True)

    # Palette hints
    st.subheader("🧭 컬러 가이드")
    hints = PALETTE_HINTS.get(season, [])
    if hints:
        st.write(", ".join(f"`{h}`" for h in hints))

    # Outfit suggestions
    st.subheader("🧩 코디 아이디어")
    for s in suggest_outfits(style, season):
        st.markdown(f"- {s}")

    # Reasoning & tips
    with st.expander("분석 근거 & 한계"):
        st.write(explain_reasoning(undertone, season, brightness, colors))
        st.markdown(
            "- **팁**: 역광/강한 색조 조명을 피하고, 얼굴이 중앙에 오도록 촬영하면 정확도가 올라갑니다.\n"
            "- **주의**: 이 앱은 가볍고 교육용 수준의 휴리스틱을 사용합니다. 전문적인 퍼스널 컬러 진단과 다를 수 있어요."
        )

    st.success("완료! 사이드바 옵션을 바꿔가며 결과가 어떻게 변하는지 시험해보세요.")

if __name__ == '__main__':
    main()
"""

reqs = "\n".join([
    "streamlit>=1.35.0",
    "Pillow>=10.2.0",
    "numpy>=1.26.0",
    "scikit-learn>=1.3.0"
])

readme = """
# 👗 AI Fashion Coordinator (Streamlit)

얼굴 사진을 업로드하면 어울리는 **브랜드 추천**과 **코디 아이디어**를 제안하는 간단한 생성형(규칙 기반) 패션 코디네이터입니다.  
학교 과제 시연용으로 설계되어 **가벼운 색상/언더톤 추정 휴리스틱**을 사용합니다.

## ✨ 기능
- 얼굴 사진 업로드 → 중앙 패치 분석으로 **언더톤/시즌 팔레트** 추정
- 이미지 **대표 색상 팔레트** 추출 (KMeans)
- 스타일/예산/젠더 무드 선택 → **브랜드 추천**
- 시즌 팔레트 기반 **컬러 가이드** & **코디 아이디어**

## 🧪 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
# Re-create with safe quoting: outer triple double quotes, inner triple single quotes.
import os, pathlib

base = "/mnt/data/ai-fashion-coordinator"
os.makedirs(base, exist_ok=True)

app_py = """
import io
import base64
from typing import List, Tuple, Dict
import numpy as np
from PIL import Image, ImageOps
import streamlit as st
from sklearn.cluster import KMeans

# =========================
# Helpers
# =========================

def to_numpy(img: Image.Image) -> np.ndarray:
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)

def resize_for_analysis(img: Image.Image, max_side: int = 512) -> Image.Image:
    w, h = img.size
    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img

def get_dominant_colors(img: Image.Image, k: int = 5) -> List[Tuple[int, int, int]]:
    '''Return k dominant colors (RGB tuples) from image using KMeans.'''
    small = resize_for_analysis(img, 256)
    arr = to_numpy(small).reshape(-1, 3).astype(np.float32)
    # Light blur via random sampling for speed
    if arr.shape[0] > 50000:
        idx = np.random.choice(arr.shape[0], 50000, replace=False)
        arr = arr[idx]
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    km.fit(arr)
    centers = np.clip(km.cluster_centers_.astype(int), 0, 255)
    # Sort by perceived luminance to get a nice order
    def luminance(c): return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]
    centers_list = [tuple(map(int, c)) for c in centers]
    centers_list.sort(key=luminance, reverse=True)
    return centers_list

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % rgb

def central_patch(img: Image.Image, size_ratio: float = 0.3) -> Image.Image:
    '''Crop a central square patch (~face region proxy).'''
    w, h = img.size
    s = int(min(w, h) * size_ratio)
    cx, cy = w // 2, h // 2
    left = max(cx - s // 2, 0)
    upper = max(cy - s // 2, 0)
    right = min(left + s, w)
    lower = min(upper + s, h)
    return img.crop((left, upper, right, lower))

def estimate_undertone(img: Image.Image) -> Dict[str, float]:
    '''
    Very lightweight skin/undertone guess using central patch average.
    Returns {'warm_score': x, 'cool_score': y, 'neutral_score': z}
    '''
    patch = central_patch(resize_for_analysis(img, 256), 0.4)
    arr = to_numpy(patch).astype(np.float32) / 255.0
    # focus on low-saturation, mid-lightness pixels to approximate skin
    # convert to HSL-ish via simple approach
    r, g, b = arr[...,0], arr[...,1], arr[...,2]
    cmax = arr.max(axis=-1)
    cmin = arr.min(axis=-1)
    delta = cmax - cmin
    light = (cmax + cmin) / 2.0
    sat = np.where(delta == 0, 0, delta / (1 - np.abs(2*light - 1) + 1e-6))
    mask = (sat < 0.35) & (light > 0.2) & (light < 0.85)
    if mask.sum() < 100:
        # fallback to full patch
        mask = np.ones_like(light, dtype=bool)
    mean_rgb = np.array([r[mask].mean(), g[mask].mean(), b[mask].mean()])
    # Warm if R is notably higher than B and slightly higher than G
    warm_score = float(np.clip((mean_rgb[0] - mean_rgb[2]) * 2 + (mean_rgb[0] - mean_rgb[1]), -1, 1))
    # Cool if B is higher than R and G
    cool_score = float(np.clip((mean_rgb[2] - mean_rgb[0]) * 2 + (mean_rgb[2] - mean_rgb[1]), -1, 1))
    # Neutral otherwise
    neutral_score = float(1 - abs(warm_score) - abs(cool_score))
    return {
        "warm_score": warm_score,
        "cool_score": cool_score,
        "neutral_score": neutral_score
    }

def classify_season(undertone: Dict[str, float], brightness_hint: float) -> str:
    '''
    Map undertone + brightness to one of seasonal palettes (Spring/Warm, Summer/Cool, Autumn/Warm Deep, Winter/Cool Deep).
    brightness_hint in [0,1].
    '''
    warm = undertone["warm_score"]
    cool = undertone["cool_score"]
    if warm > cool:
        if brightness_hint > 0.55:
            return "Spring (Warm & Bright)"
        else:
            return "Autumn (Warm & Deep)"
    else:
        if brightness_hint > 0.55:
            return "Summer (Cool & Soft)"
        else:
            return "Winter (Cool & Deep)"

def image_brightness(img: Image.Image) -> float:
    arr = to_numpy(resize_for_analysis(img, 256)).astype(np.float32) / 255.0
    # perceived luminance
    lum = 0.2126*arr[...,0] + 0.7152*arr[...,1] + 0.0722*arr[...,2]
    return float(lum.mean())

# =========================
# Brand Knowledge (simple rules)
# =========================

BRANDS = {
    "street": {
        "low": ["Uniqlo U", "GU", "Nike", "Adidas", "New Balance", "Stüssy"],
        "mid": ["Carhartt WIP", "C.P. Company", "A.P.C.", "Diesel", "BAPE"],
        "high": ["Off-White", "Palm Angels", "AMBUSH", "Maison Mihara", "Undercover"]
    },
    "minimal": {
        "low": ["Muji", "COS (sale)", "Zara (minimal line)", "H&M Studio"],
        "mid": ["COS", "A.P.C.", "Our Legacy", "Studio Nicholson"],
        "high": ["Lemaire", "Jil Sander", "The Row", "Maison Margiela (line 10)"]
    },
    "classic": {
        "low": ["Uniqlo", "Mango", "Spao (tailored)", "Arket"],
        "mid": ["Ralph Lauren", "Tommy Hilfiger", "Brooks Brothers", "A.P.C."],
        "high": ["AMI Paris", "Burberry", "Acne Studios", "Paul Smith"]
    },
    "avant": {
        "low": ["COS (sculptural)", "Zara SRPLS"],
        "mid": ["Issey Miyake Pleats", "Needles", "Kapital"],
        "high": ["Comme des Garçons", "Rick Owens", "Yohji Yamamoto", "Undercover"]
    },
    "techwear": {
        "low": ["Uniqlo (Blocktech)", "Decathlon Quechua", "Nike ACG (sale)"],
        "mid": ["And Wander", "Snow Peak", "Goldwin", "Stone Island Shadow"],
        "high": ["ACRONYM", "Veilance", "GORE-TEX Pro lines"]
    },
    "y2k": {
        "low": ["Bershka", "H&M", "Forever 21"],
        "mid": ["Diesel (D logo)", "GCDS", "Mschf (apparel)", "Ksubi"],
        "high": ["Blumarine", "Miu Miu", "Marine Serre"]
    }
}

PALETTE_HINTS = {
    "Spring (Warm & Bright)": ["ivory", "camel", "coral", "mint", "warm navy"],
    "Autumn (Warm & Deep)": ["tan", "olive", "rust", "mustard", "chocolate"],
    "Summer (Cool & Soft)": ["cool gray", "dusty rose", "lavender", "sage", "soft navy"],
    "Winter (Cool & Deep)": ["black", "optic white", "charcoal", "cobalt", "crimson"]
}

def filter_brands(style: str, budget: str, season: str, gender: str) -> List[str]:
    '''Combine by style + budget, then lightly re-rank by palette-season match.'''
    base = BRANDS.get(style, {}).get(budget, [])
    # very light re-weighting: winter/summer -> brands known for crisp neutrals; autumn/spring -> earthy/warm houses
    weight = []
    for b in base:
        w = 0
        if season.startswith("Winter") or season.startswith("Summer"):
            if b in ["COS", "A.P.C.", "Studio Nicholson", "Jil Sander", "The Row", "Acne Studios", "Arket", "Uniqlo", "Muji"]:
                w += 1
        if season.startswith("Autumn") or season.startswith("Spring"):
            if b in ["Diesel", "Kapital", "Needles", "Ralph Lauren", "Paul Smith", "Burberry", "C.P. Company"]:
                w += 1
        # light gender expression bias (purely heuristic, optional)
        if gender == "Feminine" and b in ["AMI Paris", "Miu Miu", "Blumarine", "Pleats Please", "Acne Studios"]:
            w += 0.5
        if gender == "Masculine" and b in ["Stone Island Shadow", "ACRONYM", "Carhartt WIP", "C.P. Company"]:
            w += 0.5
        weight.append((w, b))
    weight.sort(reverse=True)
    return [b for _, b in weight]

def color_swatches(colors: List[Tuple[int,int,int]]):
    cols = st.columns(len(colors))
    for i, c in enumerate(colors):
        hexv = rgb_to_hex(c)
        with cols[i]:
            st.markdown(f\"<div style='border-radius:12px;border:1px solid #eee;height:60px;background:{hexv}'></div>\", unsafe_allow_html=True)
            st.caption(hexv.upper())

def suggest_outfits(style: str, season: str) -> List[str]:
    if style == "street":
        return [
            "Loose fit denim + graphic tee + chunky sneakers",
            "Cargo pants + hoodie + cap",
            "Track pants + zip-up + retro runners"
        ]
    if style == "minimal":
        return [
            "Straight wool trousers + fine knit + leather loafers",
            "Wide chinos + boxy shirt + clean sneakers",
            "Monochrome set-up (jacket+pants) + plain tee"
        ]
    if style == "classic":
        return [
            "Oxford shirt + chino + penny loafers",
            "Navy blazer + grey trousers + white shirt",
            "Knit polo + tailored shorts + derbies"
        ]
    if style == "avant":
        return [
            "Asymmetric top + wide trousers + platform boots",
            "Textured pleats set + minimalist sneakers",
            "Deconstructed shirt + flared pants"
        ]
    if style == "techwear":
        return [
            "Waterproof shell + tapered cargos + trail shoes",
            "Softshell jacket + utility shorts + mid boots",
            "3L shell + articulated pants + crossbody"
        ]
    if style == "y2k":
        return [
            "Low-rise denim + baby tee + platform sneakers",
            "Shiny track jacket + mini skirt + boots",
            "Logo tee + flared jeans + baguette bag"
        ]
    return []

def explain_reasoning(undertone: Dict[str, float], season: str, brightness: float, dom_colors: List[Tuple[int,int,int]]) -> str:
    hexes = \", \".join(rgb_to_hex(c).upper() for c in dom_colors[:3])
    return (
        f\"중앙 영역 평균 색을 기반으로 **{season}** 팔레트를 추정했어요. \"
        f\"이미지 평균 밝기는 {brightness:.2f}이며, 대표 색(상위 3개)은 {hexes} 입니다. \"
        \"이 팔레트를 바탕으로 피부톤과 대비가 잘 맞는 브랜드/무드를 우선 추천했어요. \"
        \"※ 참고: 얼굴 인식 없이 중앙 패치로 추정하는 간단 모델이라 조명에 영향을 받습니다.\"
    )

def header_ui():
    st.markdown(
        '''
        <style>
        .big-title { font-size: 2rem; font-weight: 800; }
        .subtitle { color: #666; }
        .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#f1f5f9; margin-right:6px; font-size:0.85rem;}
        .card { border:1px solid #eee; border-radius:18px; padding:16px; background:white; }
        </style>
        ''', unsafe_allow_html=True
    )
    st.markdown("<div class='big-title'>👗 AI 패션 코디네이터</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>얼굴 사진을 업로드하면 어울리는 브랜드와 코디를 추천해줘요.</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

def sidebar_ui():
    st.sidebar.header("⚙️ 옵션")
    style = st.sidebar.selectbox("스타일", ["street", "minimal", "classic", "avant", "techwear", "y2k"], index=0)
    budget = st.sidebar.selectbox("예산", ["low", "mid", "high"], index=1)
    gender = st.sidebar.selectbox("젠더 무드", ["Androgynous", "Masculine", "Feminine"], index=0)
    k_colors = st.sidebar.slider("팔레트 색상 개수", 3, 8, 5)
    return style, budget, gender, k_colors

# =========================
# App
# =========================
def main():
    st.set_page_config(page_title="AI Fashion Coordinator", page_icon="👗", layout="wide")
    header_ui()
    style, budget, gender, k_colors = sidebar_ui()

    uploaded = st.file_uploader("얼굴 사진을 업로드하세요 (JPG/PNG)", type=["jpg","jpeg","png"])
    if uploaded is None:
        st.info("샘플 이미지가 없어요. 사진을 업로드하면 분석을 시작합니다.")
        st.stop()

    img = Image.open(uploaded)
    img_preview = ImageOps.exif_transpose(img.copy())
    st.image(img_preview, caption="업로드한 이미지", use_column_width=True)

    # Analysis
    brightness = image_brightness(img_preview)
    colors = get_dominant_colors(img_preview, k=k_colors)
    undertone = estimate_undertone(img_preview)
    season = classify_season(undertone, brightness)

    st.subheader("🎨 대표 색상")
    color_swatches(colors)
    st.caption(f"평균 밝기 추정: {brightness:.2f} / 언더톤(warm={undertone['warm_score']:.2f}, cool={undertone['cool_score']:.2f}) → **{season}**")

    # Recommendations
    st.subheader("🏷️ 추천 브랜드")
    brands = filter_brands(style, budget, season, gender)
    if not brands:
        st.write("해당 옵션에 맞는 브랜드 데이터가 부족해요. 다른 조합을 시도해보세요.")
    else:
        cols = st.columns(3)
        for i, b in enumerate(brands[:9]):
            with cols[i % 3]:
                st.markdown(f"<div class='card'><b>{b}</b><br><span class='pill'>{style}</span><span class='pill'>{budget}</span><span class='pill'>{season.split()[0]}</span></div>", unsafe_allow_html=True)

    # Palette hints
    st.subheader("🧭 컬러 가이드")
    hints = PALETTE_HINTS.get(season, [])
    if hints:
        st.write(", ".join(f"`{h}`" for h in hints))

    # Outfit suggestions
    st.subheader("🧩 코디 아이디어")
    for s in suggest_outfits(style, season):
        st.markdown(f"- {s}")

    # Reasoning & tips
    with st.expander("분석 근거 & 한계"):
        st.write(explain_reasoning(undertone, season, brightness, colors))
        st.markdown(
            "- **팁**: 역광/강한 색조 조명을 피하고, 얼굴이 중앙에 오도록 촬영하면 정확도가 올라갑니다.\\n"
            "- **주의**: 이 앱은 가볍고 교육용 수준의 휴리스틱을 사용합니다. 전문적인 퍼스널 컬러 진단과 다를 수 있어요."
        )

    st.success("완료! 사이드바 옵션을 바꿔가며 결과가 어떻게 변하는지 시험해보세요.")

if __name__ == '__main__':
    main()
"""

reqs = "streamlit>=1.35.0\nPillow>=10.2.0\nnumpy>=1.26.0\nscikit-learn>=1.3.0"

readme = """
# 👗 AI Fashion Coordinator (Streamlit)

얼굴 사진을 업로드하면 어울리는 **브랜드 추천**과 **코디 아이디어**를 제안하는 간단한 생성형(규칙 기반) 패션 코디네이터입니다.  
학교 과제 시연용으로 설계되어 **가벼운 색상/언더톤 추정 휴리스틱**을 사용합니다.

## ✨ 기능
- 얼굴 사진 업로드 → 중앙 패치 분석으로 **언더톤/시즌 팔레트** 추정
- 이미지 **대표 색상 팔레트** 추출 (KMeans)
- 스타일/예산/젠더 무드 선택 → **브랜드 추천**
- 시즌 팔레트 기반 **컬러 가이드** & **코디 아이디어**

## 🧪 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py

