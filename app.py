import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI PRO 2026")

# --- Constants & Patterns ---
GOLDEN_8_ANK = ['00', '11', '22', '33', '44', '55', '66', '77', '88', '99'] # Apne 8-10 ank yahan dalein
PATTERNS = [(0,1), (0,-1), (1,0), (-1,0), (5,0), (0,5), (1,1), (5,5), (1,-1), (4,1), (6,1)]

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

# --- Prediction Engine ---
def predict_engine(df, target_date, target_shift):
    # Aaj ka result hatakar sirf pichla data lena (True Blind Test)
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)].copy()
    if hist_df.empty: return [], ""

    last_idx = hist_df.index[-1]
    scores = defaultdict(float)
    
    # 1. Bar-wise (Pichle 7 saal ka Same Day logic)
    curr_weekday = pd.to_datetime(target_date).weekday()
    same_days = hist_df[hist_df['DATE'].dt.weekday == curr_weekday].tail(20)
    for val in same_days[target_shift]:
        scores[val] += 2.5  # High weightage to 'Bar'

    # 2. Date-wise (Monthly Logic)
    curr_day_num = pd.to_datetime(target_date).day
    same_dates = hist_df[hist_df['DATE'].dt.day == curr_day_num].tail(10)
    for val in same_dates[target_shift]:
        scores[val] += 2.0  # Weightage to 'Date'

    # 3. Pattern Jump (T1/T2 Logic)
    # Pichli shift ka result lekar pattern apply karna
    last_val = hist_df.iloc[last_idx]['DS'] # Base source
    if last_val and len(last_val) == 2:
        a, b = int(last_val[0]), int(last_val[1])
        for da, db in PATTERNS:
            na, nb = (a+da)%10, (b+db)%10
            scores[f"{na}{nb}"] += 1.5

    # 4. Golden Ank Boost
    for g in GOLDEN_8_ANK:
        scores[g] += 3.0 # Golden Ank hamesha top par rahenge

    final_sorted = sorted(scores.items(), key=lambda x: -x[1])[:30]
    return [j for j, s in final_sorted], get_val_str(df[df['DATE'] == pd.to_datetime(target_date)][target_shift].values[0])

# --- UI ---
st.title("🎯 MAYA AI: True Accuracy Predictor")
uploaded_file = st.file_uploader("Excel Upload Karein", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    for c in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Tareekh Chunein", df['DATE'].max())
    t_shift = st.selectbox("Shift Chunein", ['DS', 'FD', 'GD', 'GL', 'DB', 'SG'])
    
    if st.button("Predict Now"):
        top_30, actual = predict_engine(df, t_date, t_shift)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Top-30 Numbers ({t_shift})")
            # Grid Display
            res_html = "<div style='display:grid; grid-template-columns: repeat(5,1fr); gap:5px;'>"
            for n in top_30:
                bg = "#FFD700" if n in GOLDEN_8_ANK else "#f0f2f6"
                border = "2px solid green" if n == actual else "1px solid #ccc"
                res_html += f"<div style='background:{bg}; border:{border}; padding:10px; text-align:center; font-weight:bold;'>{n}</div>"
            res_html += "</div>"
            st.markdown(res_html, unsafe_allow_html=True)
            
        with col2:
            st.subheader("Analysis")
            if actual:
                if actual in top_30:
                    st.success(f"✅ PASS! Result: {actual}")
                else:
                    st.error(f"❌ FAIL. Result: {actual}")
            else:
                st.info("Wait: Aaj ka result abhi aana baki hai.")

            st.write(f"**Historical Strength:** {t_date.strftime('%A')} + {t_date.day} Tarikh ka logic applied.")
            
