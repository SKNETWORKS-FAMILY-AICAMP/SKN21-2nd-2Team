### 6개 피처 LGBM 단조제약 시뮬레이터 정리 (앙상블 버전)

이 문서는 **관리자 시뮬레이터용 6개 피처 + LGBM 단조제약 앙상블 모델** 구성을 정리한 문서입니다.  
실제 서비스용 전체 모델(HGB 풀 피처)와는 별도의, **시뮬레이션·설명용 서브 모델**입니다.

> **v2 업데이트**: 5개 LGBM 앙상블 + Early Stopping + scale_pos_weight 조정으로 안정성과 위험 감지 능력 향상

---

### 1. 사용 피처(6개)와 의미

`simulator_6feat_lgbm_mono.md` 와 동일 (생략)

---

### 2. 왜 이 6개 피처를 선택했는가?

`simulator_6feat_lgbm_mono.md` 와 동일 (생략)

---

### 3. 학습 스크립트 및 모델 설정 (앙상블 버전)

- **학습 스크립트**: `backend/train_simulator_6feat_lgbm_mono.py`
- **데이터**: `DATA_PATH = "data/enhanced_data_not_clean_FE_delete.csv"`
- **분할**: `TEST_SIZE = 0.2`, `RANDOM_STATE = 42`, `stratify=y`
- **모델 아키텍처**: **앙상블 (5개 LGBM 모델 평균)**
  - 각 모델은 서로 다른 `random_state`로 학습 (`RANDOM_STATE + i`, i=0~4)
  - 예측 시 5개 모델의 확률 평균을 사용 → **분산 감소 및 안정적인 예측**
- **단조 제약 벡터**:
  - `MONO_CONSTRAINTS = [+1, +1, +1, -1, -1, -1]`
  - 순서는 `SIM_FEATURES` 순서와 동일
  - **모든 앙상블 모델에 동일하게 적용** → 해석 가능성 유지
- **성능 향상 기법**:
  - **Early Stopping**: Validation set (20%) 분할 후 AUC 기준 조기 종료
  - **scale_pos_weight = 2.2**: 클래스 불균형 처리 (자동 계산값 ≈ 3.56보다 보수적으로 조정)
  - 목표: False Positive 감소하면서도 이탈자를 놓치지 않는 균형 유지
- **저장 경로**: `models/lgbm_sim_6feat_mono.pkl`
  - 저장 형식: 딕셔너리 `{'models': [모델1, 모델2, ...], 'n_models': 5, ...}`
  - 추론 시 자동으로 앙상블 평균 예측

#### 검증 성능 (검증 세트 기준)

`train_simulator_6feat_lgbm_mono.py` 실행 결과 **(앙상블 모델 최종 버전)**:

- **ROC-AUC**: `0.7388`
- **Best F1**: `0.5253`
- **Best Threshold**: `0.43`
- **Confusion Matrix (Best Threshold 기준)**:  
  - TN = 1016, FP = 170, FN = 206, TP = 208  
- **앙상블 구성**: 5개 LGBM 모델

**기본 단일 모델 대비 개선점**:
- ROC-AUC: `0.7400` → `0.7388` (거의 동등)
- Best F1: `0.5255` → `0.5253` (거의 동등)
- **False Positive 감소**: 192건 → 170건 (-11%, **오탐률 개선**)
- **예측 안정성 향상**: 5개 모델 평균으로 분산 감소
- **중요**: 크래시 빈발 유저를 MEDIUM → HIGH로 올바르게 상향 조정 (위험 감지 능력 향상)

→ 풀 피처 HGB(풀 모델)보다는 한 단계 낮지만, **6개 피처만으로는 시뮬레이터용으로 충분한 수준의 분류 성능**을 가지며,  
→ 앙상블 기법으로 **안정성과 신뢰성을 추가로 확보**함.

---

### 4. 추론 함수 및 위험도 매핑

- **추론 모듈**: `backend/inference_sim_6feat_lgbm.py`
- **메인 엔트리**: `predict_churn_6feat_lgbm(user_features: Mapping[str, Any]) -> Dict[str, Any]`
  - 입력: 위 6개 피처만 담은 딕셔너리 (누락된 값은 `NaN` → LGBM이 자체 처리)
  - 내부에서 `models/lgbm_sim_6feat_mono.pkl` 로딩
  - **앙상블 예측**: 자동으로 5개 모델 각각 예측 후 평균 계산
  - **하위 호환성**: 단일 모델 형식도 자동 감지하여 처리 가능
  - 출력에 `ensemble_size` 필드 추가 (앙상블 크기 정보)

