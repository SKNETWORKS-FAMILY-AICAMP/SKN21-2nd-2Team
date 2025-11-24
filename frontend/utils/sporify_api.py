# utils/sporify_api.py
import requests


def search_tracks(access_token: str, query: str, limit: int = 20, offset: int = 0):
    """
    Spotify API를 사용하여 트랙 검색
    """
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": limit,
        "offset": offset
    }
    
    res = requests.get(url, headers=headers, params=params)
    
    if res.status_code != 200:
        raise Exception(f"Spotify API 오류: {res.status_code} {res.text}")
    
    data = res.json()
    return data.get("tracks", {}).get("items", [])
