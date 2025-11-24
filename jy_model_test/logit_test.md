## LogisticRegression 실험 기록 (`logit_model_test`)


1. 실험 환경 요약

- **데이터**: `data/enhanced_data_not_clean_FE_delete.csv`
   - 전처리: `logit_model_test/preprocessing_pipeline.py`의 `preprocess_pipeline()`
   - 입력 피처: 원본 수치형 6 + 시계열/트렌드 기반 5 + 고객 접점 관련 4 = **총 15개 주요 수치형 피처 + One-Hot된 범주형 포함**

- **학습 스크립트**: `logit_model_test/train_experiments.py`
   - 공통 설정: `logit_model_test/config.py` (`TEST_SIZE=0.2`, `RANDOM_STATE=42`, threshold 0.05~0.40)
   - 평가 지표: F1, ROC-AUC, PR-AUC, Best Threshold (F1 기준), Precision, Recall, Confusion Matrix
   - 결과 저장: `models/metrics.json`

### 2. 1차 튜닝 (탐색 단계)

**목표**:  
-기본 모델의 성능 분석 및 튜닝 방향성 찾기

F1-score (0.478): Precision과 Recall의 조화평균. 중간 정도 성능, 불균형 데이터에서 다소 낮은 편.
AUC (0.685): ROC 곡선 아래 면적. 0.5보다 높으나, 0.7 이하이므로 개선 필요.
PR-AUC (0.456): Positive 클래스 중심 성능 평가. 낮은 값 → positive 예측이 어려움.
Precision (0.378): Positive로 예측한 것 중 실제 Positive 비율이 낮음.
Recall (0.650): Positive 샘플 대부분을 찾아내는 데는 준수.

Confusion matrix:

TN: 743, FP: 443 → Negative 잘못 분류되는 비율이 높음.
FN: 145, TP: 269 → Positive 대부분은 잡지만 FP가 많음.
Best threshold = 0.24 → 기본 0.5보다 낮춰 recall ↑ (긍정 클래스 놓치지 않음).

✅ 요약:

Recall 중심 모델 → FP 많음, Precision 낮음.
전체적으로 균형 잡힌 성능 개선 필요.


**전략**:
- `MODEL_NAME = "logit"`로 설정 후, 아래 범위에서 **약 10개 조합**을 실험
  - `C`: 0.01, 0.1, 1.0, 10, 100  
  - `penalty `:  L2 
  - `solver`: lbfgs
  - `class_weight`: None, 'balanced'
 
C : 규제 강도 (작을수록 규제 강함)
penalty : L1, L2 규제
solver : 알고리즘 선택 (lbfgs, liblinear 등)
class_weight : 클래스 불균형 조정

**관찰 결과 (대표)**:
  - `C`: 0.01
  - `penalty `:  L2 
  - `solver`: lbfgs
  - `class_weight`: None

- 1차 logit 실험들:
  - `C`: F1 ≈ 0.477~0.480, Recall ≈ 0.60~0.65, Precision ≈ 0.38~0.40
  - `class_weight`: balance : Recall 극대화, Precision 너무 낮음 → F1-score 하락
  - `class_weight`: none: F1 ≈ 0.478~0.480, Precision과 Recall 균형 좋음

- 인사이트:
  -`class_weight`: none 으로 고정시키고, Threshold에 변화를 줘 보기로 함.


---

### 3. 2차 튜닝 (국소 탐색 단계)

**목표**:  
- 1차에서 성능이 좋았던 하이퍼파라미터 조합을 중심으로 재탐색

**변경 사항**:
- Threshold 스캔 범위 축소:
  - 기존: `0.05 ~ 0.35`  
  - 2차: `0.24 ~ 0.28`

- 하이퍼파라미터는 아래 범위를 중심으로 쪼개어 파악해봄:
  - `C`= 0.015 ~ 0.03 (0.005 단위)


**관찰 결과 (2차)**:
-F1-score 변화 : 
   -최고: 0.4795 (threshold 0.24) 
   -최저: 0.4781 → 변화 폭 거의 없음 (~0.0015)
- → C 범위에서 F1-score가 거의 포화 상태
- Precision/Recall : 
   - threshold 0.24 → Recall ≈ 0.65, Precision ≈ 0.38
   - threshold 0.26 → Recall ↓ 0.60, Precision ↑ 0.40
→ threshold 조정 시 Precision/Recall trade-off는 잘 작동함

-AUC/PR-AUC
-약간의 변화는 있지만 전체적으로 0.686~0.687 수준
→ 모델 구조나 feature가 동일하면 규제 강도(C) 변경만으로 큰 개선 어려움


-- 더이상 모델의 하이퍼파라미터 변화로는 유의미한 변화값을 주지 못 함을 확인함.


### 5. 최종 선별 결과 (logit Best Run)

`models/metrics.json` 기준, 2025-11-23 logit 실험들 중 **최고 F1**은 아래 런:

- **모델**: logit 
- **성능 (Best Threshold 기준)**:
  - F1 Score: **0.4809**  
  - ROC-AUC: **0.6874**  
  - PR-AUC: **0.4587**  
  - Best Threshold: **0.26**  
  - Precision: **0.3974**  
  - Recall: **0.6086**
- **Confusion Matrix (th=0.26)**:
  - TN = 804  
  - FP = 382  
  - FN = 162  
  - TP = 252  
- **데이터/설정 메타 정보**:
  - `data_path`: `data/enhanced_data_not_clean_FE_delete.csv`  
  - `test_size`: 0.2  
  - `random_state`: 42  
  - `threshold_range`: 0.24 ~ 0.28 (step=0.01)


### 6. 최종 추천 XGB 하이퍼파라미터 (1개 선정)

`models/metrics.json` 상의 best-run 성능과 1·2차 튜닝에서 관찰한 경향을 바탕으로,  
실제 리포트/서비스에서 사용하기 좋은 **최종 추천 설정 1개**를 아래와 같이 정리:

```python
MODEL_NAME = "logit"

MODEL_PARAMS = {

    C=0.01,                 # 규제 강도, 소폭 완화 가능하지만 현재 데이터에서 최적
    penalty='l2',            # 기본 L2 규제
    solver='lbfgs',          # 안정적인 수치 최적화
   #  class_weight=None,       # balanced 옵션 적용 시 성능 변화 거의 없음
   #  max_iter=1000            # 수렴 안정화
   # 주석처리한 두 항목은 모델의 기본값임.
}
```
- 모델: LogisticRegression (logit)
- 성능 (Best Threshold 기준):
  -F1 Score: 0.4809
  -ROC-AUC: 0.6874
  -PR-AUC: 0.4587
  -Best Threshold: 0.26
  -Precision: 0.3974
  -Recall: 0.6086
-Confusion Matrix (th=0.26):
  - TN = 804  
  - FP = 382  
  - FN = 162  
  - TP = 252  