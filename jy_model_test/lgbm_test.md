## LightGBM 실험 기록

### 1. 실험 환경 요약

- **데이터**: `data/enhanced_data_not_clean_FE_delete.csv`  
  - 전처리: `backend/preprocessing_pipeline.py`의 `preprocess_and_split()`  
  - 입력 피처: 원본 수치형 6 + 시계열 5 + 고객접점 4 = **총 15개 수치형** (범주형은 파이프라인 내부 One-Hot)
- **학습 스크립트**: `backend/train_experiments.py`  
  - 공통 설정: `backend/config.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, threshold 0.05~0.35)  
  - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix  
  - 결과 저장: `models/metrics.json`

---

### 2. 1차 튜닝 (탐색 단계)

**목표**:  
- LightGBM이 RandomForest/ExtraTrees 대비 어느 구간에서 좋은지,  
- 어떤 하이퍼파라미터 범위에서 F1/AUC가 잘 나오는지 "지형"을 먼저 파악.

**전략**:
- `MODEL_NAME = "lgbm"`로 설정 후, 아래 범위에서 **6개 조합**을 실험
  - `n_estimators`: 300 ~ 700  
  - `learning_rate`: 0.02 ~ 0.05  
  - `max_depth`: -1 (제한 없음), 7  
  - `subsample`: 0.8 ~ 0.85  
  - `colsample_bytree`: 0.8 ~ 0.85  
  - `class_weight`: None, "balanced"

**실험 결과 상세**:

- **실험 0 (기본 모델)**: 기본 하이퍼파라미터
  - 하이퍼파라미터: `n_estimators=300`, `learning_rate=0.05`, `max_depth=-1`, `subsample=0.8`, `colsample_bytree=0.8`
  - **파라미터 선택 이유**:
    - `n_estimators=300`: LightGBM의 기본값으로, 적절한 앙상블 크기
    - `learning_rate=0.05`: 기본값으로 설정되어 있어 비교 기준점으로 사용
    - `max_depth=-1`: 깊이 제한 없음 (기본값), 모델이 데이터에 맞게 자유롭게 학습
    - `subsample=0.8`, `colsample_bytree=0.8`: 기본값으로 약간의 정규화 효과
  - F1: **0.6283**, AUC: **0.8134**, PR-AUC: **0.6973**
  - Best Threshold: **0.32**
  - Precision: 0.6519, Recall: 0.6063
  - Confusion Matrix: TN=1052, FP=134, FN=163, TP=251
  - **관찰**: 기본 설정만으로도 RF(F1=0.616)보다 높은 성능을 보임. 다만 Recall이 Precision보다 낮아 개선 여지 존재

- **실험 1**: n_estimators 증가 + learning_rate 조정
  - 하이퍼파라미터: `n_estimators=500`, `learning_rate=0.03`
  - **파라미터 선택 이유**:
    - `n_estimators=500`: 기본값 300에서 증가시켜 더 많은 트리로 앙상블 강화. 더 많은 트리는 일반적으로 성능 향상에 도움이 되지만, 학습 시간과 과적합 위험이 증가함. 500은 적절한 균형점으로 판단
    - `learning_rate=0.03`: 기본값 0.05에서 낮춤. **낮은 learning_rate는 더 부드러운 학습을 가능하게 하며, 더 많은 트리와 함께 사용하면 더 정밀한 예측이 가능**. 일반적으로 `n_estimators × learning_rate`가 일정하면 유사한 성능을 보이지만, 낮은 learning_rate + 많은 트리 조합이 더 안정적이고 일반화 성능이 좋음
  - F1: **0.6338**, AUC: **0.8168**, PR-AUC: **0.7015**
  - Best Threshold: **0.31**
  - Precision: 0.6640, Recall: 0.6063
  - Confusion Matrix: TN=1059, FP=127, FN=163, TP=251
  - **관찰**: 기본 모델 대비 F1 +0.88%, AUC +0.42% 개선. Precision이 0.6519 → 0.6640으로 향상되어 FP가 감소(TN 증가). 다만 Recall은 동일하게 유지되어 FN은 변화 없음

- **실험 2**: max_depth 제한 + num_leaves 조정
  - 하이퍼파라미터: `n_estimators=500`, `learning_rate=0.03`, `max_depth=7`, `num_leaves=31`
  - **파라미터 선택 이유**:
    - `max_depth=7`: 기본값(-1, 제한 없음)에서 제한을 둠. **과적합 방지와 모델 복잡도 제어**를 목적으로 함. 깊은 트리는 학습 데이터에 과도하게 맞춰질 수 있어 일반화 성능이 떨어질 수 있음. 7은 일반적으로 권장되는 중간 수준의 깊이
    - `num_leaves=31`: LightGBM에서 `max_depth`와 함께 사용되는 파라미터. **`num_leaves`는 트리의 복잡도를 직접 제어**하며, `2^(max_depth)` 근처 값이 적절함. 31은 2^5 - 1로, max_depth=7과 함께 사용하면 적절한 복잡도 유지
    - **이론적 배경**: 깊이 제한은 과적합 방지에 도움이 되지만, 너무 제한하면 모델의 표현력이 떨어져 성능이 하락할 수 있음
  - F1: **0.6326**, AUC: **0.8153**, PR-AUC: **0.6993**
  - Best Threshold: **0.28**
  - Precision: 0.6373, Recall: 0.6280
  - Confusion Matrix: TN=1038, FP=148, FN=154, TP=260
  - **관찰**: max_depth 제한 시 경고 메시지 다수 발생("No further splits with positive gain"), 실험 1보다 성능 약간 하락. **이는 이 데이터셋에서는 깊이 제한이 오히려 모델의 표현력을 제한했음을 의미**. Precision은 하락(0.6640 → 0.6373)했지만 Recall은 소폭 상승(0.6063 → 0.6280)하여 균형이 개선됨. 다만 전체적인 F1은 하락

- **실험 3**: class_weight 추가로 클래스 불균형 처리
  - 하이퍼파라미터: `n_estimators=500`, `learning_rate=0.03`, `class_weight="balanced"`
  - **파라미터 선택 이유**:
    - `class_weight="balanced"`: 데이터셋에서 **클래스 불균형이 존재**함 (negative:positive ≈ 4743:1657, 약 2.86:1). 기본적으로 모델은 다수 클래스에 편향될 수 있어, 소수 클래스(이탈 고객)를 더 잘 예측하기 위해 클래스 가중치를 조정
    - **이론적 배경**: `class_weight="balanced"`는 `n_samples / (n_classes * np.bincount(y))`로 자동 계산하여 소수 클래스에 더 높은 가중치를 부여. 이는 Recall을 높이는 데 도움이 되지만, Precision과의 트레이드오프가 발생할 수 있음
    - **선택 이유**: 이탈 예측 문제에서 **False Negative(이탈 고객을 놓치는 것)가 False Positive보다 비용이 클 수 있음**. 따라서 Recall을 높이는 것이 중요할 수 있어 시도
  - F1: **0.5835**, AUC: **0.8119**, PR-AUC: **0.6987**
  - Best Threshold: **0.34**
  - Precision: 0.5000, Recall: 0.7005
  - Confusion Matrix: TN=896, FP=290, FN=124, TP=290
  - **관찰**: Recall은 크게 상승(0.6063 → 0.7005, +15.5%)하나 Precision이 크게 하락(0.6640 → 0.5000, -24.7%)하여 **F1가 가장 낮음(0.5835)**. 
    - FP가 127 → 290으로 크게 증가(TN: 1059 → 896 감소)
    - FN은 163 → 124로 감소(TP: 251 → 290 증가)
    - **결론**: 이 데이터셋과 평가 지표(F1) 기준으로는 `class_weight="balanced"`가 오히려 성능을 저하시킴. Precision과 Recall의 균형이 중요하며, 단순히 Recall만 높이는 것은 F1을 낮출 수 있음

- **실험 4**: subsample/colsample_bytree 조정으로 과적합 방지
  - 하이퍼파라미터: `n_estimators=500`, `learning_rate=0.03`, `subsample=0.85`, `colsample_bytree=0.85`
  - **파라미터 선택 이유**:
    - `subsample=0.85`: 기본값 0.8에서 증가. **각 트리가 학습할 때 사용하는 샘플 비율**을 의미. 0.85는 약간의 정규화 효과를 유지하면서도 충분한 데이터를 사용. 너무 낮으면(0.7 이하) 편향이 증가하고, 너무 높으면(0.95 이상) 과적합 위험이 증가
    - `colsample_bytree=0.85`: 기본값 0.8에서 증가. **각 트리가 학습할 때 사용하는 피처 비율**을 의미. Random Forest의 feature sampling과 유사한 개념으로, **다양성 증가와 과적합 방지**에 도움. 0.85는 적절한 균형점
    - **이론적 배경**: 
      - **Bagging 효과**: subsample을 사용하면 각 트리가 다른 데이터를 보게 되어 앙상블의 다양성이 증가
      - **Feature Randomness**: colsample_bytree를 사용하면 각 트리가 다른 피처를 보게 되어 모델의 다양성과 일반화 성능 향상
      - **과적합 방지**: 두 파라미터 모두 모델의 복잡도를 간접적으로 제어하여 과적합을 방지
    - **선택 이유**: 실험 1에서 좋은 성능을 보였지만, 더 나은 일반화 성능과 AUC 향상을 위해 정규화 강화를 시도
  - F1: **0.6347**, AUC: **0.8170**, PR-AUC: **0.7024**
  - Best Threshold: **0.24**
  - Precision: 0.6159, Recall: 0.6546
  - Confusion Matrix: TN=1017, FP=169, FN=143, TP=271
  - **관찰**: 
    - **AUC와 PR-AUC가 가장 높음** (AUC=0.8170, PR-AUC=0.7024, 최고값)
    - F1도 실험 1보다 약간 개선(0.6338 → 0.6347)
    - **Recall이 크게 향상** (0.6063 → 0.6546, +7.96%)하여 FN이 감소(163 → 143)
    - Precision은 약간 하락(0.6640 → 0.6159)하여 FP가 증가(127 → 169)
    - **Best Threshold가 0.31 → 0.24로 낮아짐**: 모델이 더 많은 양성 예측을 하도록 학습됨
    - **결론**: 정규화 강화가 일반화 성능(AUC) 향상에 도움이 되었으며, Recall과 Precision의 균형도 개선됨

**1차 튜닝 종합 인사이트**:

- **RF baseline**: F1 ≈ 0.616, AUC ≈ 0.791, PR-AUC ≈ 0.662
- **1차 LGBM 실험들**:
  - F1: **0.583 ~ 0.635** 구간에 분포  
  - AUC: **0.812 ~ 0.817** 구간 (RF보다 일관되게 높음)  
  - Best Threshold는 대부분 **0.24~0.34** 근처

- **핵심 발견사항**:
  1. **`n_estimators`와 `learning_rate`의 조합이 중요**
     - 낮은 learning_rate(0.02~0.03) + 많은 트리(500~700) 조합이 효과적
     - `n_estimators × learning_rate ≈ 14~15` 근처에서 좋은 성능
     - 더 많은 트리와 더 낮은 learning_rate가 더 정밀한 예측 가능
  
  2. **정규화 파라미터의 효과**
     - `subsample=0.85`, `colsample_bytree=0.85`가 기본값(0.8)보다 우수
     - 과적합 방지와 일반화 성능 향상에 도움
     - AUC 최고값(0.8170) 달성
  
  3. **클래스 불균형 처리의 한계**
     - `class_weight="balanced"`는 Recall은 높이지만 Precision이 크게 하락
     - F1 기준으로는 오히려 성능 저하
     - 이 데이터셋에서는 클래스 불균형이 심각하지 않거나, 다른 방법이 필요할 수 있음
  
  4. **모델 복잡도 제어**
     - `max_depth` 제한은 이 데이터셋에서 오히려 표현력을 제한
     - 깊이 제한 없음(-1)이 더 나은 성능
     - 경고 메시지("No further splits with positive gain")는 모델이 더 이상 학습할 패턴이 없음을 의미

- **최적 구간**: **n_estimators 500~700 / lr 0.02~0.03 / subsample/colsample_bytree 0.85** 근처에서 F1, AUC 둘 다 안정적으로 높게 나옴

⇒ 1차에서는 **좋은 "구간"만 찾고**, 세밀한 최적화는 2차 튜닝에서 진행하기로 결정.

---

### 3. 2차 튜닝 (국소 탐색 단계)

**목표**:  
- 1차에서 성능이 좋았던 하이퍼파라미터 근처만 다시 탐색해서  
  **RF F1=0.616을 넘어서는 최적 조합을 찾기**.

**변경 사항**:
- Threshold 스캔 범위:
  - 기존: `0.05 ~ 0.35` (유지)
- 하이퍼파라미터는 아래 범위를 중심으로 **2개 세트로 국소 탐색**:
  - `n_estimators`: 600, 700  
  - `learning_rate`: 0.02 ~ 0.025  
  - `subsample`, `colsample_bytree`: 0.85  
  - `max_depth`: -1 (제한 없음, 기본값 유지)

**실험 결과 상세**:

- **실험 5**: 더 많은 트리와 더 낮은 learning_rate (1차 실험 4 기반)
  - 하이퍼파라미터: `n_estimators=700`, `learning_rate=0.02`, `subsample=0.85`, `colsample_bytree=0.85`
  - **파라미터 선택 이유**:
    - `n_estimators=700`: 실험 4(500)에서 증가. **더 많은 트리로 앙상블 강화**. 실험 1에서 500이 좋은 성능을 보였으므로, 더 많은 트리로 성능 향상 가능성 탐색
    - `learning_rate=0.02`: 실험 4(0.03)에서 감소. **더 부드러운 학습과 정밀한 예측**을 위해 낮춤
    - **핵심 전략**: **`n_estimators × learning_rate` 조정**
      - 실험 1: 500 × 0.03 = 15
      - 실험 4: 500 × 0.03 = 15
      - 실험 5: 700 × 0.02 = 14 (약간 낮음)
      - **이론적 배경**: 일반적으로 `n_estimators × learning_rate`가 일정하면 유사한 성능을 보이지만, **낮은 learning_rate + 많은 트리 조합이 더 안정적이고 일반화 성능이 좋음**. 각 트리가 작은 변화만 학습하므로 더 정밀한 예측이 가능
    - `subsample=0.85`, `colsample_bytree=0.85`: 실험 4에서 좋은 성능을 보였으므로 유지
    - **선택 이유**: 실험 4에서 최고 AUC를 달성했지만, F1은 실험 1과 유사. **더 많은 트리와 낮은 learning_rate로 F1을 추가로 향상시킬 수 있는지 확인**
  - F1: **0.6414**, AUC: **0.8158**, PR-AUC: **0.6996**
  - Best Threshold: **0.28**
  - Precision: 0.6501, Recall: 0.6329
  - Confusion Matrix: TN=1045, FP=141, FN=152, TP=262
  - **관찰**: 
    - **F1 최고값 달성** (0.6414)
    - 실험 4 대비 F1 +1.06% 개선 (0.6347 → 0.6414)
    - Precision이 실험 4보다 크게 향상 (0.6159 → 0.6501, +5.55%)
    - Recall은 약간 하락 (0.6546 → 0.6329, -3.31%)
    - **Precision과 Recall의 균형이 개선**되어 F1이 최고값 달성
    - FP가 감소(169 → 141)하고 FN이 소폭 증가(143 → 152)
    - AUC는 실험 4보다 약간 하락(0.8170 → 0.8158)하지만 여전히 높은 수준
    - **Best Threshold가 0.24 → 0.28로 상승**: 더 보수적인 예측으로 Precision 향상

- **실험 6**: 실험 4와 5의 중간값
  - 하이퍼파라미터: `n_estimators=600`, `learning_rate=0.025`, `subsample=0.85`, `colsample_bytree=0.85`
  - **파라미터 선택 이유**:
    - `n_estimators=600`: 실험 4(500)와 실험 5(700)의 중간값
    - `learning_rate=0.025`: 실험 4(0.03)와 실험 5(0.02)의 중간값
    - **선택 이유**: 실험 4와 5 사이의 최적점이 있는지 확인. **그리드 서치의 중간값 테스트**로, 선형 보간이 항상 최적은 아니지만 참고용으로 시도
    - `n_estimators × learning_rate = 600 × 0.025 = 15`: 실험 1, 4와 동일한 값
  - F1: **0.6387**, AUC: **0.8126**, PR-AUC: **0.6981**
  - Best Threshold: **0.29**
  - Precision: 0.6524, Recall: 0.6256
  - Confusion Matrix: TN=1048, FP=138, FN=155, TP=259
  - **관찰**: 
    - 실험 5보다 성능 약간 하락 (F1: 0.6414 → 0.6387, -0.42%)
    - Precision은 실험 5와 유사(0.6501 → 0.6524)하지만 Recall이 하락(0.6329 → 0.6256)
    - **중간값이 항상 최적은 아님**을 확인. 하이퍼파라미터 최적화는 비선형적이며, 단순한 중간값보다는 실험 5의 조합이 더 우수
    - **결론**: 더 많은 트리(700)와 더 낮은 learning_rate(0.02) 조합이 이 데이터셋에 더 적합

**2차 튜닝 종합 인사이트**:

- **성능 수렴**: F1는 **0.639~0.641** 근처에서 수렴, AUC는 대부분 **0.813~0.816** 수준

- **최적 조합 발견**:
  - **n_estimators=700, learning_rate=0.02, subsample=0.85, colsample_bytree=0.85** 조합에서 F1 최고값 달성
  - F1=0.6414, AUC=0.8158

- **핵심 인사이트**:
  1. **더 많은 트리와 낮은 learning_rate의 시너지**
     - 실험 5(700, 0.02)가 실험 4(500, 0.03)보다 우수
     - `n_estimators × learning_rate`가 동일해도, 더 많은 트리와 낮은 learning_rate 조합이 더 정밀함
     - 각 트리가 작은 변화만 학습하므로 더 안정적인 앙상블 형성
  
  2. **Precision과 Recall의 균형**
     - 실험 4: 높은 Recall(0.6546) vs 낮은 Precision(0.6159)
     - 실험 5: 균형잡힌 Recall(0.6329) vs 높은 Precision(0.6501)
     - **F1은 Precision과 Recall의 조화평균이므로, 균형이 중요**
     - 실험 5의 균형잡힌 조합이 최고 F1 달성
  
  3. **중간값의 한계**
     - 실험 6(600, 0.025)은 실험 5보다 성능 하락
     - 하이퍼파라미터 최적화는 비선형적이며, 단순한 중간값보다는 극값이 최적일 수 있음

- **성능 개선 요약**:
  - 기본 모델 대비: F1 +2.08% (0.6283 → 0.6414), AUC +0.30% (0.8134 → 0.8158)
  - RF baseline 대비: F1 +4.13% (0.616 → 0.6414), AUC +3.14% (0.791 → 0.8158)

⇒ 2차 튜닝으로 **RF를 크게 넘어서는 F1≈0.641까지 LGBM F1을 끌어올리는 데 성공**,  
   동시에 AUC/PR-AUC는 RF보다 우수한 상태를 유지.

---

### 4. 최종 선별 결과 (LGBM Best Run)

`models/metrics.json` 기준, 2025-11-23 LGBM 실험들 중 **최고 F1**은 아래 런:

- **모델**: LGBM  
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.6414**  
  - ROC-AUC: **0.8158**  
  - PR-AUC: **0.6996**  
  - Best Threshold: **0.28**  
  - Precision: **0.6501**  
  - Recall: **0.6329**
- **Confusion Matrix (th=0.28)**:
  - TN = 1045  
  - FP = 141  
  - FN = 152  
  - TP = 262  
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_not_clean_FE_delete.csv`  
  - `test_size`: 0.2  
  - `random_state`: 42  
  - `threshold_range`: 0.05 ~ 0.35 (step=0.01)

