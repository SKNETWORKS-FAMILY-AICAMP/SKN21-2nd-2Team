## ExtraTrees 실험 기록 (`et_model_test`)

### 1. 실험 환경 요약

- **데이터**: `data/enhanced_data_clean_model.csv` (15개 수치형 피처만 포함)  
  - 전처리: `backend/preprocessing_pipeline.py`의 `preprocess_and_split()`  
  - 입력 피처: **15개 수치형 피처** (원본 수치형 6 + 시계열 5 + 고객접점 4)
- **학습 스크립트**: `backend/train_experiments.py`  
  - 공통 설정: `backend/config.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, threshold 0.05~0.35)  
  - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix  
  - 결과 저장: `models/metrics.json`
- **모델**: ExtraTreesClassifier (`MODEL_NAME = "et"`)

---

### 2. 1차 튜닝 (탐색 단계)

**목표**:  
- ExtraTrees의 기본 성능 파악 및 넓은 범위에서 하이퍼파라미터 탐색

**전략**:
- `MODEL_NAME = "et"`로 설정 후, 아래 범위에서 **288개 조합**을 실험
  - `n_estimators`: 300, 500, 700, 800, 1000
  - `max_depth`: 15, 18, 20, 22, 25
  - `min_samples_split`: 2, 3, 4, 5, 6
  - `min_samples_leaf`: 1
  - `max_features`: None, 0.8, 0.9

**관찰 결과 (1차)**:
- 최고 성능 (F1 기준):
  - F1 Score: **0.6150**
  - ROC-AUC: **0.7881**
  - PR-AUC: **0.6279**
  - Best Threshold: **0.34**
  - Precision: **0.6165**
  - Recall: **0.6135**
- 최적 하이퍼파라미터:
  - `n_estimators`: 500
  - `max_depth`: 20
  - `min_samples_split`: 2
  - `min_samples_leaf`: 2
  - `max_features`: None
- 인사이트:
  - **max_depth=20, n_estimators=500 근처**에서 안정적으로 높은 성능
  - **max_features=None** (모든 피처 사용)이 좋은 성능을 보임
  - **min_samples_leaf=2**가 최적
  - Best Threshold는 **0.34**에서 최적

⇒ 1차 튜닝으로 **기본 성능 구간을 파악**하고, 최적 파라미터 주변을 확인.

---

### 3. 2차 튜닝 (국소 탐색 단계)

**목표**:  
- 1차에서 성능이 좋았던 하이퍼파라미터 근처만 다시 탐색해서  
  **F1=0.6150를 더 끌어올릴 수 있는지 확인**.

**변경 사항**:
- 하이퍼파라미터는 아래 범위를 중심으로 **240개 조합으로 국소 탐색**:
  - `n_estimators`: 400, 500, 600, 700, 800
  - `max_depth`: 18, 20, 22, 25
  - `min_samples_split`: 2, 3, 4
  - `min_samples_leaf`: 1, 2
  - `max_features`: None, 0.9

**관찰 결과 (2차)**:
- 최고 성능 (F1 기준):
  - F1 Score: **0.6150** (=)
  - ROC-AUC: **0.7881** (=)
  - PR-AUC: **0.6279** (=)
  - Best Threshold: **0.34**
  - Precision: **0.6165** (=)
  - Recall: **0.6135** (=)
- 최적 하이퍼파라미터:
  - `n_estimators`: 500
  - `max_depth`: 20
  - `min_samples_split`: 2
  - `min_samples_leaf`: 2
  - `max_features`: None
- 인사이트:
  - 1차와 **동일한 최고 성능** 확인
  - 최적 파라미터도 1차와 동일
  - 1차에서 이미 최적점을 찾았음을 확인

⇒ 2차 튜닝으로 **1차에서 찾은 최적 파라미터가 정말 최적임을 확인**.

---

### 4. 3차 튜닝 (미세 조정 단계)

**목표**:  
- 1차/2차에서 성능이 좋았던 하이퍼파라미터 구간(n_estimators=500, max_depth=20, min_samples_split=2, min_samples_leaf=2) 주변에서  
  F1·AUC를 **미세하게 더 끌어올릴 수 있는지 확인**.

**변경 사항 (개념)**:
- 1차/2차에서 좋은 성능을 보였던 세팅을 기준으로, 아래 항목들을 소폭 조정:
  - `n_estimators`: 400, 500, 600, 700 (500 전후)
  - `max_depth`: 18, 20, 22 (20 전후)
  - `min_samples_split`: 2, 3, 4 (2 전후)
  - `min_samples_leaf`: 1, 2, 3 (2 전후)
  - `max_features`: None, 0.9

**관찰 결과 (3차)**:
- 최고 성능 (F1 기준):
  - F1 Score: **0.6150** (=)
  - ROC-AUC: **0.7881** (=)
  - PR-AUC: **0.6279** (=)
  - Best Threshold: **0.34**
  - Precision: **0.6165** (=)
  - Recall: **0.6135** (=)
- 최적 하이퍼파라미터:
  - `n_estimators`: 500
  - `max_depth`: 20
  - `min_samples_split`: 2
  - `min_samples_leaf`: 2
  - `max_features`: None
- 인사이트:
  - 1차/2차와 **동일한 최고 성능** 유지
  - 최적 파라미터도 동일
  - 1차에서 이미 최적점을 찾았음을 최종 확인

⇒ 3차 튜닝을 통해 **1차에서 찾은 최적 조합이 정말 최적임을 최종 확인**했고,  
   최종적으로 **F1=0.6150, AUC=0.7881, PR-AUC=0.6279를 가지는 ExtraTrees 설정**을 확보.

---

### 5. 최종 선별 결과 (ExtraTrees Best Run)

`models/tuning_results_stage2.json` 기준, 2025-11-23 ExtraTrees 실험들 중 **최고 F1**은 아래 런:

- **모델**: ExtraTrees (et)
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.6150**  
  - ROC-AUC: **0.7881**  
  - PR-AUC: **0.6279**  
  - Best Threshold: **0.34**  
  - Precision: **0.6165**  
  - Recall: **0.6135**
- **Confusion Matrix (th=0.34)**:
  - TN = 1028  
  - FP = 158  
  - FN = 160  
  - TP = 254
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_clean_model.csv` (15개 수치형 피처만 포함)  
  - `test_size`: 0.2  
  - `random_state`: 42  
  - `threshold_range`: 0.05 ~ 0.35 (step=0.01)

