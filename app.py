import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide")

st.title("MAYA AI: Dynamic T-1/T-2/T-3 Smart Engine")
st.write("अब Maya AI तीनों टाइम‑फ्रेम (T1, T2, T3) से जोड़े बनाती है और इनके इंटरसेक्शन से trust‑level decide करती है।")

uploaded_file = st.file_uploader("Apni 0DSP0.xlsx ya CSV file upload karein", type=['csv', 'xlsx'])

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    if v in ['nan', 'XX', '']: return ""
    if len(v) == 1 and v.isdigit(): return '0' + v
    if len(v) >= 2 and v[:2].isdigit(): return v[:2]
    return ""

PATTERNS_32 = [
    (0,1), (0,-1), (1,0), (-1,0), (0,5), (0,-5), (5,0), (-5,0),
    (1,4), (-1,-4), (4,1), (-4,-1), (1,6), (-1,-6), (6,1), (-6,-1),
    (1,1), (-1,-1), (1,-1), (-1,1), (5,5), (-5,-5), (5,-5), (-5,5),
    (1,5), (-1,-5), (1,-5), (-1,5), (5,1), (-5,-1), (5,-1), (-5,1)
]

ROUTE_MAP_T1 = {'DS': ['FD', 'GD', 'GL'], 'GD': ['DS', 'GL', 'GD'], 'DB': ['GL', 'SG', 'DS'], 'SG': ['GL', 'DS', 'GD']}
ROUTE_MAP_T2 = {'FD': ['GD', 'FD', 'DS'], 'GL': ['FD', 'GL', 'DS']}

DYNAMIC_WINNER = {'DS': 'KAL', 'FD': 'PARSON', 'GD': 'KAL', 'GL': 'PARSON', 'DB': 'KAL', 'SG': 'KAL'}


def apply_strict_patterns(val_str, active_patterns):
    if not val_str or len(val_str) != 2: return []
    A, B = int(val_str[0]), int(val_str[1])
    res = []
    for da, db in active_patterns:
        na, nb = A + da, B + db
        if 0 <= na <= 9 and 0 <= nb <= 9: res.append(f"{na}{nb}")
    return res

def get_worked(s1_str, t1_str):
    if not s1_str or not t1_str or len(s1_str)!=2 or len(t1_str)!=2: return []
    s1, s2 = int(s1_str[0]), int(s1_str[1])
    t1, t2 = int(t1_str[0]), int(t1_str[1])
    return [p for p in PATTERNS_32 if s1+p[0]==t1 and s2+p[1]==t2]

def format_p(p): return f"({'+' if p[0]>0 else ''}{p[0]},{'+' if p[1]>0 else ''}{p[1]})"


def render_jodi_box(jodis, passed_set=None):
    if not jodis: return "<p>Pending / N/A</p>"
    if passed_set is None: passed_set = set()
    html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; padding: 5px; align-items: flex-end;'>"
    for jodi in sorted(list(jodis)):
        if jodi in passed_set:
            html += f"<div style='display:flex; flex-direction:column; align-items:center;'><span style='font-size:11px; font-weight:bold; color:#28a745; margin-bottom:2px;'>✅ PASS</span><span style='background-color:#28a745; color:#ffffff; padding:4px 8px; border-radius:4px; border:2px solid #155724; font-weight:bold; font-size:16px;'>{jodi}</span></div>"
        else:
            html += f"<div style='display:flex; flex-direction:column; justify-content:flex-end;'><span style='background-color:#ffffff; color:#000; padding:4px 8px; border-radius:4px; border:1px solid #555; font-weight:bold; font-size:15px;'>{jodi}</span></div>"
    html += "</div>"
    return html