#### 위험도 레벨 매핑 (`_prob_to_risk_level`)

- `p < 0.23` → `"LOW"`  
- `0.23 <= p < 0.60` → `"MEDIUM"`  
- `p >= 0.60` → `"HIGH"`  

→ `0.23` 값은 학습 시 Best F1 기준 threshold 에서 가져온 값.  
시뮬레이터/관리자 UI에서는 이 구간을 그대로 사용해 **위험도 뱃지/색상**을 표시하는 것을 권장.  
→ 앙상블 버전에서도 동일한 임계값 사용 (일관성 유지).

---

### 5. 기본 시나리오 테스트 결과 (`backend/test_scenario_lgbm.py`)

`backend/test_scenario_lgbm.py` 에서 대표적인 10개 시나리오를 정의해 LGBM 앙상블 모델로 예측:

- **1. 평범 (Clean)**  
  - `(crash=0, days=1, trend=0, freq_trend=0, skip_inc=0, login30=20)`  
  - **이탈 확률 = 0.1551 → LOW**
  - → 전체 평균(22%)보다 낮은 안전한 수준. "평범"한 유저의 현실적인 이탈률 반영.

- **2. 스킵만 증가 (Quality only)**  
  - `(crash=0, skip_inc=+30%, days=3, 나머지 보통)`  
  - **이탈 확률 = 0.3421 → MEDIUM**  
  - → "콘텐츠 불만은 있지만 이탈 직전까지는 아님" 수준으로 해석 가능.

- **3. 크래시만 많음 (Crash only)**  
  - `(crash=3, days=3, 나머지 보통)`  
  - **이탈 확률 = 0.7004 → HIGH**
  - → 크래시 3회는 심각한 기술적 문제로 인식, 고위험 판정.

- **4. 잠수만 심함 (Days only)**  
  - `(crash=0, days=21, trend=0, login30=10)`  
  - **이탈 확률 = 0.6757 → HIGH**
  - → 3주 이상 미접속은 이탈 가능성 높음.

- **5. 사용량 급감 (Trend only)**  
  - `(trend=-20%, freq_trend=-10%, 나머지 무난)`  
  - **이탈 확률 = 0.9968 → HIGH**
  - → 사용량 급감은 가장 강력한 이탈 신호.

- **6. 중간 위험 (Combo)**  
  - 여러 피처가 조금씩 안 좋은 방향(예: `crash=2, days=7, trend=-10`)  
  - **이탈 확률 = 0.5313 → MEDIUM**
  - → 악재가 여러 개 있지만 심각하지 않은 수준.

- **7. 고위험 (Crash + Days)**  
  - `(crash=3, days=21, 기타도 약간 나쁨)`  
  - **이탈 확률 = 0.8850 → HIGH**
  - → 크래시 + 잠수 복합 악재로 매우 위험.

- **8. 고위험 (Days + Trend)**  
  - `(crash=1, days=21, trend=-20%)`  
  - **이탈 확률 = 0.9978 → HIGH**
  - → 장기 미접속 + 사용량 급감은 거의 확실한 이탈 신호.

- **9. 매우 안전 (High engagement)**  
  - `(crash=0, days=0, trend=+10%, freq_trend=+8%, login30=30)`  
  - **이탈 확률 = 0.0130 → LOW**
  - → 모든 지표가 좋은 파워 유저, 이탈 가능성 극히 낮음.

- **10. 엣지 (Extreme combo)**  
  - `(crash=4, skip_inc=+35%, days=30, trend=-20%, freq_trend=-16%, login30=1)`  
  - **이탈 확률 = 1.0000 → HIGH**
  - → 모든 악재가 극단적으로 나쁜 경우, 100% 이탈 예측.

→ 전반적으로:
- "하나만 나쁘면 Medium~High, 여러 개 동시에 나쁘면 Very High, 전반적으로 좋으면 Low" 라는 패턴이 명확.
- 특히 **`crash / days_since_last_login / listening_time_trend_7d`** 3개의 조합이 위험도를 크게 결정.
- 앙상블 모델이 단일 악재와 복합 악재를 잘 구분하여 예측.

---

### 5-1. 확장된 포괄적 시나리오 테스트 (`backend/test_comprehensive_scenarios.py`)

앙상블 모델의 실전 성능을 검증하기 위해, 사람의 관점에서 **20가지 유저 페르소나 시나리오**를 설계하여 테스트:

#### 🟢 매우 안전 그룹 (Super Active Users)

