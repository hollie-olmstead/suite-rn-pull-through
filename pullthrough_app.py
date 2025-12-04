import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Config
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# 2. CSS Styling
st.markdown("""
<style>
/* General App Styling */
.stApp {background-color: #ffffff;}
.block-container {padding-top: 2rem; padding-bottom: 2rem;}

/* Hide default sidebar and collapsed control */
[data-testid="stSidebar"] {display: none;}
[data-testid="collapsedControl"] {display: none;}

/* Metric Cards Styling (Custom HTML) */
.metric-card {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-top: 4px solid #D63333; /* Red Nucleus Red Accent */
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    text-align: center;
    margin-bottom: 10px;
}
.metric-label {
    font-size: 14px; 
    color: #666; 
    font-weight: 500;
    margin-bottom: 5px;
}
.metric-value {
    font-size: 28px; 
    color: #333; 
    font-weight: 700;
}

/* Button Styling - Improved */
div.stButton > button {
    width: 100%;
    border-radius: 4px;
    font-weight: 600;
    padding: 0.5rem 1rem;
}
/* Primary Button (Save Scenario) - Red */
div.stButton > button[kind="primary"] {
    background-color: #D63333;
    border-color: #D63333;
    color: white;
    box-shadow: 0 2px 4px rgba(214, 51, 51, 0.2);
}
/* Secondary Button (Reset) - White/Grey */
div.stButton > button[kind="secondary"] {
    background-color: #ffffff;
    border-color: #e0e0e0;
    color: #333;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #D63333;
    color: #D63333;
}

/* Headers */
h1 {font-size: 2.2rem; font-weight: 700; color: #1a1a1a;}
h2 {font-size: 1.5rem; font-weight: 600; color: #333;}
h3 {font-size: 1.2rem; font-weight: 600; color: #444;}
h4 {font-size: 1.1rem; font-weight: 600; color: #555; margin-top: 1rem;}

/* Input Section Styling */
.input-section {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #eee;
}

/* Messaging Box Styling */
.messaging-box {
    background-color: #e3f2fd; /* Light Blue */
    border-left: 5px solid #2196f3;
    padding: 15px;
    border-radius: 4px;
    margin-top: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# 3. Data Simulation
np.random.seed(42)
n_doctors = 50
lats = np.random.uniform(39.95, 40.05, n_doctors)
lons = np.random.uniform(-75.25, -75.10, n_doctors)
names = [f"Dr. {chr(65+i%26)}. {['Smith', 'Johnson', 'Williams', 'Jones', 'Brown'][i%5]}" for i in range(n_doctors)]
specialties = np.random.choice(['Cardiology', 'Endocrinology', 'Internal Medicine', 'Family Practice'], n_doctors)
volumes = np.random.randint(50, 501, n_doctors)
uhc_share = np.random.uniform(0, 1.0, n_doctors)
aetna_share = np.random.uniform(0, 1.0, n_doctors)
cigna_share = np.random.uniform(0, 1.0, n_doctors)
segments = np.random.choice(['Gold', 'Silver', 'Bronze'], n_doctors)
zips = np.random.choice(['19103', '19104', '19106', '19107', '19130'], n_doctors)

df = pd.DataFrame({
    'Dr Name': names,
    'Specialty': specialties,
    'TRx Volume': volumes,
    'UHC Share %': uhc_share,
    'Aetna Share %': aetna_share,
    'Cigna Share %': cigna_share,
    'Target Segment': segments,
    'Zip Code': zips,
    'lat': lats,
    'lon': lons
})

# 4. Header Section
col_header_1, col_header_2 = st.columns([3, 1.5])
with col_header_1:
    st.title("Pull-Through Targeting Tool")
with col_header_2:
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        st.button("Reset Defaults", type="secondary", use_container_width=True)
    with c_btn2:
        st.button("Save Scenario", type="primary", use_container_width=True)

st.markdown("---")

# 5. Main Layout
col_main_left, col_main_right = st.columns([1, 3])

# --- LEFT COLUMN: INPUTS ---
with col_main_left:
    st.subheader("Scenario Inputs")
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    
    st.markdown("**Configuration**")
    
    uploaded_formulary = st.file_uploader("Upload Formulary Status (CSV)", type=['csv'])
    if uploaded_formulary:
        st.success("Formulary Data Loaded")
        
    formulary_win = st.selectbox(
        "Formulary Win", 
        ["UnitedHealthcare - National Preferred", "Aetna - Silver Tier", "Cigna - Bronze"]
    )
    
    st.markdown("---")
    
    st.markdown("**Territory Data**")
    uploaded_file = st.file_uploader("Upload Zip-to-Territory (CSV)", type=['csv'])
    if uploaded_file:
        st.success("Mapping Loaded")
        
    selected_zips = st.multiselect("Filter Zip Codes", sorted(df['Zip Code'].unique()), default=[])
    
    st.markdown("---")
    
    st.markdown("**Pull-Through Drivers**")
    competitor_access = st.selectbox(
        "Competitor Access", 
        ["Blocked / ND", "PA Required", "Open Access"]
    )
    
    call_capacity = st.slider("Call Capacity (Max Targets)", 10, 50, 25)
    
    st.markdown("---")
    
    strategy = st.radio("Strategy", ["Defensive (Protect)", "Offensive (Switch)"])
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- RIGHT COLUMN: METRICS & VIZ ---
with col_main_right:
    
    # Logic for filtering
    target_mask = pd.Series([True] * n_doctors)
    
    # 1. Filter by Formulary Logic
    if "UnitedHealthcare" in formulary_win:
        target_mask = target_mask & (df['UHC Share %'] > 0.5)
    elif "Aetna" in formulary_win:
        target_mask = target_mask & (df['Aetna Share %'] > 0.5)
    elif "Cigna" in formulary_win:
        target_mask = target_mask & (df['Cigna Share %'] > 0.5)
        
    # 2. Filter by Zip
    if selected_zips:
        target_mask = target_mask & (df['Zip Code'].isin(selected_zips))

    # 3. Apply Call Capacity Limit
    temp_df = df[target_mask].sort_values('TRx Volume', ascending=False)
    if len(temp_df) > call_capacity:
        top_n_indices = temp_df.head(call_capacity).index
        target_mask = df.index.isin(top_n_indices)

    df['Color'] = np.where(target_mask, 'Target', 'Other')
    color_map = {'Target': '#D63333', 'Other': '#e0e0e0'}
    
    target_df = df[target_mask].copy()

    # Metrics
    metric1 = len(target_df)
    potential_lift = target_df['TRx Volume'].sum() * 0.15 if not target_df.empty else 0
    revenue_impact = potential_lift * 500

    st.subheader("Targeting Summary")
    
    # Custom HTML Metric Cards
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Target Doctors</div>
            <div class="metric-value">{metric1}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Potential Volume Lift</div>
            <div class="metric-value">{potential_lift:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Est. Revenue Impact</div>
            <div class="metric-value">${revenue_impact:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- PROMINENT MESSAGING SECTION ---
    st.markdown("###")
    
    # Determine top doctor for messaging context
    top_name = target_df.sort_values('TRx Volume', ascending=False).iloc[0]['Dr Name'] if not target_df.empty else "Target Physician"
    
    if "Offensive" in strategy:
        msg_title = "Offensive Strategy: Switch Opportunity"
        msg_body = (
            f"- **Primary Message:** Great news! We have secured Preferred Status. This removes the PA hurdle for your new patients.\n"
            f"- **Context:** {top_name} is a high-volume prescriber of the competitor, likely due to previous access barriers.\n"
            f"- **Action:** Ask for the next 3 new patient starts. Highlight the simplified intake form and hub support."
        )
    else:
        msg_title = "Defensive Strategy: Protect Volume"
        msg_body = (
            f"- **Primary Message:** Clinical stability is paramount. Don't let a formulary change disrupt your patients' success.\n"
            f"- **Context:** Competitor X has gained access. {top_name} has stable patients who may be targeted for switching.\n"
            f"- **Action:** Review 'Clinical Efficacy' data. Remind them that existing patients are grandfathered and do NOT need to switch."
        )
        
    st.info(f"### {msg_title}\n{msg_body}")
    # -----------------------------------

    st.markdown("###")

    # Row 2: Map & Market Share
    c_map, c_pie = st.columns([2, 1], gap="large")
    
    with c_map:
        st.markdown("#### Geospatial View")
        fig_map = px.scatter_mapbox(
            df,
            lat='lat',
            lon='lon',
            color='Color',
            size='TRx Volume',
            hover_name='Dr Name',
            hover_data=['TRx Volume', 'Zip Code'],
            color_discrete_map=color_map,
            zoom=10,
            mapbox_style="open-street-map",
            height=400
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)
        
    with c_pie:
        st.markdown("#### Payer Mix (Targeted)")
        if not target_df.empty:
            avg_shares = {
                'UHC': target_df['UHC Share %'].mean(),
                'Aetna': target_df['Aetna Share %'].mean(),
                'Cigna': target_df['Cigna Share %'].mean(),
                'Other': 1.0 - (target_df['UHC Share %'].mean() + target_df['Aetna Share %'].mean() + target_df['Cigna Share %'].mean())
            }
            pie_df = pd.DataFrame(list(avg_shares.items()), columns=['Payer', 'Share'])
            
            fig_pie = px.pie(pie_df, values='Share', names='Payer', hole=0.4, 
                             color_discrete_sequence=['#D63333', '#333333', '#666666', '#999999'])
            fig_pie.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=True,
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No targets selected.")

    st.markdown("---")

    # Row 3: List & Drill Down
    c_list, c_detail = st.columns(2, gap="large")
    
    with c_list:
        st.markdown("#### Priority Call List")
        
        display_cols = ['Dr Name', 'Specialty', 'Zip Code', 'TRx Volume']
        if "UnitedHealthcare" in formulary_win:
            display_cols.append('UHC Share %')
        elif "Aetna" in formulary_win:
            display_cols.append('Aetna Share %')
        elif "Cigna" in formulary_win:
            display_cols.append('Cigna Share %')
            
        st.dataframe(
            target_df[display_cols].sort_values('TRx Volume', ascending=False).reset_index(drop=True), 
            hide_index=True,
            use_container_width=True,
            height=300
        )
        
        csv = target_df[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Target List (CSV)",
            data=csv,
            file_name='target_doctors.csv',
            mime='text/csv',
        )

    with c_detail:
        st.markdown("#### Physician Deep Dive")
        
        if not target_df.empty:
            doc_list = target_df.sort_values('TRx Volume', ascending=False)['Dr Name'].tolist()
            selected_doc = st.selectbox("Select Physician", doc_list)
            
            # Simulated Trend Data
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            base_vol = target_df[target_df['Dr Name'] == selected_doc]['TRx Volume'].values[0]
            trend_vol = np.random.normal(base_vol/6, 5, 6).cumsum() + base_vol 
            trend_vol = np.abs(trend_vol)
            
            trend_df = pd.DataFrame({'Month': months, 'TRx Volume': trend_vol})
            
            fig_trend = px.line(trend_df, x='Month', y='TRx Volume', title=f"{selected_doc} - 6 Month Trend", markers=True)
            fig_trend.update_traces(line_color='#D63333')
            fig_trend.update_layout(height=250, margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_trend, use_container_width=True)
            
        else:
            st.write("Select targets to view details.")
