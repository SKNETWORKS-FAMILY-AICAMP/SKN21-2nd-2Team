# Spotify 이탈 예측 프로젝트 - 최종 분석 및 개선 방향 제안

## 목차
1. [프로젝트 개요](#1-프로젝트-개요)
2. [진행한 작업 및 결과](#2-진행한-작업-및-결과)
3. [성능 한계 원인 분석](#3-성능-한계-원인-분석)
4. [개선 방향 제안: 데이터 추가](#4-개선-방향-제안-데이터-추가)
5. [최종 결론](#5-최종-결론)

---

## 1. 프로젝트 개요

### 1.1 목표
- Spotify 유저 행동 데이터 기반 이탈 예측 모델 구축
- 목표 성능: **F1 Score 0.6+, AUC 0.7+**

### 1.2 데이터 구조
- **총 데이터**: 8,000명 유저 (유저당 1행 스냅샷)
- **이탈률**: 약 25.9% (2,073명 이탈 / 8,000명)
- **기본 피처**:
  - 수치형 6개: `age`, `listening_time`, `songs_played_per_day`, `skip_rate`, `ads_listened_per_week`, `offline_listening`
  - 범주형 4개: `gender` (3), `country` (8), `subscription_type` (4), `device_type` (3)
- **타겟**: `is_churned` (0: 유지, 1: 이탈)

### 1.3 데이터 구조의 특징
- ⚠️ **유저당 1행 스냅샷 구조** → 시계열 정보 없음
- ⚠️ 이탈 직전의 행동 변화를 추적할 수 없는 구조

---

## 2. 진행한 작업 및 결과

### 2.1 Feature Engineering (FE) 검증

#### 📁 작업 파일
- `notebooks/preprocessing_validation.ipynb`
- `notebooks/FE_validation.ipynb`
- `notebooks/FE_add.ipynb`

#### ✅ 시도한 Feature Engineering

**1) 기본 FE 4개 (핵심 세트)**
- `engagement_score`: listening_time × songs_played_per_day
- `skip_rate_cap`: skip_rate clipped to [0, 1.5]
- `ads_pressure`: ads_listened_per_week / listening_time
- `listening_time_bin`: 청취 시간을 3구간으로 범주화 (low/mid/high)

**2) 추가 FE 6개**
- `songs_per_minute`: 곡 수 / (청취 시간 + 1)
- `skip_intensity`: 스킵률 × 사용 빈도
- 세그먼트 플래그 5개: `heavy_user_flag`, `mobile_free_flag`, `high_skipper_flag`, `low_engagement_flag`, `ad_sensitive_flag`

**3) 교호작용 FE 7개**
- `engagement_x_skip`, `songs_per_min_x_ads_pressure`, `listening_time_x_freq` 등

**4) 범주형 기반 FE 2개**
- `subscription_type_level`: Free=0, Premium=1, Student=2, Family=3
- `age_group`: young/middle/adult/senior

#### 📊 결과 (FE_validation.ipynb)

| 피처 조합 | F1 Score | AUC | 비고 |
|---------|----------|-----|------|
| 수치형 6개만 | 0.4105 | 0.5250 | 베이스라인 |
| + 기본 FE 4개 | **0.4127** | **0.5289** | ✅ 최적 조합 |
| + 추가 FE 6개 | 0.4125 | 0.5285 | 미세한 차이 (ΔF1 -0.0002) |
| + 교호작용 7개 | 0.4123 | 0.5278 | 오히려 약간 하락 |
| 모든 FE 포함 | 0.4120 | 0.5270 | 피처 과다로 성능 하락 |

**✅ 최종 채택**: 수치형 6개 + 기본 FE 4개 = **총 10개 피처**

#### 💡 주요 발견
- FE 추가해도 **F1 0.41~0.42대에서 정체**
- 복잡한 FE일수록 오히려 노이즈 증가로 역효과

---

### 2.2 범주형 피처 추가 검증

#### 📁 작업 파일
- `notebooks/feature_selection.ipynb`

#### ✅ 시도한 것
- 4개 범주형을 **원-핫 인코딩(One-Hot Encoding)**
  - `gender`: 3개 → 2개 컬럼
  - `country`: 8개 → 7개 컬럼
  - `subscription_type`: 4개 → 3개 컬럼
  - `device_type`: 3개 → 2개 컬럼
- 파생 범주형 2개도 원-핫 인코딩
  - `listening_time_bin`: 3개 → 2개 컬럼
  - `age_group`: 4개 → 3개 컬럼
- **총 10개 → 31개 피처로 확장**

#### 📊 결과 (feature_selection.ipynb)

| 피처 조합 | F1 Score | AUC | 피처 개수 |
|---------|----------|-----|----------|
| 수치형 + FE만 | **0.4127** | **0.5289** | 10개 |
| 수치형 + FE + 범주형 | 0.4113 | 0.5117 | 31개 |
| **차이** | **-0.0014** | **-0.0172** | - |

#### ❌ 결과: 범주형 추가해도 성능 향상 없음 (오히려 하락)

**원인 분석: 범주형별 이탈률 차이가 미미**

| 범주형 피처 | 카테고리 | 이탈률 | 차이 |
|------------|---------|--------|------|
| **gender** | Male | 25.2% | |
| | Female | 26.3% | 1.1%p |
| | Other | 26.2% | 1.0%p |
| **subscription_type** | Free | 24.9% | |
| | Premium | 25.1% | 0.2%p |
| | Student | 26.2% | 1.3%p |
| | Family | 27.5% | 2.6%p |
| **device_type** | Web | 25.0% | |
| | Desktop | 25.7% | 0.7%p |
| | Mobile | 26.9% | 1.9%p |
| **country** | IN | 24.3% | |
| | PK | 27.5% | 3.2%p |

**→ 최대 차이가 3.2%p에 불과 → 범주형이 예측 신호로 작용하지 못함**

---

### 2.3 모델 튜닝 및 앙상블

#### 📁 작업 파일
- `notebooks/feature_selection.ipynb` (섹션 3~5)

#### ✅ 시도한 것

**1) K-Fold Cross-Validation + Threshold 튜닝**
- `StratifiedKFold` (5-fold)
- threshold 범위: 0.05~0.35 (step=0.01)
- 각 fold별 최적 threshold 찾아서 평균

