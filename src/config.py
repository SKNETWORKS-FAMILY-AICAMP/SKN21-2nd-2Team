"""
모델 실험 공통 설정값을 관리하는 모듈.

다른 팀원은 이 파일에서만 데이터 경로, 사용 컬럼, 모델 타입, 하이퍼파라미터를
수정하면 동일한 코드 구조로 다양한 실험을 돌릴 수 있다.
"""

from pathlib import Path

# 프로젝트 루트 기준 경로 (run_baseline.py를 루트에서 실행한다고 가정)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 데이터 설정
DATA_PATH = PROJECT_ROOT / "data" / "enhanced_data_clean_model.csv"
TARGET_COL = "is_churned"
ID_COLS = ["user_id"]  # 필요 없으면 빈 리스트로 변경 가능

# 🔢 모델에 사용할 최종 수치형 피처 목록 (FE 5개 제거 후 15개)
# - docs/reset.md의 "Enhanced (최종 세트)"와 일치하도록 고정
NUM_FEATURE_COLS = [
    # Baseline 6개
    "age",
    "listening_time",
    "songs_played_per_day",
    "skip_rate",
    "ads_listened_per_week",
    "offline_listening",
    # 시계열 5개
    "listening_time_trend_7d",
    "login_frequency_30d",
    "days_since_last_login",
    "skip_rate_increase_7d",
    "freq_of_use_trend_14d",
    # 고객접점 4개
    "customer_support_contact",
    "payment_failure_count",
    "promotional_email_click",
    "app_crash_count_30d",
]

# 🔌 외부 전처리 파이프라인 설정 (예: backend.pipeline.run_preprocessing)
# 기본값은 False이므로, 현재는 사용하지 않는다.
USE_EXTERNAL_PIPELINE = False
PIPELINE_MODULE = "backend.pipeline"  # 예시: backend/pipeline.py 또는 .ipynb 변환본
PIPELINE_FUNC_NAME = "run_preprocessing"

# 학습/평가 설정
TEST_SIZE = 0.2
RANDOM_STATE = 42

# 사용할 모델 타입 지정 (예: "rf", "xgb", "lgbm" 등)
MODEL_NAME = "rf"

# RandomForest 기본 하이퍼파라미터
RF_PARAMS = {
    "n_estimators": 300,
    "max_depth": None,
    "min_samples_split": 5,
    "class_weight": "balanced",
    "n_jobs": -1,
    "random_state": RANDOM_STATE,
}

# 추후 XGBoost, LightGBM 등을 추가한다면 여기 dict를 정의하고
# models.py에서 불러다 쓰면 된다.
# 예시:
# XGB_PARAMS = {...}
# LGBM_PARAMS = {...}


