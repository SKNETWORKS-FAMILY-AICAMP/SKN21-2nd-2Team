## <span style="color:green">SKN21-2nd-2Team</span>

<br>

# Spotipy 이탈 예측 어플리케이션 (Spotify Churn Prediction App)
<br>

<img src="image/스포티파이.svg" alt="프로젝트 로고" width="500">

<br><br><br>


## 📌 프로젝트 개요

<img src="image/spotify_naver.png" alt="네이버-스포티파이기사" width="600">
<img src="image/spotify_naver2.png" alt="사진" width="500">

<br>

국내 음악 스트리밍 시장에서 경쟁이 심화되면서, **고객 이탈(Churn)** 은 플랫폼의 수익성과 직결되는 핵심 문제가 되었습니다.
특히 Spotify는 최근 ‘Spotify Free’ 를 **한국 시장에 론칭하며 점유율 확대**를 적극적으로 추진하고 있어,
**잠재적 이탈 고객을 조기에 식별하고 유지 전략을 세우는 능력이 더욱 중요**해지고 있습니다.

<br>

<img src="image/spotifyfree.png" alt="사진" width="600">
<div style="display:flex; gap:20px; justify-content:center;">
  <img src="image/spotifyfree2.png" alt="사진" width="200">
  <img src="image/spotify추세.jpg" alt="사진" width="200">
  <img src="image/멜론잡겠다.jpg" alt="사진" width="200">
</div>

<br>

본 프로젝트는 Spotify 사용자 데이터를 기반으로,
사용자 행동 데이터를 분석하여 **이탈 가능성**을 예측하는 웹 어플리케이션을 개발하는 것을 목표로 합니다.
이를 통해 **마케팅/운영 팀은 다음과 같은 의사결정**을 **효과적**으로 수행할 수 있습니다.

<br>

- **🔍 위험 고객을 조기에 발견하여 맞춤형 리텐션 캠페인 실행**

- **📈 유료 전환/유지 가능성이 높은 고객군 식별**

- **📊 사용자 행동 패턴을 이해하고 서비스 개선 방향 수립**

<br>

본 시스템은 단순 예측을 넘어서,
파생 변수 기반의 **행동 인사이트 분석**(Engagement Score, Skip Behavior 등) 과
**시각화 기능**을 제공하여,
**Spotify 내부 팀이 보다 직관적으로 데이터 기반 결정을 내릴 수 있도록 지원**합니다.

<br><br><br>

<h2>👥 팀 구성 및 역할 분담</h2>
<p><strong>Team 역전파</strong></p>

<table>
<tr>
<td align="center" width="200" style="vertical-align: top; height: 300px;">
  <img src="image/강하다.jpg" width="210" height="210" style="border-radius: 50%; object-fit: cover;" alt="박수빈"/>
  <br />
  <h3 style="margin: 10px 0 5px 0;">박수빈</h3>
  <p style="margin: 5px 0;">총괄 | Streamlit + Integrator</p>
  <div style="margin-top: 10px;">
    <a href="https://github.com/sbpark2930-ui">
      <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>
    </a>
  </div>
</td>

<td align="center" width="200" style="vertical-align: top; height: 300px;">
<img src="image/피카츄.jpg" width="160" height="160" style="border-radius: 50%; object-fit: cover;" alt="신지용"/>
  <br />
<br />
<h3 style="margin: 10px 0 5px 0;">신지용</h3>
<p style="margin: 5px 0;">전처리 검증 + Feature튜닝</p>
<div style="margin-top: 10px;">
<a href="https://github.com/sjy361872">
<img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>
</a>
</div>
</td>
<td align="center" width="200" style="vertical-align: top; height: 300px;">
<img src="image/초롱이.jpg" width="170" height="170" style="border-radius: 50%; object-fit: cover;" alt="윤경은"/>
  <br />
<br />
<h3 style="margin: 10px 0 5px 0;">윤경은</h3>
<p style="margin: 5px 0;">데이터분석 + 파이프라인 설계</p>
<div style="margin-top: 10px;">
<a href="https://github.com/ykgstar37-lab">
<img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>
</a>
</div>
</td>
<td align="center" width="200" style="vertical-align: top; height: 300px;">
<img src="image/짱쎈고양이.jpg" width="180" height="180" style="border-radius: 50%; object-fit: cover;" alt="정세연"/>
<br />
<h3 style="margin: 10px 0 5px 0;">정세연</h3>
<p style="margin: 5px 0;">모델 템플릿제작 + Baseline 학습</p>
<div style="margin-top: 10px;">
<a href="https://github.com/wjdtpdus25">
<img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>
</a>
</div>
</td>
<td align="center" width="200" style="vertical-align: top; height: 300px;">
<img src="image/코카인.jpg" width="150" height="150" style="border-radius: 50%; object-fit: cover;" alt="박민정"/>
<br />
<h3 style="margin: 10px 0 5px 0;">박민정</h3>
<p style="margin: 5px 0;">pipeline 구현 담당</p>
<div style="margin-top: 10px;">
<a href="https://github.com/silentkit12">
<img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/>
</a>
</div>
</td>
</tr>
</table>