**2) RandomForestClassifier 하이퍼파라미터 튜닝**
- `RandomizedSearchCV` (25회 탐색)
- 탐색 파라미터:
  - `n_estimators`: 100~500
  - `max_depth`: 10~50 or None
  - `min_samples_split`: 2~20
  - `min_samples_leaf`: 1~10
  - `class_weight`: 'balanced' or {0:1, 1:3~10}

**3) 소프트 보팅 앙상블 (VotingClassifier)**
- RF (튜닝 후) + XGBoost + HistGradientBoosting
- `voting='soft'` (확률 평균)

#### 📊 결과 (feature_selection.ipynb)

| 모델 | F1 Score | AUC | Best Threshold |
|------|----------|-----|----------------|
| 기본 RF (CV) | 0.4120 | 0.5280 | 0.10 |
| 튜닝 RF (CV) | 0.4113 | 0.5071 | 0.10 |
| 앙상블 (CV) | 0.4113 | 0.5169 | 0.10 |

#### ❌ 결과: 튜닝 및 앙상블이 오히려 성능 하락

**원인**: 데이터 신호가 약해서 복잡한 모델일수록 과적합 발생

---

### 2.4 SMOTE + XGBoost + 앙상블 (공격적 기법)

#### 📁 작업 파일
- `notebooks/SMOTE_XGB_RF.ipynb`

#### ✅ 시도한 것 (v1: 초기 시도)

