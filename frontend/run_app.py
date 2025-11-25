"""
run_app.py (Login API 모듈)
Auth: 박수빈
Date: 2025-11-18
Description
- Login 여부 Check
"""

import streamlit as st
from login import show_login_page
from main import show_main_page

def main():
    st.set_page_config(
        page_title="Main App", 
        page_icon="📘",
        layout="wide",  # FHD 화면에 맞게 wide 레이아웃 사용
        initial_sidebar_state="expanded"
    )

    # 디버깅 로그 (개발 중에만 표시)
    # with st.expander("🔍 [DEBUG] 세션 상태 확인", expanded=False):
    #     st.write(f"**page:** {st.session_state.get('page', '없음')}")
    #     st.write(f"**logged_in:** {st.session_state.get('logged_in', False)}")
    #     st.write(f"**user_info:** {st.session_state.get('user_info', None)}")
    #     st.write(f"**전체 session_state:** {dict(st.session_state)}")

    # Session Data 미존재 시 (페이지 첫 입장)
    if "page" not in st.session_state:
        st.session_state.page = "login"
        # st.write("🔍 [LOG] run_app: page 초기화 -> 'login'")
        
    # 로그인 상태 확인 (우선순위 높음)
    if st.session_state.get("logged_in") == True:
        # st.write("🔍 [LOG] run_app: logged_in=True -> show_main_page() 호출")
        show_main_page()
        return
        
    # Session Data Page 값이 'Login' 시,
    if st.session_state.page == "login":
        # st.write("🔍 [LOG] run_app: page='login' -> show_login_page() 호출")
        show_login_page()
        
    # Session Data Page 값이 'signup' 시,
    elif st.session_state.page == "signup":
        # st.write("🔍 [LOG] run_app: page='signup' -> show_signup_page() 호출")
        from signup import show_signup_page
        show_signup_page()
    else:
        # st.write(f"🔍 [LOG] run_app: page='{st.session_state.page}' -> show_main_page() 호출")
        show_main_page()

if __name__ == "__main__":
    main()