**1. 파워 유저 (매일 접속, 사용량 증가)**
- crash=0, skip_inc=-5%, days=0, trend=+15%, freq_trend=+10%, login30=30
- **이탈 확률 = 0.0107 (1.07%)** → LOW

**2. 충성 고객 (꾸준한 사용)**
- crash=0, skip_inc=0%, days=1, trend=+5%, freq_trend=+3%, login30=25
- **이탈 확률 = 0.1324 (13.24%)** → LOW

**3. 열성 신규 유저 (최근 가입, 매우 활발)**
- crash=1, skip_inc=+2%, days=0, trend=+20%, freq_trend=+15%, login30=20
- **이탈 확률 = 0.0239 (2.39%)** → LOW

#### 🟢 안전 그룹 (Normal Active Users)

**4. 일반 유저 (주 3-4회 접속)**
- crash=0, skip_inc=0%, days=2, trend=0%, freq_trend=0%, login30=15
- **이탈 확률 = 0.1828 (18.28%)** → LOW

**5. 출퇴근 유저 (규칙적 사용)**
- crash=0, skip_inc=+1%, days=1, trend=+2%, freq_trend=+1%, login30=22
- **이탈 확률 = 0.1551 (15.51%)** → LOW

**6. 주말 유저 (주말에만 집중 사용)**
- crash=0, skip_inc=0%, days=4, trend=+5%, freq_trend=+3%, login30=8
- **이탈 확률 = 0.4775 (47.75%)** → MEDIUM

#### 🟡 경고 단계 (Warning Signs)

**7. 음질 불만 유저 (스킵률만 급증)**
- crash=0, skip_inc=+25%, days=2, trend=0%, freq_trend=0%, login30=18
- **이탈 확률 = 0.1577 (15.77%)** → LOW

**8. 기술적 문제 경험 유저 (크래시 빈발)**
- crash=5, skip_inc=+3%, days=3, trend=-5%, freq_trend=-3%, login30=15
- **이탈 확률 = 0.7359 (73.59%)** → HIGH

**9. 관심 감소 유저 (사용량 서서히 감소)**
- crash=0, skip_inc=+5%, days=5, trend=-8%, freq_trend=-6%, login30=12
- **이탈 확률 = 0.5034 (50.34%)** → MEDIUM

**10. 바쁜 직장인 (최근 접속 빈도 감소)**
- crash=0, skip_inc=0%, days=10, trend=-5%, freq_trend=-4%, login30=10
- **이탈 확률 = 0.5202 (52.02%)** → MEDIUM

#### � 중간 위험 그룹 (Medium Risk)

**11. 경쟁 서비스 탐색 중 (여러 악재)**
- crash=2, skip_inc=+15%, days=7, trend=-12%, freq_trend=-8%, login30=10
- **이탈 확률 = 0.7074 (70.74%)** → HIGH

**12. 불만족 유저 (크래시 + 스킵 증가)**
- crash=4, skip_inc=+20%, days=5, trend=-8%, freq_trend=-5%, login30=12
- **이탈 확률 = 0.8278 (82.78%)** → HIGH

**13. 흥미 상실 초기 단계 (서서히 멀어짐)**
- crash=1, skip_inc=+10%, days=9, trend=-15%, freq_trend=-10%, login30=8
- **이탈 확률 = 0.9974 (99.74%)** → HIGH

#### 🔴 고위험 그룹 (High Risk)

**14. 장기 미접속 유저 (3주 이상)**
- crash=1, skip_inc=+5%, days=25, trend=-18%, freq_trend=-12%, login30=3
- **이탈 확률 = 0.9979 (99.79%)** → HIGH

**15. 크래시 피해 유저 (나쁜 경험)**
- crash=6, skip_inc=+12%, days=14, trend=-15%, freq_trend=-10%, login30=5
- **이탈 확률 = 0.9986 (99.86%)** → HIGH

**16. 거의 탈퇴 직전 (모든 지표 나쁨)**
- crash=3, skip_inc=+30%, days=20, trend=-25%, freq_trend=-20%, login30=2
- **이탈 확률 = 1.0000 (100.00%)** → HIGH

#### 🔴 매우 고위험 (Critical Risk)

**17. 완전 이탈 (한 달 미접속)**
- crash=2, skip_inc=+10%, days=30, trend=-20%, freq_trend=-15%, login30=1
- **이탈 확률 = 0.9999 (99.99%)** → HIGH

