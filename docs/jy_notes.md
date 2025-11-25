## 역할 작업 정리 (전처리 검증 + Feature 튜닝)

- **역할 요약**
  - 전처리 검증, 파생 변수(Feature Engineering) 아이디어 제안
  - EDA 기반 타당성 검증
  - 전처리/FE 관점의 성능 영향도 분석 (간단 모델 기준)
  - 2번이 만든 전처리 파이프라인 QA

---

## 1. 지금까지 한 일

- **원본 데이터 구조 이해**
  - `notebooks/preprocessing_validation.ipynb`(이전 버전 기준)에서 원본 데이터 로드 및 컬럼 구조 확인
  - 타깃 분포 확인: `is_churned=0` 약 74%, `is_churned=1` 약 26% → **불균형 데이터**임을 파악

- **baseline 통계 수집**
  - `listening_time`, `songs_played_per_day`, `skip_rate`에 대해 `median`, `max`, `q99` 계산
  - `country_top5`, `subscription_type_unique`, `device_type_unique` 등 범주형 기준값 정리

- **기본 FE 4개 구현 및 EDA**
  - `engagement_score = listening_time * songs_played_per_day`
  - `listening_time_bin` (low/mid/high 구간)
  - `skip_rate_cap` (0~1.5 cap)
  - `ads_pressure = ads_listened_per_week / listening_time`
  - 각 FE vs `is_churned`에 대해 구간별 **평균 이탈률(churn_rate)** 비교

- **추가 FE 제안 및 구현 (사전 검증)**
  - 제안한 파생 변수:
    - `songs_per_minute` = songs_played_per_day / listening_time  
    - `skip_intensity` = skip_rate_cap * songs_played_per_day  
    - `high_skip_flag` (skip_rate_cap이 높은 위험 고객 플래그)  
    - `high_ads_pressure_flag` (ads_pressure 상위 구간 플래그)  
    - `offline_heavy_user` (offline_listening=1 & listening_time>median)  
    - `age_group` (young/adult/senior)  
    - `subscription_type_level` (Free=0, Student=1, Premium=2, Family=3)
  - 위 변수들을 실제로 계산하고, 각 변수 vs `is_churned`에 대해 **구간/그룹별 churn_rate**를 확인

- **성능 영향도 1차 분석 (파이프라인 적용 전, 간단 모델 기준)**
  - 모델: `LogisticRegression(max_iter=1000)` + `SimpleImputer` + `OneHotEncoder`
  - 비교 실험:
    - **Base**: 원본 주요 변수만 사용  
    - **Base+FE**: Base + 기본 FE 4개 + 추가 FE들 포함
  - 결과 (대략):
    - Base: Accuracy ≈ 0.74, ROC-AUC ≈ 0.49, F1(이탈 클래스 기준) ≈ 0.0  
    - Base+FE: Accuracy ≈ 0.74, ROC-AUC ≈ 0.50, F1 ≈ 0.0  
  - 해석:
    - 불균형 데이터 + 단순 로지스틱 설정에서는 **거의 모두를 0(미이탈)로 예측** → Accuracy는 높게 나오지만, 이탈(1)을 잘 못 맞춰서 F1이 0에 가까움
    - Base 대비 Base+FE의 AUC 개선 폭은 매우 작아서, **간단 로지스틱 기준에서 FE 추가만으로는 성능 향상이 크지 않음**

---

## 2. 지금까지의 결론 (3번 역할 관점)

- **EDA 기반 타당성 검증**
  - 기본 FE 4개와 추가 FE들에 대해, 이탈률 패턴(구간별 churn_rate)을 확인함.
  - 일부 변수(`skip_intensity`, `high_skip_flag`, `subscription_type_level` 등)는 이탈률 차이가 어느 정도 보이지만, 전반적으로 아주 강한 분리력은 아님.

- **성능 영향도 분석 (사전 단계)**
  - 파이프라인 적용 전, **원본+FE 상태에서 간단 로지스틱 기준으로** Base vs Base+FE 성능을 비교함.
  - 결과적으로 **FE만 추가해서는 성능이 크게 개선되지 않음**을 확인.
  - 이탈 예측 성능 개선을 위해서는
    - 불균형 처리(`class_weight='balanced'`, resampling 등),
    - 더 복잡한 모델(트리 계열, 앙상블 등),
    - 혹은 추가적인 FE/도메인 아이디어
    가 함께 필요할 가능성이 큼.

---

## 3. 앞으로 할 일 (내일 이후 TODO)

- **1) 전처리 파이프라인 수령 후 QA**
  - 2번 역할이 `preprocess_pipeline()`을 완성하면:
    - `X_train, X_test, y_train, y_test`를 받아서
    - 아래 항목을 QA:
      - shape 정상 여부
      - 결측치 제거 여부
      - 타깃 분포가 원본과 크게 달라지지 않았는지
      - 설계된 FE 컬럼들이 실제로 포함되어 있는지
      - (선택) baseline_stats와 비교하여 이상치 처리가 적절한지

- **2) 파이프라인 적용 후 성능 영향도 재확인 (선택/보너스)**
  - 2번 파이프라인 결과(X_train/X_test)를 사용해:
    - Base vs Base+FE 모델을 다시 한 번 학습/평가
    - “전처리+FE 전체 묶음” 기준에서 성능이 어떻게 달라졌는지 요약
  - 필요하다면:
    - `class_weight='balanced'` 적용 버전,
    - 트리 계열 모델(baseline 정도)로 간단 비교 수행

- **3) 보고/발표용 정리**
  - 3번 역할이 한 일 정리:
    - FE 후보 리스트 + 각 변수별 churn_rate 패턴 요약
    - 간단 로지스틱에서 FE 영향도가 크지 않았다는 점
    - “이탈 예측 개선에는 전처리+불균형 처리+모델 선택이 함께 필요”라는 인사이트
  - 이 내용을 슬라이드나 README 일부로 정리하면, 최종 발표 때 3번 역할 설명에 활용 가능.

---

## 4. 내일 Cursor에게 이야기할 때 요령

- 강의실에서 Cursor를 열면, 이 파일(`docs/jy_notes.md`)을 보여주면서 이렇게 말하면 됨:
  - “이 파일 기준으로, 3번 역할이 내일 이어서 해야 할 QA/성능 영향도 분석 계획을 정리해줘.”
- 그러면 새 세션의 AI도 이 문서를 읽고,  
  **지금까지 진행 상황과 TODO를 이어받아서 도와줄 수 있음.**


