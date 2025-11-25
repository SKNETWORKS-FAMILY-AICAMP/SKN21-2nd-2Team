"""
config.py
Auth: 신지용
모델 학습/실험에서 공통으로 사용하는 설정 값을 모아둔 모듈.

현재 전처리/학습 스크립트(`backend/training/train_experiments.py`)는
이 모듈의 상수를 import 해서 데이터 경로, 테스트 비율, random_state,
threshold 스캔 범위 등을 제어합니다.

역할 분리:
- 전처리/데이터 로딩  → `backend/preprocessing_pipeline.py`
- 모델 종류/파라미터 → `backend/models.py`의 `get_model()`
- 실험 설정 값       → 이 모듈의 상수들
"""

from __future__ import annotations

# -----------------------------------------------------
# 데이터 및 전처리 관련 설정
# -----------------------------------------------------
DATA_PATH: str = "data/processed/enhanced_data_not_clean_FE_delete.csv"
TEST_SIZE: float = 0.2
RANDOM_STATE: int = 42

# 기본으로 사용할 모델 이름
DEFAULT_MODEL_NAME: str = "hgb"  # "rf", "logit" 등 models.py의 MODEL_REGISTRY 키


# -----------------------------------------------------
# 평가 관련 설정 (Threshold 스캔 범위 등)
# -----------------------------------------------------
THRESH_START: float = 0.05
THRESH_END: float = 0.45
THRESH_STEP: float = 0.01


# -----------------------------------------------------
# 메트릭 및 최종 모델 저장 위치
# -----------------------------------------------------
# 여러 실험 결과를 누적해서 저장할 JSON 파일 경로
METRICS_PATH: str = "models/metrics.json"

# 서비스에서 사용할 최종 학습 모델 pkl 경로
# - inference.py 와 training/train_experiments.py 가 공통으로 사용
# - models 디렉토리 아래에 저장
MODEL_PKL_PATH: str = "models/model_lk.pkl"


__all__ = [
    "DATA_PATH",
    "TEST_SIZE",
    "RANDOM_STATE",
    "DEFAULT_MODEL_NAME",
    "THRESH_START",
    "THRESH_END",
    "THRESH_STEP",
    "METRICS_PATH",
    "MODEL_PKL_PATH",
]



