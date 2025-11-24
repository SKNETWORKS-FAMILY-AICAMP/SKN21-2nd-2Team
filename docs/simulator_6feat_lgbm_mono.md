### 6개 피처 LGBM 단조제약 시뮬레이터 정리

이 문서는 **관리자 시뮬레이터용 6개 피처 + LGBM 단조제약 모델** 구성을 정리한 문서입니다.  
실제 서비스용 전체 모델(HGB 풀 피처)와는 별도의, **시뮬레이션·설명용 서브 모델**입니다.

---

### 1. 사용 피처(6개)와 의미

`data/enhanced_data_not_clean_FE_delete.csv` 기준, 시뮬레이터용으로 선정한 6개 수치 피처:

- **`app_crash_count_30d`**
  - 최근 30일 동안의 앱 크래시 횟수 (정수, 대략 0 ~ 4)
  - 값이 **클수록 이탈 위험 ↑** (단조 제약: `+1`)
- **`skip_rate_increase_7d`**
  - 최근 7일 스킵률 증가율 (%, 대략 -15 ~ +35)
  - 값이 **클수록(스킵률 많이 증가) 이탈 위험 ↑** (단조 제약: `+1`)
- **`days_since_last_login`**
  - 마지막 로그인 이후 경과 일수 (정수, 0 ~ 30)
  - 값이 **클수록(오래 안 들어올수록) 이탈 위험 ↑** (단조 제약: `+1`)
- **`listening_time_trend_7d`**
  - 최근 7일 청취 시간 변화율 (%, 대략 -20 ~ +20)
  - 값이 **클수록(사용량 증가) 이탈 위험 ↓** (단조 제약: `-1`)
- **`freq_of_use_trend_14d`**
  - 최근 14일 사용 빈도(trips) 변화율 (%, 대략 -16 ~ +16)
  - 값이 **클수록(사용 빈도 증가) 이탈 위험 ↓** (단조 제약: `-1`)
- **`login_frequency_30d`**
  - 최근 30일 로그인 횟수 (정수, 0 ~ 30)
  - 값이 **클수록(자주 로그인) 이탈 위험 ↓** (단조 제약: `-1`)

→ 사람 직관 기준으로 **“위험 신호 3개(크래시, 잠수, 사용량 감소)” + “안전 신호 3개(사용량/빈도/로그인 증가)”**를 한 세트로 보는 구조.

---

### 2. 왜 이 6개 피처를 선택했는가?

#### 2-1. Feature Importance + 영향도 분석 기반

- `verification.md`, `hgb_test.md`, `lgbm_test.md` 등에서 **Feature Importance**를 비교했을 때,
  - `payment_failure_count`, `app_crash_count_30d`, `freq_of_use_trend_14d`, `listening_time_trend_7d`, `skip_rate_increase_7d` 등이 상위권에 위치.
- `backend/find_good_sim_features.py` 에서 각 피처에 대해
  - **값 변화 vs 예측 확률**의 단조성(스피어만 상관) + 변화폭(effect)을 점수로 계산함.
  - 그 결과, `app_crash_count_30d`가 가장 높은 점수를 받았고,
    `days_since_last_login`, `listening_time_trend_7d`, `freq_of_use_trend_14d`, `login_frequency_30d`도 일정 수준 이상의 영향력을 보였음.

#### 2-2. 시뮬레이터에서의 “부드러운 반응”과 해석 용이성

- `backend/analyze_model_behavior.py`, `backend/test_scenario_lgbm.py` 로 여러 시나리오를 테스트한 결과,
  - **크래시 / 잠수 / 사용량 추세 3개**는 값을 조정했을 때 이탈 확률이 **크고 직관적으로** 변함.
  - `skip_rate_increase_7d`, `freq_of_use_trend_14d`, `login_frequency_30d` 는 단독으로는 영향이 약하지만,
    - “사용량/빈도/참여도”의 질적인 변화를 보조적으로 표현해 주는 축으로 유용.
- 너무 많은 피처를 시뮬레이터에 노출하면
  - 관리자 입장에서 “무엇을 어떻게 조절해야 하는지” 이해가 어려워지므로,
  - **“설명 가능한 6개 레버”**로 제한하는 것이 UX 측면에서 더 적절하다고 판단.

#### 2-3. 데이터 가용성과 현실성

- 선택된 6개는 모두 **실제 서비스에서 수집하기 상대적으로 쉬운 로그/카운트/추세 정보**에 해당:
  - 크래시 로그, 로그인 로그, 재생/스킵 로그 등.
- 향후 실제 서비스에 적용할 때도,
  - 별도의 복잡한 FE 없이도 **데이터 엔지니어링으로 충분히 확보 가능한 컬럼들**이라는 점을 고려.

#### 2-4. 정리

- 위 실험과 제약 조건들을 종합해서,
  - **“위험도를 크게 좌우하면서도, 관리자에게 설명하기 쉬운 최소 피처 집합”**으로
  - `app_crash_count_30d`, `skip_rate_increase_7d`, `days_since_last_login`,
    `listening_time_trend_7d`, `freq_of_use_trend_14d`, `login_frequency_30d` 6개를 최종 선택.

---

### 3. 학습 스크립트 및 모델 설정
### 3. 학습 스크립트 및 모델 설정

- **학습 스크립트**: `backend/train_simulator_6feat_lgbm_mono.py`
- **데이터**: `DATA_PATH = "data/enhanced_data_not_clean_FE_delete.csv"`
- **분할**: `TEST_SIZE = 0.2`, `RANDOM_STATE = 42`, `stratify=y`
- **모델 생성**: `get_model(name="lgbm", random_state=42, monotone_constraints=MONO_CONSTRAINTS)`
- **단조 제약 벡터**:
  - `MONO_CONSTRAINTS = [+1, +1, +1, -1, -1, -1]`
  - 순서는 위에서 정의한 `SIM_FEATURES` 순서와 동일
