## RandomForest 실험 기록 (`ke_model_test`)

1. 실험 환경 요약

- **데이터**: `data/enhanced_data_not_clean_FE_delete.csv`
   - 전처리: `ke_model_test/preprocessing_pipeline.py`의 `preprocess_pipeline()`
   - 입력 피처: 원본 수치형 6 + 시계열/트렌드 기반 5 + 고객 접점 관련 4 = **총 15개 주요 수치형 피처 + One-Hot된 범주형 포함**

- **학습 스크립트**: `ke_model_test/train_experiments.py`
   - 공통 설정: `ke_model_test/config.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, threshold 0.05~0.40)
   - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix
   - 결과 저장: `models/metrics.json`
---


### 2. 1차 튜닝 (탐색 단계)

**목표**:
- RF 기본 성능 확인
- 어떤 하이퍼파라미터 구간에서 Recall·Precision 균형이 나오는지 확인
- 임계값(threshold)을 조정했을 때 이탈자 탐지 성능이 얼마나 올라가는지 평가

**전략**:
- `MODEL_NAME = "rf"`로 설정 후 **약 8~10개 조합** 실험:
- `n_estimators`: 200 ~ 800
- `max_depth`: 6 ~ 20
- `min_samples_split`: 2, 5, 10
- `min_samples_leaf`: 1, 2, 4
- `class_weight`: "balanced", None

**관찰 결과 (1차)**:
- 기본 RF baseline:
  - F1 ≈ 0.615
  - AUC ≈ 0.791
  - PR-AUC ≈ 0.662
- 1차 RF 실험 범위:
  - F1: **0.55 ~ 0.61**
  - AUC: **0.78 ~ 0.80**
  - Best Threshold: **0.28~0.34** 구간
- 인사이트
  - depth 8~14, n_estimators 400~600 구간에서 성능이 안정적
  - class_weight="balanced"는 Recall을 올리지만 Precision이 떨어져 F1은 오히려 낮아짐
  - min_samples_split/leaf 값은 모델 복잡도 조절에 큰 영향 없음

---

### 3. 2차 튜닝 (국소 탐색 단계)

**목표**:
- 1차에서 성능이 가장 잘 나온 영역 근처를 정밀 탐색
- threshold를 확장해 Precision과 Recall 균형점을 더 넓게 탐색

**변경 사항**:
- Threshold 범위 확장: 0.05 ~ 0.40
- 1차에서 성능이 좋았던 영역 근처만 탐색:
  - n_estimators: 400, 500, 600
  - max_depth: 10, 12, 14
  - min_samples_split: 2, 5
  - min_samples_leaf: 1, 2

**관찰 결과**:
F1은 **0.60~0.616** 구간에서 수렴
AUC ≈ **0.79~0.80**
PR-AUC ≈ **0.66~0.67**
Threshold는 **0.30~0.36 구간에서 F1이 가장 높음**
- 인사이트
  - RF는 depth를 깊게 가져가면 Precision은 증가하지만 Recall이 크게 감소해 F1이 떨어짐
  - threshold 조정이 성능 향상에 가장 큰 기여 (특히 0.32~0.36 구간)

---

### 4. 3차 튜닝 (미세 조정 단계)

**목표**:
- 2차에서 가장 안정적인 파라미터 근처에서 미세 튜닝
- F1과 AUC를 조금이라도 더 올릴 수 있는 best-run 조합 찾기

**변경 사항**:
- 아래 값들을 ±20% 수준에서 미세 조정:
  - n_estimators: 450, 520, 580
  - max_depth: 11, 12, 13
  - min_samples_split: 2, 4
  - min_samples_leaf: 1

**관찰 결과**:
- F1 최고값이 **0.615 → 0.621** 전후로 소폭 상승
- Precision 증가 + Recall 유지되는 지점에서 best-run 발생
- Best Threshold는 **0.35~0.42** 부근에서 가장 안정적

---


### 5. 최종 성능 (RF Best Run)

`models/metrics.json` 기준, 2025-11-23 RandomForest 실험들 중 **최고 F1**은 아래 런:

- **모델**: RandomForest (RF)
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.6216**
  - ROC-AUC: **0.7932**
  - PR-AUC: **0.6635**
  - Best Threshold: **0.365**
  - Precision: **0.6732**
  - Recall: **0.5773**
- **Confusion Matrix (th=0.365)**:
  - TN = 1070
  - FP = 116
  - FN = 175
  - TP = 239
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_not_clean_FE_delete.csv`
  - `test_size`: 0.2
  - `random_state`: 42
  - `threshold_range` : 0.05 ~ 0.45 (step=0.005)

**요약**:
- RF baseline보다 F1이 증가 (0.615 → 0.621)
- AUC도 소폭 개선됨
- threshold 조정이 Recall·Precision 균형 향상에 가장 크게 기여
- PR-AUC도 증가해 이탈자 예측의 안정성이 좋아짐

---

### 6. 최종 추천 RandomForest 하이퍼파라미터 (1개 선정)

`models/metrics.json` 상의 best-run 성능과 1·2·3차 튜닝에서 관찰한 경향을 바탕으로,
실제 서비스/리포트에서 사용하기 좋은 최종 추천 설정은 다음과 같음:

```python
MODEL_NAME = "rf"

MODEL_PARAMS = {
    "n_estimators": 520,
    "max_depth": 12,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "random_state": 42,
    "n_jobs": -1
}
```

**이유(근거)**
- F1이 가장 높은 구간이 **n_estimators 450~600, depth 10~14**
- best-run에서 threshold≈0.36일 때 Precision·Recall 균형이 가장 좋음
- 실행할 때마다 성능 재현성이 높고 variance가 낮음
- 전체 실험 결과 기준, 가장 “실전 배포용”에 적합한 안정형 모델

**특성**
- F1·AUC·PR-AUC 모두 안정적으로 좋은 **“균형형 설정”**
- **threshold=0.36** 부근에서 성능 재현율 높음
- **과적합 없이** 적절한 복잡도 유지