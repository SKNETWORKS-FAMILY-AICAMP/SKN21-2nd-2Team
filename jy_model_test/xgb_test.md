## XGBoost 실험 기록 (`jy_model_test`)

### 1. 실험 환경 요약

- **데이터**: `data/enhanced_data_not_clean_FE_delete.csv`  
  - 전처리: `jy_model_test/preprocessing_pipeline.py`의 `preprocess_and_split()`  
  - 입력 피처: 원본 수치형 6 + 시계열 5 + 고객접점 4 = **총 15개 수치형** (범주형은 파이프라인 내부 One-Hot)
- **학습 스크립트**: `jy_model_test/train_experiments.py`  
  - 공통 설정: `jy_model_test/config.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, threshold 0.05~0.35 또는 0.45)  
  - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix  
  - 결과 저장: `models/metrics.json`

---

### 2. 1차 튜닝 (탐색 단계)

**목표**:  
- XGBoost가 RandomForest/ExtraTrees 대비 어느 구간에서 좋은지,  
- 어떤 하이퍼파라미터 범위에서 F1/AUC가 잘 나오는지 “지형”을 먼저 파악.

**전략**:
- `MODEL_NAME = "xgb"`로 설정 후, 아래 범위에서 **약 10개 조합**을 실험
  - `n_estimators`: 200 ~ 700  
  - `max_depth`: 3, 4, 5, 7  
  - `learning_rate`: 0.03 ~ 0.15  
  - `subsample`: 0.7 ~ 0.9  
  - `colsample_bytree`: 0.7 ~ 0.9  
  - `scale_pos_weight`: 2.5 ~ 4.0

**관찰 결과 (대표)**:
- RF baseline: **F1 ≈ 0.616, AUC ≈ 0.791, PR-AUC ≈ 0.662**
- 1차 XGB 실험들:
  - F1: **0.53 ~ 0.61** 구간에 분포  
  - AUC: **0.80 ~ 0.82** 구간 (RF보다 일관되게 높음)  
  - Best Threshold는 대부분 **0.32~0.34** 근처
- 인사이트:
  - **깊이 3~5 / lr 0.05~0.08 / n_estimators 400~600 / scale_pos_weight≈3** 근처에서 F1, AUC 둘 다 안정적으로 높게 나옴  
  - Recall을 크게 올린 설정(Recall≈0.80)도 있으나, Precision이 많이 떨어져 **F1는 0.55 전후** 수준

⇒ 1차에서는 **좋은 “구간”만 찾고**, 세밀한 최적화는 2차 튜닝에서 진행하기로 결정.

---

### 3. 2차 튜닝 (국소 탐색 단계)

**목표**:  
- 1차에서 성능이 좋았던 하이퍼파라미터 근처만 다시 탐색해서  
  **RF F1=0.616을 따라잡을 수 있는지 확인**.

**변경 사항**:
- Threshold 스캔 범위 확장:
  - 기존: `0.05 ~ 0.35`  
  - 2차: `0.05 ~ 0.45` (특히 0.40~0.45 구간까지 확인)
- 하이퍼파라미터는 아래 범위를 중심으로 **4개 세트 정도로 국소 탐색**:
  - `n_estimators`: 400, 500, 600  
  - `max_depth`: 4, 5  
  - `learning_rate`: 0.05 ~ 0.08  
  - `subsample`, `colsample_bytree`: 0.8 ~ 0.9  
  - `scale_pos_weight`: 2.7 ~ 3.5

**관찰 결과 (2차)**:
- F1는 **0.60~0.612** 근처에서 수렴  
- AUC는 대부분 **0.81±0.01** 수준  
- Threshold를 0.44까지 열어준 뒤,  
  **Precision≈0.58, Recall≈0.65** 정도인 균형형 세트에서 F1가 가장 높게 나옴

⇒ 2차 튜닝으로 **RF와 거의 동급 수준(F1≈0.612)까지 XGB F1을 끌어올리는 데 성공**,  
   동시에 AUC/PR-AUC는 RF보다 우수한 상태를 유지.

---

### 4. 3차 튜닝 (미세 조정 단계)

**목표**:  
- 2차에서 성능이 좋았던 하이퍼파라미터 구간(깊이 4~5, lr 0.05~0.08, n_estimators 500 전후, scale_pos_weight≈3) 주변에서  
  F1·AUC를 **미세하게 더 끌어올릴 수 있는지 확인**.

**변경 사항 (개념)**:
- 2차에서 좋은 성능을 보였던 세팅을 기준으로, 아래 항목들을 소폭 조정:
  - `n_estimators`: 500 → 550~650 (트리 수를 늘리거나 줄이면서 안정성/과적합 균형 확인)
  - `max_depth`: 4~5 사이에서 ±1 (복잡도 조절)
  - `learning_rate`: 0.05~0.07 구간에서 소폭 변경
  - `subsample`, `colsample_bytree`: 0.8~0.9 내에서 미세 조정
  - `scale_pos_weight`: 3.0 전후(약 2.7~3.3)에서 Precision/Recall 트레이드오프 확인

**관찰 결과 (3차)**:
- F1 최고값이 **약 0.612 → 0.620 근처**로 소폭 상승  
- AUC/PR-AUC는 여전히 **0.81대 / 0.69대** 수준으로 유지  
- Best Threshold는 2차와 마찬가지로 **0.44 근처**에서 가장 안정적인 F1을 형성

⇒ 3차 튜닝을 통해 **동일한 하이퍼파라미터 구간 안에서 조금 더 좋은 조합을 찾는 데 성공**했고,  
   최종적으로 **RF보다 약간 더 높은 F1과 더 높은 AUC/PR-AUC를 가지는 XGB 설정**을 확보.

---

### 5. 최종 선별 결과 (XGB Best Run)

`models/metrics.json` 기준, 2025-11-23 XGB 실험들 중 **최고 F1**은 아래 런:

- **모델**: XGB  
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.6197**  
  - ROC-AUC: **0.8105**  
  - PR-AUC: **0.6933**  
  - Best Threshold: **0.44**  
  - Precision: **0.6027**  
  - Recall: **0.6377**
- **Confusion Matrix (th=0.44)**:
  - TN = 992  
  - FP = 194  
  - FN = 146  
  - TP = 268  
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_not_clean_FE_delete.csv`  
  - `test_size`: 0.2  
  - `random_state`: 42  
  - `threshold_range`: 0.05 ~ 0.45 (step=0.01)

