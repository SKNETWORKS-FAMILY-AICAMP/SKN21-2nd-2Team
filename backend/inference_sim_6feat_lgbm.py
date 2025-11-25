"""
inference_sim_6feat_lgbm.py
Auth: 신지용
6개 시뮬레이터용 피처만 사용하는 LGBM(단조 제약) 전용 추론 모듈입니다.

현재 로직은 `backend/training/train_simulator_6feat_lgbm_mono.py`에서
학습/저장한 단조 제약 LGBM 모델을 로드하여,
관리자 시뮬레이터 화면에서 조정한 6개 피처로 이탈 확률을 계산합니다.

역할 분리:
- 시뮬레이터 학습/저장 → `backend/training/train_simulator_6feat_lgbm_mono.py`
- 6피처 추론          → 이 모듈의 `predict_churn_6feat_lgbm`
- API 연동            → `backend/app.py`의 `/api/predict_churn_6feat`
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

import os
import sys

import joblib
import numpy as np
import pandas as pd

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


SIM_FEATURES = [
    "app_crash_count_30d",
    "skip_rate_increase_7d",
    "days_since_last_login",
    "listening_time_trend_7d",
    "freq_of_use_trend_14d",
    "login_frequency_30d",
]

MODEL_PATH = os.path.join("models", "lgbm_sim_6feat_mono.pkl")

_SIM_MODEL = None


def _load_sim_model() -> Any:
    global _SIM_MODEL
    if _SIM_MODEL is not None:
        return _SIM_MODEL

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"6피처 전용 LGBM(단조 제약) 모델을 찾을 수 없습니다: {MODEL_PATH}\n"
            f"먼저 backend/train_simulator_6feat_lgbm_mono.py 를 실행해 모델을 학습/저장하세요."
        )

    loaded = joblib.load(MODEL_PATH)
    
    # 새로운 앙상블 형식인지 확인 (dict with 'models' key)
    if isinstance(loaded, dict) and 'models' in loaded:
        _SIM_MODEL = loaded  # 앙상블 정보 전체 저장
    else:
        # 레거시 단일 모델 형식
        _SIM_MODEL = {'models': [loaded], 'n_models': 1}
    
    return _SIM_MODEL


def _prob_to_risk_level(prob: float) -> str:
    """
    6피처 전용 LGBM(단조 제약) 모델용 위험도 매핑.

    - p < 0.23        : LOW
    - 0.23 <= p < 0.60: MEDIUM
    - 0.60 <= p       : HIGH

    (train_simulator_6feat_lgbm_mono.py 에서 Best Threshold ~= 0.23)
    """
    if prob < 0.23:
        return "LOW"
    if prob < 0.60:
        return "MEDIUM"
    return "HIGH"


def predict_churn_6feat_lgbm(user_features: Mapping[str, Any]) -> Dict[str, Any]:
    """
    6개 피처만 사용하는 LGBM(단조 제약) 시뮬레이터 전용 추론 함수.

    Parameters
    ----------
    user_features : dict
        {
          "app_crash_count_30d": int,
          "skip_rate_increase_7d": float,
          "days_since_last_login": int,
          "listening_time_trend_7d": float,
          "freq_of_use_trend_14d": float,
          "login_frequency_30d": int,
        }
    """
    try:
        model_info = _load_sim_model()

        row: Dict[str, Any] = {}
        for col in SIM_FEATURES:
            row[col] = user_features.get(col, np.nan)

        X = pd.DataFrame([row], columns=SIM_FEATURES)
        
        # 앙상블 예측: 여러 모델의 평균
        models = model_info['models']
        predictions = [model.predict_proba(X)[:, 1][0] for model in models]
        proba = float(np.mean(predictions))
        
        level = _prob_to_risk_level(proba)

        return {
            "success": True,
            "churn_prob": proba,
            "risk_level": level,
            "used_features": row,
            "ensemble_size": len(models),  # 앙상블 크기 정보 추가
        }

    except Exception as e:  # pragma: no cover
        return {
            "success": False,
            "error": f"6피처 전용 LGBM(단조 제약) 모델 예측 중 오류 발생: {e}",
        }


__all__ = ["predict_churn_6feat_lgbm"]


