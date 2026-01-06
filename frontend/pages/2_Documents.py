"""
Documents List Page.
Shows all uploaded documents and their processing status.
"""
import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="My Documents - Policy Summarizer",
    page_icon="📁",
    layout="wide"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("📁 My Documents")
st.markdown("View and manage your uploaded documents.")

# Refresh button
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

# Fetch documents
try:
    response = requests.get(
        f"{BACKEND_URL}/api/documents",
        params={"page": 1, "page_size": 50},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])
        total = data.get("total", 0)
        
        if total == 0:
            st.info("📭 No documents uploaded yet. Go to Upload to add your first document!")
            if st.button("📤 Upload Document"):
                st.switch_page("pages/1_Upload.py")
        else:
            st.markdown(f"**Total Documents:** {total}")
            st.markdown("---")
            
            # Display documents as cards
            for doc in documents:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        st.markdown(f"**📄 {doc.get('original_filename', 'Unknown')}**")
                        st.caption(f"Type: {doc.get('file_type', 'N/A')} | Size: {doc.get('file_size', 'N/A')}")
                    
                    with col2:
                        status = doc.get("status", "unknown")
                        status_colors = {
                            "pending": "🟡",
                            "processing": "🔵",
                            "completed": "🟢",
                            "failed": "🔴"
                        }
                        st.markdown(f"{status_colors.get(status, '⚪')} **{status.upper()}**")
                    
                    with col3:
                        clause_count = doc.get("clause_count", 0)
                        st.metric("Clauses", clause_count)
                    
                    with col4:
                        doc_id = doc.get("doc_id")
                        
                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)
                        
                        with btn_col1:
                            if status == "completed":
                                if st.button("📊 View", key=f"view_{doc_id}"):
                                    st.session_state["selected_doc_id"] = doc_id
                                    st.switch_page("pages/3_Summary.py")
                        
                        with btn_col2:
                            if st.button("🗑️", key=f"del_{doc_id}"):
                                del_response = requests.delete(
                                    f"{BACKEND_URL}/api/documents/{doc_id}",
                                    timeout=10
                                )
                                if del_response.status_code == 200:
                                    st.success("Deleted!")
                                    st.rerun()
                                else:
                                    st.error("Delete failed")
                    
                    # Show error if failed
                    if status == "failed" and doc.get("error_message"):
                        st.error(f"Error: {doc.get('error_message')}")
                    
                    st.markdown("---")
    else:
        st.error(f"Failed to fetch documents: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    st.error("❌ Cannot connect to backend server. Please ensure the server is running.")
    st.code(f"Backend URL: {BACKEND_URL}")
except Exception as e:
    st.error(f"Error: {str(e)}")

# Sidebar
st.sidebar.markdown("### Document Status Guide")
st.sidebar.markdown("""
- 🟡 **Pending**: Waiting to be processed
- 🔵 **Processing**: AI analysis in progress
- 🟢 **Completed**: Ready to view
- 🔴 **Failed**: Error occurred
""")
