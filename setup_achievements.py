"""
도전과제 초기 데이터 설정 스크립트
- 임의의 도전과제 생성
- 임시 계정(user_id: 1 또는 99)에 도전과제 진행 상황 설정
"""

import sys
import os
from dotenv import load_dotenv
import pymysql.cursors

# backend 디렉토리에서 실행할 때 상위 디렉토리를 sys.path에 추가
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from utils.constants import get_connection

load_dotenv()

def create_achievements():
    """도전과제 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    
    achievements = [
        {
            "title": "Pop 음악 애호가",
            "description": "Pop 장르 노래를 10번 재생하세요",
            "achievement_type": "GENRE_PLAY",
            "target_value": 10,
            "target_genre": "Pop",
            "reward_points": 100
        },
        {
            "title": "Rock 열정가",
            "description": "Rock 장르 노래를 15번 재생하세요",
            "achievement_type": "GENRE_PLAY",
            "target_value": 15,
            "target_genre": "Rock",
            "reward_points": 150
        },
        {
            "title": "K-Pop 마니아",
            "description": "K-Pop 장르 노래를 20번 재생하세요",
            "achievement_type": "GENRE_PLAY",
            "target_value": 20,
            "target_genre": "K-Pop",
            "reward_points": 200
        },
        {
            "title": "Jazz 감상가",
            "description": "Jazz 장르 노래를 5번 재생하세요",
            "achievement_type": "GENRE_PLAY",
            "target_value": 5,
            "target_genre": "Jazz",
            "reward_points": 50
        },
        {
            "title": "Hip Hop 팬",
            "description": "Hip Hop 장르 노래를 12번 재생하세요",
            "achievement_type": "GENRE_PLAY",
            "target_value": 12,
            "target_genre": "Hip Hop",
            "reward_points": 120
        },
        {
            "title": "첫 사랑의 노래",
            "description": "특정 노래를 3번 재생하세요",
            "achievement_type": "TRACK_PLAY",
            "target_value": 3,
            "target_track_uri": "spotify:track:4uLU6hMCjMI75M1A2tKUQC",
            "reward_points": 30
        },
        {
            "title": "나만의 플레이리스트",
            "description": "특정 노래를 5번 재생하세요",
            "achievement_type": "TRACK_PLAY",
            "target_value": 5,
            "target_track_uri": "spotify:track:1Je1IMUlBXcx1Fz0WE7oPT",
            "reward_points": 50
        }
    ]
    
    created_count = 0
    for achievement in achievements:
        try:
            sql = """
            INSERT INTO achievements (title, description, achievement_type, target_value, 
                                     target_track_uri, target_genre, reward_points, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """
            cursor.execute(sql, (
                achievement["title"],
                achievement["description"],
                achievement["achievement_type"],
                achievement["target_value"],
                achievement.get("target_track_uri"),
                achievement.get("target_genre"),
                achievement["reward_points"]
            ))
            created_count += 1
            print(f"[OK] 도전과제 생성: {achievement['title']}")
        except Exception as e:
            print(f"[FAIL] 도전과제 생성 실패 ({achievement['title']}): {str(e)}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n총 {created_count}개의 도전과제가 생성되었습니다.")
    return created_count


def setup_user_achievements(user_id=1):
    """임시 계정에 도전과제 진행 상황 설정"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 모든 활성화된 도전과제 조회
        cursor.execute("""
            SELECT achievement_id, title, target_value
            FROM achievements
            WHERE is_active = TRUE
            ORDER BY achievement_id ASC
        """)
        achievements = cursor.fetchall()
        
        if not achievements:
            print("[ERROR] 생성된 도전과제가 없습니다. 먼저 도전과제를 생성해주세요.")
            return
        
        print(f"\n사용자 ID {user_id}의 도전과제 진행 상황 설정 중...")
        
        # 첫 번째 도전과제: 완료
        if len(achievements) > 0:
            achievement = achievements[0]
            achievement_id = achievement["achievement_id"]
            title = achievement["title"]
            target_value = achievement["target_value"]
            sql = """
            INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed, completed_at)
            VALUES (%s, %s, %s, TRUE, NOW())
            ON DUPLICATE KEY UPDATE
                current_progress = %s,
                is_completed = TRUE,
                completed_at = NOW()
            """
            cursor.execute(sql, (user_id, achievement_id, target_value, target_value))
            print(f"[완료] {title} (진행도: {target_value}/{target_value})")
        
        # 두 번째 도전과제: 완료
        if len(achievements) > 1:
            achievement = achievements[1]
            achievement_id = achievement["achievement_id"]
            title = achievement["title"]
            target_value = achievement["target_value"]
            sql = """
            INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed, completed_at)
            VALUES (%s, %s, %s, TRUE, NOW())
            ON DUPLICATE KEY UPDATE
                current_progress = %s,
                is_completed = TRUE,
                completed_at = NOW()
            """
            cursor.execute(sql, (user_id, achievement_id, target_value, target_value))
            print(f"[완료] {title} (진행도: {target_value}/{target_value})")
        
        # 세 번째 도전과제: 진행 중 (80%)
        if len(achievements) > 2:
            achievement = achievements[2]
            achievement_id = achievement["achievement_id"]
            title = achievement["title"]
            target_value = achievement["target_value"]
            current_progress = int(target_value * 0.8)
            sql = """
            INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed)
            VALUES (%s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE
                current_progress = %s,
                is_completed = FALSE
            """
            cursor.execute(sql, (user_id, achievement_id, current_progress, current_progress))
            print(f"[진행중] {title} (진행도: {current_progress}/{target_value})")
        
        # 네 번째 도전과제: 진행 중 (50%)
        if len(achievements) > 3:
            achievement = achievements[3]
            achievement_id = achievement["achievement_id"]
            title = achievement["title"]
            target_value = achievement["target_value"]
            current_progress = int(target_value * 0.5)
            sql = """
            INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed)
            VALUES (%s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE
                current_progress = %s,
                is_completed = FALSE
            """
            cursor.execute(sql, (user_id, achievement_id, current_progress, current_progress))
            print(f"[진행중] {title} (진행도: {current_progress}/{target_value})")
        
        # 다섯 번째 도전과제: 진행 중 (30%)
        if len(achievements) > 4:
            achievement = achievements[4]
            achievement_id = achievement["achievement_id"]
            title = achievement["title"]
            target_value = achievement["target_value"]
            current_progress = int(target_value * 0.3)
            sql = """
            INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed)
            VALUES (%s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE
                current_progress = %s,
                is_completed = FALSE
            """
            cursor.execute(sql, (user_id, achievement_id, current_progress, current_progress))
            print(f"[진행중] {title} (진행도: {current_progress}/{target_value})")
        
        # 나머지는 진행 중 (10%)
        for achievement in achievements[5:]:
            achievement_id = achievement["achievement_id"]
            title = achievement["title"]
            target_value = achievement["target_value"]
            current_progress = max(1, int(target_value * 0.1))
            sql = """
            INSERT INTO user_achievements (user_id, achievement_id, current_progress, is_completed)
            VALUES (%s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE
                current_progress = %s,
                is_completed = FALSE
            """
            cursor.execute(sql, (user_id, achievement_id, current_progress, current_progress))
            print(f"[진행중] {title} (진행도: {current_progress}/{target_value})")
        
        conn.commit()
        print(f"\n[OK] 사용자 ID {user_id}의 도전과제 진행 상황이 설정되었습니다.")
        
    except Exception as e:
        print(f"[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


def main():
    """메인 함수"""
    print("=" * 50)
    print("도전과제 초기 데이터 설정")
    print("=" * 50)
    
    # 1. 도전과제 생성
    print("\n[1단계] 도전과제 생성 중...")
    create_achievements()
    
    # 2. 임시 계정(user_id=1)에 도전과제 진행 상황 설정
    print("\n[2단계] 임시 계정(user_id=1) 도전과제 진행 상황 설정 중...")
    setup_user_achievements(user_id=1)
    
    # 3. 관리자 계정(user_id=99)에도 설정 (선택적)
    print("\n[3단계] 관리자 계정(user_id=99) 도전과제 진행 상황 설정 중...")
    setup_user_achievements(user_id=99)
    
    print("\n" + "=" * 50)
    print("[OK] 모든 설정이 완료되었습니다!")
    print("=" * 50)


if __name__ == "__main__":
    main()

