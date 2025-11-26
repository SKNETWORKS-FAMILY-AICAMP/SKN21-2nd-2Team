# 데이터베이스 ERD 문서

## 테이블 목록

1. **users** - 사용자 기본 정보
2. **user_prediction** - 이탈 예측 결과
3. **user_features** - 사용자 피처 데이터 (ML 학습용)
4. **log** - 사용자 활동 로그
5. **achievements** - 도전과제 정의
6. **user_achievements** - 사용자별 도전과제 진행 상황
7. **music_playback_log** - 음악 재생 로그

---

## ERD 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                        users                                 │
├─────────────────────────────────────────────────────────────┤
│ PK  user_id                    INT AUTO_INCREMENT           │
│     name                       VARCHAR(100) NOT NULL        │
│     favorite_music             VARCHAR(50)                   │
│     password                   VARCHAR(200) NOT NULL         │
│     join_date                  DATE                          │
│     modify_date                DATE                          │
│     grade                      CHAR(2) NOT NULL              │
│ FK  selected_achievement_id    INT                           │
└─────────────────────────────────────────────────────────────┘
         │
         │ 1
         │
         │ 0..1
         ├─────────────────────────────────────────────────────┐
         │                                                     │
         │ 1                                                  │
         │                                                     │
         ▼                                                     ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│   user_prediction        │              │   user_features          │
├──────────────────────────┤              ├──────────────────────────┤
│ PK  user_id              │              │ PK  user_id              │
│     churn_rate           │              │     gender               │
│     risk_score           │              │     age                  │
│     update_date          │              │     country              │
└──────────────────────────┘              │     subscription_type    │
                                          │     listening_time       │
                                          │     songs_played_per_day │
                                          │     skip_rate            │
                                          │     device_type          │
                                          │     ads_listened_per_week│
                                          │     offline_listening    │
                                          │     is_churned           │
                                          │     listening_time_trend_7d│
                                          │     login_frequency_30d  │
                                          │     days_since_last_login│
                                          │     skip_rate_increase_7d│
                                          │     freq_of_use_trend_14d│
                                          │     customer_support_contact│
                                          │     payment_failure_count│
                                          │     promotional_email_click│
                                          │     app_crash_count_30d  │
                                          └──────────────────────────┘
         │
         │ 1
         │
         │ 0..*
         ├─────────────────────────────────────────────────────┐
         │                                                     │
         │ 1                                                  │
         │                                                     │
         ▼                                                     ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│   log                     │              │   music_playback_log     │
├──────────────────────────┤              ├──────────────────────────┤
│ PK  log_id                │              │ PK  playback_id          │
│ FK  user_id               │              │ FK  user_id              │
│     action_type           │              │     track_uri            │
│     page_name             │              │     track_name           │
│     additional_info       │              │     artist_name          │
│     created_at            │              │     genre                │
└──────────────────────────┘              │     playback_duration    │
                                          │     created_at            │
                                          └──────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    achievements                              │
├─────────────────────────────────────────────────────────────┤
│ PK  achievement_id            INT AUTO_INCREMENT            │
│     title                     VARCHAR(200) NOT NULL          │
│     description               TEXT                          │
│     achievement_type          VARCHAR(50) NOT NULL           │
│     target_value              INT NOT NULL                  │
│     target_track_uri          VARCHAR(200)                  │
│     target_genre              VARCHAR(100)                  │
│     reward_points             INT DEFAULT 0                 │
│     is_active                 BOOLEAN DEFAULT TRUE          │
│     created_at                DATETIME DEFAULT CURRENT_TIMESTAMP│
└─────────────────────────────────────────────────────────────┘
         │
         │ 1
         │
         │ 0..*
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                user_achievements                            │
├─────────────────────────────────────────────────────────────┤
│ PK  user_achievement_id       INT AUTO_INCREMENT            │
│ FK  user_id                   INT NOT NULL                  │
│ FK  achievement_id            INT NOT NULL                  │
│     current_progress          INT DEFAULT 0                 │
│     is_completed              BOOLEAN DEFAULT FALSE          │
│     completed_at              DATETIME                       │
│     created_at                DATETIME DEFAULT CURRENT_TIMESTAMP│
│     UNIQUE (user_id, achievement_id)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 테이블 상세 정보

### 1. users (사용자 기본 정보)
- **용도**: 사용자 기본 정보 저장
- **주요 컬럼**:
  - `user_id`: 사용자 고유 ID (PK)
  - `name`: 사용자 이름
  - `password`: 암호화된 비밀번호
  - `grade`: 사용자 등급 ('01': 일반, '99': 관리자, '00': 휴면)
  - `selected_achievement_id`: 선택한 칭호 ID (FK → achievements)
- **관계**:
  - 1:1 → user_prediction
  - 1:1 → user_features
  - 1:N → log
  - 1:N → music_playback_log
  - 1:N → user_achievements

### 2. user_prediction (이탈 예측 결과)
- **용도**: 이탈 예측 모델의 예측 결과 저장
- **주요 컬럼**:
  - `user_id`: 사용자 ID (PK, FK → users)
  - `churn_rate`: 이탈 확률 (0~100)
  - `risk_score`: 위험도 ('LOW', 'MEDIUM', 'HIGH')
  - `update_date`: 예측 실행 일자
- **관계**:
  - N:1 → users

