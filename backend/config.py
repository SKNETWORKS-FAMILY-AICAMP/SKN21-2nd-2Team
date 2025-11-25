"""
config.py
Auth: 신지용
모델 학습/실험에서 공통으로 사용하는 설정 값을 모아둔 모듈입니다.
다른 스크립트에서 직접 숫자를 하드코딩하지 말고,
이 모듈의 상수를 import 해서 사용하도록 합니다.
"""

from __future__ import annotations

# -----------------------------------------------------
# 데이터 및 전처리 관련 설정
# -----------------------------------------------------
DATA_PATH: str = "data/processed/enhanced_data_not_clean_FE_delete.csv"
TEST_SIZE: float = 0.2
RANDOM_STATE: int = 42

# 기본으로 사용할 모델 이름
DEFAULT_MODEL_NAME: str = "xgb"  # "rf", "logit" 등 models.py의 MODEL_REGISTRY 키


# -----------------------------------------------------
# 평가 관련 설정 (Threshold 스캔 범위 등)
# -----------------------------------------------------
THRESH_START: float = 0.05
THRESH_END: float = 0.45
THRESH_STEP: float = 0.01


# -----------------------------------------------------
# 메트릭 저장 위치
# -----------------------------------------------------
# 여러 실험 결과를 누적해서 저장할 JSON 파일 경로
METRICS_PATH: str = "models/metrics.json"


__all__ = [
    "DATA_PATH",
    "TEST_SIZE",
    "RANDOM_STATE",
    "DEFAULT_MODEL_NAME",
    "THRESH_START",
    "THRESH_END",
    "THRESH_STEP",
    "METRICS_PATH",
]