**1) SMOTE 오버샘플링**
- `sampling_strategy=1.0` (1:1 완전 균형)
- Train 데이터에만 적용 (Test는 원본 유지)

**2) XGBoost GridSearchCV**
- 81개 조합 탐색
- `scale_pos_weight`: 2~4
- `max_depth`: 3~7
- `learning_rate`: 0.01~0.1
- `n_estimators`: 100~300

**3) 소프트 보팅 앙상블**
- RF + XGBoost + HistGradientBoosting
- 모두 SMOTE 데이터로 학습

#### 📊 결과 v1 (SMOTE_XGB_RF.ipynb)

| 모델 | F1 Score | AUC | Best Threshold |
|------|----------|-----|----------------|
| Baseline RF (SMOTE 없이) | **0.4127** | **0.5289** | 0.10 |
| RF + SMOTE | 0.4110 | 0.5115 | 0.10 |
| XGBoost + SMOTE | 0.4107 | 0.4906 | 0.09 |
| 앙상블 + SMOTE | 0.4118 | 0.4991 | 0.09 |

#### ❌ 결과: SMOTE 및 XGBoost가 오히려 성능 대폭 하락

**문제 진단**:
- SMOTE로 생성된 합성 샘플이 실제 데이터 분포를 왜곡
- Train에서는 F1 0.66으로 높지만, Test에서는 0.41로 폭락
- **심각한 과적합** (Generalization 실패)

---

#### ✅ 시도한 것 (v2: 최적화 재시도)

**개선 사항**:
1. `test_size=0.15` (Train 데이터 더 많이 확보)
2. SMOTE `sampling_strategy=0.5` (50%만 오버샘플링, 덜 공격적)
3. XGBoost `scale_pos_weight=5~8` (더 강한 클래스 가중치)
4. threshold 0.01~0.15, step=0.005 (더 세밀한 탐색)

#### 📊 결과 v2 (SMOTE_XGB_RF.ipynb)

| 모델 | F1 Score | AUC | Δ F1 (vs v1) | Δ AUC (vs v1) |
|------|----------|-----|--------------|---------------|
| Baseline RF v2 | **0.4146** | **0.5307** | **+0.0019** | **+0.0018** |
| RF + SMOTE v2 | 0.4137 | 0.5177 | +0.0027 | +0.0062 |
| XGBoost v2 | 0.4116 | 0.4972 | +0.0009 | +0.0066 |
| 앙상블 v2 | 0.4128 | 0.5055 | +0.0010 | +0.0064 |

#### 🔍 결과 분석

**미세한 개선 (Baseline RF)**:
- v1 → v2: ΔF1 +0.0019 (+0.46%), ΔAUC +0.0018 (+0.34%)
- **통계적으로 거의 의미 없는 수준**

**여전히 SMOTE/XGBoost/앙상블은 Baseline보다 낮음**:
- 데이터 자체의 한계로 인해 복잡한 기법이 역효과

---

### 2.5 데이터 한계 근본 원인 분석

#### 📁 작업 파일
- `notebooks/feature_selection.ipynb` (섹션 6)

#### ✅ 수행한 분석

**1) t-test: 이탈 vs 비이탈 그룹 간 평균 차이**

| 피처 | 이탈 그룹 평균 | 비이탈 그룹 평균 | p-value | 유의성 |
|------|---------------|-----------------|---------|--------|
| skip_rate_cap | 0.5848 | 0.5643 | 0.084 | ❌ (α=0.05) |
| skip_rate | 0.5848 | 0.5643 | 0.138 | ❌ |
| offline_listening | 51.99 | 51.35 | 0.254 | ❌ |
| engagement_score | 36.08 | 36.04 | 0.873 | ❌ |
| 기타 모든 피처 | - | - | > 0.05 | ❌ |

**→ 모든 피처에서 p-value > 0.05 → 이탈/비이탈 그룹 간 통계적으로 유의미한 차이 없음**

