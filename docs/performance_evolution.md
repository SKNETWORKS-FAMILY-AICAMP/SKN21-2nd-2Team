## 모델 성능 진화 히스토리 정리

이 문서는 **Spotipy 이탈 예측 프로젝트**에서  
데이터/FE/전처리/모델 설계 변경에 따라 **성능(F1, AUC)이 어떻게 발전했는지**를  
실험 파일 단위로 정리한 기록입니다.

> 기준 지표:  
> - **F1 Score**: 1순위  
> - **ROC-AUC**: 2순위 (전체 구분 능력)  
> - **PR-AUC / Precision / Recall / Confusion Matrix**: 보조

---

### 1. 완전 초기 Baseline (원본 + 수치형만)

- **데이터**: `data/raw_data.csv`  
- **피처**: 기본 수치형 6개  
  - `age`, `listening_time`, `songs_played_per_day`, `skip_rate`, `ads_listened_per_week`, `offline_listening`
- **모델/실험 파일**
  - `notebooks/FE_validation.ipynb`  
    - Set A (기본 수치형만, LogisticRegression + StandardScaler)
- **대표 성능**
  - F1 ≈ **0.3320**  
  - AUC ≈ **0.4895**

→ **순수 원본 + 수치형만 사용**한 완전 초반 baseline.

---

### 2. 원본 + 수치형 + FE 추가

#### 2-1. Logistic + FE (수치형 + FE)

- **실험 파일**: `notebooks/FE_validation.ipynb`
- **피처**
  - Set B: 기본 수치형 6 + FE 3개  
    - `engagement_score`, `skip_rate_cap`, `ads_pressure`
- **성능 (Logistic 기준)**
  - Set A (수치형만): F1 ≈ **0.3320**, AUC ≈ **0.4895**
  - Set B (수치형 + FE 3): F1 ≈ **0.3351**, AUC ≈ **0.4893**

→ FE를 추가해도 **Logistic 기준에서는 큰 변화 없음** (F1 소폭↑, AUC 거의 동일).

#### 2-2. RandomForest + FE (최초 RF Baseline)

- **실험 파일**
  - `notebooks/FE_add.ipynb`
  - `notebooks/FE_validation.ipynb` (Set C/D)
  - `notebooks/feature_engineering_advanced.ipynb` (Baseline 섹션)
- **피처 세트 (Set D 기준)**  
  - 기본 수치형 6개 + FE 5개 = **11개 피처**
    - FE 5개: `engagement_score`, `songs_per_minute`, `skip_intensity`, `skip_rate_cap`, `ads_pressure`
- **모델**
  - `RandomForestClassifier(class_weight="balanced", n_estimators=300, max_depth=None, min_samples_split=5)`  
  - threshold 튜닝 (대략 0.1~0.3 구간)
- **대표 성능**
  - `FE_add.ipynb` / `FE_validation.ipynb`:  
    - F1 ≈ **0.412 ~ 0.413**  
    - AUC ≈ **0.53 ~ 0.54**
  - `feature_engineering_advanced.ipynb` → Baseline (Set D) 재확인:  
    - F1 ≈ **0.4153**  
    - AUC ≈ **0.5352**

→ **원본 + 수치형 + FE + RF 기준으로 F1 ≈ 0.41, AUC ≈ 0.54가 초반 상한선**처럼 보이는 구간.

---

### 3. 원본 + 수치형 + 범주형(원-핫) + FE

- **실험 파일**: `notebooks/feature_selection.ipynb`
- **데이터**: `data/raw_data.csv`
- **피처**
  - Numeric only:  
    - 수치형 + FE(Set D 관점) 위주
  - Numeric + cat:  
    - Numeric only + 범주형/구간형
      - `gender`, `country`, `subscription_type`, `device_type`  
      - `listening_time_bin`, `age_group` (카테고리형) → One-Hot 인코딩
- **모델**
  - `RandomForestClassifier(class_weight="balanced")` + threshold 튜닝
- **대표 성능 (발췌)**:

```text
=== RF + best F1 기준 성능 비교 (수치형 vs 수치형+범주형) ===
[Numeric only]   best F1 = 0.4127 @ th=0.10, AUC = 0.5289
[Numeric + cat] best F1 = 0.4113 @ th=0.10, AUC = 0.5117
```

→ **범주형 + 원핫을 추가해도, F1/AUC 모두 거의 개선되지 않고 AUC는 오히려 하락.**  
→ 이 결과를 바탕으로, 최종 파이프라인 설계에서는 “**범주형은 ColumnTransformer 내부에서 OHE만 하고, FE 5개는 최종 모델 입력에서는 제거**”하는 방향으로 정책을 잡음.

---

### 4. 시계열 + 고객접점 합성 피처 추가 (Advanced Features)

#### 4-1. 합성 피처 설계 및 생성

- **실험 파일**: `notebooks/feature_engineering_advanced.ipynb`
- **데이터**
  - 원본: `data/raw_data.csv`
  - 합성 결과: `data/enhanced_data.csv`
- **추가 피처**
  - 시계열 5개:
    - `listening_time_trend_7d`, `login_frequency_30d`,  
      `days_since_last_login`, `skip_rate_increase_7d`, `freq_of_use_trend_14d`
  - 고객접점 4개:
    - `customer_support_contact`, `payment_failure_count`,  
      `promotional_email_click`, `app_crash_count_30d`

#### 4-2. 시나리오별 성능 비교 (RF 기준)

`feature_engineering_advanced.ipynb` 中:

```text
시나리오별 성능 비교 (RandomForest + threshold 튜닝)

Baseline (기존, 11개)          F1 = 0.4153, AUC = 0.5352
+ 시계열 (5개, 총 16개)         F1 ≈ 0.4935, AUC ≈ 0.7278
+ 시계열 + 고객접점 (9개, 총 20개) F1 ≈ 0.6246, AUC ≈ 0.7938
```

- Baseline (Set D, 11개 피처) 대비:
  - F1: **0.4153 → 0.6246** (ΔF1 ≈ +0.2093, +50% 수준)  
  - AUC: **0.5352 → 0.7938** (ΔAUC ≈ +0.26)

→ **“시계열 + 고객접점” 신호를 추가하면, 데이터의 예측 가능성이 크게 올라간다**는 걸 합성 실험으로 검증.

---

### 5. 정제(clean) + FE 제거 + 시계열/고객접점 15개만 사용

시계열/고객접점 합성 실험이 성공한 뒤,  