### 3. user_features (사용자 피처 데이터)
- **용도**: ML 학습용 사용자 피처 데이터 저장
- **주요 컬럼**:
  - `user_id`: 사용자 ID (PK, FK → users)
  - `subscription_type`: 구독 유형 ('Free', 'Premium', 'Family')
  - `listening_time`: 청취 시간
  - `songs_played_per_day`: 일일 재생 곡 수
  - `login_frequency_30d`: 30일 로그인 빈도
  - 기타 ML 피처들...
- **관계**:
  - N:1 → users

### 4. log (사용자 활동 로그)
- **용도**: 사용자 활동 로그 기록
- **주요 컬럼**:
  - `log_id`: 로그 ID (PK)
  - `user_id`: 사용자 ID (FK → users)
  - `action_type`: 활동 유형 ('LOGIN', 'PAGE_VIEW', 'UNSUBSCRIBE')
  - `page_name`: 접근한 페이지 이름
  - `additional_info`: 추가 정보 (JSON)
  - `created_at`: 기록 시간
- **관계**:
  - N:1 → users

### 5. achievements (도전과제 정의)
- **용도**: 도전과제 정의 저장
- **주요 컬럼**:
  - `achievement_id`: 도전과제 ID (PK)
  - `title`: 도전과제 제목
  - `description`: 도전과제 설명
  - `achievement_type`: 도전과제 유형 ('TRACK_PLAY', 'GENRE_PLAY' 등)
  - `target_value`: 목표 값
  - `target_track_uri`: 목표 트랙 URI
  - `target_genre`: 목표 장르
  - `reward_points`: 보상 포인트
  - `is_active`: 활성화 여부
- **관계**:
  - 1:N → user_achievements
  - 1:0..1 → users (selected_achievement_id)

### 6. user_achievements (사용자별 도전과제 진행 상황)
- **용도**: 사용자별 도전과제 진행 상황 저장
- **주요 컬럼**:
  - `user_achievement_id`: 사용자 도전과제 ID (PK)
  - `user_id`: 사용자 ID (FK → users)
  - `achievement_id`: 도전과제 ID (FK → achievements)
  - `current_progress`: 현재 진행도
  - `is_completed`: 완료 여부
  - `completed_at`: 완료 시간
  - `created_at`: 시작 시간
- **제약조건**:
  - UNIQUE (user_id, achievement_id): 한 사용자는 한 도전과제를 한 번만 수행
- **관계**:
  - N:1 → users
  - N:1 → achievements

### 7. music_playback_log (음악 재생 로그)
- **용도**: 음악 재생 로그 기록
- **주요 컬럼**:
  - `playback_id`: 재생 로그 ID (PK)
  - `user_id`: 사용자 ID (FK → users)
  - `track_uri`: 트랙 URI
  - `track_name`: 트랙 이름
  - `artist_name`: 아티스트 이름
  - `genre`: 장르
  - `playback_duration`: 재생 시간 (초)
  - `created_at`: 재생 시간
- **관계**:
  - N:1 → users

---

## 외래키 관계 요약

| 부모 테이블 | 자식 테이블 | 관계 | 외래키 | 삭제 정책 |
|------------|------------|------|--------|----------|
| users | user_prediction | 1:1 | user_id | - |
| users | user_features | 1:1 | user_id | CASCADE |
| users | log | 1:N | user_id | CASCADE |
| users | music_playback_log | 1:N | user_id | CASCADE |
| users | user_achievements | 1:N | user_id | CASCADE |
| achievements | user_achievements | 1:N | achievement_id | CASCADE |
| achievements | users | 1:0..1 | selected_achievement_id | SET NULL |

---

## 인덱스 정보

### users
- PRIMARY KEY: user_id

### user_prediction
- PRIMARY KEY: user_id

### user_features
- PRIMARY KEY: user_id

### log
- PRIMARY KEY: log_id
- INDEX: idx_user_id
- INDEX: idx_action_type
- INDEX: idx_created_at

### achievements
- PRIMARY KEY: achievement_id
- INDEX: idx_achievement_type
- INDEX: idx_is_active

### user_achievements
- PRIMARY KEY: user_achievement_id
- UNIQUE: unique_user_achievement (user_id, achievement_id)
- INDEX: idx_user_id
- INDEX: idx_achievement_id
- INDEX: idx_is_completed

### music_playback_log
- PRIMARY KEY: playback_id
- INDEX: idx_user_id
- INDEX: idx_track_uri
- INDEX: idx_genre
- INDEX: idx_user_track (user_id, track_uri)
- INDEX: idx_user_genre (user_id, genre)
- INDEX: idx_created_at

---

## 테이블 생성 순서

외래키 제약조건을 고려한 테이블 생성 순서:

1. **users** (기본 테이블)
2. **achievements** (users의 selected_achievement_id FK를 위해 먼저 생성)
3. **user_prediction** (users 참조)
4. **user_features** (users 참조)
5. **log** (users 참조)
6. **music_playback_log** (users 참조)
7. **user_achievements** (users, achievements 참조)

---

## 데이터 흐름

### 이탈 예측 흐름
```
users + user_features → ML 모델 → user_prediction
```

### 도전과제 달성 흐름
```
music_playback_log → 도전과제 체크 → user_achievements 업데이트
```

### 사용자 활동 추적
```
사용자 활동 → log 테이블 기록
```

---