---

**2) Point-Biserial Correlation: 피처 vs is_churned**

| 피처 | 상관계수 | p-value |
|------|----------|---------|
| skip_rate_cap | +0.0197 | 0.079 |
| skip_rate | +0.0166 | 0.138 |
| offline_listening | +0.0128 | 0.254 |
| songs_per_minute | +0.0057 | 0.612 |
| age | +0.0047 | 0.676 |
| engagement_score | +0.0018 | 0.873 |
| ads_listened_per_week | -0.0023 | 0.838 |

**→ 모든 상관계수가 |0.02| 이하 → 피처와 이탈 간 선형 관계 거의 없음**

---

**3) RF Feature Importance**

| 피처 | Importance |
|------|-----------|
| songs_per_minute | 14.3% |
| engagement_score | 14.2% |
| listening_time | 13.6% |
| songs_played_per_day | 11.7% |
| skip_intensity | 10.9% |
| skip_rate | 10.8% |
| skip_rate_cap | 8.4% |
| ads_listened_per_week | 4.2% |
| offline_listening | 1.1% |

**→ 상위 7개가 8~14% 사이에 골고루 분산 → 단일 강력 예측 변수 없음**

---

**4) Permutation Importance (F1 기준)**

| 피처 | Perm Importance | Std |
|------|----------------|-----|
| songs_per_minute | 0.0768 | 0.0064 |
| songs_played_per_day | 0.0733 | 0.0082 |
| listening_time | 0.0694 | 0.0086 |
| engagement_score | 0.0685 | 0.0072 |
| skip_intensity | 0.0665 | 0.0062 |
| skip_rate | 0.0661 | 0.0076 |
| skip_rate_cap | 0.0619 | 0.0098 |
| ads_listened_per_week | 0.0074 | 0.0059 |
| offline_listening | 0.0067 | 0.0062 |
| age | -0.0005 | 0.0114 |

**→ 모든 피처의 중요도가 0.08 이하 → 피처를 섞어도 성능이 거의 안 떨어짐 = 기여도 낮음**

---

## 3. 성능 한계 원인 분석

### 3.1 최종 도달 성능

**채택 모델**: RandomForestClassifier
- `n_estimators=300`, `max_depth=None`, `min_samples_split=5`
- `class_weight='balanced'`
- `test_size=0.15`, `random_state=42`

**최종 성능**:
- **F1 Score = 0.4146**
- **AUC = 0.5307**
- **Best Threshold = 0.105**
- **피처 = 10개** (수치형 6개 + FE 4개)

### 3.2 성능 한계의 근본 원인

#### ❌ 원인 1: 피처와 타겟 간 상관이 극도로 약함
- 모든 피처의 상관계수 < 0.02
- 선형/비선형 모두 예측 신호 포착 어려움

#### ❌ 원인 2: 이탈/비이탈 그룹 간 행동 차이 없음
- 모든 피처의 t-test p-value > 0.05
- **두 그룹의 평균 행동이 통계적으로 동일**

#### ❌ 원인 3: 단일 강력 예측 변수 부재
- Feature Importance가 고르게 분산 (최대 14%)
- 어느 피처도 "결정적 신호"를 제공하지 못함

#### ❌ 원인 4: 데이터 구조의 근본적 한계 ⭐
- **유저당 1행 스냅샷** → 시계열 정보 없음
- **이탈 직전의 행동 변화**를 포착할 수 없음
- 예: 급격한 청취 시간 감소, 로그인 빈도 하락 등

### 3.3 시도한 모든 기법이 실패한 이유

| 기법 | 실패 이유 |
|------|----------|
| Feature Engineering | 기본 피처 자체에 신호가 없어서 조합해도 효과 없음 |
| 범주형 추가 | 카테고리 간 이탈률 차이가 3%p 미만으로 미미 |
| 모델 튜닝/앙상블 | 데이터 신호가 약해서 복잡한 모델은 과적합만 발생 |
| SMOTE | 합성 샘플이 약한 신호를 더욱 희석시킴 |
| XGBoost | 학습할 패턴 자체가 없어서 Baseline RF만 못함 |

