## 모델 검증 및 실험 요약 (README용)

### 1. 데이터 및 베이스라인
- **데이터 구조**: 8,000명 유저, 유저당 1행 스냅샷 (수치형 6개 + 범주형 4개, 타깃 `is_churned`)
- **초기 베이스라인** (`preprocessing_validation.ipynb`, `FE_validation.ipynb`):
  - 수치형 6개 + 핵심 FE 5개(engagement_score, songs_per_minute, skip_intensity, skip_rate_cap, ads_pressure) 조합(Set D)
  - **모델**: RandomForestClassifier(class_weight='balanced') + threshold 튜닝
  - **성능**: F1≈0.41, AUC≈0.54 수준에서 정체

### 2. Feature Engineering / Feature Selection 검증
- **FE 검증** (`FE_validation.ipynb`, `FE_add.ipynb`):
  - 여러 FE 세트(Set A~G) 및 추가 세그먼트/ratio/비선형 FE 후보를 실험
  - **결과**: 핵심 FE 4~5개만 남기는 것이 최선, 복잡한 교호작용·플래그를 더해도 성능 개선은 ΔF1≈0 수준
- **범주형 및 FS 검증** (`feature_selection.ipynb`):
  - `gender`, `country`, `subscription_type`, `device_type` 및 파생 범주형을 One-Hot 인코딩해 포함
  - 수치형+FE(10~11개) vs 수치형+FE+범주형(30개 이상) 비교 시 **오히려 F1/AUC 소폭 하락 → 범주형 기여도 낮음**

### 3. 모델 튜닝·SMOTE·앙상블 검증
- **모델/파라미터 튜닝** (`feature_selection.ipynb`):
  - RandomForest 하이퍼파라미터(RandomizedSearchCV), K-Fold + threshold 튜닝, 소프트보팅 앙상블(RF+XGB+HGB) 등 적용
  - **결과**: 어떤 조합도 F1 0.41±0.01, AUC 0.52~0.54 범위를 크게 넘지 못함
- **SMOTE + XGBoost + 앙상블** (`SMOTE_XGB_RF.ipynb`):
  - SMOTE(오버샘플링 비율·test_size·scale_pos_weight 등 여러 버전), XGBoost GridSearchCV, RF+XGB+HGB 앙상블 시도
  - **결과**: Train에서는 F1↑지만 Test에서는 Baseline보다 낮거나 비슷한 수준 → **심한 과적합 & 실질적 개선 실패**

### 4. 한계 원인 분석
- **통계·상관·Feature Importance 분석** (`feature_selection.ipynb` 6장, `improvement_proposal.md`):
  - 모든 피처에서 t-test p-value>0.05, 상관계수 |r|<0.02 → 이탈/비이탈 간 행동 차이가 통계적으로 거의 없음
  - RF Feature Importance & Permutation Importance도 특정 피처가 두드러지지 않고 8~14% 수준으로 고르게 분산
- **결론**:
  - 현재 구조(유저당 1행 스냅샷 + 단일 시점 피처)에서는 **F1≈0.41, AUC≈0.53이 사실상 상한**
  - 모델 변경·튜닝·SMOTE만으로는 성능을 올리기 어렵고, **데이터/피처 자체를 바꾸는 방향이 필요**함

### 5. 시계열·고객 접점 피처 추가 및 성능 향상
- **개선 아이디어 정리** (`improvement_proposal.md`):
  - Priority 1: 최근 7/14/30일 행동 변화를 담는 **시계열 피처 5개**
  - Priority 2: 고객센터 문의, 결제 실패, 프로모션 반응, 앱 크래시 등 **고객 접점 피처 4개**
  - 실제 로그 수집이 어려운 환경을 가정해, 위 피처들을 **현실적인 분포를 가진 합성 특성**으로 먼저 실험
- **합성 피처 생성 및 검증** (`feature_engineering_advanced.ipynb`):
  - 원본 베이스라인(수치형 6 + FE 5, 총 11개) 대비, **시계열 5개 + 고객 접점 4개**를 추가한 `enhanced_data.csv` 생성
  - RandomForest 기반 실험 결과:
    - Baseline: F1≈0.42, AUC≈0.54
    - +시계열 피처: F1≈0.49, AUC≈0.73
    - +시계열+고객접점(최종): **F1≈0.62, AUC≈0.79** (ΔF1 +0.20 이상, ΔAUC +0.25 이상)
  - **Feature Importance 기준 핵심 기여 피처**:
    - `payment_failure_count`, `app_crash_count_30d` (고객 접점)
    - `freq_of_use_trend_14d`, `listening_time_trend_7d`, `skip_rate_increase_7d` (시계열)

