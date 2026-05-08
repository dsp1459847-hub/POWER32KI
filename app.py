import pandas as pd
import streamlit as st
from collections import Counter

st.set_page_config(layout="wide")
st.title("MAYA AI: 32-Pattern Strict Boundary Engine")
st.write("Yeh engine Kal aur Aaj ki shifton par 32 Cross/Plus-Minus pattern lagata hai. Niyam: Agar ank 9 se bada ho jaye ya 0 se chhota (minus) ho jaye, toh use Reject kar diya jayega.")

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
    # Basic +1/-1
    (0,1), (0,-1), (1,0), (-1,0),
    # Basic Rashi +5/-5
    (0,5), (0,-5), (5,0), (-5,0),
    # 14 & 41 Family
    (1,4), (-1,-4), (4,1), (-4,-1),
    # 16 & 61 Family
    (1,6), (-1,-6), (6,1), (-6,-1),
    # 11 Family (Cross +1/-1)
    (1,1), (-1,-1), (1,-1), (-1,1),
    # 55 Family (Cross +5/-5)
    (5,5), (-5,-5), (5,-5), (-5,5),
    # 15 Family
    (1,5), (-1,-5), (1,-5), (-1,5),
    # 51 Family
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

    # UI Date Selection
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
            with st.spinner("MAYA AI 32-Pattern Math Engine chala rahi hai..."):
                
                date_kal_str = df.iloc[idx_kal]['DATE'].strftime('%d-%m-%Y')
                date_aaj_str = df.iloc[idx_aaj]['DATE'].strftime('%d-%m-%Y')
                
                # --- KAL KI SHIFTS PAR PATTERN ---
                st.markdown(f"<h3 style='color:#0056b3; border-bottom:2px solid #0056b3; padding-bottom:5px;'>1️⃣ KAL KI SHIFTS ({date_kal_str}) PAR PATTERN</h3>", unsafe_allow_html=True)
                
                all_kal_jodis = []
                grid_kal = st.columns(3)
                
                for i, shift in enumerate(cols):
                    val = df.iloc[idx_kal][shift]
                    generated_jodis = apply_strict_patterns(val)
                    all_kal_jodis.extend(generated_jodis)
                    
                    with grid_kal[i % 3]:
                        st.markdown(f"<div style='background-color:#f8f9fa; padding:10px; border-radius:5px; border:1px solid #ccc; margin-bottom:15px;'>", unsafe_allow_html=True)
                        st.markdown(f"<b style='color:#e0245e;'>🎰 {shift} ({val if val else 'XX'})</b> - {len(generated_jodis)} Valid Patterns", unsafe_allow_html=True)
                        if generated_jodis:
                            st.code(" | ".join(generated_jodis))
                        else:
                            st.write("N/A")
                        st.markdown("</div>", unsafe_allow_html=True)

                # --- AAJ KI SHIFTS PAR PATTERN ---
                st.markdown(f"<h3 style='color:#0056b3; border-bottom:2px solid #0056b3; padding-bottom:5px; margin-top:20px;'>2️⃣ AAJ KI SHIFTS ({date_aaj_str}) PAR PATTERN</h3>", unsafe_allow_html=True)
                
                grid_aaj = st.columns(3)
                for i, shift in enumerate(cols):
                    val = df.iloc[idx_aaj][shift]
                    generated_jodis = apply_strict_patterns(val)
                    
                    with grid_aaj[i % 3]:
                        st.markdown(f"<div style='background-color:#e8f4f8; padding:10px; border-radius:5px; border:1px solid #b8daff; margin-bottom:15px;'>", unsafe_allow_html=True)
                        st.markdown(f"<b style='color:#0056b3;'>🎰 {shift} ({val if val else 'XX'})</b> - {len(generated_jodis)} Valid Patterns", unsafe_allow_html=True)
                        if generated_jodis:
                            st.code(" | ".join(generated_jodis))
                        else:
                            st.write("Pending / N/A")
                        st.markdown("</div>", unsafe_allow_html=True)

                # --- FREQUENCY & ANALYSIS ---
                st.markdown(f"<h3 style='color:#28a745; border-bottom:2px solid #28a745; padding-bottom:5px; margin-top:20px;'>3️⃣ DATA ANALYSIS (Kal Ke Numbers Se)</h3>", unsafe_allow_html=True)
                
                if all_kal_jodis:
                    freq_counter = Counter(all_kal_jodis)
                    
                    col1, col2 = st.columns(2)
                    
                    # Kaunsa number kitni baar aaya
                    with col1:
                        st.markdown("#### 🔄 Jodis Frequency (Kaun Kitni Baar Aaya)")
                        
                        jodis_by_freq = defaultdict(list)
                        for jodi, count in freq_counter.items():
                            jodis_by_freq[count].append(jodi)
                            
                        for count in sorted(jodis_by_freq.keys(), reverse=True):
                            color = "red" if count >= 3 else ("blue" if count == 2 else "black")
                            st.markdown(f"<b style='color:{color};'>{count} Baar Aane Wale:</b> {', '.join(sorted(jodis_by_freq[count]))}", unsafe_allow_html=True)

                    # Bahar Haruf Tracker
                    with col2:
                        st.markdown("#### 🎯 Bahar (Unit) Haruf Tracker")
                        bahar_digits = [jodi[1] for jodi in all_kal_jodis]
                        bahar_counts = Counter(bahar_digits)
                        
                        b_list = []
                        for b, count in bahar_counts.most_common():
                            b_list.append(f"**Bahar {b}**: {count} bar")
                        st.write(" | ".join(b_list))
                        
                        top_bahar = bahar_counts.most_common(1)[0][0] if bahar_counts else None
                        
                        if top_bahar:
                            st.markdown(f"<div style='background-color:#d4edda; padding:10px; border-radius:5px; border:1px solid #c3e6cb; margin-top:10px;'>", unsafe_allow_html=True)
                            st.markdown(f"<b style='color:#155724;'>🔥 Sabse Zyada Aane Wala Bahar Ank: {top_bahar}</b>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                    # --- FINAL 33 VIP NUMBERS ---
                    st.markdown(f"<h3 style='color:#dc3545; border-bottom:2px solid #dc3545; padding-bottom:5px; margin-top:30px;'>🔥 FINAL VIP NUMBERS (Filtered) 🔥</h3>", unsafe_allow_html=True)
                    st.write("Is list mein wo numbers hain jo 1 se zyada baar aaye hain, PLUS wo saare numbers jinke bahar aaj ka 'Top Bahar' ank hai.")
                    
                    final_vips = set()
                    
                    # Add jodis that came more than 1 time
                    for jodi, count in freq_counter.items():
                        if count > 1:
                            final_vips.add(jodi)
                            
                    # Add all jodis ending with Top Bahar
                    if top_bahar:
                        for jodi in set(all_kal_jodis):
                            if jodi[1] == top_bahar:
                                final_vips.add(jodi)
                                
                    # Format for display
                    vips_list = sorted(list(final_vips))
                    
                    st.markdown(f"<div style='background-color:#fff3cd; padding:15px; border-radius:10px; border:2px dashed #ffe8a1; text-align:center;'>", unsafe_allow_html=True)
                    st.markdown(f"<h4 style='color:#856404; margin-top:0;'>👑 Total VIP Numbers: {len(vips_list)} 👑</h4>", unsafe_allow_html=True)
                    
                    j_chunks = [vips_list[x:x+8] for x in range(0, len(vips_list), 8)]
                    for chunk in j_chunks:
                        st.code(" | ".join(chunk))
                        
                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.warning("Kal ki shifton mein koi valid number nahi mila.")
else:
    st.info("Kripya engine chalane ke liye 0DSP0 sheet upload karein.")
          