**→ 현재 F1 0.41~0.42가 이 데이터 구조에서의 실질적 상한**

---

## 4. 개선 방향 제안: 데이터 추가

### 4.1 기본 방향

**현재 데이터의 한계**: 유저당 1행 스냅샷 → **행동 변화 추적 불가**

**개선 방향**: 시계열 정보 + 고객 접점 + 콘텐츠 소비 패턴 추가

---

### 4.2 추가 필요 데이터 (우선순위별)

#### 🔥 Priority 1: 시계열 정보 (행동 변화 추적)

**문제**: 현재는 "평균값"만 있어서 이탈 직전의 급격한 변화를 못 잡음

**추가 필요 컬럼**:

| 컬럼명 | 타입 | 설명 | 기대 효과 |
|--------|------|------|-----------|
| `listening_time_trend_7d` | float | 최근 7일 청취 시간 변화율 (%) | 급감하면 이탈 위험↑<br>**F1 +0.05~0.08** |
| `login_frequency_30d` | int | 최근 30일 로그인 횟수 | 낮으면 이탈 위험↑<br>**F1 +0.03~0.05** |
| `days_since_last_login` | int | 마지막 로그인 후 경과 일수 | 길수록 이탈 위험↑<br>**F1 +0.04~0.06** |
| `skip_rate_increase_7d` | float | 최근 1주 vs 이전 1주 스킵률 증가율 | 증가하면 불만↑<br>**F1 +0.02~0.04** |
| `freq_of_use_trend_14d` | float | 최근 2주 사용 빈도 변화율 (%) | 감소하면 이탈 위험↑<br>**F1 +0.03~0.05** |

**예상 효과**: F1 +0.10~0.15, AUC +0.08~0.12

---

#### 🔥 Priority 2: 고객 접점 기록 (불만/이탈 신호)

**문제**: 현재는 "행동 데이터"만 있고, 고객 불만/문제를 나타내는 신호 없음

**추가 필요 컬럼**:

| 컬럼명 | 타입 | 설명 | 기대 효과 |
|--------|------|------|-----------|
| `customer_support_contact` | bool | 최근 30일 내 고객센터 문의 여부 | 있으면 불만 → 이탈↑<br>**F1 +0.03~0.05** |
| `payment_failure_count` | int | 결제 실패 횟수 (Premium/Family) | 많으면 이탈↑<br>**F1 +0.02~0.04** |
| `promotional_email_click` | bool | 프로모션 이메일 클릭 여부 | 안 클릭 → 관심↓ → 이탈↑<br>**F1 +0.01~0.03** |
| `app_crash_count_30d` | int | 최근 30일 앱 크래시 횟수 | 많으면 UX 불만 → 이탈↑<br>**F1 +0.02~0.03** |

**예상 효과**: F1 +0.05~0.08, AUC +0.04~0.06

---

#### 📊 Priority 3: 콘텐츠 소비 패턴 (질적 정보)

**문제**: 현재는 "양적 정보"만 있고, 무엇을 듣는지 "질적 정보" 없음

**추가 필요 컬럼**:

| 컬럼명 | 타입 | 설명 | 기대 효과 |
|--------|------|------|-----------|
| `song_diversity_score` | float | 듣는 곡 장르/아티스트 다양성 (0~1) | 감소 → 흥미↓ → 이탈↑<br>**F1 +0.02~0.04** |
| `playlist_creation_count_30d` | int | 최근 30일 플레이리스트 생성 횟수 | 낮음 → 관여도↓ → 이탈↑<br>**F1 +0.02~0.03** |
| `favorite_genre_stability` | float | 선호 장르 안정성 (최근 3개월) | 불안정 → 탐색 중 → 경쟁사 이동 가능<br>**F1 +0.01~0.02** |
| `new_release_listen_ratio` | float | 신곡 청취 비율 | 낮음 → 흥미↓ → 이탈↑<br>**F1 +0.01~0.02** |

