import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide")
st.title("MAYA AI: 32-Pattern Strict Boundary Engine (Live Pass Tracker)")
st.write("Yeh engine Kal aur Aaj ki shifton par 32 pattern lagata hai. **Naya Jaadu:** Jo prediction 'Aaj' ki shift mein sach mein PASS ho gayi hai, wo automatic Hare (Green) dabbe mein highlight ho jayegi!")

uploaded_file = st.file_uploader("Apni 0DSP0.xlsx ya CSV file upload karein", type=['csv', 'xlsx'])

# --- HELPER FUNCTIONS ---
def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    if v in ['nan', 'XX', '']: return ""
    if len(v) == 1 and v.isdigit(): return '0' + v
    if len(v) >= 2 and v[:2].isdigit(): return v[:2]
    return ""

# EXACT 32 PATTERNS (Andar, Bahar)
PATTERNS_32 = [
    (0,1), (0,-1), (1,0), (-1,0),
    (0,5), (0,-5), (5,0), (-5,0),
    (1,4), (-1,-4), (4,1), (-4,-1),
    (1,6), (-1,-6), (6,1), (-6,-1),
    (1,1), (-1,-1), (1,-1), (-1,1),
    (5,5), (-5,-5), (5,-5), (-5,5),
    (1,5), (-1,-5), (1,-5), (-1,5),
    (5,1), (-5,-1), (5,-1), (-5,1)
]

def apply_strict_patterns(val_str):
    if not val_str or len(val_str) != 2:
        return []
    
    A = int(val_str[0])
    B = int(val_str[1])
    valid_jodis = []
    
    for delta_a, delta_b in PATTERNS_32:
        new_a = A + delta_a
        new_b = B + delta_b
        
        # STRICT RULE: 0 se chhota nahi, 9 se bada nahi
        if 0 <= new_a <= 9 and 0 <= new_b <= 9:
            valid_jodis.append(f"{new_a}{new_b}")
            
    return valid_jodis

