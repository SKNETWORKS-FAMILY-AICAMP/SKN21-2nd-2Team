# utils/state_manager.py
import streamlit as st


def init_session():
    """
    Spotify 관련 세션 상태 초기화
    """
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None
    if "token_expires_at" not in st.session_state:
        st.session_state.token_expires_at = None


def save_tokens(token_data: dict):
    """
    Spotify 토큰 정보를 세션에 저장
    """
    st.session_state.access_token = token_data.get("access_token")
    st.session_state.refresh_token = token_data.get("refresh_token")
    
    # expires_in (초 단위) → 만료 시각 계산
    expires_in = token_data.get("expires_in", 3600)
    import time
    st.session_state.token_expires_at = time.time() + expires_in
