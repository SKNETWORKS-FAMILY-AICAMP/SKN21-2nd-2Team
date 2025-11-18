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
    ''' Login 여부 Check 함수'''
    st.set_page_config(page_title="Main App", page_icon="📘")

    # Session Data가 로그인 일 시,
    if st.session_state.get("logged_in", False):
        # 메인 화면
        show_main_page()
    else:
        # 로그인 화면
        show_login_page()

if __name__ == "__main__":
    main()