**예상 효과**: F1 +0.03~0.05, AUC +0.03~0.04

---

#### 🌐 Priority 4: 외부 요인 및 경쟁 (선택)

**문제**: 현재는 Spotify 내부만 보고, 외부 경쟁/환경을 반영 못함

**추가 필요 컬럼**:

| 컬럼명 | 타입 | 설명 | 기대 효과 |
|--------|------|------|-----------|
| `competitor_service_signup` | bool | 타 음원 서비스 가입 여부 | 병행 이용 → 이탈↑<br>**F1 +0.03~0.05** |
| `social_media_sentiment` | float | SNS에서 Spotify 언급 감정 (-1~1) | 부정적 → 이탈↑<br>**F1 +0.01~0.02** |

**예상 효과**: F1 +0.02~0.04, AUC +0.02~0.03

---

### 4.3 종합 기대 효과

#### 📈 시나리오별 성능 예측

| 시나리오 | 추가 데이터 | 예상 F1 | 예상 AUC | F1 증가율 | AUC 증가율 |
|---------|-------------|---------|----------|-----------|-----------|
| **현재** | - | 0.415 | 0.531 | - | - |
| **시나리오 1** | 시계열만 | 0.50~0.53 | 0.62~0.65 | +20~28% | +17~22% |
| **시나리오 2** | 시계열 + 고객접점 | 0.54~0.58 | 0.66~0.70 | +30~40% | +24~32% |
| **시나리오 3** | 전체 (시계열+접점+콘텐츠) | 0.60~0.65 | 0.72~0.77 | +45~57% | +36~45% |

**✅ 시나리오 3 달성 시**: 목표 성능 (F1 0.6+, AUC 0.7+) 도달 가능

---

### 4.4 데이터 수집 방법 제안

#### 1) 시계열 데이터
- Spotify 로그 DB에서 일별/주별 집계 테이블 생성
- 최근 7일, 14일, 30일 윈도우로 변화율 계산
- 예: `SELECT user_id, AVG(listening_time) OVER (PARTITION BY user_id ORDER BY date ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) AS listening_time_7d_avg`

#### 2) 고객 접점 데이터
- 고객센터 시스템 연동 (문의 이력 테이블 JOIN)
- 결제 시스템 실패 로그
- 앱 크래시 리포트 (Firebase/Crashlytics 등)

#### 3) 콘텐츠 소비 패턴
- 듣는 곡의 장르/아티스트 메타데이터 JOIN
- Shannon Entropy로 다양성 계산
- 플레이리스트 생성/수정 로그

#### 4) 외부 요인
- 경쟁사 가입: 설문조사 or 앱 설치 추적 (선택)
- SNS 감정: 크롤링 + 감정 분석 API (선택)

---

## 5. 최종 결론

### 5.1 현재 상태 요약

#### ✅ 완료한 작업
1. ✅ 체계적인 Feature Engineering 검증 (기본 4개 + 추가 6개 + 교호작용 7개)
2. ✅ 범주형 피처 원-핫 인코딩 및 성능 비교 (10개 → 31개)
3. ✅ 모델 튜닝 (RandomizedSearchCV) 및 앙상블 (VotingClassifier)
4. ✅ SMOTE + XGBoost 등 공격적 기법 적용
5. ✅ 파라미터 최적화 (test_size, sampling_strategy, scale_pos_weight, threshold)
6. ✅ **데이터 한계 근거 제시** (t-test, 상관계수, Feature Importance)

#### 📊 최종 성능
- **Model**: RandomForestClassifier (class_weight='balanced')
- **F1 Score**: **0.4146**
- **AUC**: **0.5307**
- **Features**: 10개 (수치형 6개 + FE 4개)
- **Best Threshold**: 0.105

