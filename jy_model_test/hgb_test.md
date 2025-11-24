## HistGradientBoosting 실험 기록 (`ke_model_hgb_est`)

1. 실험 환경 요약

- **데이터**: `data/enhanced_data_not_clean_FE_delete.csv`
   - 전처리: `ke_model_test/preprocessing_pipeline.py`의 `preprocess_pipeline()`
   - 입력 피처: 원본 수치형 6 + 시계열/트렌드 기반 5 + 고객 접점 관련 4 = **총 15개 주요 수치형 피처 + One-Hot된 범주형 포함**

- **학습 스크립트**: `ke_model_test/train_experiments_hgb.py`
   - 공통 설정: `ke_model_test/config_hgb.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, threshold 0.05~0.40(step=0.005))
   - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix
   - 결과 저장: `models/metrics22.json`

---

### 2. 1차 튜닝 (탐색 단계)

**목표**:
- 기본 HGB(HistGradientBoostingClassifier)가 RF/XGB 대비 어떤 특성을 가지는지 확인
- F1·AUC가 잘 나오는 대략적인 구간 파악
- Threshold 영향 확인

**전략**:
- 기본값 + 소규모 튜닝 중심
- 아래 범위에서 실험 세트 구성:
  - `max_depth`: 3 ~ 5
  - `learning_rate`: 0.03 ~ 0.08
  - `max_bins`: 128 ~ 255
  - `l2_regularization`: 0 ~ 1
  - `min_samples_leaf`: 15 ~ 40

**관찰 결과 (1차)**:
- F1: **0.618 ~ 0.643** 구간
- AUC: **0.806 ~ 0.814**
- PR-AUC: **0.691 ~ 0.698**
- Best Threshold: **0.26 ~ 0.30**
- Precision/Recall 밸런스가 자연스럽게 맞춰지는 형태로
    → RF보다 **더 균형 있는 형태의 예측 경향**
- **인사이트**
  - HGB는 learning_rate가 낮고(≤0.07),
    **얕은 depth(3~4) + 충분한 Leaf 수**일 때 가장 안정적
  - Threshold는 거의 항상 **0.26~0.30**에서 수렴
  - Recall 상승이 잘 되는 구조라, RF/XGB 대비
    **“적절히 균형적인 모델"**의 느낌이 강함

---

### 3. 2차 튜닝 (국소 탐색)

**목표**:
- 1차에서 잘 나온 하이퍼파라미터 근처에서 F1을 조금 더 끌어올리기
- Precision·Recall 균형을 유지한 채 성능 향상 가능성 확인

**변경 사항**:
- learning_rate: 0.04 ~ 0.07
- max_depth: 3, 4
- min_samples_leaf: 15 ~ 25
- l2_regularization: 0.0 ~ 0.5
- max_bins: 200~255


**관찰 결과**:
가장 높은 F1이 **0.6427** 근처에서 형성
AUC는 **0.809±0.003** 수준
PR-AUC는 **0.691~0.698**, XGB 대비 약 0.01~0.02 낮음
Threshold는 **0.26** 근처가 안정적
- **인사이트**
  - threshold 최적화 기반의 F1 튜닝에서
    **0.26~0.30** 범위에서 최고 성능을 안정적으로 달성한다는 점이 강점.
  - 불균형 데이터(Churn) 환경에서 Precision과 Recall을 동시에 잡는 균형형 모델로 매우 적합한 선택임을 확인.

---

### 4. 최종 성능 (RF Best Run)

`models/metrics22.json` 기준, 2025-11-23 HistGradientBoosting 실험들 중 **최고 F1**은 아래 런:

- **모델**: HistGradientBoosting (HGB)
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.6427**
  - ROC-AUC: **0.8093**
  - PR-AUC: **0.6910**
  - Best Threshold: **0.26**
  - Precision: **0.6381**
  - Recall: **0.6473**
- **Confusion Matrix (th=0.26)**:
  - TN = 1034
  - FP = 152
  - FN = 146
  - TP = 268
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_not_clean_FE_delete.csv`
  - `test_size`: 0.2
  - `random_state`: 42
  - `threshold_range` : 0.05 ~ 0.45 (step=0.005)

**요약**:
- **Recall = 0.6473** → churn 유저(Positive)를 놓치지 않는 성향
- **Precision = 0.6381** → 과도한 False Positive 없이 균형 유지
- **F1 = 0.6427**는 RF(≈0.616), XGB(≈0.620)보다 가장 높은 값
- AUC는 XGB(≈0.81)에 근접, RF보다 우수

**F1 점수 기준 HGB가 팀 모델 중 최고 성능 모델**
(AUC/PR-AUC는 XGB가 조금 더 우수)

---

### 5. 최종 추천 HistGradientBoosting 하이퍼파라미터 (1개 선정)

`models/metrics22.json` 상의 위 관찰 결과 + best-run 기준으로 실제 레포트/서비스에 적합한 추천값은 아래와 같음:

```python
MODEL_NAME = "hgb"

MODEL_PARAMS = {
    "learning_rate": 0.06,
    "max_depth": 3,
    "max_bins": 255,
    "l2_regularization": 0.3,
    "min_samples_leaf": 20,
}

```

**이유(근거)**
- `max_depth=3`: 과적합 방지 + 안정적 일반화
- `blearning_rate=0.06`: 빠르지 않은 학습 속도 → 최적 F1 관측
- `max_bins=255`: 성능·시간 균형상 최적
- `min_samples_leaf=20`: 노이즈 제거 및 Recall 안정화
- `l2_regularization=0.3`: 중간값이 가장 안정적 성능

**비교**
| 모델                       | F1        | AUC    | PR-AUC | 비고              |
| ------------------------ | --------- | ------ | ------ | --------------- |
| **RandomForest**         | ~0.616    | ~0.791 | ~0.662 | baseline 대비 안정적 |
| **XGBoost**              | ~0.620    | ~0.810 | ~0.693 | AUC/PR-AUC 최강   |
| **HistGradientBoosting** | **0.643** | ~0.809 | ~0.691 | **F1 최고 모델**    |


**결론**
- **Churn 분류에서 F1 기준 HGB가 가장 우수한 모델로 선정 가능**
- AUC 중심 보고서를 만든다면 XGB도 좋은 선택