**18. 최악의 경험 유저 (극단적 악재)**
- crash=8, skip_inc=+40%, days=28, trend=-30%, freq_trend=-25%, login30=1
- **이탈 확률 = 1.0000 (100.00%)** → HIGH

#### 🔵 특수 케이스 (Edge Cases)

**19. 복귀 유저 (오랜만에 재접속, 사용량 회복 중)**
- crash=0, skip_inc=0%, days=15, trend=+10%, freq_trend=+8%, login30=5
- **이탈 확률 = 0.3131 (31.31%)** → MEDIUM
- → 오래 안 들어왔지만 최근 긍정적 트렌드 → 단조 제약이 이를 올바르게 반영

**20. 시험 기간 학생 (일시적 감소)**
- crash=0, skip_inc=0%, days=12, trend=-10%, freq_trend=-8%, login30=8
- **이탈 확률 = 0.5266 (52.66%)** → MEDIUM

#### 테스트 결과 요약

동일한 20개 시나리오에 대해 단일 모델과 앙상블 비교 (`backend/compare_models.py`):

- **평균 확률 차이**: +7.62% (앙상블이 평균적으로 더 높은 이탈 확률 예측, 더 보수적)
- **최대 차이**: +21.02% (시험 기간 학생 케이스)
- **위험도 변경**: 20건 중 2건 (10%)
  - "기술적 문제 경험 유저": MEDIUM → **HIGH** (크래시 빈발을 더 심각하게 판단, **올바른 상향**)
  - "복귀 유저": LOW → MEDIUM (오랜 미접속을 더 신중하게 판단)

**앙상블의 장점 (검증 완료)**:
- ✅ 크래시 등 심각한 문제를 HIGH로 올바르게 상향 (False Negative 감소)
- ✅ 5개 모델 평균으로 예측 분산 감소, 안정성 향상
- ✅ 극단 케이스(99~100%)에서는 단일 모델과 거의 동일 (성능 유지)
- ✅ 단조 제약 유지로 해석 가능성은 그대로, 신뢰성만 추가 확보

---

### 6. 활용 가이드 (시뮬레이터 / 관리자 기능)

- **입력 스펙**: 프론트/관리자는 위 6개 피처만 입력 받아 `/api/...` 등으로 전달
  - 나머지 전체 피처는 사용하지 않으며, 이 모델은 **완전히 6개 피처 전용 모델**임.
- **출력 해석**:
  - `churn_prob`는 0~1 사이 확률 (백분율 ×100% 로 표기 가능)
  - `risk_level`은 단순화된 위험도 구간 (LOW/MEDIUM/HIGH)
  - `ensemble_size`는 앙상블 크기 (5개 모델 = 더 신뢰성 있는 예측)
  - 실제 이탈 여부와 1:1로 매칭되는 "정답"이 아니라, **위험도 스코어/참고 지표**로 사용하는 것을 권장.
- **설계 의도**:
  - 서비스 전체 모델(HGB 풀 피처)은 그대로 유지하면서,
  - 6개 핵심 피처를 조절해 볼 수 있는 **관리자용 "What-if" 시뮬레이터 엔진**으로 활용.
  - 특히 **크래시/잠수/사용량 감소**를 중심으로, "값을 올리면(또는 줄이면) 위험도가 어느 방향으로 바뀌는지"를 직관적으로 보여주는 데 초점.
- **프로덕션 배포**:
  - **앙상블 모델 사용 권장**: 기본 모델 대비 크게 느리지 않으면서도 (+7.6% 보수적 예측) 안정성과 위험 감지 능력 향상
  - 추론 속도: 5개 모델 순차 예측이지만, 피처가 6개뿐이라 **실시간 추론에 충분히 빠름**
  - 메모리: 약 5배 증가하지만, LGBM 경량 모델이라 **실용적 수준** (전체 ~수 MB)

---

### 7. 성능 개선 과정 요약

1. **기본 단일 모델 (v1)**
   - 단순 LGBM + 단조 제약
   - ROC-AUC: 0.7400, F1: 0.5255

2. **앙상블 모델 (v2 - 최종)**
   - 5개 LGBM 앙상블 + Early Stopping + scale_pos_weight=2.2
   - ROC-AUC: 0.7388, F1: 0.5253 (거의 동등)
   - **False Positive 11% 감소** (192 → 170)
   - **크래시 빈발 유저를 HIGH로 올바르게 상향**
   -안정적인 예측으로 **프로덕션 사용 권장**

→ 단조 제약을 유지하면서도, 앙상블 기법으로 **해석 가능성 + 안정성**을 동시에 확보.
