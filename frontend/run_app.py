"""
run_app.py (Login API 모듈)
Auth: 박수빈
Date: 2025-11-18
Description
- 실 Login 여부 Check
"""

import streamlit as st
from login import show_login_page
from main import show_main_page

def main():
    st.set_page_config(page_title="Main App", page_icon="📘")

    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "signup":
        from signup import show_signup_page
        show_signup_page()
    else:
        show_main_page()

if __name__ == "__main__":
    main()
