## KNN 실험 기록 (`jy_model_test`)

### 1. 실험 환경 요약

- **데이터**: `data/enhanced_data_not_clean_FE_delete.csv`  
  - 전처리: `jy_model_test/preprocessing_pipeline.py`의 `preprocess_and_split()`  
  - 입력 피처: 수치형 + 범주형(OHE)까지 포함한 고차원 희소 벡터  
- **학습 스크립트**: `jy_model_test/train_experiments.py`  
  - 공통 설정: `jy_model_test/config.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, `THRESH_END=0.6`)  
  - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix  
  - 결과 저장: `models/metrics.json`

---

### 2. 1차 튜닝 (k 크기 대략 탐색)

**목표**:  
- KNN의 핵심 하이퍼파라미터인 `n_neighbors(k)`에 따라 성능이 어떻게 변하는지 “대략적인 지형” 파악.

**전략**:
- 모델: `MODEL_NAME = "knn"`  
- 공통 설정:
  - `weights = "distance"`
  - `metric = "minkowski"`
  - `p = 2` (유클리드 거리)
- 아래와 같이 **k만 바꿔가며 여러 세트 실행**:
  - 예: `n_neighbors ∈ {5, 10, 20, 30, 35, ...}` (여러 값 시도)

**관찰 결과 (대표)**:
- 1차에서의 KNN 성능 범위:
  - F1: **0.43 ~ 0.48** 수준
  - ROC-AUC: **0.61 ~ 0.67** 수준
  - PR-AUC: **0.36 ~ 0.42** 수준
- Threshold:
  - best_threshold는 대략 **0.19 ~ 0.26** 구간에 많이 분포  
  - threshold가 너무 낮을 때(0.05 근처)는 Recall은 높지만 FP가 과도하게 늘어나 Precision/F1이 급격히 악화
- 인사이트:
  - k가 너무 작을 때: 과적합에 가까운 형태로 FP가 크게 늘어나 Precision이 많이 떨어짐
  - k가 너무 클 때: 예측이 지나치게 보수적이 되어 Recall이 크게 감소
  - 대략 **중간 k (20~35 근처)**에서 F1·AUC가 상대적으로 안정적

⇒ 1차에서는 **“중간 정도 k에서 제일 나은 편이며, 전체적으로 RF/XGB보다 한 단계 낮다”**는 감만 확보.

---

### 3. 2차 튜닝 (k=20~35 국소 탐색)

**목표**:  
- 1차에서 상대적으로 좋았던 **중간 k 구간(약 20~35)** 만 다시 촘촘히 탐색해,  
  이 데이터에서의 **사실상 최선에 가까운 KNN 조합**을 찾는 것.

**변경 사항**:
- `weights = "distance"`, `metric="minkowski"`, `p=2`는 그대로 두고  
  `n_neighbors`만 아래 값들로 국소 탐색:
  - `n_neighbors`: 15, 20, 25, 30, 35

**관찰 결과 (2차)**:
- F1는 **약 0.46 ~ 0.49** 구간에서 수렴
- AUC는 **0.67±0.01** 수준, PR-AUC는 **0.41±0.02** 수준
- 이 중 **k≈30 근처에서 F1가 가장 높게 측정**됨:
  - F1 ≈ **0.4908**
  - AUC ≈ **0.6764**
  - PR-AUC ≈ **0.4244**
  - Best Threshold ≈ **0.26**
  - Precision ≈ **0.4243**, Recall ≈ **0.5821**

⇒ 2차 결과 기준으로 **k≈30, weights="distance"**가 이 데이터에서의 KNN “sweet spot”으로 판단.

---

### 4. 3차 튜닝 (미세 조정: k 주변 + 거리/가중치)

**목표**:  
- 2차에서 도출한 `k≈30` 근처를 기준으로,  
  **k ±5**, `weights`, 거리 파라미터 `p`를 조금씩 조정해 F1·AUC·PR-AUC가 소폭이라도 개선되는지 확인.

**변경 사항 (개념)**:
- 기준 세트:
  - `n_neighbors = 30`, `weights = "distance"`, `metric="minkowski"`, `p=2`
- 주변 탐색:
  - `n_neighbors = 25`, `35` 정도로 ±5 조정
  - `weights`: `"distance"` vs `"uniform"` 비교
  - `p`: 2(유클리드) 기준에서 일부 실험은 `p=1`(맨해튼)으로 변경

**관찰 결과 (3차)**:
- F1 최고값은 **2차와 거의 동일한 약 0.49 수준**에서 머물렀고, 더 크게 올라가지는 않음
- 일부 조합에서 PR-AUC가 **0.47 근처**까지 올라가기도 했지만,
  - 이때 F1은 오히려 0.47 수준으로 떨어져,  
    전체 밸런스(서비스용 의사결정 기준)에서는 큰 이득이 없다고 판단

⇒ 3차 미세 조정으로 **일부 조합의 PR-AUC는 약간 좋아졌지만,  
   F1 기준 전체 성능 레벨은 2차와 동일선상에 머무름**을 확인.

---

### 5. 최종 선별 결과 (KNN Best Run)

`models/metrics.json` 기준, 2025-11-23까지의 KNN 실험들 중 **최고 F1**은 아래 런:

- **모델**: KNN  
- **하이퍼파라미터 (개념적으로 추정)**:
  - `MODEL_NAME = "knn"`
  - `n_neighbors ≈ 30`
  - `weights = "distance"`
  - `metric = "minkowski"`
  - `p = 2`
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.4908**  
  - ROC-AUC: **0.6764**  
  - PR-AUC: **0.4244**  
  - Best Threshold: **0.26**  
  - Precision: **0.4243**  
  - Recall: **0.5821**
- **Confusion Matrix (th≈0.26)**:
  - TN = 859  
  - FP = 327  
  - FN = 173  
  - TP = 241  
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_not_clean_FE_delete.csv`  
  - `test_size`: 0.2  
  - `random_state`: 42  
  - `threshold_range`: 0.05 ~ 0.60 (step=0.01)

---

### 6. RF / XGB vs KNN 최종 비교 (요약)

- **RF (기존 Best)**  
  - F1 ≈ **0.616**  
  - ROC-AUC ≈ **0.791**  
  - PR-AUC ≈ **0.662**
- **XGB (기존 Best)**  
  - F1 ≈ **0.620**  
  - ROC-AUC ≈ **0.811**  
  - PR-AUC ≈ **0.693**
- **KNN (3차까지 튜닝 후 Best)**  
  - F1 ≈ **0.491**  
  - ROC-AUC ≈ **0.676**  
  - PR-AUC ≈ **0.424**

⇒ 이 데이터/전처리(고차원 OHE + 표준화) 조합에서는  
   **KNN은 3차 튜닝까지 진행해도 RF/XGB에 비해 F1·AUC·PR-AUC 모두 한 단계 낮은 수준**으로,  
   최종적으로는 **“거리 기반 모델의 한계를 확인해 준 비교용 베이스라인”** 역할에 가깝다고 정리할 수 있음.***