- **저장 경로**: `models/lgbm_sim_6feat_mono.pkl`

#### 검증 성능 (검증 세트 기준)

`train_simulator_6feat_lgbm_mono.py` 실행 결과:

- **ROC-AUC**: `0.7400`
- **Best F1**: `0.5255`
- **Best Threshold**: `0.23`
- **Confusion Matrix (Best Threshold 기준)**:  
  - TN = 994, FP = 192, FN = 198, TP = 216  

→ 풀 피처 HGB(풀 모델)보다는 한 단계 낮지만, **6개 피처만으로는 시뮬레이터용으로 충분한 수준의 분류 성능**을 가짐.

---

### 4. 추론 함수 및 위험도 매핑

- **추론 모듈**: `backend/inference_sim_6feat_lgbm.py`
- **메인 엔트리**: `predict_churn_6feat_lgbm(user_features: Mapping[str, Any]) -> Dict[str, Any]`
  - 입력: 위 6개 피처만 담은 딕셔너리 (누락된 값은 `NaN` → LGBM이 자체 처리)
  - 내부에서 `models/lgbm_sim_6feat_mono.pkl` 로딩 후 `predict_proba` 사용

#### 위험도 레벨 매핑 (`_prob_to_risk_level`)

- `p < 0.23` → `"LOW"`  
- `0.23 <= p < 0.60` → `"MEDIUM"`  
- `p >= 0.60` → `"HIGH"`  

→ `0.23` 값은 학습 시 Best F1 기준 threshold 에서 가져온 값.  
시뮬레이터/관리자 UI에서는 이 구간을 그대로 사용해 **위험도 뱃지/색상**을 표시하는 것을 권장.

---

### 5. 시나리오 테스트 결과 요약 (`backend/test_scenario_lgbm.py`)

`backend/test_scenario_lgbm.py` 에서 대표적인 10개 시나리오를 정의해 LGBM 단조제약 모델로 예측:

- **1. 평범 (Clean)**  
  - `(crash=0, days=1, trend=0, freq_trend=0, skip_inc=0, login30=20)`  
  - **이탈 확률 ≈ 0.07 → LOW**
- **2. 스킵만 증가 (Quality only)**  
  - `(crash=0, skip_inc=+30%, days=3, 나머지 보통)`  
  - **이탈 확률 ≈ 0.22 → LOW 상단**  
  - → “콘텐츠 불만은 있지만 이탈 직전까지는 아님” 수준으로 해석 가능.
- **3. 크래시만 많음 (Crash only)**  
  - `(crash=3, days=3, 나머지 보통)`  
  - **이탈 확률 ≈ 0.51 → MEDIUM**
- **4. 잠수만 심함 (Days only)**  
  - `(crash=0, days=21, trend=0, login30=10)`  
  - **이탈 확률 ≈ 0.51 → MEDIUM**
- **5. 사용량 급감 (Trend only)**  
  - `(trend=-20%, freq_trend=-10%, 나머지 무난)`  
  - **이탈 확률 ≈ 0.99 → HIGH**
- **6. 중간 위험 (Combo)**  
  - 여러 피처가 조금씩 안 좋은 방향(예: `crash=2, days=7, trend=-10`)  
  - **이탈 확률 ≈ 0.32 → MEDIUM**
- **7. 고위험 (Crash + Days)**  
  - `(crash=3, days=21, 기타도 약간 나쁨)`  
  - **이탈 확률 ≈ 0.85 → HIGH**
- **8. 고위험 (Days + Trend)**  
  - `(crash=1, days=21, trend=-20%)`  
  - **이탈 확률 ≈ 0.99 → HIGH**
- **9. 매우 안전 (High engagement)**  
  - `(crash=0, days=0, trend=+10%, freq_trend=+8%, login30=30)`  
  - **이탈 확률 ≈ 0.01 → LOW**
- **10. 엣지 (Extreme combo)**  
  - `(crash=4, skip_inc=+35%, days=30, trend=-20%, freq_trend=-16%, login30=1)`  
  - **이탈 확률 ≈ 1.00 → HIGH**

→ 전반적으로:
- “하나만 나쁘면 Medium, 여러 개 동시에 나쁘면 High, 전반적으로 좋으면 Low” 라는 패턴이 잘 나타남.
- 특히 **`crash / days_since_last_login / listening_time_trend_7d`** 3개의 조합이 위험도를 크게 결정.

---

### 6. 활용 가이드 (시뮬레이터 / 관리자 기능)

- **입력 스펙**: 프론트/관리자는 위 6개 피처만 입력 받아 `/api/...` 등으로 전달
  - 나머지 전체 피처는 사용하지 않으며, 이 모델은 **완전히 6개 피처 전용 모델**임.
- **출력 해석**:
  - `churn_prob`는 0~1 사이 확률 (백분율 ×100% 로 표기 가능)
  - `risk_level`은 단순화된 위험도 구간 (LOW/MEDIUM/HIGH)
  - 실제 이탈 여부와 1:1로 매칭되는 “정답”이 아니라, **위험도 스코어/참고 지표**로 사용하는 것을 권장.
- **설계 의도**:
  - 서비스 전체 모델(HGB 풀 피처)은 그대로 유지하면서,
  - 6개 핵심 피처를 조절해 볼 수 있는 **관리자용 “What-if” 시뮬레이터 엔진**으로 활용.
  - 특히 **크래시/잠수/사용량 감소**를 중심으로, “값을 올리면(또는 줄이면) 위험도가 어느 방향으로 바뀌는지”를 직관적으로 보여주는 데 초점.