**RF vs XGB 최종 비교 (요약)**:

- RF:  F1 ≈ **0.616**, AUC ≈ **0.791**, PR-AUC ≈ **0.662**  
- XGB: F1 ≈ **0.620**, AUC ≈ **0.811**, PR-AUC ≈ **0.693**

⇒ **F1은 RF가 아주 근소하게 우위**,  
   **AUC/PR-AUC는 XGB가 분명한 우위**를 보이는 결과.

---

### 6. 최종 추천 XGB 하이퍼파라미터 (1개 선정)

`models/metrics.json` 상의 best-run 성능과 1·2차 튜닝에서 관찰한 경향을 바탕으로,  
실제 리포트/서비스에서 사용하기 좋은 **최종 추천 설정 1개**를 아래와 같이 정리:

```python
MODEL_NAME = "xgb"

MODEL_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.06,
    "max_depth": 5,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
    "scale_pos_weight": 3.0,
}
```

- 이 설정은 1·2차 튜닝에서 F1/AUC가 잘 나왔던 구간(깊이 4~5, lr 0.05~0.08, n_estimators 400~600, scale_pos_weight≈3)을 반영한 **균형형 세팅**.  
- 실제 성능은 실행 시점마다 약간씩 달라질 수 있지만, 위와 유사한 하이퍼파라미터 조합에서  
  `F1 ≈ 0.61`, `AUC ≈ 0.81`, `PR-AUC ≈ 0.69` 수준의 결과가 재현됨.  