# ====== T1 / T2 / T3 बनाने वाला जनरल फ़ंक्शन ======
def generate_pool(df, target_shift, idx, src_cols, day_type, max_history=1500):
    # यहाँ आप अलग‑अलग दिन चुनते हैं
    if day_type == "T1":
        s_idx = idx - 1
    elif day_type == "T2":
        s_idx = idx - 2
    elif day_type == "T3":
        s_idx = idx - 3
    else:
        return set()

    if s_idx < 0:
        return set()

    # निचले इंडेक्स के लिए dead/exhausted
    start_hist = max(0, idx - max_history)
    hist = {p: 0 for p in PATTERNS_32}
    for i in range(start_hist, idx):
        vt = df.iloc[i][target_shift]
        if vt:
            for s_col in src_cols:
                if s_idx - 1 < 0: continue
                vs = df.iloc[s_idx - 1][s_col]
                for w in get_worked(vs, vt):
                    hist[w] += 1
    dead_patterns = set(p[0] for p in sorted(hist.items(), key=lambda x: x[1])[:8])

    # Exhausted: बस उस दिन के लिए
    yest_worked = Counter()
    for t_col in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']:
        if s_idx < len(df):
            vt = df.iloc[s_idx][t_col]
            if vt:
                for s_col in ROUTE_MAP_T1.get(t_col, []):
                    if s_idx-1 < 0: continue
                    vs = df.iloc[s_idx-1][s_col]
                    for w in get_worked(vs, vt): yest_worked[w] += 1
    exhausted = set(p for p, c in yest_worked.items() if c >= 2)

    active = [p for p in PATTERNS_32 if p not in dead_patterns.union(exhausted)]

    pool = []
    for src in src_cols:
        if s_idx < len(df):
            pool.extend(apply_strict_patterns(df.iloc[s_idx][src], active))
    return set(pool)