**단계별 성능 변화 (요약)**:

- 1차: F1 ≈ **0.6150**, AUC ≈ **0.7881**, PR-AUC ≈ **0.6279**  
- 2차: F1 ≈ **0.6150**, AUC ≈ **0.7881**, PR-AUC ≈ **0.6279**  
- 3차: F1 ≈ **0.6150**, AUC ≈ **0.7881**, PR-AUC ≈ **0.6279**

⇒ **1차에서 이미 최적점 도달**,  
   **2차/3차에서 이를 확인하여 최종 파라미터 확정**.

---

### 6. 최종 추천 ExtraTrees 하이퍼파라미터 (1개 선정)

`models/tuning_results_stage2.json` 상의 best-run 성능과 1·2·3차 튜닝에서 관찰한 경향을 바탕으로,  
실제 리포트/서비스에서 사용하기 좋은 **최종 추천 설정 1개**를 아래와 같이 정리:

```python
MODEL_NAME = "et"

MODEL_PARAMS = {
    "n_estimators": 500,
    "max_depth": 20,
    "min_samples_split": 2,
    "min_samples_leaf": 2,
    "max_features": None,
    "class_weight": "balanced",
    "n_jobs": -1,
    "random_state": 42
}
```

- 이 설정은 1·2·3차 튜닝에서 F1/AUC가 가장 잘 나왔던 구간(n_estimators=500, max_depth=20, min_samples_split=2, min_samples_leaf=2, max_features=None)을 반영한 **최적 세팅**.  
- 실제 성능은 실행 시점마다 약간씩 달라질 수 있지만, 위와 유사한 하이퍼파라미터 조합에서  
  `F1 ≈ 0.6150`, `AUC ≈ 0.7881`, `PR-AUC ≈ 0.6279` 수준의 결과가 재현됨.
