"""
main.py (플랫폼 Main 화면)
Auth: 박수빈
Date: 2025-11-18
Description
- 홈 화면
- 내 정보 수정
- Admin 사용자 데이터 관리
- Admin 사용자 조회
"""
import streamlit as st
import requests
import pandas as pd
import numpy as np
import os
import streamlit.components.v1 as components
from utils.spotify_auth import get_login_url
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (matplotlib)
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

API_URL = "http://localhost:5000/api"

# selectbox input field 편집 불가 처리
st.markdown("""
<style>
/* Streamlit의 selectbox는 Baseweb 컴포넌트의 input 요소를 사용 */
/* 해당 input 요소의 편집을 불가능하게 만듦 */
div[data-baseweb="select"] input {
    pointer-events: none !important;   /* 클릭 후 텍스트 수정 불가 */
}

/* 커서를 텍스트 수정 커서가 아닌 기본 화살표로 변경 */
div[data-baseweb="select"] input {
    caret-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

value = st.selectbox("옵션 선택", ["A", "B", "C"])

# ----------------------------------------------------------
# 음악 카테고리 목록 로드 함수
# ----------------------------------------------------------
def get_music_categories():
    """
    user_data.csv에서 음악 카테고리 목록을 읽어옴
    """
    try:
        csv_path = os.path.join("data", "user_data.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if "Favorite_Music" in df.columns:
                categories = sorted(df["Favorite_Music"].dropna().unique().tolist())
                return categories
    except Exception as e:
        st.write(f"🔍 [LOG] 음악 카테고리 로드 오류: {e}")
    
    # 기본값 (CSV 로드 실패 시)
    return [
        "Alternative", "Blues", "Classical", "Country", "EDM",
        "Folk", "Hip Hop", "House", "Indie", "Jazz",
        "K-Pop", "Latin", "Metal", "Pop", "R&B",
        "Reggae", "Rock", "Soul", "Techno", "Trap"
    ]

# ----------------------------------------------------------
# API 호출 유틸 함수
# ----------------------------------------------------------
# ----------------------------------------------------------
# API 호출 유틸 함수
# ----------------------------------------------------------
def call_api(endpoint: str):
    """
    Flask API(endpoint)를 GET 요청으로 호출하는 함수
    """
    try:
        res = requests.get(f"{API_URL}/{endpoint}")
        if res.status_code == 200:
            try:
                return True, res.json()
            except ValueError as e:
                # JSON 파싱 실패 시 텍스트 반환
                return False, {"error": f"JSON 파싱 실패: {str(e)}, 응답: {res.text[:200]}"}
        else:
            return False, {"error": f"HTTP {res.status_code}: {res.text[:200]}"}
    except Exception as e:
        return False, {"error": str(e)}

def call_api_post(endpoint: str, payload: dict):
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=payload)
        return True, res.json()
    except Exception as e:
        return False, {"error": str(e)}

def search_tracks_api(query, limit=20, offset=0):
    """
    백엔드 API를 호출하여 트랙 검색
    """
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        params = {
            "q": query,
            "limit": limit,
            "offset": offset
        }
        res = requests.get(f"{API_URL}/music/search", headers=headers, params=params)
        
        if res.status_code == 200:
            return res.json().get("tracks", [])
        else:
            st.error(f"검색 실패: {res.text}")
            return []
    except Exception as e:
        st.error(f"API 호출 중 오류: {str(e)}")
        return []

# ----------------------------------------------------------
# 서브 페이지 함수들
# ----------------------------------------------------------
def show_home_page():
    render_top_guide_banner("home")
    
    user = st.session_state.user_info
    grade = user.get("grade") if user else None
    
    # 관리자(99)는 통계 화면, 일반 유저(01)는 음악 재생 화면
    if grade == "99":
        show_admin_home_page()
    else:
        show_user_home_page()


def show_user_home_page():
    """일반 유저(01) 홈 화면 - 음악 재생"""
    st.markdown("## 🎵 Music Search & Player")
    
    # Spotify 토큰 확인 (필수)
    if "access_token" not in st.session_state or not st.session_state.access_token:
        st.error("⚠️ Spotify 인증이 필요합니다.")
        st.info("로그인 화면으로 이동하여 Spotify 인증을 먼저 완료해주세요.")
        if st.button("🔐 로그인 화면으로 이동"):
            st.session_state.page = "login"
            st.session_state.logged_in = False
            st.rerun()
        st.stop()

    # 메인 컨텐츠 영역 (검색 및 플레이어)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("음악 검색")
        
        # 검색 입력
        search_query = st.text_input("검색어를 입력하세요", placeholder="곡명, 아티스트명 등...", key="search_input")
        
        # 상세 필터
        with st.expander("🔍 상세 필터"):
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                # 연도 필터
                current_year = 2025
                year_range = st.slider("발매 연도", 1950, current_year, (2000, current_year))
                
                # 인기도 필터
                min_popularity = st.slider("최소 인기도", 0, 100, 0, help="0: 인기 없음, 100: 매우 인기 있음")
            
            with col_filter2:
                # 장르 필터
                genres = ["k-pop", "pop", "hip-hop", "r-b", "rock", "jazz", "classical", "electronic"]
                selected_genres = st.multiselect("장르 선택", genres)
                
                # 태그 필터
                st.markdown("###### 태그")
                col_tag1, col_tag2 = st.columns(2)
                with col_tag1:
                    tag_new = st.checkbox("🔥 최신 발매 (New)", value=False)
                with col_tag2:
                    tag_hipster = st.checkbox("💎 숨겨진 명곡 (Hipster)", value=False)
        
        # 검색 버튼
        search_button = st.button("🔍 검색", type="primary", use_container_width=True)

        # 검색 실행 (검색 버튼 클릭 또는 필터 변경 시)
        # 필터 변경 시 자동 검색을 원하면 아래 조건 유지, 아니면 search_button만 사용
        should_search = search_button
        
        if should_search:
            # 고급 검색 쿼리 생성
            advanced_query = f"{search_query}" if search_query else ""
            
            if year_range:
                advanced_query += f" year:{year_range[0]}-{year_range[1]}"
            
            if selected_genres:
                for genre in selected_genres:
                    advanced_query += f" genre:\"{genre}\""
            
            if tag_new:
                advanced_query += " tag:new"
            if tag_hipster:
                advanced_query += " tag:hipster"
            
            if not advanced_query.strip():
                st.warning("검색어 또는 필터를 입력해주세요.")
            else:
                st.session_state.last_query = advanced_query
                st.session_state.search_offset = 0
                st.session_state.search_results = []
                st.session_state.has_more = True
                
                with st.spinner("검색 중..."):
                    new_tracks = search_tracks_api(advanced_query, limit=20, offset=0)
                    
                    # 인기도 필터 적용
                    if min_popularity > 0:
                        new_tracks = [t for t in new_tracks if t.get("popularity", 0) >= min_popularity]
                    
                    st.session_state.search_results = new_tracks
                    
                    if len(new_tracks) < 20:
                        st.session_state.has_more = False
                    else:
                        st.session_state.search_offset = 20

        # 결과 표시
        tracks = st.session_state.get("search_results", [])
        
        if tracks:
            st.write(f"**{len(tracks)}개의 결과를 찾았습니다**")
            
            for idx, track in enumerate(tracks):
                track_name = track.get("name", "알 수 없음")
                artists = ", ".join([artist.get("name", "") for artist in track.get("artists", [])])
                album = track.get("album", {}).get("name", "알 수 없음")
                duration_ms = track.get("duration_ms", 0)
                duration_str = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                
                images = track.get("album", {}).get("images", [])
                image_url = images[0].get("url") if images else None
                track_uri = track.get("uri", "")
                
                with st.container(border=True):
                    cols = st.columns([1, 4, 1])
                    with cols[0]:
                        if image_url:
                            st.image(image_url, width=60)
                        else:
                            st.write("🎵")
                    with cols[1]:
                        st.markdown(f"**{track_name}**")
                        st.caption(f"👤 {artists} | 💿 {album}")
                        st.caption(f"⏱️ {duration_str}")
                    with cols[2]:
                        if st.button("▶", key=f"play_{idx}", help="이 곡 재생"):
                            st.session_state.selected_track = {
                                "uri": track_uri,
                                "name": track_name,
                                "artists": artists,
                                "image_url": image_url
                            }
                            
                            st.rerun()
            
            if st.session_state.get("has_more", False):
                 if st.button("더 보기 (Load More)", key="load_more_btn", use_container_width=True):
                     with st.spinner("추가 로딩 중..."):
                         current_offset = st.session_state.get("search_offset", 0)
                         query = st.session_state.get("last_query", "")
                         
                         new_tracks = search_tracks_api(query, limit=20, offset=current_offset)
                         
                         # 인기도 필터 적용
                         if min_popularity > 0:
                             new_tracks = [t for t in new_tracks if t.get("popularity", 0) >= min_popularity]
                         
                         st.session_state.search_results.extend(new_tracks)
                         
                         if len(new_tracks) < 20:
                             st.session_state.has_more = False
                         else:
                             st.session_state.search_offset = current_offset + 20
                     
                     st.rerun()

        elif st.session_state.get("last_query"):
            st.info("검색 결과가 없습니다.")
    
    with col2:
        st.subheader("플레이어")
        
        selected_track = st.session_state.get("selected_track")
        
        if selected_track:
            # 플레이어 HTML 로드 (경로 수정: frontend/components/player.html)
            player_html_path = os.path.join("frontend", "components", "player.html")
            # 만약 실행 위치가 frontend 내부라면 components/player.html 일 수도 있음.
            # 안전하게 절대 경로 또는 상대 경로 확인
            if not os.path.exists(player_html_path):
                 player_html_path = os.path.join("components", "player.html")

            if os.path.exists(player_html_path):
                with open(player_html_path, "r", encoding="utf-8") as f:
                    player_html = f.read()
                
                # 사용자 ID와 API URL 추가
                user_id = st.session_state.user_info.get("user_id") if st.session_state.get("user_info") else ""
                api_url = API_URL
                
                player_html = player_html.replace("{{ACCESS_TOKEN}}", st.session_state.access_token)
                player_html = player_html.replace("{{INITIAL_TRACK_URI}}", selected_track.get("uri", ""))
                player_html = player_html.replace("{{USER_ID}}", str(user_id))
                player_html = player_html.replace("{{API_URL}}", api_url)
                
                components.html(player_html, height=400)
                
                st.write(f"**{selected_track.get('name', '알 수 없음')}**")
                st.write(f"👤 {selected_track.get('artists', '알 수 없음')}")
            else:
                st.warning(f"플레이어 파일을 찾을 수 없습니다: {player_html_path}")
        else:
            st.info("재생할 트랙을 선택하세요.")
            st.write("검색 결과에서 **▶ 재생** 버튼을 클릭하면 플레이어가 표시됩니다.")


def show_admin_home_page():
    """관리자(99) 홈 화면 - 유저 위험도 및 이탈률 통계"""
    st.markdown("## 📊 유저 위험도 및 이탈률 통계")
    
    try:
        # 전체 유저 예측 데이터 조회
        res = requests.get(f"{API_URL}/user_prediction")
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                predictions = data.get("rows", [])
                
                if predictions:
                    # 데이터프레임 생성
                    df = pd.DataFrame(predictions)
                    
                    # 통계 요약
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_users = len(df)
                        st.metric("전체 유저 수", f"{total_users}명")
                    with col2:
                        avg_churn = df['churn_rate'].mean() if 'churn_rate' in df.columns else 0
                        st.metric("평균 이탈률", f"{avg_churn:.1f}%")
                    with col3:
                        high_risk = len(df[df['risk_score'] == 'HIGH']) if 'risk_score' in df.columns else 0
                        st.metric("고위험 유저", f"{high_risk}명")
                    with col4:
                        medium_risk = len(df[df['risk_score'] == 'MEDIUM']) if 'risk_score' in df.columns else 0
                        st.metric("중위험 유저", f"{medium_risk}명")
                    
                    st.markdown("---")
                    
                    # 위험도 분포 차트 (한눈에 보이도록 3개 차트를 한 줄에)
                    col_chart1, col_chart2, col_chart3 = st.columns(3)
                    
                    with col_chart1:
                        st.markdown("#### 위험도 분포")
                        if 'risk_score' in df.columns:
                            risk_counts = df['risk_score'].value_counts()
                            
                            fig, ax = plt.subplots(figsize=(5, 4))
                            fig.patch.set_facecolor('none')
                            ax.set_facecolor('none')
                            
                            colors = {'LOW': '#2ecc71', 'MEDIUM': '#f39c12', 'HIGH': '#e74c3c', 'UNKNOWN': '#95a5a6'}
                            risk_labels = {'LOW': '낮음', 'MEDIUM': '중간', 'HIGH': '높음', 'UNKNOWN': '알 수 없음'}
                            
                            labels = [risk_labels.get(r, r) for r in risk_counts.index]
                            values = risk_counts.values
                            chart_colors = [colors.get(r, '#95a5a6') for r in risk_counts.index]
                            
                            # 텍스트 색상을 밝게 설정
                            ax.pie(values, labels=labels, autopct='%1.1f%%', colors=chart_colors, 
                                  startangle=90, textprops={'color': 'white', 'fontsize': 9})
                            ax.set_title('위험도 분포', fontsize=11, fontweight='bold', color='white')
                            plt.tight_layout(pad=0.5)
                            st.pyplot(fig, use_container_width=True)
                            plt.close()
                        else:
                            st.info("위험도 데이터가 없습니다.")
                    
                    with col_chart2:
                        st.markdown("#### 이탈률 분포")
                        if 'churn_rate' in df.columns:
                            fig, ax = plt.subplots(figsize=(5, 4))
                            fig.patch.set_facecolor('none')
                            ax.set_facecolor('none')
                            
                            # 이탈률 구간별 분류
                            bins = [0, 20, 40, 60, 80, 100]
                            labels_bin = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
                            df_temp = df.copy()
                            df_temp['churn_range'] = pd.cut(df_temp['churn_rate'], bins=bins, labels=labels_bin, include_lowest=True)
                            churn_counts = df_temp['churn_range'].value_counts().sort_index()
                            
                            ax.bar(churn_counts.index, churn_counts.values, color='#3498db')
                            ax.set_xlabel('이탈률 구간', fontsize=9, color='white')
                            ax.set_ylabel('유저 수', fontsize=9, color='white')
                            ax.set_title('이탈률 분포', fontsize=11, fontweight='bold', color='white')
                            ax.tick_params(axis='x', rotation=45, labelsize=8, colors='white')
                            ax.tick_params(axis='y', labelsize=8, colors='white')
                            ax.spines['bottom'].set_color('white')
                            ax.spines['top'].set_color('white')
                            ax.spines['left'].set_color('white')
                            ax.spines['right'].set_color('white')
                            plt.tight_layout(pad=0.5)
                            st.pyplot(fig, use_container_width=True)
                            plt.close()
                        else:
                            st.info("이탈률 데이터가 없습니다.")
                    
                    with col_chart3:
                        st.markdown("#### 위험도별 평균 이탈률")
                        if 'risk_score' in df.columns and 'churn_rate' in df.columns:
                            risk_labels = {'LOW': '낮음', 'MEDIUM': '중간', 'HIGH': '높음', 'UNKNOWN': '알 수 없음'}
                            risk_churn = df.groupby('risk_score')['churn_rate'].agg(['mean']).reset_index()
                            risk_churn.columns = ['위험도', '평균 이탈률']
                            risk_churn['위험도'] = risk_churn['위험도'].map(risk_labels).fillna(risk_churn['위험도'])
                            risk_churn['평균 이탈률'] = risk_churn['평균 이탈률'].round(2)
                            
                            fig, ax = plt.subplots(figsize=(5, 4))
                            fig.patch.set_facecolor('none')
                            ax.set_facecolor('none')
                            
                            colors_map = {'낮음': '#2ecc71', '중간': '#f39c12', '높음': '#e74c3c', '알 수 없음': '#95a5a6'}
                            bar_colors = [colors_map.get(r, '#95a5a6') for r in risk_churn['위험도']]
                            bars = ax.bar(risk_churn['위험도'], risk_churn['평균 이탈률'], color=bar_colors)
                            ax.set_xlabel('위험도', fontsize=9, color='white')
                            ax.set_ylabel('평균 이탈률 (%)', fontsize=9, color='white')
                            ax.set_title('위험도별 평균 이탈률', fontsize=11, fontweight='bold', color='white')
                            
                            # 값 표시
                            for bar in bars:
                                height = bar.get_height()
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                       f'{height:.1f}%',
                                       ha='center', va='bottom', fontsize=8, color='white')
                            
                            ax.tick_params(axis='x', labelsize=8, colors='white')
                            ax.tick_params(axis='y', labelsize=8, colors='white')
                            ax.spines['bottom'].set_color('white')
                            ax.spines['top'].set_color('white')
                            ax.spines['left'].set_color('white')
                            ax.spines['right'].set_color('white')
                            plt.tight_layout(pad=0.5)
                            st.pyplot(fig, use_container_width=True)
                            plt.close()
                        else:
                            st.info("데이터가 없습니다.")
                    
                    st.markdown("---")
                    
                    # 위험도별 상세 통계 테이블
                    if 'risk_score' in df.columns and 'churn_rate' in df.columns:
                        risk_labels = {'LOW': '낮음', 'MEDIUM': '중간', 'HIGH': '높음', 'UNKNOWN': '알 수 없음'}
                        risk_churn = df.groupby('risk_score')['churn_rate'].agg(['mean', 'count']).reset_index()
                        risk_churn.columns = ['위험도', '평균 이탈률', '유저 수']
                        risk_churn['위험도'] = risk_churn['위험도'].map(risk_labels).fillna(risk_churn['위험도'])
                        risk_churn['평균 이탈률'] = risk_churn['평균 이탈률'].round(2)
                        st.dataframe(risk_churn, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # 상세 데이터 테이블
                    st.subheader("유저별 상세 정보")
                    display_df = df.copy()
                    risk_labels = {'LOW': '낮음', 'MEDIUM': '중간', 'HIGH': '높음', 'UNKNOWN': '알 수 없음'}
                    
                    # 필요한 컬럼만 선택하고 이름 변경
                    if 'risk_score' in display_df.columns:
                        display_df['risk_score'] = display_df['risk_score'].map(risk_labels).fillna(display_df['risk_score'])
                    
                    # 컬럼 이름 매핑 (실제 컬럼에 맞게)
                    column_mapping = {}
                    if 'user_id' in display_df.columns:
                        column_mapping['user_id'] = '유저 ID'
                    if 'churn_rate' in display_df.columns:
                        column_mapping['churn_rate'] = '이탈률 (%)'
                    if 'risk_score' in display_df.columns:
                        column_mapping['risk_score'] = '위험도'
                    if 'update_date' in display_df.columns:
                        column_mapping['update_date'] = '업데이트 날짜'
                    
                    display_df = display_df.rename(columns=column_mapping)
                    
                    # 필요한 컬럼만 선택
                    display_columns = [col for col in ['유저 ID', '이탈률 (%)', '위험도', '업데이트 날짜'] if col in display_df.columns]
                    display_df = display_df[display_columns]
                    
                    st.dataframe(display_df, use_container_width=True, height=400)
                else:
                    st.info("예측 데이터가 없습니다. 먼저 이탈 예측을 실행해주세요.")
            else:
                st.error(f"데이터 조회 실패: {data.get('error', '알 수 없는 오류')}")
        else:
            if res.status_code == 404:
                st.info("user_prediction 테이블이 존재하지 않습니다. 먼저 테이블을 생성해주세요.")
            else:
                st.error(f"API 오류: {res.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# ----------------------------------------------------------
# 상단 배너
# ----------------------------------------------------------
def render_top_guide_banner(page_name="default"):
    """
    각 화면별 이용 가이드 배너를 표시합니다.
    
    Args:
        page_name: 화면 이름 ("home", "profile", "logs", "churn_single", "churn_bulk", 
                   "churn_6feat", "prediction_results", "prediction_csv", "user_admin", 
                   "user_search", "feature_b", "default")
    """
    guides = {
        "home": """
            <b style="font-size:17px;">🎵 홈 화면 이용 가이드</b><br>
            • Spotify 음악 검색 및 재생 기능을 사용할 수 있습니다.<br>
            • 검색어를 입력하고 원하는 트랙을 찾아 재생하세요.<br>
            • Spotify 인증이 필요합니다. 로그인 화면에서 인증을 완료해주세요.<br>
            • 재생할 트랙을 선택하면 플레이어가 자동으로 표시됩니다.
        """,
        "profile": """
            <b style="font-size:17px;">👤 개인정보 수정 이용 가이드</b><br>
            • 이름, 좋아하는 음악, 등급을 수정할 수 있습니다.<br>
            • 등급은 관리자(99)만 수정 가능합니다.<br>
            • 정보를 수정한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다.<br>
            • 구독해지를 하시면 휴면 유저(등급 00)로 전환되고 이탈 위험도가 높음으로 설정됩니다.<br>
            • 관리자는 구독해지 기능을 사용할 수 없습니다.
        """,
        "logs": """
            <b style="font-size:17px;">📋 로그 조회 이용 가이드</b><br>
            • 사용자 활동 로그를 조회할 수 있습니다. (관리자 전용)<br>
            • User ID로 특정 사용자의 로그만 필터링할 수 있습니다.<br>
            • 액션 타입(LOGIN, PAGE_VIEW, UNSUBSCRIBE)으로 필터링할 수 있습니다.<br>
            • 페이지 크기를 조정하여 한 번에 볼 로그 수를 설정할 수 있습니다.<br>
            • 로그는 최신순으로 정렬되어 표시됩니다.
        """,
        "churn_single": """
            <b style="font-size:17px;">📊 단일 유저 이탈 예측 이용 가이드</b><br>
            • User ID를 입력하고 '유저 데이터 불러오기' 버튼을 클릭하세요.<br>
            • user_features 테이블에서 해당 유저의 데이터를 자동으로 불러옵니다.<br>
            • 피처 값을 수정한 후 '예측 실행' 버튼을 클릭하면 이탈 확률과 위험도를 확인할 수 있습니다.<br>
            • 예측 결과는 자동으로 user_prediction 테이블에 저장됩니다.<br>
            • 이탈 확률은 0~100%로 표시되며, 위험도는 LOW/MEDIUM/HIGH로 표시됩니다.
        """,
        "churn_bulk": """
            <b style="font-size:17px;">📊 배치 이탈 예측 이용 가이드</b><br>
            • CSV 파일을 업로드하거나 수동으로 데이터를 입력할 수 있습니다.<br>
            • CSV 파일에는 user_id 컬럼이 포함되어야 하며, user_features 테이블에서 자동으로 조회됩니다.<br>
            • 여러 유저의 이탈 확률을 한 번에 예측할 수 있습니다.<br>
            • 예측 결과는 차트로 시각화되어 표시됩니다.<br>
            • 모든 예측 결과는 자동으로 user_prediction 테이블에 저장됩니다.
        """,
        "churn_6feat": """
            <b style="font-size:17px;">📊 6피처 이탈 예측 이용 가이드</b><br>
            • 6개의 핵심 피처만 사용하여 이탈 예측을 수행합니다.<br>
            • 필수 피처: app_crash_count_30d, skip_rate_increase_7d, days_since_last_login,<br>
            &nbsp;&nbsp;listening_time_trend_7d, freq_of_use_trend_14d, login_frequency_30d<br>
            • User ID를 입력하면 user_features 테이블에서 자동으로 데이터를 불러옵니다.<br>
            • 예측 결과는 user_prediction 테이블에 자동으로 저장됩니다.
        """,
        "prediction_results": """
            <b style="font-size:17px;">📈 예측 결과 조회 이용 가이드</b><br>
            • user_prediction 테이블에 저장된 예측 결과를 조회할 수 있습니다. (관리자 전용)<br>
            • User ID로 특정 사용자의 예측 결과를 검색할 수 있습니다.<br>
            • 위험도(LOW/MEDIUM/HIGH)로 필터링할 수 있습니다.<br>
            • 예측 결과는 테이블 형식으로 표시되며, 통계 정보도 함께 제공됩니다.
        """,
        "prediction_csv": """
            <b style="font-size:17px;">📁 예측 결과 CSV 관리 이용 가이드</b><br>
            • CSV 파일을 업로드하여 일괄 예측을 수행할 수 있습니다. (관리자 전용)<br>
            • 필수 컬럼: user_id, app_crash_count_30d, skip_rate_increase_7d, days_since_last_login,<br>
            &nbsp;&nbsp;listening_time_trend_7d, freq_of_use_trend_14d, login_frequency_30d<br>
            • 예측 결과를 CSV 파일로 다운로드할 수 있습니다.<br>
            • 예측 결과는 user_prediction 테이블에 자동으로 저장됩니다.
        """,
        "user_admin": """
            <b style="font-size:17px;">🛠 사용자 데이터 관리 이용 가이드</b><br>
            • 데이터베이스 테이블을 생성하고 CSV 데이터를 import할 수 있습니다. (관리자 전용)<br>
            • User Table, User Features Table, User Prediction Table, Log Table을 생성할 수 있습니다.<br>
            • CSV 파일을 업로드하여 user_features 테이블에 데이터를 삽입할 수 있습니다.<br>
            • 기본 경로의 CSV 파일(data/enhanced_data_not_clean_FE_delete.csv)을 사용할 수도 있습니다.
        """,
        "user_search": """
            <b style="font-size:17px;">🔍 사용자 조회 이용 가이드</b><br>
            • 이름, User ID, 좋아하는 음악, 등급으로 사용자를 검색할 수 있습니다. (관리자 전용)<br>
            • 각 사용자의 등급을 수정할 수 있습니다.<br>
            • 사용자의 위험도(이탈 위험도)를 확인할 수 있습니다.<br>
            • 페이징 기능을 사용하여 많은 사용자 데이터를 효율적으로 조회할 수 있습니다.
        """,
        "feature_b": """
            <b style="font-size:17px;">⚙️ 기능 B 이용 가이드</b><br>
            • 기능 B의 내용을 여기에 작성하세요.
        """,
        "achievements": """
            <b style="font-size:17px;">🏆 도전과제 이용 가이드</b><br>
            • 특정 노래나 장르의 노래를 일정 횟수 이상 들으면 도전과제를 달성할 수 있습니다.<br>
            • 노래를 재생하면 자동으로 재생 로그가 기록되고 도전과제 진행도가 업데이트됩니다.<br>
            • 도전과제를 완료하면 보상 포인트를 받을 수 있습니다.<br>
            • 완료된 도전과제와 진행 중인 도전과제를 확인할 수 있습니다.<br>
            • 완료된 도전과제를 칭호로 선택하여 사이드바에 표시할 수 있습니다.
        """,
        "achievements_admin": """
            <b style="font-size:17px;">🏆 도전과제 관리 이용 가이드</b><br>
            • 도전과제를 생성, 조회, 삭제할 수 있습니다. (관리자 전용)<br>
            • 도전과제 타입: GENRE_PLAY (장르별 재생), TRACK_PLAY (특정 노래 재생)<br>
            • 목표 값, 보상 포인트 등을 설정할 수 있습니다.<br>
            • 생성된 도전과제는 모든 사용자에게 적용됩니다.
        """,
        "default": """
            <b style="font-size:17px;">📘 이용 가이드</b><br>
            • 왼쪽 사이드바에서 원하는 기능을 선택하세요.<br>
            • 권한(grade)에 따라 접근 가능한 메뉴가 달라질 수 있습니다.<br>
            • 관리자(99)는 추가 관리 기능을 사용할 수 있습니다.<br>
            • 모든 페이지 상단에 이 안내가 항상 표시됩니다.
        """
    }
    
    guide_text = guides.get(page_name, guides["default"])
    
    st.markdown(
        f"""
        <div style="
            background-color: #1f2937;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            color: white;
            font-size: 16px;
            border-left: 5px solid #3b82f6;
        ">
            {guide_text}
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------------------------------------------------
# 개인정보 수정 함수
# ----------------------------------------------------------
def show_profile_page():
    """
    개인 정보 확인 및 수정 페이지
    """
    render_top_guide_banner("profile")
    # 화면 접근 로그 기록
    user = st.session_state.user_info
    user_id = user.get("user_id") if user else None
    if user_id:
        try:
            requests.post(f"{API_URL}/log", json={
                "user_id": user_id,
                "action_type": "PAGE_VIEW",
                "page_name": "개인정보 수정"
            })
        except:
            pass  # 로그 기록 실패해도 계속 진행

    # stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬을 위한 CSS
    st.markdown("""
    <style>
    /* stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 {
        padding-right: 0 !important;
        margin-right: 0 !important;
        justify-content: flex-end !important;
        display: flex !important;
        gap: 0.5rem !important;
    }
    
    /* stHorizontalBlock 내부 컬럼들의 불필요한 패딩 제거 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"] {
        padding-right: 0.25rem !important;
        padding-left: 0.25rem !important;
    }
    
    /* 빈 컬럼(첫 번째 컬럼)의 너비 최소화 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:first-child {
        flex-grow: 1;
        min-width: 0;
    }
    
    /* 버튼이 있는 컬럼은 자동 크기 조정 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:not(:first-child) {
        flex-shrink: 0;
    }
    
    /* 버튼 스타일 - 적절한 크기 */
    button[kind="primary"] {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    
    button:not([kind="primary"]) {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("👤 개인 정보 수정")

    user = st.session_state.user_info
    user_id = user.get("user_id")
    grade = user.get("grade")
    
    # ------------------------------
    # API에서 최신 사용자 정보 조회
    # test 계정(user_id 99, 1)인 경우 API 호출 건너뛰기
    # ------------------------------
    is_test_account = (user_id == 99 or user_id == 1)
    
    if is_test_account:
        # test 계정은 세션 정보만 사용
        current_name = user.get("name", "")
        current_fav_music = user.get("favorite_music", "")
        current_grade = user.get("grade", "")
        st.info("ℹ️ 테스트 계정입니다. 세션 정보를 사용합니다.")
    else:
        try:
            res = requests.get(f"{API_URL}/users/{user_id}")
            if res.status_code == 200:
                user_data = res.json()
                
                # 딕셔너리 형태로 반환되므로 직접 접근
                current_name = user_data.get("name", user.get("name", ""))
                current_fav_music = user_data.get("favorite_music", user.get("favorite_music", ""))
                current_grade = user_data.get("grade", user.get("grade", ""))
                
                # 세션 정보도 업데이트
                st.session_state.user_info["name"] = current_name
                st.session_state.user_info["favorite_music"] = current_fav_music
                st.session_state.user_info["grade"] = current_grade
                
                st.write("🔍 [LOG] API에서 최신 사용자 정보 조회 완료")
            else:
                # API 조회 실패 시 세션 정보 사용
                st.warning("⚠️ 최신 정보를 불러오지 못했습니다. 세션 정보를 사용합니다.")
                current_name = user.get("name", "")
                current_fav_music = user.get("favorite_music", "")
                current_grade = user.get("grade", "")
        except Exception as e:
            st.warning(f"⚠️ 사용자 정보 조회 중 오류 발생: {e}. 세션 정보를 사용합니다.")
            current_name = user.get("name", "")
            current_fav_music = user.get("favorite_music", "")
            current_grade = user.get("grade", "")

    # ------------------------------
    # 임시 입력값 저장용 세션 상태 초기화
    # ------------------------------
    if f"temp_profile_{user_id}_name" not in st.session_state:
        st.session_state[f"temp_profile_{user_id}_name"] = current_name
    if f"temp_profile_{user_id}_music" not in st.session_state:
        st.session_state[f"temp_profile_{user_id}_music"] = current_fav_music
    if f"temp_profile_{user_id}_grade" not in st.session_state:
        st.session_state[f"temp_profile_{user_id}_grade"] = current_grade

    # ------------------------------
    # 입력 폼
    # ------------------------------
    st.markdown("### 📝 정보 수정")
    st.info("💡 정보를 수정한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다.")
    
    # 이름 입력 (임시 세션 상태 사용)
    temp_name = st.text_input(
        "이름", 
        value=st.session_state[f"temp_profile_{user_id}_name"], 
        key=f"profile_name_{user_id}"
    )
    st.session_state[f"temp_profile_{user_id}_name"] = temp_name
    
    # 좋아하는 음악 selectbox (임시 세션 상태 사용)
    music_categories = get_music_categories()
    temp_music_value = st.session_state[f"temp_profile_{user_id}_music"]
    
    # 빈 값 포함 옵션 리스트 생성
    music_categories_with_empty = [""] + music_categories
    
    # selectbox의 key를 통해 세션 상태에서 현재 값을 가져오거나, 없으면 temp_music_value 사용
    selectbox_key = f"profile_music_select_{user_id}"
    if selectbox_key not in st.session_state:
        # 세션 상태에 없으면 temp_music_value를 사용하여 인덱스 계산
        if temp_music_value and temp_music_value in music_categories_with_empty:
            current_music_index = music_categories_with_empty.index(temp_music_value)
        else:
            current_music_index = 0
    else:
        # 세션 상태에 값이 있으면 해당 값의 인덱스 사용
        current_value = st.session_state[selectbox_key]
        if current_value in music_categories_with_empty:
            current_music_index = music_categories_with_empty.index(current_value)
        else:
            current_music_index = 0
    
    selected_music = st.selectbox(
        "좋아하는 음악",
        options=music_categories_with_empty,
        index=current_music_index,
        key=selectbox_key,
        help="음악 장르를 선택한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다."
    )
    # 버튼 클릭 시에만 세션 상태 업데이트하도록 주석 처리
    # st.session_state[f"temp_profile_{user_id}_music"] = selected_music

    # grade 옵션 정의 (key: value 형태)
    grade_options = {
        "01": "일반회원",
        "99": "관리자"
    }
    
    # grade 수정은 관리자만 가능 (99가 아니면 disabled)
    if grade == "99":
        # 관리자는 select box로 선택 가능
        grade_display_options = [f"{k}: {v}" for k, v in grade_options.items()]
        temp_grade = st.session_state[f"temp_profile_{user_id}_grade"]
        
        # selectbox의 key를 통해 세션 상태에서 현재 값을 가져오거나, 없으면 temp_grade 사용
        selectbox_key = f"profile_grade_select_{user_id}"
        if selectbox_key not in st.session_state:
            # 세션 상태에 없으면 temp_grade를 사용하여 인덱스 계산
            current_grade_display = f"{temp_grade}: {grade_options.get(temp_grade, '')}"
            if current_grade_display in grade_display_options:
                current_grade_index = grade_display_options.index(current_grade_display)
            else:
                current_grade_index = 0
        else:
            # 세션 상태에 값이 있으면 해당 값의 인덱스 사용
            current_value = st.session_state[selectbox_key]
            if current_value in grade_display_options:
                current_grade_index = grade_display_options.index(current_value)
            else:
                current_grade_index = 0
        
        # selectbox의 key를 고정하여 값 변경 시 자동 업데이트 방지
        # 버튼 클릭 시에만 값을 읽도록 처리
        selected_grade_display = st.selectbox(
            "등급",
            options=grade_display_options,
            index=current_grade_index,
            key=selectbox_key,
            help="등급을 선택한 후 '저장' 버튼을 클릭해야 변경사항이 적용됩니다."
        )
        # 선택된 값에서 key 추출 (예: "01: 일반회원" -> "01")
        # 버튼 클릭 시에만 세션 상태 업데이트하도록 주석 처리
        # temp_grade_value = selected_grade_display.split(":")[0].strip()
        # st.session_state[f"temp_profile_{user_id}_grade"] = temp_grade_value
    else:
        # 일반 사용자는 disabled select box
        grade_display_options = [f"{k}: {v}" for k, v in grade_options.items()]
        temp_grade = st.session_state[f"temp_profile_{user_id}_grade"]
        
        # selectbox의 key를 통해 세션 상태에서 현재 값을 가져오거나, 없으면 temp_grade 사용
        selectbox_key = f"profile_grade_disabled_{user_id}"
        if selectbox_key not in st.session_state:
            # 세션 상태에 없으면 temp_grade를 사용하여 인덱스 계산
            current_grade_display = f"{temp_grade}: {grade_options.get(temp_grade, '')}"
            if current_grade_display in grade_display_options:
                current_grade_index = grade_display_options.index(current_grade_display)
            else:
                current_grade_index = 0
        else:
            # 세션 상태에 값이 있으면 해당 값의 인덱스 사용
            current_value = st.session_state[selectbox_key]
            if current_value in grade_display_options:
                current_grade_index = grade_display_options.index(current_value)
            else:
                current_grade_index = 0
        
        selected_grade_display = st.selectbox(
            "등급",
            options=grade_display_options,
            index=current_grade_index,
            disabled=True,
            help="등급은 관리자(99)만 수정할 수 있습니다.",
            key=selectbox_key
        )
        st.info("ℹ️ 등급은 관리자만 수정할 수 있습니다.")

    # 현재 정보 표시
    with st.expander("📋 현재 정보 확인", expanded=False):
        grade_display_name = grade_options.get(current_grade, current_grade)
        st.write(f"**사용자 ID:** {user_id}")
        st.write(f"**이름:** {current_name}")
        st.write(f"**좋아하는 음악:** {current_fav_music if current_fav_music else '(없음)'}")
        st.write(f"**등급:** {current_grade} ({grade_display_name})")

    # ------------------------------
    # 구독해지 섹션 (등급 99는 제외)
    # ------------------------------
    if grade != "99":  # 관리자는 구독해지 불가
        st.markdown("---")
        st.markdown("### 🚪 구독해지")
        st.warning("⚠️ 구독해지를 하시면 이탈 위험도가 높음으로 설정됩니다.")
        
        # 구독해지 모달 상태 관리
        if f"unsubscribe_modal_{user_id}" not in st.session_state:
            st.session_state[f"unsubscribe_modal_{user_id}"] = False
        
        unsubscribe_button = st.button("구독해지", type="secondary", key=f"unsubscribe_button_{user_id}")
        
        if unsubscribe_button:
            st.session_state[f"unsubscribe_modal_{user_id}"] = True
        
            # 구독해지 모달 표시
            if st.session_state[f"unsubscribe_modal_{user_id}"]:
                with st.container():
                    st.markdown("---")
                    st.markdown("### 📝 구독해지 양식")
                    st.info("구독해지를 진행하시겠습니까? 이탈 위험도가 높음으로 설정됩니다.")
                    
                    reason = st.selectbox(
                        "구독해지 사유",
                        ["", "서비스 불만", "가격 문제", "사용 빈도 감소", "다른 서비스 이용", "기타"],
                        key=f"unsubscribe_reason_{user_id}"
                    )
                    
                    feedback = st.text_area(
                        "의견 및 피드백 (선택사항)",
                        placeholder="서비스 개선을 위한 의견을 남겨주세요.",
                        key=f"unsubscribe_feedback_{user_id}"
                    )
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        pass
                    with col2:
                        confirm_button = st.button("확인", type="primary", key=f"unsubscribe_confirm_{user_id}")
                    with col3:
                        cancel_button = st.button("취소", key=f"unsubscribe_cancel_{user_id}")
                    
                    if cancel_button:
                        st.session_state[f"unsubscribe_modal_{user_id}"] = False
                        st.rerun()
                    
                    if confirm_button:
                        try:
                            with st.spinner("구독해지 처리 중..."):
                                payload = {
                                    "user_id": user_id,
                                    "reason": reason,
                                    "feedback": feedback
                                }
                                res = requests.post(f"{API_URL}/unsubscribe", json=payload)
                                
                                if res.status_code == 200:
                                    result = res.json()
                                    if result.get("success"):
                                        st.success("✅ 구독해지가 처리되었습니다. 휴면 유저로 전환되었고 이탈 위험도가 높음으로 설정되었습니다.")
                                        st.session_state[f"unsubscribe_modal_{user_id}"] = False
                                        # 세션 정보 업데이트 (등급을 00으로 변경)
                                        st.session_state.user_info["grade"] = "00"
                                        st.rerun()
                                    else:
                                        st.error(result.get("error", "구독해지 처리 실패"))
                                else:
                                    st.error(f"구독해지 처리 중 오류 발생: {res.status_code}")
                        except Exception as e:
                            st.error(f"오류 발생: {str(e)}")

    # ------------------------------
    # 저장 버튼 (버튼 클릭 시에만 실제 저장, 우측 정렬, 동일선상에 가로 배치, 적당한 간격)
    # ------------------------------
    st.markdown("---")
    btn_col1, btn_col2, btn_col3 = st.columns([4, 1.1, 1.1])
    with btn_col1:
        pass  # 빈 공간
    with btn_col2:
        save_button = st.button("💾 저장", type="primary", key=f"save_button_{user_id}")
    with btn_col3:
        reset_button = st.button("🔄 초기화", key=f"reset_button_{user_id}")
    
    if reset_button:
            # 임시 세션 상태를 현재 DB 값으로 초기화
            st.session_state[f"temp_profile_{user_id}_name"] = current_name
            st.session_state[f"temp_profile_{user_id}_music"] = current_fav_music
            st.session_state[f"temp_profile_{user_id}_grade"] = current_grade
            
            # selectbox 값도 초기화 (rerun 후 자동으로 반영됨)
            # 하지만 명시적으로 초기화하려면 key를 삭제하거나 재설정
            if f"profile_music_select_{user_id}" in st.session_state:
                del st.session_state[f"profile_music_select_{user_id}"]
            if f"profile_grade_select_{user_id}" in st.session_state:
                del st.session_state[f"profile_grade_select_{user_id}"]
            if f"profile_grade_disabled_{user_id}" in st.session_state:
                del st.session_state[f"profile_grade_disabled_{user_id}"]
            
            st.success("입력값이 초기화되었습니다.")
            st.rerun()
    
    if save_button:
        # 임시 세션 상태에서 값 가져오기
        new_name = st.session_state[f"temp_profile_{user_id}_name"]
        
        # selectbox에서 현재 선택된 값을 읽어서 세션 상태에 저장
        # 좋아하는 음악 selectbox 값 읽기
        selected_music = st.session_state.get(f"profile_music_select_{user_id}", "")
        new_music = selected_music if selected_music else ""
        
        # grade selectbox 값 읽기
        if grade == "99":
            # selectbox의 key로 저장된 현재 값을 읽어옴
            # Streamlit은 selectbox의 값을 자동으로 session_state에 저장함
            selected_grade_display = st.session_state.get(f"profile_grade_select_{user_id}", f"{current_grade}: {grade_options.get(current_grade, '')}")
            new_grade = selected_grade_display.split(":")[0].strip()
        else:
            new_grade = st.session_state[f"temp_profile_{user_id}_grade"]
        
        # 세션 상태 업데이트 (버튼 클릭 시에만)
        st.session_state[f"temp_profile_{user_id}_music"] = new_music
        st.session_state[f"temp_profile_{user_id}_grade"] = new_grade
        
        # 입력값 검증
        if not new_name.strip():
            st.error("이름은 필수 입력 항목입니다.")
            return

        # grade 값 검증 (01 또는 99만 허용)
        if new_grade not in grade_options:
            st.error(f"등급은 {', '.join(grade_options.keys())} 중 하나만 선택 가능합니다.")
            return

        # 변경사항 확인
        has_changes = (
            new_name.strip() != current_name or
            new_music.strip() != (current_fav_music or "") or
            new_grade != current_grade
        )
        
        if not has_changes:
            st.info("변경된 내용이 없습니다.")
            return

        # test 계정인 경우 API 호출 없이 세션 정보만 업데이트
        if is_test_account:
            st.info("ℹ️ 테스트 계정입니다. 세션 정보만 업데이트됩니다. (DB에는 저장되지 않습니다.)")
            
            # 세션 정보 업데이트
            st.session_state.user_info["name"] = new_name.strip()
            st.session_state.user_info["favorite_music"] = new_music.strip() if new_music else ""
            st.session_state.user_info["grade"] = new_grade
            
            # 임시 세션 상태도 업데이트 (최신 값으로 동기화)
            st.session_state[f"temp_profile_{user_id}_name"] = new_name.strip()
            st.session_state[f"temp_profile_{user_id}_music"] = new_music.strip() if new_music else ""
            st.session_state[f"temp_profile_{user_id}_grade"] = new_grade
            
            st.success("✅ 테스트 계정 정보가 업데이트되었습니다.")
            st.rerun()
        else:
            payload = {
                "user_id": user_id,
                "name": new_name.strip(),
                "favorite_music": new_music.strip() if new_music else "",
                "grade": new_grade,
            }

            st.write("🔍 [LOG] 수정 요청 데이터:", payload)
            
            with st.spinner("정보를 저장하는 중..."):
                ok, res = call_api_post("update_user_data", payload)

            if ok and res.get("success"):
                st.success("✅ 정보가 성공적으로 수정되었습니다.")

                # 세션 정보 업데이트
                st.session_state.user_info["name"] = payload["name"]
                st.session_state.user_info["favorite_music"] = payload["favorite_music"]
                st.session_state.user_info["grade"] = payload["grade"]
                
                # 임시 세션 상태도 업데이트 (최신 값으로 동기화)
                st.session_state[f"temp_profile_{user_id}_name"] = payload["name"]
                st.session_state[f"temp_profile_{user_id}_music"] = payload["favorite_music"]
                st.session_state[f"temp_profile_{user_id}_grade"] = payload["grade"]

                st.rerun()
            else:
                error_msg = res.get("error", "알 수 없는 오류가 발생했습니다.")
                st.error(f"❌ 수정 실패: {error_msg}")
                st.write("🔍 [LOG] API 응답:", res)

# ----------------------------------------------------------
# 사용자 조회 함수
# ----------------------------------------------------------
def search_user():
    render_top_guide_banner("user_search")
    st.subheader("🔍 사용자 조회")
    
    # FHD 화면에 맞는 CSS 스타일 추가
    st.markdown("""
    <style>
    /* 사용자 조회 페이지 최대 너비 확장 */
    div[data-testid="stVerticalBlock"] {
        max-width: 100%;
    }
    
    /* 필터 컬럼 간격 조정 */
    div[data-testid="column"] {
        padding: 0.25rem;
    }
    
    /* 입력 필드 너비 최적화 */
    div[data-testid="stTextInput"] {
        width: 100%;
    }
    
    div[data-testid="stSelectbox"] {
        width: 100%;
    }
    
    /* stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 {
        padding-right: 0 !important;
        margin-right: 0 !important;
        justify-content: flex-end !important;
        display: flex !important;
        gap: 0.5rem !important;
    }
    
    /* stHorizontalBlock 내부 컬럼들의 불필요한 패딩 제거 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"] {
        padding-right: 0.25rem !important;
        padding-left: 0.25rem !important;
    }
    
    /* 빈 컬럼(첫 번째 컬럼)의 너비 최소화 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:first-child {
        flex-grow: 1;
        min-width: 0;
    }
    
    /* 버튼이 있는 컬럼은 자동 크기 조정 */
    .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:not(:first-child) {
        flex-shrink: 0;
    }
    
    /* 버튼 스타일 - 적절한 크기 */
    button[kind="primary"] {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    
    button:not([kind="primary"]) {
        min-height: 2.5rem;
        font-size: 1rem;
        padding: 0.5rem 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # 조회 필드 UI - 한 줄에 나열하여 보기 좋게 정리 (FHD 기준으로 더 넓게)
    st.markdown("### 조회 조건")
    
    # 필터 필드들을 한 줄에 나열 (FHD 화면에 맞게 비율 조정)
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([2.5, 2.5, 2.5, 2.5, 1.5])
    
    with filter_col1:
        search_name = st.text_input("이름 조회", placeholder="이름을 입력하세요")
    with filter_col2:
        search_user_id = st.text_input("User ID", placeholder="사용자 ID를 입력하세요")
    with filter_col3:
        # 좋아하는 음악을 selectbox로 변경
        music_categories = get_music_categories()
        music_filter_options = ["전체"] + music_categories
        selected_music_filter = st.selectbox("좋아하는 음악", options=music_filter_options, key="search_music_filter")
        if selected_music_filter == "전체":
            search_music = ""
        else:
            search_music = selected_music_filter
    with filter_col4:
        # 등급을 selectbox로 변경
        grade_filter_options = ["전체", "01: 일반회원", "99: 관리자", "00: 휴면"]
        selected_grade_filter = st.selectbox("등급", options=grade_filter_options, key="search_grade_filter")
        if selected_grade_filter == "전체":
            search_grade = ""
        else:
            search_grade = selected_grade_filter.split(":")[0].strip()
    with filter_col5:
        page_size = st.selectbox("페이지 크기", [10, 20, 30, 50], index=1)

    # 페이지 상태 및 조회 실행 여부 관리
    if "user_page" not in st.session_state:
        st.session_state.user_page = 1
    if "search_executed" not in st.session_state:
        st.session_state.search_executed = False
    if "search_params" not in st.session_state:
        st.session_state.search_params = {}

    page = st.session_state.user_page

    # 조회 버튼 (우측 정렬)
    st.markdown("---")
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        pass  # 빈 공간
    with col_btn2:
        search_button = st.button("🔍 조회 실행", type="primary")
    
    if search_button:
        # 조회 실행 시 세션 상태 업데이트
        st.session_state.user_page = 1  # 첫 페이지로 리셋
        st.session_state.search_executed = True
        st.session_state.search_params = {
            "name": search_name,
            "user_id": search_user_id,
            "favorite_music": search_music,
            "grade": search_grade,
            "page_size": page_size
        }
        st.rerun()

    # 조회가 실행되지 않았으면 조회 결과를 표시하지 않음
    if not st.session_state.search_executed:
        st.info("💡 조회 조건을 입력한 후 '조회 실행' 버튼을 클릭하세요.")
        return

    # 저장된 조회 파라미터 사용 (버튼 클릭 시에만 업데이트)
    saved_params = st.session_state.search_params
    current_search_name = saved_params.get("name", "")
    current_search_user_id = saved_params.get("user_id", "")
    current_search_music = saved_params.get("favorite_music", "")
    current_search_grade = saved_params.get("grade", "")
    current_page_size = saved_params.get("page_size", page_size)

    # API 요청 URL 구성
    api_url = (
        f"users_search?page={page}&page_size={current_page_size}"
        f"&name={current_search_name}"
        f"&user_id={current_search_user_id}"
        f"&favorite_music={current_search_music}"
        f"&grade={current_search_grade}"
    )

    ok, res = call_api(api_url)

    if not ok or not res.get("success"):
        st.error("조회 중 오류가 발생하였습니다.")
        st.write(res)
        return

    rows = res["rows"]
    total_rows = res["total_rows"]
    total_pages = res["total_pages"]

    st.write(f"총 {total_rows}명, 페이지 {page}/{total_pages}")

    # 테이블 표시 및 grade 수정 기능
    if rows:
        st.markdown("### 사용자 목록 및 등급 수정")
        st.info("💡 각 사용자의 등급을 선택한 후 '저장' 버튼을 클릭하여 수정할 수 있습니다.")
        
        # grade 옵션 정의
        grade_options = {
            "01": "일반회원",
            "99": "관리자",
            "00": "휴면"
        }
        grade_display_options = [f"{k}: {v}" for k, v in grade_options.items()]
        
        # 위험도 표시 옵션
        risk_score_colors = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴",
            "UNKNOWN": "⚪"
        }
        
        # 각 row의 실제 값 길이를 모두 고려하여 컬럼 비율 동적 계산
        # 모든 row의 각 컬럼 값 길이를 수집
        user_id_lengths = [len(str(row.get('user_id', ''))) for row in rows]
        name_lengths = [len(str(row.get('name', ''))) for row in rows]
        music_lengths = [len(str(row.get('favorite_music', '') or '(없음)')) for row in rows]
        date_lengths = [len(str(row.get('join_date', ''))) for row in rows]
        
        # 최대값과 평균값을 모두 고려 (최대값이 너무 크면 평균값도 고려)
        max_user_id_len = max(user_id_lengths, default=5)
        avg_user_id_len = sum(user_id_lengths) / len(user_id_lengths) if user_id_lengths else 5
        
        max_name_len = max(name_lengths, default=10)
        avg_name_len = sum(name_lengths) / len(name_lengths) if name_lengths else 10
        
        max_music_len = max(music_lengths, default=15)
        avg_music_len = sum(music_lengths) / len(music_lengths) if music_lengths else 15
        
        max_date_len = max(date_lengths, default=10)
        avg_date_len = sum(date_lengths) / len(date_lengths) if date_lengths else 10
        
        # 헤더 텍스트 길이도 고려
        header_id_len = len("ID")
        header_name_len = len("이름")
        header_music_len = len("좋아하는 음악")
        header_date_len = len("가입일")
        header_grade_len = len("등급")
        header_action_len = len("작업")
        
        # 각 컬럼의 최대 길이 계산 (헤더, 최대값, 평균값의 가중 평균)
        # 최대값에 70%, 평균값에 20%, 헤더에 10% 가중치 부여
        col_id_max = max(max_user_id_len, header_id_len) * 0.7 + avg_user_id_len * 0.2 + header_id_len * 0.1
        col_name_max = max(max_name_len, header_name_len) * 0.7 + avg_name_len * 0.2 + header_name_len * 0.1
        col_music_max = max(max_music_len, header_music_len) * 0.7 + avg_music_len * 0.2 + header_music_len * 0.1
        col_date_max = max(max_date_len, header_date_len) * 0.7 + avg_date_len * 0.2 + header_date_len * 0.1
        col_grade_max = max(len("99: 관리자"), header_grade_len)  # grade dropdown 최대 길이
        col_action_max = max(len("💾 저장"), header_action_len)  # 버튼 텍스트 길이
        
        # 컬럼 비율 조정 (길이에 비례하되 최소/최대값 제한)
        # FHD 화면 기준으로 더 넓은 비율 사용
        base_ratio = 1.5  # 기본 비율 증가
        id_ratio = max(1.5, min(3.5, col_id_max / 3 + base_ratio))
        name_ratio = max(3.0, min(8.0, col_name_max / 4 + base_ratio * 2))
        music_ratio = max(3.0, min(8.0, col_music_max / 4 + base_ratio * 2))
        date_ratio = max(2.5, min(5.0, col_date_max / 6 + base_ratio * 1.5))
        grade_ratio = max(3.0, min(5.0, col_grade_max / 5 + base_ratio * 1.8))
        action_ratio = max(2.5, min(4.5, col_action_max / 4 + base_ratio * 1.5))
        
        col_ratios = [id_ratio, name_ratio, music_ratio, date_ratio, grade_ratio, action_ratio]
        
        # CSS 스타일 추가로 텍스트 줄바꿈 및 컬럼 너비 최적화 (FHD 기준)
        st.markdown("""
        <style>
        /* 메인 컨테이너 최대 너비 확장 */
        .main .block-container {
            max-width: 95%;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        
        /* 컬럼 너비 최적화 */
        .user-table-container {
            overflow-x: auto;
            width: 100%;
        }
        
        .user-table-container div[data-testid="column"] {
            word-wrap: break-word;
            word-break: break-word;
            overflow-wrap: break-word;
            min-width: fit-content;
        }
        
        /* 테이블 행 스타일 개선 */
        div[data-testid="column"] {
            padding: 0.5rem;
        }
        
        /* selectbox 너비 최적화 */
        div[data-testid="stSelectbox"] {
            width: 100%;
        }
        
        /* stHorizontalBlock 클래스의 우측 여백 제거 및 버튼 우측 정렬 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 {
            padding-right: 0 !important;
            margin-right: 0 !important;
            justify-content: flex-end !important;
            display: flex !important;
            gap: 0.5rem !important;
        }
        
        /* stHorizontalBlock 내부 컬럼들의 불필요한 패딩 제거 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"] {
            padding-right: 0.25rem !important;
            padding-left: 0.25rem !important;
        }
        
        /* 빈 컬럼(첫 번째 컬럼)의 너비 최소화 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:first-child {
            flex-grow: 1;
            min-width: 0;
        }
        
        /* 버튼이 있는 컬럼은 자동 크기 조정 */
        .stHorizontalBlock.st-emotion-cache-1permvm.e196pkbe2 > div[data-testid="column"]:not(:first-child) {
            flex-shrink: 0;
        }
        
        /* 버튼 스타일 - 적절한 크기로 조정 및 우측 정렬 */
        .button-container {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
            align-items: center;
        }
        
        button[kind="primary"] {
            min-height: 2.5rem;
            font-size: 1rem;
            padding: 0.5rem 1.5rem;
        }
        
        button:not([kind="primary"]) {
            min-height: 2.5rem;
            font-size: 1rem;
            padding: 0.5rem 1.5rem;
        }
        
        /* 버튼 호버 효과 */
        button:hover {
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 헤더 행 (위험도 추가)
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7 = st.columns(col_ratios + [2.0])
        with header_col1:
            st.markdown("**ID**")
        with header_col2:
            st.markdown("**이름**")
        with header_col3:
            st.markdown("**좋아하는 음악**")
        with header_col4:
            st.markdown("**가입일**")
        with header_col5:
            st.markdown("**등급**")
        with header_col6:
            st.markdown("**위험도**")
        with header_col7:
            st.markdown("**작업**")
        
        st.markdown("---")
        
        # 각 row에 대해 수정 가능한 UI 생성
        for idx, row in enumerate(rows):
            with st.container():
                col1, col2, col3, col4, col5, col6, col7 = st.columns(col_ratios + [2.0])
                
                with col1:
                    st.write(f"**{row['user_id']}**")
                
                with col2:
                    # 텍스트가 잘리지 않도록 처리 (줄바꿈 허용)
                    name_text = str(row.get('name', ''))
                    if len(name_text) > 20:
                        # 긴 이름은 줄바꿈 표시
                        st.markdown(f"<div style='word-wrap: break-word;'>{name_text}</div>", unsafe_allow_html=True)
                    else:
                        st.write(name_text)
                
                with col3:
                    # 텍스트가 잘리지 않도록 처리 (줄바꿈 허용)
                    music_text = str(row.get('favorite_music', '') or '(없음)')
                    if len(music_text) > 20:
                        # 긴 음악명은 줄바꿈 표시
                        st.markdown(f"<div style='word-wrap: break-word;'>{music_text}</div>", unsafe_allow_html=True)
                    else:
                        st.write(music_text)
                
                with col4:
                    join_date = row.get('join_date', '')
                    if join_date:
                        st.write(str(join_date))
                    else:
                        st.write("")
                
                with col5:
                    # 현재 grade에 맞는 인덱스 찾기
                    current_grade = row.get('grade', '01')
                    current_grade_index = 0
                    for i, (k, v) in enumerate(grade_options.items()):
                        if k == current_grade:
                            current_grade_index = i
                            break
                    
                    # grade dropdown (수정용) - 현재 값이 이미 매핑되어 있음
                    selected_grade_display = st.selectbox(
                        "등급",
                        options=grade_display_options,
                        index=current_grade_index,
                        key=f"user_grade_select_{row['user_id']}_{page}",
                        label_visibility="collapsed"
                    )
                    selected_grade = selected_grade_display.split(":")[0].strip()
                
                with col6:
                    # 위험도 표시
                    risk_score = row.get('risk_score', 'UNKNOWN')
                    risk_color = risk_score_colors.get(risk_score, '⚪')
                    churn_rate = row.get('churn_rate', 0)
                    if risk_score == 'UNKNOWN':
                        st.write(f"{risk_color} {risk_score}")
                    else:
                        st.write(f"{risk_color} {risk_score} ({churn_rate}%)")
                
                with col7:
                    # 저장 버튼 (적절한 크기로 조정)
                    if st.button("💾 저장", key=f"save_grade_{row['user_id']}_{page}", type="primary"):
                        # grade가 변경되었는지 확인
                        if selected_grade != current_grade:
                            # API 호출하여 grade 수정
                            payload = {
                                "user_id": row['user_id'],
                                "name": row['name'],
                                "favorite_music": row.get('favorite_music', ''),
                                "grade": selected_grade
                            }
                            
                            with st.spinner(f"사용자 {row['user_id']}의 등급을 수정하는 중..."):
                                ok, res = call_api_post("update_user_data", payload)
                            
                            if ok and res.get("success"):
                                st.success(f"✅ 사용자 {row['name']} (ID: {row['user_id']})의 등급이 '{selected_grade}'로 변경되었습니다.")
                                st.rerun()
                            else:
                                error_msg = res.get("error", "알 수 없는 오류가 발생했습니다.")
                                st.error(f"❌ 수정 실패: {error_msg}")
                        else:
                            st.info("변경된 내용이 없습니다.")
                
                if idx < len(rows) - 1:  # 마지막 행이 아니면 구분선 표시
                    st.markdown("---")
        
        # 기존 테이블 형식도 유지 (참고용)
        with st.expander("📋 테이블 형식 보기", expanded=False):
            df = pd.DataFrame(rows)
            desired_order = ["user_id", "name", "favorite_music", "join_date", "grade"]
            df = df[desired_order]
            st.table(df)
    else:
        st.info("조회 결과가 없습니다.")
        return

    # 페이징 버튼 UI
    colA, colB, colC = st.columns(3)

    with colA:
        if st.button("⬅ 이전 페이지"):
            if page > 1:
                st.session_state.user_page -= 1
                st.rerun()

    with colB:
        st.write(f"현재 페이지: {page}")

    with colC:
        if st.button("다음 페이지 ➡"):
            if page < total_pages:
                st.session_state.user_page += 1
                st.rerun()

def show_feature_b():
    render_top_guide_banner("feature_b")
    st.subheader("기능 B")
    st.write("기능 B의 내용을 여기에 작성하세요.")


# ----------------------------------------------------------
# 도전과제 페이지 함수
# ----------------------------------------------------------
def show_achievements_admin_page():
    """도전과제 관리 페이지 (관리자용)"""
    render_top_guide_banner("achievements_admin")
    st.header("🏆 도전과제 관리")
    st.write("도전과제를 생성, 수정, 삭제할 수 있습니다.")
    st.markdown("---")
    
    user = st.session_state.user_info
    user_id = user.get("user_id") if user else None
    grade = user.get("grade") if user else None
    
    if grade != "99":
        st.error("관리자만 접근 가능한 페이지입니다.")
        return
    
    tab1, tab2 = st.tabs(["도전과제 목록", "새 도전과제 생성"])
    
    with tab1:
        st.subheader("📋 도전과제 목록")
        try:
            res = requests.get(f"{API_URL}/achievements")
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    achievements = data.get("achievements", [])
                    
                    if achievements:
                        for achievement in achievements:
                            achievement_id = achievement.get('achievement_id')
                            
                            # 도전과제 통계 조회
                            statistics = None
                            try:
                                res_stats = requests.get(f"{API_URL}/achievements/{achievement_id}/statistics")
                                if res_stats.status_code == 200:
                                    stats_data = res_stats.json()
                                    if stats_data.get("success"):
                                        statistics = stats_data
                            except:
                                pass
                            
                            with st.container(border=True):
                                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                                with col1:
                                    st.markdown(f"### {achievement.get('title', '')}")
                                    st.write(achievement.get('description', ''))
                                    st.caption(f"타입: {achievement.get('achievement_type', '')} | 목표: {achievement.get('target_value', 0)} | 보상: {achievement.get('reward_points', 0)} 포인트")
                                    if achievement.get('target_genre'):
                                        st.caption(f"목표 장르: {achievement.get('target_genre')}")
                                    if achievement.get('target_track_uri'):
                                        st.caption(f"목표 트랙: {achievement.get('target_track_uri')}")
                                    status = "활성" if achievement.get('is_active') else "비활성"
                                    st.caption(f"상태: {status}")
                                    
                                    # 달성 통계 표시
                                    if statistics:
                                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                                        with col_stat1:
                                            st.metric("달성자", f"{statistics.get('completed_count', 0)}명")
                                        with col_stat2:
                                            st.metric("진행 중", f"{statistics.get('in_progress_count', 0)}명")
                                        with col_stat3:
                                            st.metric("달성률", f"{statistics.get('completion_rate', 0)}%")
                                        
                                        # 달성한 유저 목록 (expander)
                                        if statistics.get('completed_count', 0) > 0:
                                            with st.expander(f"달성한 유저 목록 ({statistics.get('completed_count', 0)}명)", expanded=False):
                                                completed_users = statistics.get('completed_users', [])
                                                if completed_users:
                                                    for user in completed_users:
                                                        completed_at = user.get('completed_at', '')
                                                        if completed_at:
                                                            completed_at = completed_at[:10]  # 날짜만 표시
                                                        st.write(f"• {user.get('name', '')} (ID: {user.get('user_id', '')}) - {completed_at}")
                                                else:
                                                    st.info("달성한 유저가 없습니다.")
                                with col2:
                                    if achievement.get('is_active'):
                                        st.success("활성")
                                    else:
                                        st.info("비활성")
                                with col3:
                                    if st.button("통계 보기", key=f"view_stats_{achievement_id}", use_container_width=True):
                                        # 통계 상세 보기
                                        if statistics:
                                            st.info(f"**{achievement.get('title', '')} 통계**")
                                            st.write(f"전체 사용자: {statistics.get('total_users', 0)}명")
                                            st.write(f"달성자: {statistics.get('completed_count', 0)}명")
                                            st.write(f"진행 중: {statistics.get('in_progress_count', 0)}명")
                                            st.write(f"달성률: {statistics.get('completion_rate', 0)}%")
                                with col4:
                                    if st.button("삭제", key=f"delete_achievement_{achievement_id}", type="secondary", use_container_width=True):
                                        try:
                                            res_delete = requests.delete(f"{API_URL}/achievements/{achievement_id}")
                                            if res_delete.status_code == 200:
                                                st.success("도전과제가 삭제되었습니다!")
                                                st.rerun()
                                            else:
                                                error_data = res_delete.json() if res_delete.headers.get('content-type', '').startswith('application/json') else {}
                                                error_msg = error_data.get('error', '삭제 실패')
                                                st.error(error_msg)
                                        except Exception as e:
                                            st.error(f"오류: {str(e)}")
                    else:
                        st.info("등록된 도전과제가 없습니다.")
                else:
                    st.error(f"도전과제 조회 실패: {data.get('error', '알 수 없는 오류')}")
            else:
                st.error(f"API 오류: {res.status_code}")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
    
    with tab2:
        st.subheader("➕ 새 도전과제 생성")
        
        with st.form("create_achievement_form"):
            title = st.text_input("도전과제 제목 *", placeholder="예: Pop 음악 애호가")
            description = st.text_area("도전과제 설명", placeholder="예: Pop 장르 노래를 10번 재생하세요")
            
            achievement_type = st.selectbox("도전과제 타입 *", ["GENRE_PLAY", "TRACK_PLAY"])
            target_value = st.number_input("목표 값 *", min_value=1, value=10, step=1)
            reward_points = st.number_input("보상 포인트", min_value=0, value=100, step=10)
            
            target_genre = None
            target_track_uri = None
            
            if achievement_type == "GENRE_PLAY":
                target_genre = st.text_input("목표 장르 *", placeholder="예: Pop, Rock, K-Pop")
            elif achievement_type == "TRACK_PLAY":
                target_track_uri = st.text_input("목표 트랙 URI *", placeholder="예: spotify:track:...")
            
            submitted = st.form_submit_button("도전과제 생성", type="primary")
            
            if submitted:
                if not title or not achievement_type or not target_value:
                    st.error("필수 항목을 모두 입력해주세요.")
                elif achievement_type == "GENRE_PLAY" and not target_genre:
                    st.error("목표 장르를 입력해주세요.")
                elif achievement_type == "TRACK_PLAY" and not target_track_uri:
                    st.error("목표 트랙 URI를 입력해주세요.")
                else:
                    try:
                        payload = {
                            "title": title,
                            "description": description,
                            "achievement_type": achievement_type,
                            "target_value": target_value,
                            "target_genre": target_genre,
                            "target_track_uri": target_track_uri,
                            "reward_points": reward_points
                        }
                        res = requests.post(f"{API_URL}/achievements", json=payload)
                        if res.status_code == 200:
                            result = res.json()
                            if result.get("success"):
                                st.success(f"✅ 도전과제가 생성되었습니다! (ID: {result.get('achievement_id')})")
                                st.rerun()
                            else:
                                st.error(result.get("error", "도전과제 생성 실패"))
                        else:
                            error_data = res.json() if res.headers.get('content-type', '').startswith('application/json') else {}
                            error_msg = error_data.get('error', f'HTTP {res.status_code} 오류')
                            st.error(f"API 오류: {error_msg}")
                    except Exception as e:
                        st.error(f"오류 발생: {str(e)}")


def show_achievements_page():
    """도전과제 페이지"""
    render_top_guide_banner("achievements")
    st.header("🏆 도전과제")
    
    user = st.session_state.user_info
    user_id = user.get("user_id") if user else None
    
    if not user_id:
        st.error("로그인이 필요합니다.")
        return
    
    try:
        # 사용자의 도전과제 조회
        res = requests.get(f"{API_URL}/users/{user_id}/achievements")
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                achievements = data.get("achievements", [])
                
                if achievements and len(achievements) > 0:
                    # 완료된 도전과제와 진행 중인 도전과제 분리
                    completed = [a for a in achievements if a.get("is_completed")]
                    in_progress = [a for a in achievements if not a.get("is_completed")]
                    
                    # 완료된 도전과제
                    if completed:
                        st.subheader("✅ 완료된 도전과제")
                        
                        # 현재 선택한 칭호 조회
                        selected_achievement_id = None
                        try:
                            res_selected = requests.get(f"{API_URL}/users/{user_id}/selected_achievement")
                            if res_selected.status_code == 200:
                                data_selected = res_selected.json()
                                if data_selected.get("success") and data_selected.get("selected_achievement"):
                                    selected_achievement_id = data_selected.get("selected_achievement").get("achievement_id")
                        except:
                            pass
                        
                        for achievement in completed:
                            achievement_id = achievement.get('achievement_id')
                            is_selected = (selected_achievement_id == achievement_id)
                            
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    if is_selected:
                                        st.markdown(f"### 🏆 {achievement.get('title', '')} ⭐ (현재 칭호)")
                                    else:
                                        st.markdown(f"### 🏆 {achievement.get('title', '')}")
                                    st.write(achievement.get('description', ''))
                                    st.caption(f"보상: {achievement.get('reward_points', 0)} 포인트")
                                    if achievement.get('completed_at'):
                                        st.caption(f"완료일: {achievement['completed_at'][:10]}")
                                with col2:
                                    if is_selected:
                                        st.success("⭐ 칭호")
                                        if st.button("칭호 해제", key=f"deselect_title_{achievement_id}", use_container_width=True):
                                            try:
                                                res_update = requests.put(
                                                    f"{API_URL}/users/{user_id}/selected_achievement",
                                                    json={"achievement_id": None}
                                                )
                                                if res_update.status_code == 200:
                                                    st.success("칭호가 해제되었습니다!")
                                                    st.rerun()
                                                else:
                                                    st.error("칭호 해제 실패")
                                            except Exception as e:
                                                st.error(f"오류: {str(e)}")
                                    else:
                                        if st.button("칭호로 선택", key=f"select_title_{achievement_id}", use_container_width=True):
                                            try:
                                                res_update = requests.put(
                                                    f"{API_URL}/users/{user_id}/selected_achievement",
                                                    json={"achievement_id": achievement_id}
                                                )
                                                if res_update.status_code == 200:
                                                    st.success("칭호가 선택되었습니다!")
                                                    st.rerun()
                                                else:
                                                    error_data = res_update.json() if res_update.headers.get('content-type', '').startswith('application/json') else {}
                                                    error_msg = error_data.get('error', '칭호 선택 실패')
                                                    st.error(error_msg)
                                            except Exception as e:
                                                st.error(f"오류: {str(e)}")
                                    st.success("✅ 완료")
                    
                    # 진행 중인 도전과제
                    if in_progress:
                        st.subheader("🎯 진행 중인 도전과제")
                        for achievement in in_progress:
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"### 🎯 {achievement.get('title', '')}")
                                    st.write(achievement.get('description', ''))
                                    
                                    # 진행도 표시
                                    current_progress = achievement.get('current_progress', 0)
                                    target_value = achievement.get('target_value', 1)
                                    progress_percent = min((current_progress / target_value) * 100, 100)
                                    
                                    st.progress(progress_percent / 100)
                                    st.caption(f"진행도: {current_progress} / {target_value} ({progress_percent:.1f}%)")
                                    
                                    # 도전과제 타입별 정보 표시
                                    achievement_type = achievement.get('achievement_type', '')
                                    if achievement_type == 'TRACK_PLAY':
                                        track_uri = achievement.get('target_track_uri', '')
                                        if track_uri:
                                            st.caption(f"🎵 목표 트랙: {track_uri}")
                                    elif achievement_type == 'GENRE_PLAY':
                                        genre = achievement.get('target_genre', '')
                                        if genre:
                                            st.caption(f"🎵 목표 장르: {genre}")
                                    
                                    st.caption(f"보상: {achievement.get('reward_points', 0)} 포인트")
                                with col2:
                                    st.info("진행 중")
                    else:
                        st.info("진행 중인 도전과제가 없습니다.")
                    
                    # 전체 도전과제 통계
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("전체 도전과제", len(achievements))
                    with col2:
                        st.metric("완료", len(completed))
                    with col3:
                        st.metric("진행 중", len(in_progress))
                else:
                    st.info("아직 도전과제가 없습니다.")
                    st.info("💡 관리자에게 문의하여 도전과제를 생성해주세요.")
            else:
                error_msg = data.get('error', '알 수 없는 오류')
                st.error(f"도전과제 조회 실패: {error_msg}")
                if "테이블이 존재하지 않습니다" in error_msg:
                    st.info("💡 먼저 '사용자 데이터 관리' 메뉴에서 다음 테이블들을 생성해주세요:")
                    st.info("  - Achievements Table 생성")
                    st.info("  - User Achievements Table 생성")
                    st.info("  - Music Playback Log Table 생성")
        else:
            try:
                error_data = res.json()
                error_msg = error_data.get('error', f'HTTP {res.status_code} 오류')
            except:
                error_msg = f'HTTP {res.status_code} 오류'
            st.error(f"API 오류: {error_msg}")
            if res.status_code == 500:
                st.info("💡 서버 오류가 발생했습니다. 백엔드 로그를 확인해주세요.")
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# ----------------------------------------------------------
# 로그 조회 함수
# ----------------------------------------------------------
def show_logs_page():
    """로그 조회 화면"""
    render_top_guide_banner("logs")
    st.header("📋 로그 조회")
    st.write("사용자 활동 로그를 조회합니다.")
    st.markdown("---")
    
    # 조회 필터
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 1])
    
    with filter_col1:
        search_user_id = st.text_input("User ID", placeholder="사용자 ID를 입력하세요", key="log_search_user_id")
    with filter_col2:
        action_type_options = ["전체", "LOGIN", "PAGE_VIEW", "UNSUBSCRIBE"]
        selected_action = st.selectbox("액션 타입", options=action_type_options, key="log_action_type")
        search_action_type = "" if selected_action == "전체" else selected_action
    with filter_col3:
        page_size = st.selectbox("페이지 크기", [20, 50, 100, 200], index=1, key="log_page_size")
    with filter_col4:
        st.write("")  # 빈 공간
        search_button = st.button("🔍 조회", type="primary", key="log_search_button")
    
    # 페이지 상태 관리
    if "log_page" not in st.session_state:
        st.session_state.log_page = 1
    if "log_search_executed" not in st.session_state:
        st.session_state.log_search_executed = False
    if "log_search_params" not in st.session_state:
        st.session_state.log_search_params = {}
    
    if search_button:
        st.session_state.log_page = 1
        st.session_state.log_search_executed = True
        st.session_state.log_search_params = {
            "user_id": search_user_id,
            "action_type": search_action_type,
            "page_size": page_size
        }
        st.rerun()
    
    if not st.session_state.log_search_executed:
        st.info("💡 조회 조건을 입력한 후 '조회' 버튼을 클릭하세요.")
        return
    
    # 저장된 조회 파라미터 사용
    saved_params = st.session_state.log_search_params
    current_user_id = saved_params.get("user_id", "")
    current_action_type = saved_params.get("action_type", "")
    current_page_size = saved_params.get("page_size", page_size)
    page = st.session_state.log_page
    
    # API 요청
    api_url = f"logs?page={page}&page_size={current_page_size}"
    if current_user_id:
        api_url += f"&user_id={current_user_id}"
    if current_action_type:
        api_url += f"&action_type={current_action_type}"
    
    ok, res = call_api(api_url)
    
    if not ok or not res.get("success"):
        st.error("로그 조회 중 오류가 발생하였습니다.")
        st.write(res)
        return
    
    rows = res["rows"]
    total_rows = res["total_rows"]
    total_pages = res["total_pages"]
    
    st.write(f"총 {total_rows}개 로그, 페이지 {page}/{total_pages}")
    st.markdown("---")
    
    if rows:
        # 테이블 표시
        df = pd.DataFrame(rows)
        # 컬럼 순서 조정
        df = df[['log_id', 'user_id', 'user_name', 'action_type', 'page_name', 'additional_info', 'created_at']]
        df.columns = ['로그 ID', '사용자 ID', '사용자 이름', '액션 타입', '페이지명', '추가 정보', '기록 시간']
        
        st.dataframe(df, use_container_width=True, height=400)
        
        # 페이징 버튼
        colA, colB, colC = st.columns(3)
        with colA:
            if st.button("⬅ 이전 페이지", key="log_prev"):
                if page > 1:
                    st.session_state.log_page -= 1
                    st.rerun()
        with colB:
            st.write(f"현재 페이지: {page}")
        with colC:
            if st.button("다음 페이지 ➡", key="log_next"):
                if page < total_pages:
                    st.session_state.log_page += 1
                    st.rerun()
    else:
        st.info("조회 결과가 없습니다.")


# ----------------------------------------------------------
# 이탈 예측 화면들 (GRADE=99 전용)
# ----------------------------------------------------------

def show_churn_prediction_page():
    """단일 유저 이탈 예측 화면"""
    render_top_guide_banner("churn_single")
    st.header("📊 단일 유저 이탈 예측")
    st.write("전체 피처를 사용하여 유저의 이탈 확률을 예측합니다.")
    st.markdown("---")
    
    # 테이블 생성 안내 및 버튼
    with st.expander("⚠️ 테이블이 없으면 먼저 생성하세요"):
        if st.button("📊 User Prediction Table 생성", key="init_pred_table_1"):
            try:
                res = requests.get(f"{API_URL}/init_user_prediction_table")
                if res.status_code == 200:
                    st.success("테이블 생성 완료!")
                else:
                    st.error(f"테이블 생성 실패: {res.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    # User ID 입력
    user_id = st.number_input("User ID", min_value=1, value=1, step=1)
    
    if st.button("유저 데이터 불러오기"):
        try:
            res = requests.get(f"{API_URL}/user_features/{user_id}")
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    st.session_state[f"user_features_{user_id}"] = data.get("data", {})
                    st.success("유저 데이터를 불러왔습니다.")
                else:
                    st.error(data.get("error", "데이터를 불러올 수 없습니다."))
            else:
                st.error(f"API 오류: {res.status_code}")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
    
    # 피처 입력 폼
    if f"user_features_{user_id}" in st.session_state:
        features = st.session_state[f"user_features_{user_id}"]
        
        st.subheader("피처 입력")
        col1, col2 = st.columns(2)
        
        with col1:
            listening_time = st.number_input("listening_time", value=float(features.get("listening_time", 0)), step=1.0)
            songs_played_per_day = st.number_input("songs_played_per_day", value=float(features.get("songs_played_per_day", 0)), step=1.0)
            payment_failure_count = st.number_input("payment_failure_count", value=int(features.get("payment_failure_count", 0)), step=1)
            app_crash_count_30d = st.number_input("app_crash_count_30d", value=int(features.get("app_crash_count_30d", 0)), step=1)
        
        with col2:
            subscription_type = st.selectbox("subscription_type", ["Free", "Premium"], index=0 if features.get("subscription_type") == "Free" else 1)
            customer_support_contact = st.number_input("customer_support_contact", value=int(features.get("customer_support_contact", 0)), step=1)
        
        # 추가 피처들 (필요한 경우)
        feature_dict = {
            "user_id": user_id,
            "listening_time": listening_time,
            "songs_played_per_day": songs_played_per_day,
            "payment_failure_count": payment_failure_count,
            "app_crash_count_30d": app_crash_count_30d,
            "subscription_type": subscription_type,
            "customer_support_contact": customer_support_contact
        }
        
        # 기존 피처들 병합
        for key, value in features.items():
            if key not in feature_dict and key != "user_id":
                feature_dict[key] = value
        
        if st.button("예측 실행", type="primary"):
            try:
                payload = {
                    "user_id": user_id,  # user_id 포함하여 user_features에서 조회
                    "features": feature_dict
                }
                res = requests.post(f"{API_URL}/predict_churn", json=payload)
                if res.status_code == 200:
                    result = res.json()
                    if result.get("success"):
                        st.success("예측 완료!")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("이탈 확률", f"{result.get('churn_prob', 0):.2%}")
                        with col2:
                            risk_level = result.get("risk_level", "UNKNOWN")
                            risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk_level, "⚪")
                            st.metric("위험도", f"{risk_color} {risk_level}")
                        with col3:
                            st.metric("모델", result.get("model_name", "default"))
                    else:
                        st.error(result.get("error", "예측 실패"))
                else:
                    st.error(f"API 오류: {res.status_code} {res.text}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")

def show_churn_prediction_bulk_page():
    """배치 예측 화면"""
    render_top_guide_banner("churn_bulk")
    st.header("📊 배치 이탈 예측")
    st.write("여러 유저의 이탈 확률을 한 번에 예측합니다.")
    st.markdown("---")
    
    # CSV 업로드 또는 수동 입력
    input_method = st.radio("입력 방법", ["CSV 업로드", "수동 입력"])
    
    if input_method == "CSV 업로드":
        uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            # NaN, inf, -inf 값 정리
            df = df.replace([np.inf, -np.inf], np.nan)
            
            st.dataframe(df.head(20))
            st.info(f"총 {len(df)}개 행이 로드되었습니다.")
            
            if st.button("배치 예측 실행", type="primary"):
                try:
                    # dict로 변환 시 NaN/None 값 처리
                    # user_id만 포함하여 전송 (user_features 테이블에서 조회)
                    rows = []
                    for _, row in df.iterrows():
                        # user_id만 포함 (나머지는 user_features 테이블에서 조회)
                        user_id_val = row.get('user_id')
                        if pd.notna(user_id_val):
                            try:
                                row_dict = {"user_id": int(user_id_val)}
                                rows.append(row_dict)
                            except:
                                continue
                    
                    payload = {"rows": rows}
                    res = requests.post(f"{API_URL}/predict_churn_bulk", json=payload)
                    if res.status_code == 200:
                        result = res.json()
                        if result.get("success"):
                            results_df = pd.DataFrame(result.get("results", []))
                            st.success("배치 예측 완료!")
                            
                            # 에러가 있는 행 제외
                            valid_results = results_df[~results_df.get('error').notna()] if 'error' in results_df.columns else results_df
                            
                            if len(valid_results) > 0 and 'churn_prob' in valid_results.columns:
                                # 탭으로 테이블과 차트 분리
                                tab1, tab2, tab3 = st.tabs(["📊 데이터 테이블", "📈 이탈 확률 분포", "🎯 위험도 분석"])
                                
                                with tab1:
                                    st.dataframe(results_df, use_container_width=True)
                                    
                                    # 통계 요약
                                    st.subheader("📊 통계 요약")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("총 예측 수", len(valid_results))
                                    with col2:
                                        avg_churn = valid_results['churn_prob'].mean() * 100
                                        st.metric("평균 이탈 확률", f"{avg_churn:.1f}%")
                                    with col3:
                                        high_risk = len(valid_results[valid_results.get('risk_level') == 'HIGH']) if 'risk_level' in valid_results.columns else 0
                                        st.metric("고위험 유저", high_risk)
                                    with col4:
                                        max_churn = valid_results['churn_prob'].max() * 100
                                        st.metric("최대 이탈 확률", f"{max_churn:.1f}%")
                                
                                with tab2:
                                    st.subheader("이탈 확률 분포")
                                    
                                    # 히스토그램
                                    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
                                    
                                    # 이탈 확률 히스토그램
                                    axes[0].hist(valid_results['churn_prob'] * 100, bins=20, edgecolor='black', alpha=0.7, color='#ff6b6b')
                                    axes[0].set_xlabel('이탈 확률 (%)')
                                    axes[0].set_ylabel('유저 수')
                                    axes[0].set_title('이탈 확률 분포')
                                    axes[0].grid(True, alpha=0.3)
                                    
                                    # 상위 20명 바 차트
                                    top_users = valid_results.nlargest(20, 'churn_prob')
                                    axes[1].barh(range(len(top_users)), top_users['churn_prob'] * 100, color='#ee5a6f')
                                    axes[1].set_yticks(range(len(top_users)))
                                    axes[1].set_yticklabels([f"User {uid}" for uid in top_users.get('user_id', range(len(top_users)))], fontsize=8)
                                    axes[1].set_xlabel('이탈 확률 (%)')
                                    axes[1].set_title('상위 20명 이탈 확률')
                                    axes[1].grid(True, alpha=0.3, axis='x')
                                    
                                    plt.tight_layout()
                                    st.pyplot(fig)
                                    
                                    # 이탈 확률 구간별 분포
                                    st.subheader("이탈 확률 구간별 분포")
                                    bins = [0, 0.3, 0.5, 0.7, 1.0]
                                    labels = ['낮음 (0-30%)', '보통 (30-50%)', '높음 (50-70%)', '매우 높음 (70-100%)']
                                    valid_results['churn_category'] = pd.cut(valid_results['churn_prob'], bins=bins, labels=labels, include_lowest=True)
                                    category_counts = valid_results['churn_category'].value_counts().sort_index()
                                    
                                    col1, col2 = st.columns([1, 2])
                                    with col1:
                                        st.dataframe(category_counts.reset_index().rename(columns={'index': '구간', 'churn_category': '유저 수'}))
                                    with col2:
                                        st.bar_chart(category_counts)
                                
                                with tab3:
                                    st.subheader("위험도 분석")
                                    
                                    if 'risk_level' in valid_results.columns:
                                        # 위험도별 분포
                                        risk_counts = valid_results['risk_level'].value_counts()
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.write("위험도별 유저 수")
                                            risk_df = risk_counts.reset_index()
                                            risk_df.columns = ['위험도', '유저 수']
                                            # 위험도 순서 정렬
                                            risk_order = ['LOW', 'MEDIUM', 'HIGH']
                                            risk_df['위험도'] = pd.Categorical(risk_df['위험도'], categories=risk_order, ordered=True)
                                            risk_df = risk_df.sort_values('위험도')
                                            st.dataframe(risk_df, use_container_width=True)
                                        
                                        with col2:
                                            # 파이 차트
                                            fig, ax = plt.subplots(figsize=(8, 8))
                                            colors = {'LOW': '#51cf66', 'MEDIUM': '#ffd43b', 'HIGH': '#ff6b6b'}
                                            risk_colors = [colors.get(risk, '#95a5a6') for risk in risk_counts.index]
                                            ax.pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%', 
                                                  colors=risk_colors, startangle=90)
                                            ax.set_title('위험도 분포')
                                            st.pyplot(fig)
                                        
                                        # 위험도별 평균 이탈 확률
                                        st.subheader("위험도별 평균 이탈 확률")
                                        risk_avg = valid_results.groupby('risk_level')['churn_prob'].mean() * 100
                                        risk_avg_df = risk_avg.reset_index()
                                        risk_avg_df.columns = ['위험도', '평균 이탈 확률 (%)']
                                        risk_avg_df['위험도'] = pd.Categorical(risk_avg_df['위험도'], categories=risk_order, ordered=True)
                                        risk_avg_df = risk_avg_df.sort_values('위험도')
                                        
                                        col1, col2 = st.columns([1, 2])
                                        with col1:
                                            st.dataframe(risk_avg_df, use_container_width=True)
                                        with col2:
                                            st.bar_chart(risk_avg.set_axis(risk_avg.index))
                                    else:
                                        st.info("위험도 정보가 없습니다.")
                            else:
                                st.dataframe(results_df, use_container_width=True)
                                if len(valid_results) == 0:
                                    st.warning("예측 결과가 없거나 모든 행에서 오류가 발생했습니다.")
                        else:
                            st.error(result.get("error", "예측 실패"))
                    else:
                        error_msg = f"API 오류: {res.status_code}"
                        try:
                            error_detail = res.json()
                            if isinstance(error_detail, dict) and "error" in error_detail:
                                error_msg += f"\n{error_detail['error']}"
                            else:
                                error_msg += f"\n{res.text[:200]}"
                        except:
                            error_msg += f"\n{res.text[:200]}"
                        st.error(error_msg)
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")
    else:
        st.info("수동 입력 기능은 추후 구현 예정입니다.")

def show_churn_prediction_6feat_page():
    """6피처 시뮬레이터 화면"""
    render_top_guide_banner("churn_6feat")
    st.header("🎯 6피처 이탈 예측 시뮬레이터")
    st.write("6개 핵심 피처만 사용하여 이탈 확률을 예측합니다.")
    st.markdown("---")
    
    # 테이블 생성 안내 및 버튼
    with st.expander("⚠️ 테이블이 없으면 먼저 생성하세요"):
        if st.button("📊 User Prediction Table 생성", key="init_pred_table_2"):
            try:
                res = requests.get(f"{API_URL}/init_user_prediction_table")
                if res.status_code == 200:
                    st.success("테이블 생성 완료!")
                else:
                    st.error(f"테이블 생성 실패: {res.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    user_id = st.number_input("User ID", min_value=1, value=1, step=1)
    
    st.subheader("6개 핵심 피처 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        app_crash_count_30d = st.number_input("앱 크래시 횟수 (30일)", min_value=0, value=0, step=1, key="crash")
        skip_rate_increase_7d = st.number_input("스킵률 증가 (7일, %)", min_value=0.0, value=0.0, step=0.1, key="skip")
        days_since_last_login = st.number_input("마지막 로그인 경과일", min_value=0, value=0, step=1, key="login_days")
    
    with col2:
        listening_time_trend_7d = st.number_input("청취 시간 추세 (7일, %)", value=0.0, step=0.1, key="listening")
        freq_of_use_trend_14d = st.number_input("사용 빈도 추세 (14일, %)", value=0.0, step=0.1, key="freq")
        login_frequency_30d = st.number_input("로그인 빈도 (30일)", min_value=0, value=0, step=1, key="login_freq")
    
    if st.button("예측 실행", type="primary"):
        try:
            payload = {
                "user_id": user_id,
                "features": {
                    "app_crash_count_30d": app_crash_count_30d,
                    "skip_rate_increase_7d": skip_rate_increase_7d,
                    "days_since_last_login": days_since_last_login,
                    "listening_time_trend_7d": listening_time_trend_7d,
                    "freq_of_use_trend_14d": freq_of_use_trend_14d,
                    "login_frequency_30d": login_frequency_30d
                }
            }
            res = requests.post(f"{API_URL}/predict_churn_6feat", json=payload)
            if res.status_code == 200:
                result = res.json()
                if result.get("success"):
                    st.success("예측 완료! (결과가 DB에 저장되었습니다)")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("이탈률", f"{result.get('churn_rate', 0)}%")
                    with col2:
                        risk_score = result.get("risk_score", "UNKNOWN")
                        risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk_score, "⚪")
                        st.metric("위험도", f"{risk_color} {risk_score}")
                    with col3:
                        st.metric("업데이트 날짜", result.get("update_date", "N/A"))
                else:
                    st.error(result.get("error", "예측 실패"))
            else:
                st.error(f"API 오류: {res.status_code} {res.text}")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

def show_prediction_results_page():
    """예측 결과 조회 화면"""
    render_top_guide_banner("prediction_results")
    st.header("📋 예측 결과 조회")
    st.write("저장된 예측 결과를 조회합니다.")
    st.markdown("---")
    
    # 테이블 생성 안내 및 버튼
    with st.expander("⚠️ 테이블이 없으면 먼저 생성하세요"):
        if st.button("📊 User Prediction Table 생성", key="init_pred_table_3"):
            try:
                res = requests.get(f"{API_URL}/init_user_prediction_table")
                if res.status_code == 200:
                    st.success("테이블 생성 완료!")
                else:
                    st.error(f"테이블 생성 실패: {res.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    tab1, tab2 = st.tabs(["단일 유저 조회", "전체 조회"])
    
    with tab1:
        user_id = st.number_input("User ID", min_value=1, value=1, step=1, key="result_user_id")
        if st.button("조회", key="result_single"):
            try:
                res = requests.get(f"{API_URL}/user_prediction/{user_id}")
                if res.status_code == 200:
                    result = res.json()
                    if result.get("success"):
                        data = result.get("data", {})
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("User ID", data.get("user_id"))
                        with col2:
                            st.metric("이탈률", f"{data.get('churn_rate', 0)}%")
                        with col3:
                            risk_score = data.get("risk_score", "UNKNOWN")
                            risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk_score, "⚪")
                            st.metric("위험도", f"{risk_color} {risk_score}")
                        with col4:
                            st.metric("업데이트 날짜", data.get("update_date", "N/A")[:10] if data.get("update_date") else "N/A")
                    else:
                        st.warning(result.get("error", "데이터를 찾을 수 없습니다."))
                else:
                    st.error(f"API 오류: {res.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    with tab2:
        user_ids_input = st.text_input("User IDs (쉼표로 구분, 비워두면 전체 조회)", value="")
        if st.button("조회", key="result_all"):
            try:
                params = {}
                if user_ids_input.strip():
                    params["user_ids"] = user_ids_input.strip()
                
                res = requests.get(f"{API_URL}/user_prediction", params=params)
                if res.status_code == 200:
                    result = res.json()
                    if result.get("success"):
                        rows = result.get("rows", [])
                        if rows:
                            df = pd.DataFrame(rows)
                            st.dataframe(df, use_container_width=True)
                            
                            # 통계
                            st.subheader("통계")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("총 예측 수", len(rows))
                            with col2:
                                high_risk = sum(1 for r in rows if r.get("risk_score") == "HIGH")
                                st.metric("고위험 유저", high_risk)
                            with col3:
                                avg_churn = sum(r.get("churn_rate", 0) for r in rows) / len(rows) if rows else 0
                                st.metric("평균 이탈률", f"{avg_churn:.1f}%")
                        else:
                            st.info("조회된 결과가 없습니다.")
                    else:
                        st.error(result.get("error", "조회 실패"))
                else:
                    st.error(f"API 오류: {res.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")

def show_prediction_csv_page():
    """CSV 업로드/다운로드 화면"""
    render_top_guide_banner("prediction_csv")
    st.header("📁 예측 결과 CSV 관리")
    st.write("CSV 파일을 업로드하여 일괄 예측하거나, 예측 결과를 다운로드합니다.")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["CSV 업로드 (일괄 예측)", "CSV 다운로드"])
    
    with tab1:
        st.subheader("CSV 업로드")
        st.write("""
        **필수 컬럼:**
        - user_id
        - app_crash_count_30d
        - skip_rate_increase_7d
        - days_since_last_login
        - listening_time_trend_7d
        - freq_of_use_trend_14d
        - login_frequency_30d
        """)
        
        uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"], key="upload_csv")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head(10))
                
                required_cols = [
                    "user_id", "app_crash_count_30d", "skip_rate_increase_7d",
                    "days_since_last_login", "listening_time_trend_7d",
                    "freq_of_use_trend_14d", "login_frequency_30d"
                ]
                
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    st.error(f"필수 컬럼이 없습니다: {', '.join(missing_cols)}")
                else:
                    if st.button("일괄 예측 실행", type="primary"):
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                            res = requests.post(f"{API_URL}/upload_prediction_csv", files=files)
                            if res.status_code == 200:
                                result = res.json()
                                if result.get("success"):
                                    st.success(f"✅ {result.get('processed_rows', 0)}개 행 처리 완료!")
                                else:
                                    st.error(result.get("error", "처리 실패"))
                            else:
                                st.error(f"API 오류: {res.status_code} {res.text}")
                        except Exception as e:
                            st.error(f"오류 발생: {str(e)}")
            except Exception as e:
                st.error(f"CSV 파일 읽기 오류: {str(e)}")
    
    with tab2:
        st.subheader("예측 결과 다운로드")
        st.write("저장된 모든 예측 결과를 CSV 파일로 다운로드합니다.")
        
        if st.button("CSV 다운로드", type="primary"):
            try:
                res = requests.get(f"{API_URL}/download_prediction_csv")
                if res.status_code == 200:
                    st.download_button(
                        label="다운로드",
                        data=res.content,
                        file_name="user_prediction.csv",
                        mime="text/csv"
                    )
                    st.success("CSV 파일이 준비되었습니다. 다운로드 버튼을 클릭하세요.")
                else:
                    st.error(f"API 오류: {res.status_code}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")

# ----------------------------------------------------------
# 사용자 데이터 관리 도구 (API 호출 기반)
# ----------------------------------------------------------
def show_user_admin_tools():
    render_top_guide_banner("user_admin")
    st.header("🛠 사용자 데이터 관리 도구")
    st.write("Flask API(app.py)에서 제공하는 기능을 실행합니다.")
    st.markdown("---")

    # User 테이블 생성
    if st.button("📘 User Table 생성"):
        ok, res = call_api("init_user_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    # User Features 테이블 생성
    if st.button("📊 User Features Table 생성"):
        ok, res = call_api("init_user_features_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    # User Prediction 테이블 생성
    if st.button("📊 User Prediction Table 생성"):
        ok, res = call_api("init_user_prediction_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    # Log 테이블 생성
    if st.button("📋 Log Table 생성"):
        ok, res = call_api("init_log_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    st.markdown("---")
    st.subheader("도전과제 관련 테이블")
    
    # Achievements 테이블 생성
    if st.button("🏆 Achievements Table 생성"):
        ok, res = call_api("init_achievements_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)
    
    # User Achievements 테이블 생성
    if st.button("📊 User Achievements Table 생성"):
        ok, res = call_api("init_user_achievements_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)
    
    # Music Playback Log 테이블 생성
    if st.button("🎵 Music Playback Log Table 생성"):
        ok, res = call_api("init_music_playback_log_table")
        if ok:
            st.success(res.get("message", "테이블 생성 완료"))
        else:
            st.error(res)

    st.markdown("---")
    st.subheader("CSV 데이터 Import")
    
    # CSV → DB Insert 실행 (users)
    if st.button("📥 Users CSV → DB Insert 실행"):
        ok, res = call_api("import_users_from_csv")
        if ok:
            st.success(res.get("message", "CSV Import 완료"))
        else:
            st.error(res)

    st.markdown("---")
    st.subheader("User Features CSV Import")
    
    # CSV 파일 업로드 방식
    uploaded_file = st.file_uploader(
        "CSV 파일 업로드 (user_features 테이블에 데이터 삽입)",
        type=["csv"],
        help="user_id 컬럼이 포함된 CSV 파일을 업로드하세요."
    )
    
    if uploaded_file is not None:
        try:
            # CSV 미리보기
            df_preview = pd.read_csv(uploaded_file)
            st.write("**업로드된 파일 미리보기:**")
            st.dataframe(df_preview.head(10))
            st.info(f"총 {len(df_preview)}개 행이 있습니다.")
            
            # 필수 컬럼 확인
            if 'user_id' not in df_preview.columns:
                st.error("❌ 'user_id' 컬럼이 필수입니다. CSV 파일에 user_id 컬럼이 있는지 확인하세요.")
            else:
                if st.button("📥 CSV 데이터 Import 실행", type="primary"):
                    try:
                        with st.spinner("CSV 데이터를 import하는 중..."):
                            # 파일을 다시 읽어서 전송
                            uploaded_file.seek(0)  # 파일 포인터를 처음으로
                            files = {'file': (uploaded_file.name, uploaded_file, 'text/csv')}
                            res = requests.post(f"{API_URL}/import_user_features_from_csv", files=files)
                            
                            if res.status_code == 200:
                                result = res.json()
                                if result.get("success"):
                                    inserted = result.get("inserted_count", 0)
                                    error_count = result.get("error_count", 0)
                                    
                                    st.success(f"✅ {result.get('message', 'CSV Import 완료')}")
                                    
                                    if error_count > 0:
                                        st.warning(f"⚠️ {error_count}개 행에서 오류가 발생했습니다.")
                                        errors = result.get("errors")
                                        if errors:
                                            with st.expander("오류 상세 보기"):
                                                for error in errors:
                                                    st.text(error)
                                else:
                                    st.error(result.get("error", "CSV Import 실패"))
                            else:
                                st.error(f"API 오류: {res.status_code} {res.text[:200]}")
                    except Exception as e:
                        st.error(f"오류 발생: {str(e)}")
        except Exception as e:
            st.error(f"CSV 파일 읽기 오류: {str(e)}")
    
    st.markdown("---")
    st.write("**또는 기본 경로의 CSV 파일 사용:**")
    
    # 기본 경로 CSV Import (기존 기능)
    if st.button("📥 기본 경로 CSV Import 실행 (data/enhanced_data_not_clean_FE_delete.csv)"):
        try:
            with st.spinner("CSV 데이터를 import하는 중..."):
                res = requests.post(f"{API_URL}/import_user_features_from_csv")
                if res.status_code == 200:
                    result = res.json()
                    if result.get("success"):
                        inserted = result.get("inserted_count", 0)
                        error_count = result.get("error_count", 0)
                        
                        st.success(f"✅ {result.get('message', 'CSV Import 완료')}")
                        
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count}개 행에서 오류가 발생했습니다.")
                            errors = result.get("errors")
                            if errors:
                                with st.expander("오류 상세 보기"):
                                    for error in errors:
                                        st.text(error)
                    else:
                        st.error(result.get("error", "CSV Import 실패"))
                else:
                    st.error(f"API 오류: {res.status_code} {res.text[:200]}")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")


# ----------------------------------------------------------
# 메인 화면 (로그인 후 진입)
# ----------------------------------------------------------
def show_main_page():
    """
    로그인 성공 후 보여지는 메인 화면
    """
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.error("로그인 후 이용 가능한 메뉴입니다.")
        st.stop()

    user = st.session_state.user_info
    user_id = user.get("user_id")
    grade = user.get("grade")
    
    # ---------------------------
    # 사용자 정보 사이드바 출력
    # ---------------------------
    with st.sidebar:
        st.markdown("### 👤 로그인 정보")
        st.write(f"**ID:** {user['user_id']}")
        st.write(f"**이름:** {user['name']}")
        st.write(f"**등급:** {user['grade']}")
        
        # 선택한 칭호 표시
        try:
            res = requests.get(f"{API_URL}/users/{user_id}/selected_achievement")
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("selected_achievement"):
                    achievement = data.get("selected_achievement")
                    st.markdown("---")
                    st.markdown("### 🏆 칭호")
                    st.markdown(f"**{achievement.get('title', '')}**")
                    st.caption(achievement.get('description', ''))
        except:
            pass  # 칭호 조회 실패해도 계속 진행
        
        st.markdown("---")
        
    # # ---------------------------
    # # 메인 화면 제목
    # # ---------------------------
    # st.title("📘 메인 화면")

    # -------------------------
    # 사이드바 메뉴
    # -------------------------
    menu_items = ["홈", "내 정보", "도전과제", "기능 B"]
    
    # grade = 99 → 관리자 메뉴 추가 (접두사로 구분)
    if grade == "99":
        menu_items.extend([
            "🔧 도전과제 관리",
            "🔧 사용자 데이터 관리", 
            "🔧 사용자 조회",
            "🔧 이탈 예측 (단일)",
            "🔧 이탈 예측 (배치)",
            "🔧 이탈 예측 (6피처)",
            "🔧 예측 결과 조회",
            "🔧 예측 CSV 관리",
            "🔧 로그 조회"
        ])
    
    # 하나의 radio 버튼으로 통합
    menu = st.sidebar.radio("메뉴 선택", menu_items)
    
    # 접두사 제거하여 실제 메뉴 이름 추출
    if menu.startswith("🔧 "):
        menu = menu.replace("🔧 ", "")
    
    # 화면 접근 로그 기록
    if user_id:
        try:
            page_name_map = {
                "홈": "홈",
                "내 정보": "개인정보 수정",
                "사용자 조회": "사용자 조회",
                "기능 B": "기능 B",
                "도전과제": "도전과제",
                "도전과제 관리": "도전과제 관리",
                "사용자 데이터 관리": "사용자 데이터 관리",
                "이탈 예측 (단일)": "이탈 예측 (단일)",
                "이탈 예측 (배치)": "이탈 예측 (배치)",
                "이탈 예측 (6피처)": "이탈 예측 (6피처)",
                "예측 결과 조회": "예측 결과 조회",
                "예측 CSV 관리": "예측 CSV 관리",
                "로그 조회": "로그 조회"
            }
            page_name = page_name_map.get(menu, menu)
            requests.post(f"{API_URL}/log", json={
                "user_id": user_id,
                "action_type": "PAGE_VIEW",
                "page_name": page_name
            }, timeout=1)
        except:
            pass  # 로그 기록 실패해도 계속 진행

    if menu == "홈":
        show_home_page()
    elif menu == "내 정보":
        show_profile_page()
    elif menu == "도전과제":
        show_achievements_page()
    elif menu == "도전과제 관리":
        if grade == "99":
            show_achievements_admin_page()
        else:
            st.error("권한이 없습니다.")
    elif menu == "사용자 조회":
        if grade == "99":
            search_user()
        else:
            st.error("권한이 없습니다.")
    elif menu == "기능 B":
        show_feature_b()
    elif menu == "사용자 데이터 관리":
        if grade == "99":
            show_user_admin_tools()
        else:
            st.error("권한이 없습니다.")
    elif menu == "이탈 예측 (단일)":
        if grade == "99":
            show_churn_prediction_page()
        else:
            st.error("권한이 없습니다.")
    elif menu == "이탈 예측 (배치)":
        if grade == "99":
            show_churn_prediction_bulk_page()
        else:
            st.error("권한이 없습니다.")
    elif menu == "이탈 예측 (6피처)":
        if grade == "99":
            show_churn_prediction_6feat_page()
        else:
            st.error("권한이 없습니다.")
    elif menu == "예측 결과 조회":
        if grade == "99":
            show_prediction_results_page()
        else:
            st.error("권한이 없습니다.")
    elif menu == "예측 CSV 관리":
        if grade == "99":
            show_prediction_csv_page()
        else:
            st.error("권한이 없습니다.")
    elif menu == "로그 조회":
        if grade == "99":
            show_logs_page()
        else:
            st.error("권한이 없습니다.")

    # -------------------------
    # 로그아웃
    # -------------------------
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.page = "login"
        st.rerun()
