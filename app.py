#!/usr/bin/env python3
"""
MicroCFO Streamlit App - AI Financial Assistant for Hugging Face Spaces
Uses Gemini 1.5 Flash with Google File API for superior document vision
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

# Custom CSS for premium look
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(90deg, #818CF8, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
        # Create a temporary file on the server
        suffix = f".{uploaded_file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # Upload to Google (The "Magic" Step)
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
        st.image("https://img.icons8.com/fluency/96/money-bag.png", width=80)
        st.title("MicroCFO")
        st.markdown("*AI Financial Assistant for Indian MSMEs*")
        
        st.divider()
        
        page = st.radio(
            "Navigate to",
            ["🏠 Home", "📄 Invoice Scanner", "⚖️ Compliance Check", "💰 Subsidy Hunter"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # API Status
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Key Missing")
            st.caption("Set GEMINI_API_KEY in Secrets")
        
        st.divider()
        st.info("📄 Supports: PNG, JPG, PDF\n\n🔍 Works with scanned docs & handwriting!")
        
        return page


# Pages
def home_page():
    st.title("🏦 MicroCFO")
    st.markdown("### AI-Powered Financial Assistant for Indian MSMEs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2)); 
                    border-radius: 16px; padding: 2rem; text-align: center; border: 1px solid rgba(99, 102, 241, 0.3);">
            <h3>📄 Visual Auditor</h3>
            <p>Scan invoices with AI-powered fraud detection. Works with scanned PDFs & handwriting!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2)); 
                    border-radius: 16px; padding: 2rem; text-align: center; border: 1px solid rgba(34, 197, 94, 0.3);">
            <h3>⚖️ Legal Sentinel</h3>
            <p>Get instant answers on GST, tax compliance and legal requirements</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(234, 179, 8, 0.2), rgba(245, 158, 11, 0.2)); 
                    border-radius: 16px; padding: 2rem; text-align: center; border: 1px solid rgba(234, 179, 8, 0.3);">
            <h3>💰 Subsidy Hunter</h3>
            <p>Discover government schemes and subsidies for your business</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### ✨ Powered by Gemini 1.5 Flash Vision")
    st.markdown("""
    - 🔍 **Scanned PDFs** - Reads photos saved as PDFs that traditional tools can't parse
    - ✍️ **Handwriting** - Understands handwritten notes and annotations
    - ☁️ **Cloud Processing** - No heavy processing on your device
    """)


def invoice_scanner_page():
    st.title("📄 Visual Auditor")
    st.markdown("Upload an invoice to analyze it for fraud detection and compliance")
    
    model = init_gemini()
    
    if not model:
        st.error("⚠️ API key not configured. Please set GEMINI_API_KEY in Secrets.")
        return
    
    uploaded_file = st.file_uploader(
        "Upload Invoice Document",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Upload a clear image or PDF of your invoice"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Show preview if it's an image
            if uploaded_file.type in ["image/png", "image/jpeg"]:
                st.image(uploaded_file, caption="Preview", use_container_width=True)
            elif uploaded_file.type == "application/pdf":
                st.success("📄 PDF Loaded (Preview not available for PDF)")
                st.info(f"File: {uploaded_file.name}")
        
        with col2:
            if st.button("🔍 Analyze Invoice", use_container_width=True):
                # Upload to Google File API
                google_file = process_uploaded_file(uploaded_file)
                
                if google_file:
                    # The CFO Auditor Prompt
                    system_prompt = """
                    You are an expert AI Accountant and Financial Auditor for Indian MSMEs.
                    Analyze this invoice/document carefully.
                    
                    **EXTRACTION TASKS:**
                    1. Extract: Vendor Name, Invoice Date (YYYY-MM-DD), Total Amount, Tax Amount, GSTIN
                    2. Categorize each line item as: Capital Goods, Raw Material, Personal/Entertainment, or Service
                    
                    **FRAUD DETECTION:**
                    3. Check for: Mismatched fonts, blurred/tampered numbers, handwritten overrides
                    4. Note if this is a handwritten bill
                    
                    **COMPLIANCE CHECKS:**
                    5. Flag items NOT eligible for Input Tax Credit (ITC)
                    6. Flag if GSTIN is missing but tax is charged
                    7. Flag if invoice is >30 days old
                    
                    **OUTPUT FORMAT (JSON):**
                    {
                      "vendor_name": "string",
                      "invoice_date": "YYYY-MM-DD",
                      "total_amount": number,
                      "tax_amount": number,
                      "gstin": "string or null",
                      "is_handwritten": boolean,
                      "tampering_detected": boolean,
                      "confidence_score": number (0.0 to 1.0),
                      "line_items": [{"description": "string", "amount": number, "category": "string"}],
                      "compliance_flags": ["array of warning strings"],
                      "is_valid_business_expense": boolean,
                      "summary": "Brief analysis summary"
                    }
                    """
                    
                    try:
                        with st.spinner("🔍 Analyzing pixels and text..."):
                            response = model.generate_content([system_prompt, google_file])
                            response_text = response.text.strip()
                            
                            # Extract JSON
                            if "```json" in response_text:
                                response_text = response_text.split("```json")[1].split("```")[0].strip()
                            elif "```" in response_text:
                                response_text = response_text.split("```")[1].split("```")[0].strip()
                            
                            st.session_state.invoice_result = json.loads(response_text)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, show raw response
                        st.markdown("### 📊 Analysis Result")
                        st.write(response.text)
                        return
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
                        return
    
    if st.session_state.invoice_result:
        result = st.session_state.invoice_result
        
        st.divider()
        st.markdown("### 📊 Analysis Results")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vendor", result.get('vendor_name', 'N/A')[:20])
        col2.metric("Total Amount", f"₹{result.get('total_amount', 0):,.2f}")
        col3.metric("Tax Amount", f"₹{result.get('tax_amount', 0):,.2f}")
        col4.metric("Confidence", f"{result.get('confidence_score', 0)*100:.0f}%")
        
        # Summary
        if result.get('summary'):
            st.info(f"📝 **Summary:** {result['summary']}")
        
        # Fraud detection
        col1, col2 = st.columns(2)
        
        with col1:
            if result.get('tampering_detected'):
                st.error("⚠️ TAMPERING DETECTED - Manual verification required")
            else:
                st.success("✅ No tampering detected")
            
            if result.get('is_handwritten'):
                st.warning("📝 Handwritten bill - Verify amounts manually")
            
            if result.get('is_valid_business_expense'):
                st.success("✅ Valid business expense")
            else:
                st.warning("⚠️ May not be a valid business expense")
        
        with col2:
            if result.get('gstin'):
                st.success(f"✅ GSTIN: {result['gstin']}")
            else:
                st.warning("⚠️ Missing GSTIN")
            
            st.info(f"📅 Invoice Date: {result.get('invoice_date', 'N/A')}")
        
        # Compliance flags
        if result.get('compliance_flags'):
            st.markdown("### ⚠️ Compliance Flags")
            for flag in result['compliance_flags']:
                st.warning(flag)
        
        # Line items
        if result.get('line_items'):
            st.markdown("### 📋 Line Items")
            for item in result['line_items']:
                cat_emoji = {"Capital Goods": "🏭", "Raw Material": "📦", "Service": "🔧", "Personal/Entertainment": "🎭"}.get(item.get('category', ''), "📌")
                st.markdown(f"- {cat_emoji} **{item['description']}**: ₹{item.get('amount', 0):,.2f} ({item.get('category', 'Unknown')})")


def compliance_check_page():
    st.title("⚖️ Legal Sentinel")
    st.markdown("Get instant answers on GST, tax compliance and legal requirements")
    
    model = init_gemini()
    
    if not model:
        st.error("⚠️ API key not configured. Please set GEMINI_API_KEY in Secrets.")
        return
    
    # Common questions
    st.markdown("### Quick Questions")
    quick_questions = [
        "Can I claim ITC on food and beverages?",
        "What is the GST rate for software services?",
        "When is the deadline for GSTR-3B filing?",
        "Is ITC available on vehicles for business use?"
    ]
    
    col1, col2 = st.columns(2)
    for i, q in enumerate(quick_questions):
        with col1 if i % 2 == 0 else col2:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                st.session_state.compliance_query = q
    
    st.divider()
    
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

Provide a structured response:
1. Risk Level: LOW / MEDIUM / HIGH
2. Relevant Law Section (with Act name)
3. Clear explanation
4. Recommended compliant action

Format as JSON:
{{
  "risk_level": "LOW|MEDIUM|HIGH",
  "relevant_section": "Section and Act name",
  "explanation": "Clear explanation",
  "compliant_action": "Specific action to take"
}}"""
            
            try:
                with st.spinner("Analyzing..."):
                    response = model.generate_content(prompt)
                    response_text = response.text.strip()
                    
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    st.session_state.compliance_result = json.loads(response_text)
            except json.JSONDecodeError:
                st.markdown("### 📋 Response")
                st.write(response.text)
                return
            except Exception as e:
                st.error(f"Error: {e}")
                return
    
    if st.session_state.compliance_result:
        result = st.session_state.compliance_result
        
        st.divider()
        st.markdown("### 📋 Compliance Assessment")
        
        # Risk level with color coding
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
        
        st.markdown(f"**✅ Recommended Action:** {result.get('compliant_action', 'N/A')}")