# --- UI HELPER FOR SQUARE BOX (PASS/FAIL TRACKER) ---
def render_jodi_box(jodis, passed_set=None):
    """Jodis ko chakor dabbe mein wrap karega. Jo pass honge unhe Green karega."""
    if not jodis:
        return "<p>Pending / N/A</p>"
    
    if passed_set is None:
        passed_set = set()
        
    html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; padding: 5px; align-items: flex-end;'>"
    for jodi in jodis:
        if jodi in passed_set:
            # HARA DABBA (GREEN BOX) FOR PASSED JODI
            html += f"""
            <div style='display:flex; flex-direction:column; align-items:center;'>
                <span style='font-size:11px; font-weight:bold; color:#28a745; margin-bottom:2px;'>✅ PASS</span>
                <span style='background-color: #28a745; color: #ffffff; padding: 4px 8px; border-radius: 4px; border: 2px solid #155724; font-weight: bold; font-size: 16px; box-shadow: 0px 0px 5px rgba(40,167,69,0.6);'>{jodi}</span>
            </div>
            """
        else:
            # NORMAL WHITE BOX
            html += f"""
            <div style='display:flex; flex-direction:column; justify-content:flex-end;'>
                <span style='background-color: #ffffff; color: #000000; padding: 4px 8px; border-radius: 4px; border: 1px solid #555; font-weight: bold; font-size: 15px;'>{jodi}</span>
            </div>
            """
    html += "</div>"
    return html

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    df = df.dropna(subset=['DATE'])
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    
    for c in cols:
        df[c] = df[c].apply(get_val_str)

    st.markdown("### 📅 Tareekh Chunein")
    max_valid_date = df['DATE'].max().date()
    selected_date = st.date_input("Aaj ki Tareekh:", value=max_valid_date, 
                                  min_value=df['DATE'].min().date(), max_value=max_valid_date)
                                  
    sel_date_pd = pd.to_datetime(selected_date)
    date_match = df[df['DATE'] == sel_date_pd]
    
    if date_match.empty:
        st.error("Sheet mein is date ka data nahi hai.")
    else:
        idx_aaj = date_match.index[0]
        idx_kal = idx_aaj - 1
        
        if idx_kal < 0:
            st.warning("Kal (Yesterday) ka data available nahi hai.")
        else:
            with st.spinner("MAYA AI Live Tracker aur 32-Pattern Engine chala rahi hai..."):
                
                date_kal_str = df.iloc[idx_kal]['DATE'].strftime('%d-%m-%Y')
                date_aaj_str = df.iloc[idx_aaj]['DATE'].strftime('%d-%m-%Y')
                
                # --- AAJ KYA KHULA HAI? (LIVE TRACKER SET) ---
                aaj_actual_vals = set()
                for c in cols:
                    val = df.iloc[idx_aaj][c]
                    if val and len(val) == 2:
                        aaj_actual_vals.add(val)
                
                # --- KAL KI SHIFTS PAR PATTERN ---
                st.markdown(f"<h3 style='color:#0056b3; border-bottom:2px solid #0056b3; padding-bottom:5px;'>1️⃣ KAL KI SHIFTS ({date_kal_str}) KI PREDICTION</h3>", unsafe_allow_html=True)
                
                all_kal_jodis = []
                grid_kal = st.columns(3)
                
                for i, shift in enumerate(cols):
                    val = df.iloc[idx_kal][shift]
                    generated_jodis = apply_strict_patterns(val)
                    all_kal_jodis.extend(generated_jodis)
                    
                    with grid_kal[i % 3]:
                        st.markdown(f"<div style='background-color:#f8f9fa; padding:10px; border-radius:5px; border:1px solid #ccc; margin-bottom:15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
                        st.markdown(f"<b style='color:#e0245e;'>🎰 {shift} ({val if val else 'XX'})</b> - {len(generated_jodis)} Valid Patterns", unsafe_allow_html=True)
                        # Pass actual today values to render box
                        st.markdown(render_jodi_box(generated_jodis, passed_set=aaj_actual_vals), unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                # --- AAJ KI SHIFTS PAR PATTERN (Inka pass kal pata chalega) ---
                st.markdown(f"<h3 style='color:#0056b3; border-bottom:2px solid #0056b3; padding-bottom:5px; margin-top:20px;'>2️⃣ AAJ KI SHIFTS ({date_aaj_str}) SE KAL KI PREDICTION</h3>", unsafe_allow_html=True)
                
                grid_aaj = st.columns(3)
                for i, shift in enumerate(cols):
                    val = df.iloc[idx_aaj][shift]
                    generated_jodis = apply_strict_patterns(val)
                    
                    with grid_aaj[i % 3]:
                        st.markdown(f"<div style='background-color:#e8f4f8; padding:10px; border-radius:5px; border:1px solid #b8daff; margin-bottom:15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
                        st.markdown(f"<b style='color:#0056b3;'>🎰 {shift} ({val if val else 'XX'})</b> - {len(generated_jodis)} Valid Patterns", unsafe_allow_html=True)
                        st.markdown(render_jodi_box(generated_jodis), unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                # --- FREQUENCY & ANALYSIS ---
                st.markdown(f"<h3 style='color:#28a745; border-bottom:2px solid #28a745; padding-bottom:5px; margin-top:20px;'>3️⃣ DATA ANALYSIS (Kal Ke Numbers Se)</h3>", unsafe_allow_html=True)
                
                if all_kal_jodis:
                    freq_counter = Counter(all_kal_jodis)
                    
                    col1, col2 = st.columns(2)
                    
                    # Kaunsa number kitni baar aaya
                    with col1:
                        st.markdown("#### 🔄 Jodis Frequency")
                        st.write("(Kaunsa number kitni baar aaya)")
                        
                        jodis_by_freq = defaultdict(list)
                        for jodi, count in freq_counter.items():
                            jodis_by_freq[count].append(jodi)
                            
                        for count in sorted(jodis_by_freq.keys(), reverse=True):
                            color = "red" if count >= 3 else ("blue" if count == 2 else "black")
                            bg_color = "#ffeeba" if count >= 2 else "transparent"
                            
                            st.markdown(f"<div style='background-color:{bg_color}; padding:8px; border-radius:5px; margin-bottom:5px;'>", unsafe_allow_html=True)
                            st.markdown(f"<b style='color:{color}; font-size:16px;'>{count} Baar Aane Wale:</b>", unsafe_allow_html=True)
                            st.markdown(render_jodi_box(sorted(jodis_by_freq[count]), passed_set=aaj_actual_vals), unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Bahar Haruf Tracker
                    with col2:
                        st.markdown("#### 🎯 Bahar (Unit) Haruf Tracker")
                        bahar_digits = [jodi[1] for jodi in all_kal_jodis]
                        bahar_counts = Counter(bahar_digits)
                        
                        b_list = []
                        for b, count in bahar_counts.most_common():
                            b_list.append(f"<span style='background-color:#e2e3e5; padding:4px 8px; border-radius:4px; font-weight:bold; margin:2px; display:inline-block;'>Bahar {b}: {count} bar</span>")
                        
                        st.markdown(" ".join(b_list), unsafe_allow_html=True)
                        
                        top_bahar = bahar_counts.most_common(1)[0][0] if bahar_counts else None
                        
                        if top_bahar:
                            st.markdown(f"<div style='background-color:#d4edda; padding:15px; border-radius:8px; border:2px solid #28a745; margin-top:15px; text-align:center;'>", unsafe_allow_html=True)
                            st.markdown(f"<h3 style='color:#155724; margin:0;'>🔥 Sabse Zyada Aane Wala Bahar Ank: {top_bahar}</h3>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                    # --- FINAL VIP NUMBERS ---
                    st.markdown(f"<h3 style='color:#dc3545; border-bottom:2px solid #dc3545; padding-bottom:5px; margin-top:30px;'>🔥 FINAL VIP NUMBERS (Filtered) 🔥</h3>", unsafe_allow_html=True)
                    st.write("Jo numbers 1 se zyada baar aaye hain, PLUS jinke bahar 'Top Bahar' ank hai.")
                    
                    final_vips = set()
                    for jodi, count in freq_counter.items():
                        if count > 1:
                            final_vips.add(jodi)
                    if top_bahar:
                        for jodi in set(all_kal_jodis):
                            if jodi[1] == top_bahar:
                                final_vips.add(jodi)
                                
                    vips_list = sorted(list(final_vips))
                    
                    st.markdown(f"<div style='background-color:#fff3cd; padding:15px; border-radius:10px; border:2px dashed #ffe8a1; text-align:center;'>", unsafe_allow_html=True)
                    st.markdown(f"<h4 style='color:#856404; margin-top:0;'>👑 Total VIP Numbers: {len(vips_list)} 👑</h4>", unsafe_allow_html=True)
                    
                    # Boxed VIP output with PASS tracking
                    html_vip = "<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; align-items: flex-end;'>"
                    for vip in vips_list:
                        if vip in aaj_actual_vals:
                            html_vip += f"""
                            <div style='display:flex; flex-direction:column; align-items:center;'>
                                <span style='font-size:12px; font-weight:bold; color:#28a745; margin-bottom:2px;'>✅ MEGA PASS</span>
                                <span style='background-color: #28a745; color: #fff; padding: 6px 12px; border-radius: 5px; border: 2px solid #155724; font-weight: bold; font-size: 18px; box-shadow: 0px 0px 8px rgba(40,167,69,0.8);'>{vip}</span>
                            </div>
                            """
                        else:
                            html_vip += f"""
                            <div style='display:flex; flex-direction:column; justify-content:flex-end;'>
                                <span style='background-color: #ffc107; color: #000; padding: 6px 12px; border-radius: 5px; border: 2px solid #b38600; font-weight: bold; font-size: 18px;'>{vip}</span>
                            </div>
                            """
                    html_vip += "</div>"
                    st.markdown(html_vip, unsafe_allow_html=True)
                        
                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.warning("Kal ki shifton mein koi valid number nahi mila.")
else:
    st.info("Kripya engine chalane ke liye 0DSP0 sheet upload karein.")
    
