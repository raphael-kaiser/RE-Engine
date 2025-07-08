import streamlit as st
import os
from re_engine_core import run_job

# Page configuration
st.set_page_config(
    page_title="RE Engine - Mallorca Property Analyzer",
    page_icon="🏠",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 1rem 0;
    background: linear-gradient(90deg, #1f77b4, #ff7f0e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 2rem;
}
.success-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    margin: 1rem 0;
}
.error-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    margin: 1rem 0;
}
.info-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🏠 RE Engine</h1>', unsafe_allow_html=True)
st.markdown('<h3 style="text-align: center; color: #666;">Mallorca Real Estate Investment Analyzer</h3>', unsafe_allow_html=True)

# Description
st.markdown("""
<div class="info-box">
<strong>How it works:</strong>
<ol>
<li>Paste an Idealista property URL from Mallorca</li>
<li>Click "Analyze Property" to process</li>
<li>The system will extract property data, run AI analysis, and write results to Google Sheets</li>
<li>Results include investment analysis, reform costs, comparable properties, and more</li>
</ol>
</div>
""", unsafe_allow_html=True)

# Input section
st.subheader("🔗 Property URL Input")
url = st.text_input(
    "Paste Idealista Property URL:", 
    placeholder="https://www.idealista.com/inmueble/12345678/",
    help="Enter a valid Idealista property URL for a Mallorca property"
)

# Validation
if url and "idealista.com" not in url:
    st.warning("⚠️ Please enter a valid Idealista URL")

# Process button and results
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 Analyze Property", type="primary", use_container_width=True):
        if not url:
            st.error("Please enter a property URL first!")
        elif "idealista.com" not in url:
            st.error("Please enter a valid Idealista URL!")
        else:
            # Show processing message
            with st.spinner("🔄 Processing property... This may take 30-60 seconds"):
                # Get service account info from Streamlit secrets
                service_account_info = None
                try:
                    if hasattr(st, 'secrets') and 'gcreds' in st.secrets:
                        service_account_info = dict(st.secrets.gcreds)
                        st.write("✅ Service account credentials loaded from secrets")
                    else:
                        st.error("❌ No service account credentials found in Streamlit secrets")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ Error loading secrets: {str(e)}")
                    st.stop()
                

                
                # Run the job
                result = run_job(url, service_account_info)
                
            # Display results
            if result["success"]:
                st.markdown(f"""
                <div class="success-box">
                <strong>✅ Success!</strong><br>
                {result["message"]}<br>
                <strong>Property Code:</strong> {result.get("property_code", "N/A")}<br>
                <strong>Fields Filled:</strong> {result["filled_fields"]}/{result["total_fields"]}
                </div>
                """, unsafe_allow_html=True)
                
                st.success("Property data has been written to Google Sheets!")
                st.balloons()
                
            else:
                st.markdown(f"""
                <div class="error-box">
                <strong>❌ Error:</strong><br>
                {result["error"]}
                </div>
                """, unsafe_allow_html=True)
                
                # Additional debugging info
                st.write("🔧 **Debug Information:**")
                st.write(f"- OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not Set'}")
                st.write(f"- Idealista API Key: {'✅ Set' if os.getenv('IDEALISTA_API_KEY') else '❌ Not Set'}")
                if service_account_info:
                    st.write(f"- Service Account Type: {service_account_info.get('type', 'Unknown')}")
                    st.write(f"- Project ID: {service_account_info.get('project_id', 'Unknown')}")

# Information section
st.markdown("---")
st.subheader("📊 What Gets Analyzed")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    **Property Data:**
    - Location & Area
    - Price & Surface Area
    - Plot Size & Features
    - Building Type & Condition
    """)

with col2:
    st.markdown("""
    **AI Analysis:**
    - Investment Priority (A/B/C)
    - Reform Cost per m²
    - Market Comparables
    - Location Scoring (1-10)
    """)

with col3:
    st.markdown("""
    **Business Intelligence:**
    - Critical Business Case
    - Sales Price Projection
    - Risk Assessment
    - Professional Email Draft
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
<strong>RE Engine</strong> - Powered by OpenAI & Idealista API<br>
Results are written to: <em>Raphael Project Selection 2025 → Business Cases 2025</em>
</div>
""", unsafe_allow_html=True)

# Environment check (always show for debugging)
with st.expander("🔧 Environment Status"):
    st.write("**API Keys Status:**")
    st.write(f"- OpenAI API Key: {'✅ Set (' + os.getenv('OPENAI_API_KEY', '')[:20] + '...)' if os.getenv('OPENAI_API_KEY') else '❌ Not Set'}")
    st.write(f"- Idealista API Key: {'✅ Set (' + os.getenv('IDEALISTA_API_KEY', '')[:20] + '...)' if os.getenv('IDEALISTA_API_KEY') else '❌ Not Set'}")
    
    if hasattr(st, 'secrets') and 'gcreds' in st.secrets:
        gcreds = st.secrets.gcreds
        st.write("**Google Sheets Configuration:**")
        st.write(f"- Type: {gcreds.get('type', 'Unknown')}")
        st.write(f"- Project ID: {gcreds.get('project_id', 'Unknown')}")
        st.write(f"- Client Email: {gcreds.get('client_email', 'Unknown')}")
        st.write(f"- Private Key: {'✅ Present' if gcreds.get('private_key') else '❌ Missing'}")
    else:
        st.write("- Google Sheets: ❌ Not Configured") 