# app.py  --- Streamlit Fit Checker (ASCII-only, single file)
# Run: streamlit run app.py

import math
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Fit Checker - Brand Size Fit", layout="centered")

st.title("👕 Fit Checker")
st.caption("Predict fit by brand/size using your height/weight (and optional chest). ASCII-only to avoid encoding issues.")

# ---------- Example data (body chest circumference ranges, cm) ----------
SIZE_DATA = {
    "Nike": {
        "tops_men_unisex": {
            "XS": (81, 88),
            "S":  (88, 96),
            "M":  (96, 104),
            "L":  (104, 112),
            "XL": (112, 124),
            "XXL":(124, 136),
        }
    },
    "adidas": {
        "tops_men_unisex": {
            "XS": (82, 87),
            "S":  (88, 94),
            "M":  (95, 102),
            "L":  (103, 111),
            "XL": (112, 121),
            "XXL":(122, 132),
        }
    },
    "UNIQLO": {
        "tops_men_unisex": {
            "XS": (80, 88),
            "S":  (85, 92),
            "M":  (88, 96),
            "L":  (96, 104),
            "XL": (104, 112),
            "XXL":(112, 120),
        }
    },
    "ZARA": {
        "tops_men_unisex": {
            "XS": (88, 92),
            "S":  (92, 96),
            "M":  (96, 100),
            "L":  (100, 104),
            "XL": (104, 108),
            "XXL":(108, 112),
        }
    },
}

PREF_TOL = {"slim": 2.0, "regular": 4.0, "oversized": 6.0}  # cm

# ---------- Helpers ----------
def round1(x: float) -> float:
    return math.floor(x * 10 + 0.5) / 10.0

def bmi(height_cm: float, weight_kg: float) -> float:
    m = height_cm / 100.0
    if m <= 0 or weight_kg <= 0:
        return float("nan")
    return weight_kg / (m * m)

def estimate_chest(height_cm: float, weight_kg: float) -> float:
    # Simple demo formula:
    # est_chest = 0.54 * height(cm) + 1.2 * (BMI - 22)
    b = bmi(height_cm, weight_kg)
    if not math.isfinite(b):
        return float("nan")
    est = 0.54 * height_cm + 1.2 * (b - 22.0)
    # clamp to a reasonable range for demo
    return max(70.0, min(130.0, est))

def explain_fit(my_chest: float, rng: tuple[float, float], pref: str) -> tuple[str, str]:
    """Return (badge, message)."""
    lo, hi = rng
    tol = PREF_TOL.get(pref, 4.0)
    if my_chest < lo - tol:
        return ("loose", f"Loose (roomy). Your chest is {round1(lo - my_chest)} cm below the suggested min {lo}.")
    elif my_chest < lo:
        return ("loose", f"Loose. {round1(lo - my_chest)} cm below min {lo}.")
    elif my_chest <= hi:
        return ("true_to_size", f"True to size. Within {lo}–{hi} cm range.")
    elif my_chest <= hi + tol:
        return ("slightly_tight", f"Slightly tight. {round1(my_chest - hi)} cm above max {hi}.")
    else:
        return ("tight", f"Tight (small). {round1(my_chest - hi)} cm above max {hi}.")

def pick_best_size(my_chest: float, size_map: dict[str, tuple[float, float]], pref: str):
    tol = PREF_TOL.get(pref, 4.0)
    scored = []
    for size, (lo, hi) in size_map.items():
        mid = (lo + hi) / 2.0
        diff = abs(my_chest - mid)
        penalty = 0.0
        if my_chest > hi + tol:
            penalty = (my_chest - hi)
        elif my_chest < lo - tol:
            penalty = (lo - my_chest)
        score = diff + 1.2 * penalty
        scored.append((score, size, (lo, hi)))
    scored.sort(key=lambda x: x[0])
    best = scored[0]
    return best[1], best[2]  # size, range

# ---------- UI ----------
st.subheader("1) Your measurements")
c1, c2, c3 = st.columns(3)
with c1:
    height = st.number_input("Height (cm)", min_value=100.0, max_value=220.0, value=167.0, step=0.1)
with c2:
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=60.0, step=0.1)
with c3:
    chest  = st.number_input("Chest (cm, optional)", min_value=60.0, max_value=150.0, value=0.0, step=0.1)

pref = st.radio("Fit preference", ["slim", "regular", "oversized"], index=1, horizontal=True)

st.subheader("2) Brand & size")
bcol1, bcol2, bcol3 = st.columns(3)
brands = list(SIZE_DATA.keys())
with bcol1:
    brand = st.selectbox("Brand", brands, index=0)
with bcol2:
    category = st.selectbox("Category", ["tops_men_unisex"], index=0)
with bcol3:
    sizes = list(SIZE_DATA[brand][category].keys())
    size = st.selectbox("Size", sizes, index=sizes.index("M") if "M" in sizes else 0)

# ---------- Actions ----------
st.markdown("---")
colA, colB = st.columns(2)

with colA:
    if st.button("Check fit for selected size"):
        if not (height and weight):
            st.warning("Please input height and weight.")
        else:
            my_chest = chest if chest > 0 else estimate_chest(height, weight)
            badge, msg = explain_fit(round1(my_chest), SIZE_DATA[brand][category][size], pref)
            st.success(f"{brand} / {category} / {size}")
            st.info(f"Your chest used: {round1(my_chest)} cm (entered or estimated)")
            st.write(f"Result: **{badge}** — {msg}")
            lo, hi = SIZE_DATA[brand][category][size]
            st.caption(f"Reference range: {lo}–{hi} cm • Preference tolerance ±{PREF_TOL.get(pref,4.0)} cm")

with colB:
    if st.button("Find my recommended size across brands"):
        if not (height and weight):
            st.warning("Please input height and weight.")
        else:
            my_chest = chest if chest > 0 else estimate_chest(height, weight)
            st.info(f"Your chest used: {round1(my_chest)} cm (entered or estimated)")
            for bname, cats in SIZE_DATA.items():
                sname, rng = pick_best_size(round1(my_chest), cats[category], pref)
                badge, msg = explain_fit(round1(my_chest), rng, pref)
                st.write(f"**{bname}** → recommended: **{sname}**  (range {rng[0]}–{rng[1]} cm)")
                st.caption(f"{badge}: {msg}")

st.markdown("---")
with st.expander("Notes for school submission"):
    st.write(
        "- Data are demo chest ranges (body circumference) by brand. Adjust with official brand charts for a real project.\n"
        "- If chest is empty, it is estimated from height/weight via a simple BMI-based formula.\n"
        "- Fit decision uses preference tolerance (±2/4/6 cm for slim/regular/oversized)."
    )