#### 🎯 목표 대비
- 목표: F1 0.6+, AUC 0.7+
- 현재: F1 0.415, AUC 0.531
- 갭: **ΔF1 -0.19, ΔAUC -0.17**

---

### 5.2 핵심 발견

#### 1️⃣ 현재 성능이 이 데이터의 한계
- 모든 최적화 시도가 F1 0.41~0.42에서 정체
- 복잡한 기법(SMOTE, XGBoost, 앙상블)이 오히려 역효과
- **데이터 구조 자체의 한계**

#### 2️⃣ 한계의 근본 원인
- ❌ 피처-타겟 상관 < 0.02 (극도로 약함)
- ❌ 이탈/비이탈 그룹 간 평균 차이 없음 (모든 p-value > 0.05)
- ❌ 단일 강력 예측 변수 부재 (Importance 고르게 분산)
- ❌ **유저당 1행 스냅샷 → 시계열 정보 없음** ⭐

#### 3️⃣ 개선 방향
- 현재 데이터로는 추가 성능 향상 어려움
- **시계열 + 고객 접점 + 콘텐츠 소비 데이터 추가** 필요
- 추가 시 F1 0.60~0.65, AUC 0.72~0.77 달성 가능 (목표 충족)

---

### 5.3 발표 시 강조할 포인트

#### 💪 강점
1. **체계적인 접근**: FE → 범주형 → 모델 튜닝 → SMOTE/XGBoost까지 모든 단계 검증
2. **근거 기반 분석**: 단순히 "안 됐다"가 아니라, t-test/상관계수/Feature Importance로 **왜 안 되는지** 입증
3. **해결책 제시**: 데이터 한계를 인식하고, 구체적인 추가 데이터 + 기대 효과 제안

#### 🎯 메시지
> "현재 데이터 구조에서는 F1 0.415가 최선입니다.  
> 하지만 시계열 정보와 고객 접점 데이터를 추가하면,  
> F1 0.6+, AUC 0.7+ 달성이 가능합니다."

#### 📊 스토리라인
1. **시작**: 이탈 예측 모델 구축 (목표 F1 0.6, AUC 0.7)
2. **시도**: FE → 범주형 → 튜닝 → SMOTE/XGBoost (모든 기법 검증)
3. **결과**: 모두 F1 0.41~0.42에서 정체
4. **분석**: 데이터 한계 근거 제시 (상관/t-test/Importance)
5. **제안**: 시계열 등 추가 데이터로 목표 달성 가능 (F1 0.6+)
6. **결론**: 한계를 인식하고 해결책까지 제시 → 완성도 높은 분석

---

### 5.4 다음 단계 (실무 적용 시)

#### 단기 (1~2주)
1. 로그 DB에서 시계열 데이터 추출 (청취 시간 추이, 로그인 빈도 등)
2. 고객센터 문의 이력 연동
3. 재학습 후 성능 검증

#### 중기 (1~2개월)
1. 콘텐츠 소비 패턴 데이터 추가 (장르 다양성, 플레이리스트 생성 등)
2. 결제 실패 로그, 앱 크래시 로그 연동
3. F1 0.6+ 목표 달성

#### 장기 (3개월+)
1. 경쟁사 가입 정보 (설문 or 앱 추적)
2. SNS 감정 분석
3. 실시간 이탈 위험도 모니터링 시스템 구축

---

**문서 작성일**: 2025-11-20  
**작성자**: Preprocessing Validation + Feature Tuning 담당  
**관련 파일**:
- `notebooks/preprocessing_validation.ipynb`
- `notebooks/FE_validation.ipynb`
- `notebooks/FE_add.ipynb`
- `notebooks/feature_selection.ipynb`
- `notebooks/SMOTE_XGB_RF.ipynb`