def subsidy_hunter_page():
    st.title("💰 Subsidy Hunter")
    st.markdown("Discover government schemes and subsidies for your business")
    
    model = init_gemini()
    
    if not model:
        st.error("⚠️ API key not configured. Please set GEMINI_API_KEY in Secrets.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        sector = st.selectbox(
            "Select your sector",
            ["Manufacturing", "Textile", "Food Processing", "Agriculture", 
             "IT/Technology", "Pharma", "Services", "Women Entrepreneur", "Rural Business"]
        )
    
    with col2:
        capex = st.number_input(
            "Capital Expenditure (₹)",
            min_value=0,
            value=500000,
            step=100000,
            format="%d"
        )
    
    state = st.selectbox(
        "State (optional)",
        ["All India", "Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "Uttar Pradesh", 
         "Rajasthan", "Madhya Pradesh", "West Bengal", "Telangana", "Other"]
    )
    
    if st.button("🔍 Find Subsidies", use_container_width=True):
        prompt = f"""You are an expert in Indian Government schemes and subsidies for MSMEs.

Find applicable subsidies for:
- Sector: {sector}
- Capital Expenditure: ₹{capex:,.0f}
- State: {state}

Provide 3-5 REAL government schemes with accurate details:
1. Scheme Name (official name)
2. Benefit (subsidy %, amount, or type)
3. Eligibility criteria
4. Implementing ministry/department
5. Official application link

Format as JSON array:
[{{
  "name": "Official Scheme Name",
  "benefit": "Description of benefit",
  "eligibility": "Who can apply",
  "ministry": "Implementing ministry",
  "link": "Official URL",
  "max_subsidy": "Maximum amount if applicable"
}}]"""
        
        try:
            with st.spinner("Searching for applicable schemes..."):
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                st.session_state.subsidy_result = json.loads(response_text)
        except json.JSONDecodeError:
            st.markdown("### 🎯 Available Schemes")
            st.write(response.text)
            return
        except Exception as e:
            st.error(f"Error: {e}")
            return
    
    if st.session_state.subsidy_result:
        result = st.session_state.subsidy_result
        
        if isinstance(result, list):
            st.divider()
            st.markdown(f"### 🎯 Found {len(result)} Applicable Schemes")
            
            for scheme in result:
                with st.expander(f"📋 {scheme.get('name', 'Unknown Scheme')}", expanded=True):
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
    
    if page == "🏠 Home":
        home_page()
    elif page == "📄 Invoice Scanner":
        invoice_scanner_page()
    elif page == "⚖️ Compliance Check":
        compliance_check_page()
    elif page == "💰 Subsidy Hunter":
        subsidy_hunter_page()


if __name__ == "__main__":
    main()
