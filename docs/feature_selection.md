📄 Feature Selection 문서 (Churn Prediction)

작성자: 정세연  
작성일: 2025-11-20  


---

## 📌 0. 요약

### Feature 구성 (Raw + Engineered)

| 구분 | 개수 | Features |
|------|------|----------|
| **Raw Numeric** | 6개 | age, listening_time, songs_played_per_day, skip_rate, ads_listened_per_week, offline_listening |
| **Raw Categorical** | 4개 | gender, country, subscription_type, device_type |
| **Engineered** | 8개 | engagement_score, songs_per_minute, skip_intensity, ads_pressure, skip_rate_cap, listening_time_bin, age_group, subscription_type_level |
| **Target** | 1개 | is_churned |
| **총 입력 Feature** | **18개** | Raw 10개 + Engineered 8개 |

### 제외/보류 Feature

| 구분 | Features |
|------|----------|
| **완전 제외** | user_id, Name, Password |
| **원본 제외 (파생 고려)** | JoinDate, ModifyDate |
| **보류 (추가 분석 필요)** | Favorite_Music, Grade |

---

## 1. 목적

고객 이탈(churn) 여부(`is_churned`)를 예측하는 모델을 위해:

- 원본 컬럼 중 어떤 것을 **직접 feature로 사용할지**
- 어떤 컬럼은 **전처리/파생 변수(Feature Engineering)를 통해 가공해서 사용할지**
- 어떤 컬럼은 **사용하지 않을지** 를 정리한 문서입니다

---

## 2. 데이터 구조 요약

### 2.1 기본 정보

- **총 레코드**: 8,000
- **총 컬럼**: 12
- **타깃 변수**: `is_churned` (0/1)  

### 2.2 변수 유형

- **범주형(Categorical)**:  
  `gender`, `country`, `subscription_type`, `device_type`
- **수치형(Numeric)**:  
  `age`, `listening_time`, `songs_played_per_day`, `skip_rate`, `ads_listened_per_week`, `offline_listening`
- **ID 컬럼**:  
  `user_id` (모델 학습에서 제외)

---

## 3. 모델링 및 전처리 전제

- **기본 모델 가정**: Tree-based 모델 (CatBoost, LightGBM, XGBoost 등)  
- **범주형 처리**: One-Hot Encoding 또는 Target Encoding (특히 `subscription_type`, `device_type`)  
- **수치형 처리**: Median Impute + Winsorizing (이상치 처리) 중심  
- **스케일링**: Tree 계열에서는 필수가 아니므로 **옵션**으로 처리  
- **전처리 파이프라인**: train/test에 동일하게 적용 가능한 함수/클래스 형태로 구현 예정

---

## 4. Target

### `is_churned`
- **정의**: 고객 이탈(churn) 여부 (1: 이탈, 0: 유지)
- **역할**: Binary Classification 타깃 변수

---

## 5. Raw Feature 선택

### 5.1 Numeric – 사용

| Feature | 설명 | 전처리 전략 & 근거 |
|---------|------|-------------------|
| `age` | 사용자 나이 | 그대로 사용 또는 `age_group` 파생 변수로 활용. 세대별 이탈(churn) 차이 반영 가능 |
| `listening_time` | 기간 내 총 청취 시간 | **결측치 → median 대체** 필요. 서비스 몰입도 반영. 일부 구간화(binning) 후보 |
| `songs_played_per_day` | 하루 평균 재생 곡 수 | **결측치 → median 대체** 필요. 활동량/빈도 지표 |
| `skip_rate` | 전체 재생 중 스킵 비율 | **상단값 cap** (예: 1.5 이하로 제한). 콘텐츠 피로도/불만의 직접 지표 |
| `ads_listened_per_week` | 주간 광고 청취 횟수 | **상위 percentile 기반 윈저라이징**. 광고 피로도와 이탈(churn) 관련 |
| `offline_listening` | 오프라인 재생 횟수 | 그대로 사용. **EDA 결과**: offline 사용 유저 이탈률 차이 존재 |

> ※ `listening_time`, `songs_played_per_day`는 **결측치가 존재**하므로 median 기반 Impute를 기본으로 한다.  

---

### 5.2 Categorical – 사용

| Feature | 설명 | 전처리 전략 & 근거 |
|---------|------|-------------------|
| `gender` | 사용자 성별 | One-Hot 또는 단순 category 인코딩. 이탈(churn) 차이 일부 존재 가능 |
| `country` | 국가 코드 | **Top-5 + 나머지(Other)로 그룹화** 후 인코딩. 국가별 churn_rate 차이 반영 (cardinality 관리) |
| `subscription_type` | Free/Family/Premium/Student 등 | One-Hot + `subscription_type_level` 파생 변수. **EDA 결과**: Family 플랜 이탈률 가장 높음 |
| `device_type` | Desktop/Web/Mobile 등 사용 기기 | One-Hot Encoding. **EDA 결과**: Mobile 중심 사용자 이탈률이 더 높음 |

---

## 6. Feature Engineering (파이프라인 설계 기반)

파이프라인 설계에서 제안된 파생 변수(Feature Engineering) 아이디어를 정리하면 다음과 같다.

### 6.1 수치형 결합/비율 기반

#### 1. `engagement_score`
- **정의**: `listening_time × songs_played_per_day`  
- **의미**: 얼마나 자주, 얼마나 오래 사용하는지를 곱으로 표현한 "참여도 강도"  
- **기대 효과**: 단일 변수보다 이탈(churn)과 더 강한 상관관계 형성 기대