### 6. 전처리·파이프라인 정리
- **전처리 정책 및 데이터 버전** (`preprocessing_validation_v2.ipynb`, `reset.md`):
  - 합성 피처 포함 데이터 `enhanced_data.csv` 생성 후,
    - 결측/이상치 처리 버전: `enhanced_data_clean.csv`
    - FE 5개를 제거한 최종 모델 입력용: `enhanced_data_clean_model.csv` (원본 수치형 6 + 시계열 5 + 고객 접점 4 = **총 15개 수치형**)
  - EDA는 `enhanced_data_clean.csv`, 모델 학습은 `enhanced_data_clean_model.csv` 기준으로 사용
- **백엔드 파이프라인 및 실험 구조** (`backend/preprocessing_pipeline.py`, `backend/models.py`, `backend/train_experiments.py`):
  - sklearn `ColumnTransformer` 기반 전처리 파이프라인(결측/이상치 처리 + 수치형 스케일링 + 범주형 One-Hot)
  - `get_model()` + `MODEL_REGISTRY` 구조로 모델 생성, `MODEL_PARAMS` 딕셔너리로 하이퍼파라미터 튜닝
  - 실험 결과는 `models/metrics.json`에 누적 저장하도록 설계

### 7. 최종 정리 포인트 (README에 강조할 메시지)
- **현재 데이터(스냅샷)만 사용**했을 때는, 다양한 FE/FS/튜닝/SMOTE/XGBoost/앙상블을 모두 시도해도 **F1≈0.41, AUC≈0.53 근처에서 정체**됨.
- **시계열 + 고객 접점 피처를 추가**한 `enhanced_data.csv` 실험에서는, 동일한 모델(RF)로도 **F1≈0.62, AUC≈0.79까지 성능이 크게 상승**하는 것을 확인함.
- 이를 통해 **“모델을 바꾸는 것보다, 이탈 직전 행동 변화와 고객 접점을 담는 피처를 설계·수집하는 것이 핵심”**이라는 결론에 도달했고,
  실제 서비스 환경에서는 로그·고객센터·결제/에러 데이터를 결합한 피처 설계를 가장 우선순위로 두어야 한다는 인사이트를 얻음.

### 8. XGBoost 모델 실험 요약 (3번 역할)

- **실험 환경**:
  - 데이터: `data/enhanced_data_not_clean_FE_delete.csv`
  - 전처리: `backend/preprocessing_pipeline.py` / `jy_model_test/preprocessing_pipeline.py` 의 `preprocess_and_split()`
  - 학습 스크립트: `backend/train_experiments.py`, `jy_model_test/train_experiments.py`
  - 결과 로그: `models/metrics.json`
- **RF baseline (동일 데이터/파이프라인 기준)**:
  - F1 ≈ **0.616**, AUC ≈ **0.791**, PR-AUC ≈ **0.662**
- **XGB 1차 튜닝 (탐색)**:
  - `n_estimators` 200~700, `max_depth` 3/4/5/7, `learning_rate` 0.03~0.15, `subsample`/`colsample_bytree` 0.7~0.9, `scale_pos_weight` 2.5~4.0 범위에서 약 10개 조합 실험
  - F1 ≈ 0.53~0.61, AUC ≈ 0.80~0.82 구간 → **깊이 3~5, lr 0.05~0.08, n_estimators 400~600, scale_pos_weight≈3** 근처가 가장 안정적
- **XGB 2차 튜닝 (국소 탐색)**:
  - Threshold 범위를 0.05~0.45로 확장, 1차에서 좋은 구간 주변만 4개 세트로 재탐색
  - F1 ≈ **0.60~0.612**에서 수렴, AUC는 대부분 0.81±0.01 수준
- **XGB 3차 튜닝 (미세 조정)**:
  - 2차에서 성능이 좋은 세팅을 기준으로 `n_estimators`/`max_depth`/`learning_rate`/`scale_pos_weight`를 소폭 조정
  - 최종적으로 F1 ≈ **0.620**, AUC ≈ **0.811**, PR-AUC ≈ **0.693**, Best Threshold ≈ **0.44** 수준의 런 확보
- **RF vs XGB (최종, 개별 실험 기준)**:
  - RF:  F1 ≈ **0.616**, AUC ≈ **0.791**, PR-AUC ≈ **0.662**
  - XGB: F1 ≈ **0.620**, AUC ≈ **0.811**, PR-AUC ≈ **0.693**
  - ⇒ **F1은 거의 비슷하거나 XGB가 근소 우위**, AUC/PR-AUC는 XGB가 명확히 우위  
  - 팀 전체 모델 비교(다른 팀원의 모델)는 아직 진행 중이며, XGB 결과는 **3번 역할의 개별 실험 결과**로 README에 정리 예정