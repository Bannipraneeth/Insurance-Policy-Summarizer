"""
Shared configuration utilities for Streamlit frontend.
Supports both Streamlit Cloud secrets and environment variables.
"""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_backend_url() -> str:
    """
    Get backend URL from Streamlit secrets or environment variable.
    Priority: Streamlit secrets > Environment variable > Default
    """
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        if hasattr(st, 'secrets') and 'BACKEND_URL' in st.secrets:
            return st.secrets['BACKEND_URL']
    except Exception:
        pass
    
    # Fall back to environment variable
    return os.getenv("BACKEND_URL", "http://localhost:8000")


# Export for easy import
BACKEND_URL = get_backend_url()