#### 2. `songs_per_minute`
- **정의**: `songs_played_per_day / (listening_time + 1)`  
- **의미**: 단위 시간당 재생 곡 수 (짧게 많이 듣는지, 길게 듣는지 패턴 반영)  
- **※ 주의**: `listening_time`이 0인 경우를 방지하기 위해 분모에 +1 처리

#### 3. `skip_intensity`
- **정의**: `skip_rate × songs_played_per_day`  
- **의미**: 단순 비율이 아니라, 실제 "스킵 행동량"을 반영하는 지표  

#### 4. `ads_pressure`
- **정의**: `ads_listened_per_week / (listening_time + 1)`  
- **의미**: 청취 시간 대비 광고 노출 강도 (광고 피로도)
- **※ 주의**: `listening_time`이 0인 경우를 방지하기 위해 분모에 +1 처리

---

### 6.2 변환/캡핑/구간화

#### 5. `skip_rate_cap`
- **정의**: `skip_rate`를 상한값(예: 1.5)으로 cap 처리  
- **목적**: 극단적인 스킵 비율 값(5 이상 등)로 인한 학습 왜곡 방지

#### 6. `listening_time_bin`
- **정의**: listening_time을 low / mid / high 구간으로 binning  
- **목적**: 트리 모델에서 구간별 규칙 학습을 돕고, 해석력 향상

---

### 6.3 범주형 레벨링/세분화

#### 7. `age_group`
- **정의**: 나이를 구간(예: 10대/20대/30대/40대+ 혹은 MZ/GenX 등)으로 그룹화  
- **목적**: 세대/연령대별 이탈(churn) 패턴을 쉽게 학습·해석

#### 8. `subscription_type_level`
- **정의**: subscription_type을 **이탈 위험도 점수**로 매핑  
- **매핑 규칙**: 높을수록 이탈 위험 높음
  - Family = 3 (이탈률 가장 높음)
  - Premium = 2
  - Student = 1  
  - Free = 0 (이탈률 가장 낮음)
- **근거**: EDA 결과 Family > Premium > Student > Free 순으로 이탈률이 높았음  
- **목적**: 모델이 요금제 간 상대적 위험도를 쉽게 학습하도록 지원

---

## 7. 사용하지 않는 Feature
### 7.1 완전 제외

| Feature | 이유 |
|---------|------|
| `user_id` | 순수 식별자. 예측 정보 없음, 과적합 위험만 증가 |
| `Name` | 개인정보. 모델에 불필요 + 프라이버시 이슈 |
| `Password` | 보안 정보. 절대 학습에 사용해서는 안 됨 |

---

### 7.2 원본 상태로는 사용하지 않고, 파생만 고려

| Feature | 상태 | 이유 |
|---------|------|------|
| `JoinDate` | 원본 제외 | 날짜 raw 값 자체는 의미 약하고 noise 큼. 향후 `days_since_join` 등으로 변환 시 사용 고려 |
| `ModifyDate` | 원본 제외 | 마지막 활동일 정보는 유의미하나, raw date 대신 `days_since_modify` 등 파생 변수 필요 |

> **⚠️ 중요:**  
> **JoinDate/ModifyDate 기반 파생 변수는 아직 구현 전**이므로,  
> template 상에서는 제외하되, 추후 EDA/FE에서 확장 여지로 남겨둔다.

---

### 7.3 보류 (추가 해석/전처리 후 재검토)

| Feature | 이유 |
|---------|------|
| `Favorite_Music` | high cardinality 가능. 장르/카테고리 수준으로 가공 필요 |
| `Grade` | 등급의 정의/스케일이 명확하지 않음. 분포 및 의미 확인 후 포함 여부 결정 |

---

## 8. train_template.py / preprocess_data()와의 연결

### 8.1 확정 사용하는 Features

#### Raw Features (10개)
- **Numeric**: `age`, `listening_time`, `songs_played_per_day`, `skip_rate`, `ads_listened_per_week`, `offline_listening`
- **Categorical**: `gender`, `country`, `subscription_type`, `device_type`

#### Engineered Features (8개)
- `engagement_score`, `songs_per_minute`, `skip_intensity`, `ads_pressure`
- `skip_rate_cap`, `listening_time_bin`, `age_group`, `subscription_type_level`

#### Target (1개)
- `is_churned`

**총 18개 입력 Feature 사용**

---

### 8.2 preprocess_data() 내에서 적용될 전처리/FE 흐름 (개요)

추후 `preprocess_data(df)` 또는 별도 `fe_pipeline` 모듈에서 아래 순서로 처리:

#### 1. Drop Unused Columns
- `user_id`, `Name`, `Password` 제거  

#### 2. 결측치 처리
- `listening_time`, `songs_played_per_day` → median Impute  

#### 3. 이상치/캡핑
- `skip_rate` → 상한값 cap (`skip_rate_cap` 생성)  
- `ads_listened_per_week` → percentile 기반 윈저라이징  

#### 4. Feature Engineering
- `engagement_score`, `songs_per_minute`, `skip_intensity`, `ads_pressure` 생성
- `age_group`, `subscription_type_level`, `listening_time_bin` 생성
- **※ FE 과정에서 발생한 새로운 결측치/Inf/NaN 처리**
  - 나눗셈 결과 Inf 발생 시 → 적절한 상한값으로 대체
  - 새로운 결측치 발생 시 → median/mode 재적용

#### 5. 범주형 인코딩
- One-Hot Encoding: `subscription_type`, `device_type` (+ 필요 시 gender)
- `country`는 **top-5 + 기타 그룹화** 후 인코딩  

#### 6. (옵션) 스케일링
- Tree 모델에서는 생략 가능하나, Logistic Regression 등 추가 모델 검증 시 활용 가능

---