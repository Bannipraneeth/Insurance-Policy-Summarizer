"""
Summary View Page.
Displays document summaries with filtering and traceability.
"""
import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Summary View - Policy Summarizer",
    page_icon="📊",
    layout="wide"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Risk level colors
RISK_COLORS = {
    "critical": "#ff4444",
    "high": "#ff8800",
    "medium": "#ffcc00",
    "low": "#00cc44"
}

RISK_EMOJIS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢"
}

st.title("📊 Document Summary")

# Get document ID from session or sidebar
doc_id = st.session_state.get("selected_doc_id")

# Document selector in sidebar
st.sidebar.markdown("### Select Document")

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
            
            selected_doc = st.sidebar.selectbox(
                "Choose a document",
                list(doc_options.keys()),
                index=current_idx
            )
            
            doc_id = doc_options[selected_doc]
            st.session_state["selected_doc_id"] = doc_id
        else:
            st.sidebar.warning("No processed documents available")
            
except requests.exceptions.ConnectionError:
    st.sidebar.error("Cannot connect to backend")

# Filters in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

risk_filter = st.sidebar.multiselect(
    "Risk Level",
    ["critical", "high", "medium", "low"],
    default=[]
)

clause_type_filter = st.sidebar.multiselect(
    "Clause Type",
    ["coverage", "exclusion", "condition", "limitation", "obligation", "definition", "termination", "claim"],
    default=[]
)

entity_type_filter = st.sidebar.multiselect(
    "Entity Type",
    ["monetary_amount", "coverage_item", "exclusion", "time_period", "condition", "date", "party", "limit", "deductible"],
    default=[]
)

# Main content
if doc_id:
    try:
        # Build query params
        params = {}
        if risk_filter:
            params["risk_level"] = risk_filter
        if clause_type_filter:
            params["clause_type"] = clause_type_filter
        if entity_type_filter:
            params["entity_type"] = entity_type_filter
        
        # Fetch summaries
        response = requests.get(
            f"{BACKEND_URL}/api/summaries/{doc_id}",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get("stats", {})
            summaries = data.get("summaries", [])
            
            # Document header
            st.markdown(f"### 📄 {data.get('document_name', 'Document')}")
            
            # Stats row
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Clauses", stats.get("total", 0))
            with col2:
                st.metric("🔴 Critical", stats.get("critical", 0))
            with col3:
                st.metric("🟠 High", stats.get("high", 0))
            with col4:
                st.metric("🟡 Medium", stats.get("medium", 0))
            with col5:
                st.metric("🟢 Low", stats.get("low", 0))
            
            st.markdown("---")
            
            # Show filtered count
            if any([risk_filter, clause_type_filter, entity_type_filter]):
                st.info(f"Showing {data.get('filtered_count', 0)} of {stats.get('total', 0)} clauses (filtered)")
            
            # Summary cards
            if not summaries:
                st.warning("No summaries match the selected filters.")
            else:
                for i, summary in enumerate(summaries):
                    risk_level = summary.get("risk_level", "low")
                    risk_color = RISK_COLORS.get(risk_level, "#0d0c0c")
                    risk_emoji = RISK_EMOJIS.get(risk_level, "⚪")
                    
                    # Create expandable card
                    section = summary.get("section_number", f"Clause {i+1}")
                    clause_type = summary.get("clause_type", "General")
                    
                    with st.expander(
                        f"{risk_emoji} **{section}** - {clause_type.title()} | Risk: {risk_level.upper()}",
                        expanded=(risk_level in ["critical", "high"])
                    ):
                        # Summary section
                        st.markdown("#### 📝 Summary")
                        st.markdown(
                            f'<div style="background-color: #191a1c; padding: 1rem; border-left: 4px solid {risk_color}; border-radius: 4px;">'
                            f'{summary.get("summary_text", "No summary available")}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Two columns for details
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Entities
                            st.markdown("#### 🏷️ Extracted Entities")
                            entities = summary.get("entities", [])
                            if entities:
                                for entity in entities:
                                    entity_type = entity.get("entity_type", "unknown")
                                    value = entity.get("value", "")
                                    st.markdown(
                                        f'<span style="background-color: #e9ecef; padding: 0.2rem 0.5rem; '
                                        f'border-radius: 1rem; margin: 0.1rem; display: inline-block; font-size: 0.85rem;">'
                                        f'<b>{entity_type}:</b> {value[:100]}</span>',
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.caption("No entities extracted")
                        
                        with col2:
                            # Risk details
                            st.markdown("#### ⚠️ Risk Assessment")
                            st.markdown(f"**Level:** {risk_emoji} {risk_level.upper()}")
                            st.markdown(f"**Confidence:** {summary.get('confidence_score', 0):.0%}")
                            
                            risk_indicators = summary.get("risk_indicators")
                            if risk_indicators:
                                try:
                                    indicators = json.loads(risk_indicators)
                                    if indicators.get("explanation"):
                                        st.caption(indicators.get("explanation"))
                                except:
                                    pass
                        
                        # Original text (traceability)
                        st.markdown("---")
                        st.markdown("#### 📜 Original Text")
                        original = summary.get("original_text", "")
                        if len(original) > 1000:
                            original = original[:1000] + "..."
                        st.text_area(
                            "Original clause text",
                            original,
                            height=150,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"orig_{summary.get('summary_id', i)}"
                        )
                        
                        # Feedback section
                        st.markdown("#### ⭐ Rate this Summary")
                        rating_col, comment_col = st.columns([1, 2])
                        
                        with rating_col:
                            rating = st.slider(
                                "Rating",
                                1, 5, 3,
                                key=f"rating_{summary.get('summary_id', i)}",
                                label_visibility="collapsed"
                            )
                        
                        with comment_col:
                            if st.button("Submit Feedback", key=f"fb_{summary.get('summary_id', i)}"):
                                try:
                                    fb_response = requests.post(
                                        f"{BACKEND_URL}/api/feedback",
                                        json={
                                            "summary_id": summary.get("summary_id"),
                                            "rating": rating,
                                            "comment": ""
                                        },
                                        timeout=10
                                    )
                                    if fb_response.status_code == 200:
                                        st.success("Thanks for your feedback!")
                                except:
                                    st.error("Failed to submit feedback")
                        
                        st.markdown("---")
        else:
            st.error(f"Failed to load summaries: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("👈 Select a document from the sidebar to view its summary.")
    st.markdown("Or [upload a new document](/Upload)")

# Export buttons at bottom
if doc_id:
    st.markdown("---")
    st.markdown("### 💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export PDF", use_container_width=True):
            st.session_state["export_format"] = "pdf"
            st.session_state["export_doc_id"] = doc_id
            st.switch_page("pages/4_Export.py")
    
    with col2:
        if st.button("📋 Export JSON", use_container_width=True):
            st.session_state["export_format"] = "json"
            st.session_state["export_doc_id"] = doc_id
            st.switch_page("pages/4_Export.py")
    
    with col3:
        if st.button("📊 Export CSV", use_container_width=True):
            st.session_state["export_format"] = "csv"
            st.session_state["export_doc_id"] = doc_id
            st.switch_page("pages/4_Export.py")
