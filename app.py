#!/usr/bin/env python3
"""
MicroCFO Streamlit App - AI Financial Assistant for Hugging Face Spaces
UI Design matched to Vercel React Frontend
"""

import streamlit as st
import google.generativeai as genai
import os
import tempfile
import json

# Page configuration
st.set_page_config(
    page_title="MicroCFO - AI Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching Vercel/React frontend design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main container - Light slate background */
    .main {
        background-color: #F8FAFC;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Headers - Slate 800 */
    h1 {
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 1.875rem !important;
    }
    
    h2, h3 {
        color: #334155 !important;
        font-weight: 600 !important;
    }
    
    p, span, label {
        color: #64748B;
    }
    
    /* Primary Button - Trust Blue */
    .stButton > button {
        background-color: #1E40AF !important;
        color: white !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton > button:hover {
        background-color: #1E3A8A !important;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Secondary/Outline buttons */
    .stButton > button[kind="secondary"] {
        background-color: white !important;
        color: #1E40AF !important;
        border: 1px solid #E2E8F0 !important;
    }
    
    /* Sidebar - Corporate dark */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #F1F5F9 !important;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: #CBD5E1 !important;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #FFFFFF !important;
    }
    
    /* Cards - White with slate border */
    .card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    
    .card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    /* Quick action cards */
    .quick-action {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .quick-action:hover {
        border-color: #1E40AF;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.1);
    }
    
    .quick-action-icon {
        width: 3rem;
        height: 3rem;
        border-radius: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.75rem auto;
        font-size: 1.5rem;
    }
    
    .icon-blue { background-color: #DBEAFE; }
    .icon-purple { background-color: #EDE9FE; }
    .icon-green { background-color: #D1FAE5; }
    .icon-orange { background-color: #FFEDD5; }
    
    /* Agent cards */
    .agent-card {
        background: #F8FAFC;
        border: 1px solid #F1F5F9;
        border-radius: 0.75rem;
        padding: 1rem;
        transition: all 0.2s;
    }
    
    .agent-card:hover {
        border-color: #E2E8F0;
    }
    
    .agent-icon {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.25rem;
    }
    
    .bg-blue { background-color: #3B82F6; }
    .bg-purple { background-color: #8B5CF6; }
    .bg-green { background-color: #10B981; }
    .bg-orange { background-color: #F97316; }
    
    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .badge-success {
        background-color: #D1FAE5;
        color: #065F46;
    }
    
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
    }
    
    .badge-danger {
        background-color: #FEE2E2;
        color: #991B1B;
    }
    
    .badge-info {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    
    /* Status dot */
    .status-dot {
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background-color: #10B981;
        display: inline-block;
        margin-right: 0.375rem;
    }
    
    /* Metrics */
    .stMetric {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1rem;
    }
    
    .stMetric label {
        color: #64748B !important;
        font-size: 0.875rem !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #1E293B !important;
        font-weight: 700 !important;
    }
    
    /* Success/Warning/Error boxes */
    .stSuccess {
        background-color: #D1FAE5;
        border-color: #10B981;
    }
    
    .stWarning {
        background-color: #FEF3C7;
        border-color: #F59E0B;
    }
    
    .stError {
        background-color: #FEE2E2;
        border-color: #EF4444;
    }
    
    /* File uploader */
    .stFileUploader {
        background: white;
        border: 2px dashed #E2E8F0;
        border-radius: 0.75rem;
        padding: 2rem;
    }
    
    .stFileUploader:hover {
        border-color: #1E40AF;
    }
    
    /* Text inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border: 1px solid #E2E8F0 !important;
        border-radius: 0.5rem !important;
        background: white !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #1E40AF !important;
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1) !important;
    }
    
    /* Divider */
    hr {
        border-color: #E2E8F0 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: white !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 0.75rem !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# --- CONFIGURATION ---
def init_gemini():
    """Initialize Gemini API"""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None


def process_uploaded_file(uploaded_file):
    """Saves uploaded file to temp path and uploads to Gemini File API"""
    try:
        suffix = f".{uploaded_file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        with st.spinner("📤 Uploading to Gemini Vision..."):
            google_file = genai.upload_file(tmp_path)
            
        return google_file
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None


def init_session_state():
    """Initialize session state variables"""
    if 'invoice_result' not in st.session_state:
        st.session_state.invoice_result = None
    if 'compliance_result' not in st.session_state:
        st.session_state.compliance_result = None
    if 'subsidy_result' not in st.session_state:
        st.session_state.subsidy_result = None


# Sidebar navigation
def sidebar():
    with st.sidebar:
        # Logo area
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💰</div>
            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700;">MicroCFO</h2>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; opacity: 0.8;">AI Financial Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "📄 Document Scanner", "⚖️ Compliance Check", "💰 Subsidy Explorer"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # API Status
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: rgba(16, 185, 129, 0.1); border-radius: 0.5rem;">
                <span class="status-dot"></span>
                <span style="font-size: 0.875rem;">API Connected</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ API Key Missing")
            st.caption("Set GEMINI_API_KEY in Secrets")
        
        st.divider()
        
        st.markdown("""
        <div style="padding: 0.75rem; background: rgba(59, 130, 246, 0.1); border-radius: 0.5rem; font-size: 0.75rem;">
            <p style="margin: 0 0 0.5rem 0; font-weight: 500;">📄 Supported Formats</p>
            <p style="margin: 0; opacity: 0.8;">PNG, JPG, PDF</p>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">✨ Works with scanned docs</p>
        </div>
        """, unsafe_allow_html=True)
        
        return page


# Pages
def dashboard_page():
    # Header
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Dashboard")
        st.markdown('<p style="margin-top: -0.5rem;">Welcome back! Here\'s your financial health overview.</p>', unsafe_allow_html=True)
    with col2:
        st.button("🔔 3 New Alerts", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("### Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="quick-action">
            <div class="quick-action-icon icon-blue">📤</div>
            <span style="font-size: 0.875rem; font-weight: 500; color: #334155;">Upload Invoice</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="quick-action">
            <div class="quick-action-icon icon-purple">📷</div>
            <span style="font-size: 0.875rem; font-weight: 500; color: #334155;">Scan Document</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="quick-action">
            <div class="quick-action-icon icon-green">🔍</div>
            <span style="font-size: 0.875rem; font-weight: 500; color: #334155;">Check Eligibility</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="quick-action">
            <div class="quick-action-icon icon-orange">📋</div>
            <span style="font-size: 0.875rem; font-weight: 500; color: #334155;">Compliance Report</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Grid
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Financial Health Score
        st.markdown("""
        <div class="card">
            <h3 style="margin: 0 0 1rem 0; font-size: 1rem;">Financial Health Score</h3>
            <div style="text-align: center; padding: 1.5rem 0;">
                <div style="width: 120px; height: 120px; border-radius: 50%; background: conic-gradient(#10B981 0% 72%, #E2E8F0 72% 100%); margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                    <div style="width: 90px; height: 90px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 1.75rem; font-weight: 700; color: #1E293B;">72</span>
                    </div>
                </div>
            </div>
            <div style="margin-top: 1rem;">
                <div style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.25rem;">
                        <span style="color: #64748B;">Compliance</span>
                        <span style="color: #1E293B; font-weight: 500;">85%</span>
                    </div>
                    <div style="height: 0.5rem; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                        <div style="width: 85%; height: 100%; background: #10B981; border-radius: 9999px;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.25rem;">
                        <span style="color: #64748B;">Cash Flow</span>
                        <span style="color: #1E293B; font-weight: 500;">65%</span>
                    </div>
                    <div style="height: 0.5rem; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                        <div style="width: 65%; height: 100%; background: #F59E0B; border-radius: 9999px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.25rem;">
                        <span style="color: #64748B;">Subsidies</span>
                        <span style="color: #1E293B; font-weight: 500;">70%</span>
                    </div>
                    <div style="height: 0.5rem; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                        <div style="width: 70%; height: 100%; background: #3B82F6; border-radius: 9999px;"></div>
                    </div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 0.75rem; background: #D1FAE5; border-radius: 0.5rem; border: 1px solid #A7F3D0;">
                <div style="display: flex; align-items: center; gap: 0.5rem; color: #065F46; font-weight: 500;">
                    📈 +5% improvement
                </div>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; color: #047857;">compared to last month</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # AI Agent Activity
        st.markdown("""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 1rem;">AI Agent Activity</h3>
                <a href="#" style="font-size: 0.875rem; color: #1E40AF; text-decoration: none;">View All →</a>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div class="agent-card">
                    <div style="display: flex; gap: 0.75rem;">
                        <div class="agent-icon bg-blue">👁️</div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-weight: 500; color: #1E293B;">Visual Auditor</span>
                                <span class="badge badge-success"><span class="status-dot"></span>Active</span>
                            </div>
                            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: #64748B;">12 documents processed today</p>
                            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">2 minutes ago</p>
                        </div>
                    </div>
                </div>
                <div class="agent-card">
                    <div style="display: flex; gap: 0.75rem;">
                        <div class="agent-icon bg-purple">⚖️</div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-weight: 500; color: #1E293B;">Legal Sentinel</span>
                                <span class="badge badge-success"><span class="status-dot"></span>Active</span>
                            </div>
                            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: #64748B;">3 alerts this week</p>
                            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">1 hour ago</p>
                        </div>
                    </div>
                </div>
                <div class="agent-card">
                    <div style="display: flex; gap: 0.75rem;">
                        <div class="agent-icon bg-green">🔍</div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-weight: 500; color: #1E293B;">Subsidy Hunter</span>
                                <span class="badge badge-success"><span class="status-dot"></span>Active</span>
                            </div>
                            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: #64748B;">5 opportunities found</p>
                            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">30 minutes ago</p>
                        </div>
                    </div>
                </div>
                <div class="agent-card">
                    <div style="display: flex; gap: 0.75rem;">
                        <div class="agent-icon bg-orange">✉️</div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="font-weight: 500; color: #1E293B;">Negotiator</span>
                                <span class="badge badge-success"><span class="status-dot"></span>Active</span>
                            </div>
                            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: #64748B;">8 emails sent this month</p>
                            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">4 hours ago</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bottom Stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="margin: 0; font-size: 0.875rem; color: #64748B;">Penalties Avoided</p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: 700; color: #10B981;">₹45,000</p>
                </div>
                <div style="width: 3rem; height: 3rem; background: #D1FAE5; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                    📉
                </div>
            </div>
            <p style="margin: 1rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">3 penalties avoided this quarter</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="margin: 0; font-size: 0.875rem; color: #64748B;">Subsidies Claimed</p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: 700; color: #3B82F6;">₹2,50,000</p>
                </div>
                <div style="width: 3rem; height: 3rem; background: #DBEAFE; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                    📈
                </div>
            </div>
            <p style="margin: 1rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">2 schemes approved this year</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="margin: 0; font-size: 0.875rem; color: #64748B;">Documents Processed</p>
                    <p style="margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: 700; color: #8B5CF6;">156</p>
                </div>
                <div style="width: 3rem; height: 3rem; background: #EDE9FE; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                    📋
                </div>
            </div>
            <p style="margin: 1rem 0 0 0; font-size: 0.75rem; color: #94A3B8;">98% accuracy rate</p>
        </div>
        """, unsafe_allow_html=True)


def document_scanner_page():
    st.title("Document Scanner")
    st.markdown('<p style="margin-top: -0.5rem;">Upload an invoice or document to analyze it with AI</p>', unsafe_allow_html=True)
    
    model = init_gemini()
    
    if not model:
        st.error("⚠️ API key not configured. Please set GEMINI_API_KEY in Secrets.")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="margin: 0 0 1rem 0; font-size: 1rem;">Upload Document</h3>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Drop your file here",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Supports PNG, JPG, and PDF files",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if uploaded_file.type in ["image/png", "image/jpeg"]:
                st.image(uploaded_file, caption="Preview", use_container_width=True)
            else:
                st.success(f"📄 {uploaded_file.name} loaded")
            
            if st.button("🔍 Analyze Document", use_container_width=True):
                google_file = process_uploaded_file(uploaded_file)
                
                if google_file:
                    system_prompt = """You are an expert AI Accountant and Financial Auditor for Indian MSMEs.
                    Analyze this invoice/document carefully.
                    
                    Extract: Vendor Name, Invoice Date (YYYY-MM-DD), Total Amount, Tax Amount, GSTIN
                    Check for: Tampering, handwritten overrides, missing information
                    Flag: Items not eligible for ITC, missing GSTIN with tax charged
                    
                    Output as JSON:
                    {
                      "vendor_name": "string",
                      "invoice_date": "YYYY-MM-DD",
                      "total_amount": number,
                      "tax_amount": number,
                      "gstin": "string or null",
                      "is_handwritten": boolean,
                      "tampering_detected": boolean,
                      "confidence_score": number,
                      "line_items": [{"description": "string", "amount": number, "category": "string"}],
                      "compliance_flags": ["warnings"],
                      "is_valid_business_expense": boolean,
                      "summary": "Brief analysis"
                    }"""
                    
                    try:
                        with st.spinner("🔍 Analyzing document..."):
                            response = model.generate_content([system_prompt, google_file])
                            response_text = response.text.strip()
                            
                            if "```json" in response_text:
                                response_text = response_text.split("```json")[1].split("```")[0].strip()
                            elif "```" in response_text:
                                response_text = response_text.split("```")[1].split("```")[0].strip()
                            
                            st.session_state.invoice_result = json.loads(response_text)
                    except json.JSONDecodeError:
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        if st.session_state.invoice_result:
            result = st.session_state.invoice_result
            
            st.markdown("""<div class="card"><h3 style="margin: 0 0 1rem 0; font-size: 1rem;">Analysis Results</h3>""", unsafe_allow_html=True)
            
            # Metrics
            m1, m2 = st.columns(2)
            m1.metric("Vendor", result.get('vendor_name', 'N/A')[:15])
            m2.metric("Confidence", f"{result.get('confidence_score', 0)*100:.0f}%")
            
            m3, m4 = st.columns(2)
            m3.metric("Total", f"₹{result.get('total_amount', 0):,.0f}")
            m4.metric("Tax", f"₹{result.get('tax_amount', 0):,.0f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Status checks
            if result.get('tampering_detected'):
                st.error("⚠️ Tampering Detected")
            else:
                st.success("✅ No tampering detected")
            
            if result.get('gstin'):
                st.success(f"✅ GSTIN: {result['gstin']}")
            else:
                st.warning("⚠️ Missing GSTIN")
            
            if result.get('is_valid_business_expense'):
                st.success("✅ Valid business expense")
            
            # Compliance flags
            if result.get('compliance_flags'):
                st.markdown("**Compliance Flags:**")
                for flag in result['compliance_flags']:
                    st.warning(flag)
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align: center; padding: 3rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                <h3 style="margin: 0; color: #64748B;">No document analyzed yet</h3>
                <p style="margin: 0.5rem 0 0 0; color: #94A3B8;">Upload and analyze a document to see results</p>
            </div>
            """, unsafe_allow_html=True)


def compliance_check_page():
    st.title("Compliance Check")
    st.markdown('<p style="margin-top: -0.5rem;">Get instant answers on GST, tax compliance and legal requirements</p>', unsafe_allow_html=True)
    
    model = init_gemini()
    
    if not model:
        st.error("⚠️ API key not configured. Please set GEMINI_API_KEY in Secrets.")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick Questions
    st.markdown("### Quick Questions")
    col1, col2 = st.columns(2)
    
    questions = [
        "Can I claim ITC on food and beverages?",
        "What is the GST rate for software services?",
        "When is the deadline for GSTR-3B filing?",
        "Is ITC available on vehicles for business use?"
    ]
    
    for i, q in enumerate(questions):
        with col1 if i % 2 == 0 else col2:
            if st.button(q, key=f"q_{i}", use_container_width=True):
                st.session_state.compliance_query = q
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Custom query
    query = st.text_area(
        "Ask your compliance question",
        value=st.session_state.get('compliance_query', ''),
        placeholder="e.g., Can I claim ITC on office furniture?",
        height=100
    )
    
    if st.button("🔍 Check Compliance", use_container_width=True):
        if query:
            prompt = f"""You are an expert in Indian GST and Tax Law for MSMEs.

Question: {query}

Provide a response with:
1. Risk Level: LOW / MEDIUM / HIGH
2. Relevant Law Section
3. Clear explanation
4. Recommended action

Format as JSON:
{{
  "risk_level": "LOW|MEDIUM|HIGH",
  "relevant_section": "Section and Act",
  "explanation": "Clear explanation",
  "compliant_action": "What to do"
}}"""
            
            try:
                with st.spinner("Analyzing..."):
                    response = model.generate_content(prompt)
                    text = response.text.strip()
                    
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                    
                    st.session_state.compliance_result = json.loads(text)
            except:
                st.write(response.text)
    
    if st.session_state.compliance_result:
        result = st.session_state.compliance_result
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        risk = result.get('risk_level', 'MEDIUM')
        if risk == 'LOW':
            st.success(f"🟢 Risk Level: {risk}")
        elif risk == 'HIGH':
            st.error(f"🔴 Risk Level: {risk}")
        else:
            st.warning(f"🟡 Risk Level: {risk}")
        
        st.info(f"📖 **Relevant Section:** {result.get('relevant_section', 'N/A')}")
        
        if result.get('explanation'):
            st.markdown(f"**Explanation:** {result['explanation']}")
        
        st.success(f"✅ **Recommended Action:** {result.get('compliant_action', 'N/A')}")


def subsidy_explorer_page():
    st.title("Subsidy Explorer")
    st.markdown('<p style="margin-top: -0.5rem;">Discover government schemes and subsidies for your business</p>', unsafe_allow_html=True)
    
    model = init_gemini()
    
    if not model:
        st.error("⚠️ API key not configured. Please set GEMINI_API_KEY in Secrets.")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sector = st.selectbox(
            "Business Sector",
            ["Manufacturing", "Textile", "Food Processing", "Agriculture", 
             "IT/Technology", "Pharma", "Services", "Women Entrepreneur", "Rural Business"]
        )
    
    with col2:
        capex = st.number_input(
            "Capital Expenditure (₹)",
            min_value=0,
            value=500000,
            step=100000
        )
    
    with col3:
        state = st.selectbox(
            "State",
            ["All India", "Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", 
             "Uttar Pradesh", "Rajasthan", "Madhya Pradesh", "West Bengal", "Telangana"]
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔍 Find Subsidies", use_container_width=True):
        prompt = f"""Find Indian government subsidies for:
- Sector: {sector}
- Capital: ₹{capex:,.0f}
- State: {state}

Return 3-5 schemes as JSON array:
[{{"name": "Scheme Name", "benefit": "Benefit description", "eligibility": "Who can apply", "ministry": "Ministry name", "link": "URL", "max_subsidy": "Amount"}}]"""
        
        try:
            with st.spinner("Searching schemes..."):
                response = model.generate_content(prompt)
                text = response.text.strip()
                
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                st.session_state.subsidy_result = json.loads(text)
        except:
            st.write(response.text)
    
    if st.session_state.subsidy_result and isinstance(st.session_state.subsidy_result, list):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 🎯 Found {len(st.session_state.subsidy_result)} Schemes")
        
        for scheme in st.session_state.subsidy_result:
            with st.expander(f"📋 {scheme.get('name', 'Unknown')}", expanded=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**💰 Benefit:** {scheme.get('benefit', 'N/A')}")
                    st.markdown(f"**✅ Eligibility:** {scheme.get('eligibility', 'N/A')}")
                    st.markdown(f"**🏛️ Ministry:** {scheme.get('ministry', 'N/A')}")
                with col2:
                    if scheme.get('max_subsidy'):
                        st.metric("Max Subsidy", scheme['max_subsidy'])
                
                if scheme.get('link'):
                    st.markdown(f"🔗 [Apply Here]({scheme['link']})")


# Main app
def main():
    init_session_state()
    page = sidebar()
    
    if page == "🏠 Dashboard":
        dashboard_page()
    elif page == "📄 Document Scanner":
        document_scanner_page()
    elif page == "⚖️ Compliance Check":
        compliance_check_page()
    elif page == "💰 Subsidy Explorer":
        subsidy_explorer_page()


if __name__ == "__main__":
    main()