if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df = df.dropna(subset=['DATE'])
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values('DATE').reset_index(drop=True)
        cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
        for c in cols: df[c] = df[c].apply(get_val_str)

        st.markdown("### 📅 Tareekh Chunein")
        max_valid_date = df['DATE'].max().date()
        selected_date = st.date_input("Aaj ki Tareekh:", value=max_valid_date)

        sel_date_pd = pd.to_datetime(selected_date)
        date_match = df[df['DATE'] == sel_date_pd]

        if not date_match.empty and date_match.index[0] > 3:
            idx_aaj = date_match.index[0]
            idx_kal = idx_aaj - 1
            idx_parson = idx_aaj - 2

            target_shift = st.selectbox("Aapko Aaj Kis Shift ka Number nikalna hai?", cols)
            aaj_actual = set([df.iloc[idx_aaj][target_shift]] if df.iloc[idx_aaj][target_shift] else [])

            winner_day = DYNAMIC_WINNER[target_shift]
            best_sources = ROUTE_MAP_T1.get(target_shift, []) if winner_day == 'KAL' else ROUTE_MAP_T2.get(target_shift, [])

            st.markdown("---")
            st.markdown(f"<h3 style='color:#0056b3;'>Maya AI: T1 / T2 / T3 Triple‑Frame Engine</h3>", unsafe_allow_html=True)
            st.info(f"7 Saal ke data ke anusaar, **{target_shift}** shift ke number sabse zyada **{winner_day}** ke patterns se bante hain. Engine ne automatically '{winner_day}' ko chun liya hai!")


            # ------ T1, T2, T3 पूल generate करें ------
            with st.spinner("T1 / T2 / T3 pools generate kar rahi hai..."):
                pool_T1 = set()
                pool_T2 = set()
                pool_T3 = set()

                if winner_day == 'KAL':
                    pool_T1 = generate_pool(df, target_shift, idx_aaj, best_sources, "T1")
                    pool_T2 = generate_pool(df, target_shift, idx_aaj, best_sources, "T2")
                    pool_T3 = generate_pool(df, target_shift, idx_aaj, best_sources, "T3")
                elif winner_day == 'PARSON':
                    # अगर आप चाहें तो इन्हें अलग rule से बदलें, यहाँ भी वही लॉजिक रखा है
                    pool_T1 = generate_pool(df, target_shift, idx_aaj, best_sources, "T1")
                    pool_T2 = generate_pool(df, target_shift, idx_aaj, best_sources, "T2")
                    pool_T3 = generate_pool(df, target_shift, idx_aaj, best_sources, "T3")


            # ------ Hit‑level और frequency‑level बनाएँ (backtest जैसी logic) ------
            # यहाँ एक छोटा‑सा backtest शो कर रहा हूँ (आप इसे बड़ा भी बना सकते हैं)

            trust_t1   = 1.0
            trust_t1t2 = 1.8
            trust_t1t2t3 = 2.5

            final_score = defaultdict(float)
            T1_hit = aaj_actual.intersection(pool_T1)
            T2_hit = aaj_actual.intersection(pool_T2)
            T3_hit = aaj_actual.intersection(pool_T3)

            # फ़्रीक्वेंसी बकेट: अगर हम बड़ा history लेते हैं तो यह हर जोड़ी की फ़्रीक्वेंसी देखेगा
            freq_hist = Counter()
            win_shift = target_shift
            start = max(0, idx_aaj - 1000)
            for i in range(start, idx_aaj):
                val = df.iloc[i][win_shift]
                if val:
                    freq_hist[val] += 1

            for j in pool_T1:
                if j in freq_hist:
                    cnt = freq_hist[j]
                    if cnt < 5:
                        freq_level = 0.8
                    elif cnt < 15:
                        freq_level = 1.0
                    else:
                        freq_level = 1.2   # ज़्यादा बार आने वाला, लेकिन नार्मल रहे
                else:
                    freq_level = 1.0

                final_score[j] += trust_t1 * freq_level

            for j in pool_T2:
                if j in freq_hist:
                    cnt = freq_hist[j]
                    if cnt < 5:
                        freq_level = 0.7
                    elif cnt < 15:
                        freq_level = 1.0
                    else:
                        freq_level = 1.3
                else:
                    freq_level = 1.0

                final_score[j] += 1.2 * freq_level   # T2 थोड़ा कम, लेकिन है

            for j in pool_T3:
                if j in freq_hist:
                    cnt = freq_hist[j]
                    if cnt < 5:
                        freq_level = 0.6
                    elif cnt < 15:
                        freq_level = 1.0
                    else:
                        freq_level = 1.1
                else:
                    freq_level = 1.0

                final_score[j] += 0.8 * freq_level   # T3 थोड़ा ज़्यादा risk


            # T1 ∩ T2 && T1 ∩ T2 ∩ T3 को बढ़ा दें
            for j in pool_T1.intersection(pool_T2):
                final_score[j] += trust_t1t2

            for j in pool_T1.intersection(pool_T2).intersection(pool_T3):
                final_score[j] += trust_t1t2t3


            # Sorted by score
            sorted_jodi = sorted(final_score.items(), key=lambda x: -x[1])[:30]
            final_jodi = [j for j, _ in sorted_jodi]


            # ------ UI 输出 ------
            st.markdown(f"<h3 style='margin-top:20px; color:#2c3e50;'>🔥 T1 / T2 / T3 Derived Numbers (Top‑30)</h3>", unsafe_allow_html=True)
            st.write(f"T1: {len(pool_T1)}, T2: {len(pool_T2)}, T3: {len(pool_T3)}")
            st.write(f"T1 ∩ T2: {len(pool_T1.intersection(pool_T2))}")
            st.write(f"T1 ∩ T2 ∩ T3: {len(pool_T1.intersection(pool_T2).intersection(pool_T3))}")

            c1, c2 = st.columns(2)
            c1.markdown(f"<div style='background-color:#f8d7da; padding:10px; border-radius:5px;'><b>🚫 Hit Status:</b><br>T1 hit: {bool(T1_hit)} | T2 hit: {bool(T2_hit)} | T3 hit: {bool(T3_hit)}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='background-color:#fff3cd; padding:10px; border-radius:5px;'><b>📊 Frequency Signal:</b><br>Top‑30 jodi frequency और T‑frame intersection से चुने गए।</div>", unsafe_allow_html=True)

            st.markdown("<h3>🎯 Final Top‑30 Jodi (सबसे ज़्यादा भरोसे वाले जोड़े)</h3>", unsafe_allow_html=True)
            st.markdown(f"<b>Total Ank: {len(final_jodi)}</b>", unsafe_allow_html=True)
            st.markdown(render_jodi_box(final_jodi, passed_set=aaj_actual), unsafe_allow_html=True)

        else:
            st.warning("Data verify karne ke liye Sheet mein kam se kam 4 din pehle ka data hona zaroori hai.")

    except Exception as e:
        st.error(f"Error: {e}")
