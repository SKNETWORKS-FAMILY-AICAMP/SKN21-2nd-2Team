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
사용자 행동 데이터를 분석하여 이탈 가능성을 예측하는 웹 어플리케이션을 개발하는 것을 목표로 합니다.
이를 통해 마케팅/운영 팀은 다음과 같은 의사결정을 효과적으로 수행할 수 있습니다.

<br>

**🔍 위험 고객을 조기에 발견하여 맞춤형 리텐션 캠페인 실행**

**📈 유료 전환/유지 가능성이 높은 고객군 식별**

**📊 사용자 행동 패턴을 이해하고 서비스 개선 방향 수립**

본 시스템은 단순 예측을 넘어서,
파생 변수 기반의 **행동 인사이트 분석**(Engagement Score, Skip Behavior 등) 과
시각화 기능을 제공하여,
Spotify 내부 팀이 보다 직관적으로 데이터 기반 결정을 내릴 수 있도록 지원합니다.
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

## 📁 Project Structure

본 프로젝트는 5인의 역할 분담을 통해 단계별로 **데이터 분석 → 전처리 → 모델링 → 서비스 UI**까지  
효율적으로 구축되었습니다. 아래는 각 역할 흐름을 기반으로 정리한 프로젝트 구조입니다.

<br>

### 🔹 1. 데이터 분석 & 파이프라인 설계  
**담당:** 데이터 분석 + 파이프라인 설계 리더  
**역할 요약:** 데이터 구조 파악 및 전체 전처리 설계

- 원본 데이터 구조 분석 (`info()`, `describe()`)
- 수치형/범주형 변수 파악
- Feature 사용/제거 기준 설정
- 스케일링/인코딩 방식 결정
- Feature Engineering 아이디어 제안
- **산출물:**  
  - `docs/pipeline_design.md`  
  - Feature 리스트 문서

<br>

### 🔹 2. 전처리 파이프라인 구현  
**담당:** 백엔드 + 파이프라인 구현  
**역할 요약:** 전처리를 실제 코드로 완성시키는 역할

- 결측치 처리, 인코딩, 스케일링 코드 구현
- Train/Test Split 함수화
- DataFrame → X, y 변환 함수 제작
- 최종 파이프라인 실행 함수 완성
- **산출물:**  
  - `preprocessing.py`  
  - `X_train.pkl`, `X_test.pkl`  
  - `y_train.pkl`, `y_test.pkl`

<br>

### 🔹 3. 전처리 검증 + Feature 튜닝  
**담당:** FE Engineer + QA  
**역할 요약:** 전처리 품질 검사 및 Feature 개선

- 전처리 파이프라인 품질 체크
- Feature 타당성 검증
- 성능 영향을 주는 변수 탐색
- 개선된 Feature 리스트 작성
- **산출물:**  
  - `preprocessing_validation.ipynb`  
  - FE 개선안 문서

<br>


### 🔹 4. 모델 템플릿 제작 + Baseline 학습  
**담당:** ML Engineer  
**역할 요약:** 모델링 구조를 잡고 베이스라인 모델 제작

- 공통 모델 템플릿 개발
- Logistic Regression 등 Baseline 학습
- 성능 평가 함수 제작
- 전체 팀이 공유할 수 있는 모델 구조 제공
- **산출물:**  
  - `train_template.py`  
  - `model_lr.pkl`

<br>

### 🔹 5. Streamlit UI 제작 + 최종 통합  
**담당:** Frontend + Integrator  
**역할 요약:** 최종 서비스를 UI로 구현하고 발표용으로 정리

- Streamlit 기반 UI 개발
- 최종 모델 로드 및 예측 기능 구현
- 모델 비교 후 최종 선정
- 발표 자료 / README.md 구성
- **산출물:**  
  - `frontend/run_app.py`  
  - 발표 자료  
  - `README.md`

<br><br><br>



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


## 🗄️ Database Structure

본 프로젝트는 Flask API 서버와 MySQL 데이터베이스를 연동하여  
사용자 로그인, 예측 기록 저장을 처리합니다.  
데이터베이스는 PyMySQL 기반으로 연결되며 아래와 같은 구조로 설계되었습니다.

<br>

### 🔹 DB Schema Overview
- **DBMS:** MySQL  
- **Driver:** PyMySQL  
- **사용 목적:**
  - 사용자 관리 (가입/로그인)
  - 예측 요청 기록 저장
  - 향후 개선을 위한 사용자 행동 로그 관리

<br>

### 🔹 주요 테이블 구조

#### 1) `Original Dataset` — 원본 피처 테이블
| 컬럼명                   | 타입        | 설명               | 
| --------------------- | --------- | ---------------- |
| user_id               | INT       | 사용자 고유 ID        | 
| gender                | VARCHAR   | 성별 (Male/Female) | 
| age                   | INT       | 사용자 나이           | 
| country               | VARCHAR   | 접속 국가            | 
| subscription_type     | VARCHAR   | 요금제 종류           |
| listening_time        | FLOAT     | 하루 음악 청취 시간(분)   | 
| songs_played_per_day  | FLOAT     | 하루 재생 곡수         |
| skip_rate             | FLOAT     | 스킵률              |
| device_type           | VARCHAR   | 기기 종류            |
| ads_listened_per_week | INT       | 주간 광고 시청 수       |
| offline_listening     | INT (0/1) | 오프라인 재생 기능 여부    |
| is_churned            | INT(0/1)  | 이탈 여부            |

<br>

#### 2) `Feature Engineering` — 파생 변수 테이블
| 컬럼명                | 타입      | 설명                                |
| --------------------- | --------- | ------------------------------------ |
| engagement_score   | FLOAT   | 청취시간 + 재생곡수 기반 참여도 지표             |
| listening_time_bin | VARCHAR | very_low ~ high 구간화               |
| skip_intensity     | FLOAT   | skip_rate × songs_played_per_day  |
| skip_index         | FLOAT   | songs_played / (skip_rate + 1e-5) |


<br>

#### 3) `Target Variable` 
| 컬럼명        | 타입       | 설명              |
| --------------------- | --------- | ------------------------------------ |
| is_churned | INT(0/1) | 1 = 이탈 / 0 = 유지 |


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