</div>


<br><br><br>
## 🛠 Tech Stack

### 🎛 Backend (API 서버)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![PyMySQL](https://img.shields.io/badge/PyMySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![bcrypt](https://img.shields.io/badge/bcrypt-3388FF?style=for-the-badge&logo=security&logoColor=white)

<br>

### 📊 Data Processing & Analysis
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)

<br>

### 📈 Data Visualization
![matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=plotly&logoColor=white)
![seaborn](https://img.shields.io/badge/Seaborn-4C72B0?style=for-the-badge&logo=python&logoColor=white)

<br>

### 💾 Model Saving / Utility
![joblib](https://img.shields.io/badge/joblib-4B8BBE?style=for-the-badge&logo=python&logoColor=white)





</div>
<br><br><br>


<div> 

<br>



### 📁 실제 폴더 구조
</div>

```plaintext
SKN21-2ND-2TEAM/
│
├── backend/                    # Flask API 서버
│   └── app.py
├── data/                       # 데이터 및 통계 파일
├── docs/                       # 파이프라인 설계 문서 및 참고 자료
├── frontend/                   # Streamlit UI
│   └── run_app.py
├── models/                     # 모델 및 학습 템플릿
├── notebooks/                  # EDA / 전처리 검증 노트북
│
├── requirements.txt            # 패키지 리스트
└── README.md                   # 프로젝트 설명 문서
```
<br>
<div> 

<br><br><br>


## 📊 1)  Data & Baseline Setup

- **데이터 구조**: 8,000명 유저, 유저당 1행 스냅샷 (수치형 6개 + 범주형 4개, 타깃 `is_churned`)
     ### 🔹 `Original Dataset` — 원본 피처 테이블
    | 컬럼명                   | 타입        | 설명               | 
    | --------------------- | --------- | ---------------- |
    | `user_id`              | INT       | 사용자 고유 ID        | 
    | `gender`                | VARCHAR   | 성별 (Male/Female) | 
    | `age`                   | INT       | 사용자 나이           | 
    | `country`               | VARCHAR   | 접속 국가            | 
    | `subscription_type`     | VARCHAR   | 요금제 종류           |
    | `listening_time`        | FLOAT     | 하루 음악 청취 시간(분)   | 
    | `songs_played_per_day`  | FLOAT     | 하루 재생 곡수         |
    | `skip_rate`             | FLOAT     | 스킵률              |
    | `device_type`           | VARCHAR   | 기기 종류            |
    | `ads_listened_per_week` | INT       | 주간 광고 시청 수       |
    | `offline_listening`     | INT (0/1) | 오프라인 재생 기능 여부    |
    | **`is_churned`**            | INT(0/1)  | 이탈 여부            |

<br>

- **초기 베이스라인** (`preprocessing_validation.ipynb`, `FE_validation.ipynb`):
  - 수치형 6개 + 핵심 FE 5개(engagement_score, songs_per_minute, skip_intensity, skip_rate_cap, ads_pressure) 조합(Set D)
     ### 🔹`Feature Engineering` — 파생 변수 테이블
    | 컬럼명                | 타입      | 설명                                |
    | --------------------- | --------- | ------------------------------------ |
    | `engagement_score`   | FLOAT   | listening_time × songs_played_per_day             |
    | `songs_per_minute` | FLOAT | songs_played_per_day / listening_time               |
    | `skip_intensity`     | FLOAT   | skip_rate × songs_played_per_day  |
    | `skip_rate_cap`         | FLOAT   | skip_rate.clip(0, 1.5) |
    | `ads_pressure`         | FLOAT   | ads_listened_per_week / listening_time |

  - **모델**: RandomForestClassifier(class_weight='balanced') + threshold 튜닝
  - **성능**: F1≈0.41, AUC≈0.54 수준에서 정체


<br>

## 🛠️ 2) Feature Engineering & Feature Selection 검증
- **FE 검증** (`FE_validation.ipynb`, `FE_add.ipynb`):
  - 여러 FE 세트(Set A~G) 및 추가 세그먼트/ratio/비선형 FE 후보를 실험
  - **결과**: 핵심 FE 4~5개만 남기는 것이 최선, 복잡한 교호작용·플래그를 더해도 성능 개선은 ΔF1≈0 수준
- **범주형 및 FS 검증** (`feature_selection.ipynb`):
  - `gender`, `country`, `subscription_type`, `device_type` 및 파생 범주형을 One-Hot 인코딩해 포함
  - 수치형+FE(10~11개) vs 수치형+FE+범주형(30개 이상) 비교 시 **오히려 F1/AUC 소폭 하락 → 범주형 기여도 낮음**

## 🎯 3) Model Tuning·SMOTE·앙상블 검증
- **모델/파라미터 튜닝** (`feature_selection.ipynb`):
  - RandomForest 하이퍼파라미터(RandomizedSearchCV), K-Fold + threshold 튜닝, 소프트보팅 앙상블(RF+XGB+HGB) 등 적용
  - **결과**: 어떤 조합도 F1 0.41±0.01, AUC 0.52~0.54 범위를 크게 넘지 못함
- **SMOTE + XGBoost + 앙상블** (`SMOTE_XGB_RF.ipynb`):
  - SMOTE(오버샘플링 비율·test_size·scale_pos_weight 등 여러 버전), XGBoost GridSearchCV, RF+XGB+HGB 앙상블 시도
  - **결과**: Train에서는 F1↑지만 Test에서는 Baseline보다 낮거나 비슷한 수준 → **심한 과적합 & 실질적 개선 실패**

## ⚠️ 4) Limitations & Root Cause Analysis(한계 원인 분석)
- **통계·상관·Feature Importance 분석** (`feature_selection.ipynb` 6장, `improvement_proposal.md`):
  - 모든 피처에서 t-test p-value>0.05, 상관계수 |r|<0.02 → 이탈/비이탈 간 행동 차이가 통계적으로 거의 없음
  - RF Feature Importance & Permutation Importance도 특정 피처가 두드러지지 않고 8~14% 수준으로 고르게 분산
- **결론**:
  - 현재 구조(유저당 1행 스냅샷 + 단일 시점 피처)에서는 **F1≈0.41, AUC≈0.53이 사실상 상한**
  - 모델 변경·튜닝·SMOTE만으로는 성능을 올리기 어렵고, **데이터/피처 자체를 바꾸는 방향이 필요**함


## 💡 5) 시계열·고객 접점 Features 추가 및 성능 향상
- **개선 아이디어 정리 (`improvement_proposal.md`)**:
  - Priority 1: 최근 7/14/30일 행동 변화를 담는 **시계열 피처 5개**
  - Priority 2: 고객센터 문의, 결제 실패, 프로모션 반응, 앱 크래시 등 **고객 접점 피처 4개**
     ### 🔹 `Time-Series Behavioral Trends` - 시계열features(5개)
      | 피처명 | 타입 | 설명 | 예상 기여도 |
      |--------|------|------|-------------|
      | `listening_time_trend_7d` | float | 최근 7일 청취 시간 변화율 (%) | 높음 |
      | `login_frequency_30d` | int | 최근 30일 로그인 횟수 | 높음 |
      | `days_since_last_login` | int | 마지막 로그인 후 경과 일수 | 높음 |
      | `skip_rate_increase_7d` | float | 최근 1주 vs 이전 1주 스킵률 증가율 | 중간 |
      | `freq_of_use_trend_14d` | float | 최근 2주 사용 빈도 변화율 (%) | 높음 |
     ### 🔹 `Customer Interaction Signalss` - 고객접점features(4개)
      | 피처명 | 타입 | 설명 | 예상 기여도 |
      |--------|------|------|-------------|
      | `customer_support_contact` | bool | 최근 30일 내 고객센터 문의 여부 | 중간 |
      | `payment_failure_count` | int | 결제 실패 횟수 | 높음 |
      | `promotional_email_click` | bool | 프로모션 이메일 클릭 여부 | 낮음 |
      | `app_crash_count_30d` | int | 최근 30일 앱 크래시 횟수 | 중간 |
  - 실제 로그 수집이 어려운 환경을 가정해, 위 피처들을 **현실적인 분포를 가진 합성 특성**으로 먼저 실험
- **합성 피처 생성 및 검증** (`feature_engineering_advanced.ipynb`):
  - 원본 베이스라인(수치형 6 + FE 5, 총 11개) 대비, **시계열 5개 + 고객 접점 4개**를 추가한 `enhanced_data.csv` 생성
  - RandomForest 기반 실험 결과:
    - Baseline: F1≈0.42, AUC≈0.54
    - +시계열 피처: F1≈0.49, AUC≈0.73
    - +시계열+고객접점(최종): **F1≈0.62, AUC≈0.79** (ΔF1 +0.20 이상, ΔAUC +0.25 이상)
  - **Feature Importance 기준 핵심 기여 피처**:
    - `payment_failure_count`, `app_crash_count_30d` (고객 접점)
    - `freq_of_use_trend_14d`, `listening_time_trend_7d`, `skip_rate_increase_7d` (시계열)

## 🧹 6) Preprocessing Pipeline Refinement


## 🧩 7) Final Summary & Key Takeaways


## 🏆 8) Final Model Comparison & Selection (HGB Selected)

### 🔹 DB Schema Overview
- **DBMS:** MySQL  
- **Driver:** PyMySQL  
- **사용 목적:**
  - 사용자 관리 (가입/로그인)
  - 예측 요청 기록 저장
  - 향후 개선을 위한 사용자 행동 로그 관리

<br>


<br>


<br>

##### 4) `Customer Interaction Signalss`
| 피처명 | 타입 | 설명 | 예상 기여도 |
|--------|------|------|-------------|
| `customer_support_contact` | bool | 최근 30일 내 고객센터 문의 여부 | 중간 |
| `payment_failure_count` | int | 결제 실패 횟수 | 높음 |
| `promotional_email_click` | bool | 프로모션 이메일 클릭 여부 | 낮음 |
| `app_crash_count_30d` | int | 최근 30일 앱 크래시 횟수 | 중간 |

<br><br><br>


## 💡 주요 기능 (Key Features)

본 프로젝트는 Spotify 사용자 행동 데이터를 기반으로  
**이탈 확률을 예측**하고, 이를 Streamlit UI를 통해 시각화하고 제공합니다.

<br>

### ⭐ 1. 사용자 입력 기반 이탈 예측
- 사용자가 직접 **listening_time, skip_rate, engagement_score, ads_pressure** 값을 입력
- Flask API 서버가 모델을 통해 **이탈 확률(Churn Probability)**을 계산
- "잔존 / 이탈" 여부를 즉시 제공

<br>

### 📊 2. 시각화 기반 데이터 확인
- 입력된 값에 따라 간단한 시각화를 제공
- 사용자 행동 변수들의 해석을 지원
- Feature 간 상관관계 및 churn 영향 확인 가능

<br>

### 📁 3. 전처리 파이프라인 자동 적용
- Train/Test 데이터와 동일한 전처리 흐름을 API에서 자동 적용
- 인코딩, 스케일링, Feature 변환이 일관되게 진행됨  
- 모델 입력 오류 방지

<br>

### 🤖 4. Baseline ML 모델 기반 예측
- Logistic Regression Baseline 모델 적용
- 전처리 + 학습 + 평가 흐름 자동화
- `.pkl`로 저장된 모델을 API에서 로드하여 실시간 예측

<br>

### 🗄️ 5. MySQL 사용자 관리 & 예측 이력 저장
- 회원가입 / 로그인 기능 지원
- bcrypt 기반 안전한 비밀번호 해싱
- 예측 요청 시 DB에 자동 저장:
  - 입력값 (listening_time, skip_rate 등)
  - 예측 결과(churn probability)
  - 요청 시간

<br>

### 🖥️ 6. Streamlit 기반 단일 페이지 UI
- 직관적이고 심플한 UI 구성
- 버튼 클릭만으로 예측 수행
- 온라인 서비스 형태와 유사한 구조

<br>

### 🔧 7. 팀 기반 구조화된 파이프라인
- 파트별 책임(데이터 분석 / 전처리 / 모델링 / UI / 통합)이 명확
- 실제 서비스 개발 과정과 유사한 협업 프로세스 구성


<br><br><br>

## 📝 팀원 소감 (Team Retrospective)
<br>

| 🧑‍💼 이름 | 🛠 역할 | 💬 소감 |
|-----------|-----------|-----------|
| **박수빈** | Frontend / PM / Integrator | 나는 짱쎄다 |
| **신지용** | Feature Engineer / QA | 울랄라 |
| **윤경은** | Data Lead / Pipeline | |
| **정세연** | ML Engineer / Modeling |  |
| **박민정** | Backend / Data Pipeline | |
