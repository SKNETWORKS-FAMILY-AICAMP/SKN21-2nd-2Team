"""
spotify_auth.py (Spotify 인증 유틸리티)
Auth: 박수빈
Date: 2025-11-18
Description
- Spotify 로그인 URL 생성
- Authorization Code를 Access Token으로 교환
- Refresh Token으로 Access Token 갱신
- 타임아웃 및 재시도 로직 처리
"""

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
    
    # 타임아웃 설정 및 재시도 로직
    max_retries = 3
    timeout = 30  # 30초 타임아웃
    
    for attempt in range(max_retries):
        try:
            res = requests.post(url, data=data, timeout=timeout)
            if res.status_code != 200:
                error_detail = res.text
                raise Exception(f"토큰 발급 실패: {res.status_code} {error_detail}\\n사용된 Redirect URI: {REDIRECT_URI}")
            return res.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue  # 재시도
            else:
                raise Exception(f"Spotify 토큰 발급 타임아웃: {max_retries}번 시도 후 실패했습니다. 네트워크 연결을 확인해주세요.")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                continue  # 재시도
            else:
                raise Exception(f"Spotify 토큰 발급 중 오류 발생: {str(e)}")
    
    # 이 코드는 실행되지 않아야 하지만 안전을 위해 추가
    raise Exception("토큰 발급 실패: 알 수 없는 오류")


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

    # 타임아웃 설정 및 재시도 로직
    max_retries = 3
    timeout = 30  # 30초 타임아웃
    
    for attempt in range(max_retries):
        try:
            res = requests.post(url, data=data, timeout=timeout)
            if res.status_code != 200:
                raise Exception(f"리프레시 실패: {res.status_code} {res.text}")
            return res.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue  # 재시도
            else:
                raise Exception(f"Spotify 토큰 갱신 타임아웃: {max_retries}번 시도 후 실패했습니다. 네트워크 연결을 확인해주세요.")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                continue  # 재시도
            else:
                raise Exception(f"Spotify 토큰 갱신 중 오류 발생: {str(e)}")
    
    # 이 코드는 실행되지 않아야 하지만 안전을 위해 추가
    raise Exception("토큰 갱신 실패: 알 수 없는 오류")
