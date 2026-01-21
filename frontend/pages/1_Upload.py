"""
Upload Document Page.
Allows users to upload documents for processing.
"""
import streamlit as st
import requests
from config import BACKEND_URL

st.set_page_config(
    page_title="Upload Document - Policy Summarizer",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Upload Document")
st.markdown("Upload your insurance policy or Terms & Conditions document for AI-powered analysis.")

# File upload section
st.markdown("### Select a Document")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "txt", "html", "jpg", "jpeg", "png"],
    help="Supported formats: PDF, TXT, HTML, JPG, PNG (max 25MB)"
)

if uploaded_file is not None:
    # File info
    st.markdown("### 📄 File Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("File Name", uploaded_file.name)
    with col2:
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.metric("File Size", f"{file_size:.2f} MB")
    with col3:
        file_type = uploaded_file.type or uploaded_file.name.split('.')[-1]
        st.metric("File Type", file_type)
    
    # Upload button
    st.markdown("---")
    
    if st.button("🚀 Upload and Process", type="primary", use_container_width=True):
        with st.spinner("Uploading document..."):
            try:
                # Reset file position
                uploaded_file.seek(0)
                
                # Upload to backend
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(
                    f"{BACKEND_URL}/api/documents/upload",
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Document uploaded successfully!")
                    
                    # Show document info
                    st.markdown("### Document Status")
                    st.json({
                        "Document ID": result.get("doc_id"),
                        "Filename": result.get("original_filename"),
                        "Status": result.get("status"),
                        "Uploaded": result.get("uploaded_at")
                    })
                    
                    st.info("⏳ Processing has started in the background. Check 'My Documents' to see the status.")
                    
                    # Navigation buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📁 Go to My Documents"):
                            st.switch_page("pages/2_Documents.py")
                    with col2:
                        if st.button("📤 Upload Another"):
                            st.rerun()
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"❌ Upload failed: {error_detail}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend server. Please ensure the server is running.")
                st.info(f"Backend URL: {BACKEND_URL}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

else:
    # Instructions when no file is selected
    st.markdown("---")
    st.markdown("### 📋 Instructions")
    
    st.markdown("""
    1. **Click** the file upload area above or drag and drop a file
    2. **Wait** for the file to load
    3. **Click** "Upload and Process" to start AI analysis
    4. **View** your results in the Summary page
    """)
    
    st.markdown("### ✅ Supported File Types")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Document Formats:**
        - 📄 PDF (text and scanned)
        - 📝 Plain Text (.txt)
        - 🌐 HTML pages
        """)
    
    with col2:
        st.markdown("""
        **Image Formats (with OCR):**
        - 🖼️ JPEG images
        - 🖼️ PNG images
        """)
    
    st.warning("⚠️ Maximum file size: 25 MB")

# Sidebar
st.sidebar.markdown("### Upload Tips")
st.sidebar.info("""
**For best results:**
- Use high-quality PDF files
- Ensure scanned documents are legible
- Text-based PDFs work best
- Large documents may take longer to process
""")
