"""
Policy Summarizer - Streamlit Frontend
Main application entry point with navigation.
"""
import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Policy Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Global styles */
    .main {
        padding: 1rem;
    }
    
    /* Risk level badges */
    .risk-critical {
        background-color: #ff4444;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .risk-high {
        background-color: #ff8800;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .risk-medium {
        background-color: #ffcc00;
        color: black;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .risk-low {
        background-color: #00cc44;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    
    /* Card styling */
    .summary-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
    }
    
    /* Status badges */
    .status-pending {
        color: #ffc107;
    }
    .status-processing {
        color: #17a2b8;
    }
    .status-completed {
        color: #28a745;
    }
    .status-failed {
        color: #dc3545;
    }
    
    /* Entity tags */
    .entity-tag {
        display: inline-block;
        background-color: #e9ecef;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin: 0.1rem;
        font-size: 0.85rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("📄 Policy Summarizer")
st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")
st.sidebar.page_link("app.py", label="🏠 Home", icon="🏠")
st.sidebar.page_link("pages/1_Upload.py", label="📤 Upload Document")
st.sidebar.page_link("pages/2_Documents.py", label="📁 My Documents")
st.sidebar.page_link("pages/3_Summary.py", label="📊 View Summary")
st.sidebar.page_link("pages/4_Export.py", label="💾 Export")
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
AI-powered document analysis for insurance policies and Terms & Conditions.

**Features:**
- 📄 PDF, TXT, HTML support
- 🔍 Automatic clause detection
- 🏷️ Entity extraction
- ⚠️ Risk scoring
- 📊 Export reports
""")

# Main content
st.markdown("""
<div class="main-header">
    <h1>🔍 AI-Based Policy & T&C Summarization System</h1>
    <p>Transform complex legal documents into clear, actionable insights</p>
</div>
""", unsafe_allow_html=True)

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📤 Upload Documents")
    st.markdown("""
    Upload insurance policies, terms & conditions, or any legal document.
    
    **Supported formats:**
    - PDF documents
    - Text files (.txt)
    - HTML pages
    - Scanned images (OCR)
    """)
    if st.button("Upload Now", key="btn_upload"):
        st.switch_page("pages/1_Upload.py")

with col2:
    st.markdown("### 🔍 Automatic Analysis")
    st.markdown("""
    Our AI automatically extracts and analyzes:
    
    - **Clauses**: Identifies key sections
    - **Entities**: Coverage, exclusions, amounts
    - **Risks**: Critical issues highlighted
    - **Summaries**: Plain language explanations
    """)

with col3:
    st.markdown("### 📊 Actionable Insights")
    st.markdown("""
    Get clear, traceable summaries:
    
    - ⚠️ Risk-level indicators
    - 🔗 Link summary to original text
    - 📑 Filter by risk or type
    - 💾 Export to PDF/JSON/CSV
    """)

st.markdown("---")

# Quick stats (if any documents exist)
st.markdown("### 📈 Quick Stats")
st.info("Upload your first document to see analytics here!")

# How it works
st.markdown("---")
st.markdown("### 🔄 How It Works")

steps = st.columns(4)
with steps[0]:
    st.markdown("#### 1️⃣ Upload")
    st.markdown("Upload your policy document or T&C file")
    
with steps[1]:
    st.markdown("#### 2️⃣ Process")
    st.markdown("AI extracts text, detects clauses, and identifies entities")
    
with steps[2]:
    st.markdown("#### 3️⃣ Summarize")
    st.markdown("Each clause gets a concise summary with risk assessment")
    
with steps[3]:
    st.markdown("#### 4️⃣ Review")
    st.markdown("View summaries, filter by risk, trace back to original text")
