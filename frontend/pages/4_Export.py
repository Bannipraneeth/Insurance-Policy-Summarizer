"""
Export Page.
Download document analysis in various formats.
"""
import streamlit as st
import requests
from config import BACKEND_URL

st.set_page_config(
    page_title="Export - Policy Summarizer",
    page_icon="💾",
    layout="wide"
)

st.title("💾 Export Document Analysis")

# Get document ID and format from session
doc_id = st.session_state.get("export_doc_id") or st.session_state.get("selected_doc_id")
export_format = st.session_state.get("export_format")

# Document selector
st.markdown("### Select Document")

try:
    docs_response = requests.get(
        f"{BACKEND_URL}/api/documents",
        params={"page": 1, "page_size": 50},
        timeout=10
    )
    
    if docs_response.status_code == 200:
        documents = docs_response.json().get("documents", [])
        completed_docs = [d for d in documents if d.get("status") == "completed"]
        
        if completed_docs:
            doc_options = {d["original_filename"]: d["doc_id"] for d in completed_docs}
            
            # Find current selection
            current_idx = 0
            if doc_id:
                for i, (name, did) in enumerate(doc_options.items()):
                    if did == doc_id:
                        current_idx = i
                        break
            
            selected_doc = st.selectbox(
                "Choose a document to export",
                list(doc_options.keys()),
                index=current_idx
            )
            
            doc_id = doc_options[selected_doc]
        else:
            st.warning("No processed documents available for export.")
            st.stop()
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to backend server.")
    st.stop()

st.markdown("---")

# Export options
st.markdown("### Export Format")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 📄 PDF Report")
    st.markdown("""
    Formatted document with:
    - Summary statistics
    - Risk-coded summaries
    - Professional layout
    """)
    if st.button("Download PDF", type="primary", use_container_width=True):
        with st.spinner("Generating PDF..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/api/export/{doc_id}/pdf",
                    timeout=60
                )
                if response.status_code == 200:
                    st.download_button(
                        label="📥 Save PDF File",
                        data=response.content,
                        file_name=f"{selected_doc}_analysis.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("Failed to generate PDF")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.markdown("#### 📋 JSON Data")
    st.markdown("""
    Structured data including:
    - All summaries
    - Extracted entities
    - Risk scores
    - Original text references
    """)
    if st.button("Download JSON", type="primary", use_container_width=True):
        with st.spinner("Generating JSON..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/api/export/{doc_id}/json",
                    timeout=60
                )
                if response.status_code == 200:
                    st.download_button(
                        label="📥 Save JSON File",
                        data=response.content,
                        file_name=f"{selected_doc}_analysis.json",
                        mime="application/json",
                        use_container_width=True
                    )
                else:
                    st.error("Failed to generate JSON")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col3:
    st.markdown("#### 📊 CSV Spreadsheet")
    st.markdown("""
    Tabular data for:
    - Excel/Google Sheets
    - Data analysis
    - Easy filtering
    """)
    if st.button("Download CSV", type="primary", use_container_width=True):
        with st.spinner("Generating CSV..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/api/export/{doc_id}/csv",
                    timeout=60
                )
                if response.status_code == 200:
                    st.download_button(
                        label="📥 Save CSV File",
                        data=response.content,
                        file_name=f"{selected_doc}_analysis.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.error("Failed to generate CSV")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")

# Preview section
st.markdown("### Preview Data")

if st.checkbox("Show JSON preview"):
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/export/{doc_id}/json",
            timeout=30
        )
        if response.status_code == 200:
            st.json(response.json())
    except Exception as e:
        st.error(f"Error loading preview: {str(e)}")

# Navigation
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("← Back to Summary"):
        st.session_state["selected_doc_id"] = doc_id
        st.switch_page("pages/3_Summary.py")

with col2:
    if st.button("📁 View All Documents"):
        st.switch_page("pages/2_Documents.py")