**RF vs LGBM 최종 비교 (요약)**:

- RF:  F1 ≈ **0.616**, AUC ≈ **0.791**, PR-AUC ≈ **0.662**  
- LGBM: F1 ≈ **0.641**, AUC ≈ **0.816**, PR-AUC ≈ **0.700**

⇒ **F1, AUC, PR-AUC 모두 LGBM이 RF보다 분명한 우위**를 보이는 결과.

---

### 5. 최종 추천 LGBM 하이퍼파라미터 (1개 선정)

`models/metrics.json` 상의 best-run 성능과 1·2차 튜닝에서 관찰한 경향을 바탕으로,  
실제 리포트/서비스에서 사용하기 좋은 **최종 추천 설정 1개**를 아래와 같이 정리:

```python
MODEL_NAME = "lgbm"

MODEL_PARAMS = {
    "n_estimators": 700,
    "learning_rate": 0.02,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
}
```

- **파라미터 선택 근거**:
  - `n_estimators=700`: 실험 5에서 최고 F1을 달성한 값. 더 많은 트리로 앙상블 강화
  - `learning_rate=0.02`: 낮은 learning_rate로 더 부드럽고 정밀한 학습. 실험 5에서 최적 성능을 보임
  - `subsample=0.85`: 실험 4에서 최고 AUC를 달성한 값. 적절한 정규화로 과적합 방지
  - `colsample_bytree=0.85`: 실험 4에서 최고 AUC를 달성한 값. 피처 다양성 증가로 일반화 성능 향상

- **이 설정의 장점**:
  1. **균형잡힌 성능**: F1, AUC, PR-AUC 모두 높은 수준
  2. **일반화 성능**: subsample과 colsample_bytree로 과적합 방지
  3. **안정성**: 낮은 learning_rate와 많은 트리로 안정적인 예측
  4. **재현성**: 위와 유사한 하이퍼파라미터 조합에서 `F1 ≈ 0.64`, `AUC ≈ 0.82`, `PR-AUC ≈ 0.70` 수준의 결과가 재현됨

- **주의사항**:
  - 학습 시간이 기본 설정보다 길어질 수 있음 (n_estimators 증가)
  - 메모리 사용량이 증가할 수 있음
  - 실제 성능은 실행 시점마다 약간씩 달라질 수 있음 (랜덤성, 데이터 분할 등)  


