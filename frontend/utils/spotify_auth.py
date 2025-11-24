# utils/spotify_auth.py
# ----------------------------------------------------------
# 파일명: frontend/utils/spotify_auth.py
# 설명: Spotify 인증 관련 유틸리티. 로그인 URL 생성, 토큰 교환 및 갱신 기능을 제공합니다.
# 작성일: 2025-11-24
# 작성자: Antigravity (AI Assistant)
# ----------------------------------------------------------

import os
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
# REDIRECT_URI 기본값 설정
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:5000/spotify/callback")

SCOPE = "user-read-private user-read-email streaming user-read-playback-state user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"


def get_login_url():
    """
    Spotify 로그인 페이지 URL 반환
    """
    base_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def get_token_from_code(code: str):
    """
    Authorization Code를 Access Token으로 교환
    """
    if not code:
        raise Exception("Authorization code가 제공되지 않았습니다.")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        raise Exception("CLIENT_ID 또는 CLIENT_SECRET이 설정되지 않았습니다.")
    
    if not REDIRECT_URI:
        raise Exception("REDIRECT_URI가 설정되지 않았습니다.")
    
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    
    # 디버깅: redirect_uri 확인 (실제로는 로그에 출력하지 않음)
    print(f"토큰 교환 시도 - Redirect URI: {REDIRECT_URI}")

    res = requests.post(url, data=data)
    if res.status_code != 200:
        error_detail = res.text
        raise Exception(f"토큰 발급 실패: {res.status_code} {error_detail}\\n사용된 Redirect URI: {REDIRECT_URI}")
    return res.json()


def refresh_token(refresh_token: str):
    """
    Refresh Token으로 Access Token 갱신
    """
    url = "https://accounts.spotify.com/api/token"

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    res = requests.post(url, data=data)
    if res.status_code != 200:
        raise Exception(f"리프레시 실패: {res.status_code} {res.text}")
    return res.json()
