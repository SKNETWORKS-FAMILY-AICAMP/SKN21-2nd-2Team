"""
inference.py
Auth: 신지용
전처리 파이프라인(`backend/preprocessing_pipeline.py`)과
모델 팩토리(`backend/models.py`)를 조합해, 단일 유저의
이탈 확률(churn_prob)을 계산하는 추론 모듈.

현재 로직은 `data/processed`에 저장된 전처리 아티팩트
(`preprocess_and_split` + `save_processed_data`)를 로드한 뒤,
요청 시 모델을 학습/캐싱하여 예측에 사용합니다.

역할 분리:
- 전처리/아티팩트 저장 → `backend/preprocessing_pipeline.py`
- 모델 종류/파라미터   → `backend/models.py`의 `get_model()`
- 단일/배치 예측 API   → 이 모듈의 `predict_churn` 및 `backend/app.py`의 관련 엔드포인트

간단 사용 예시:
    from backend.inference import predict_churn

    result = predict_churn(
        user_features={
            "listening_time": 180,
            "songs_played_per_day": 40,
            "payment_failure_count": 1,
            "app_crash_count_30d": 0,
            "subscription_type": "Premium",
            "customer_support_contact": True,
        },
        model_name="hgb",  # 생략 시 backend.config.DEFAULT_MODEL_NAME 사용
    )
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

import numpy as np
import pandas as pd

from backend.config import DEFAULT_MODEL_NAME, RANDOM_STATE
from backend.models import get_model
from backend.preprocessing_pipeline import load_processed_data


# ---------------------------------------------------------
# 모듈 전역 캐시 (서버 최초 1회만 로딩/학습)
# ---------------------------------------------------------
_ARTIFACTS_LOADED: bool = False
_PREPROCESSOR = None
_MODEL_CACHE: Dict[str, Any] = {}


def _load_artifacts_if_needed() -> None:
    """
    data/processed/*.pkl 에 저장된 전처리 결과를 로드하고,
    ColumnTransformer(preprocessor) 객체를 메모리에 적재합니다.

    - X_train_processed, X_test_processed: 사용하지 않고 버립니다(이미 변환된 행렬)
    - y_train, y_test: 현재는 사용하지 않지만, 필요 시 확장 가능
    """
    global _ARTIFACTS_LOADED, _PREPROCESSOR

    if _ARTIFACTS_LOADED and _PREPROCESSOR is not None:
        return

    # backend/preprocessing_pipeline.save_processed_data() 가 저장한 경로를 그대로 사용
    _, _, _, _, preprocessor = load_processed_data(save_dir="data/processed")

    _PREPROCESSOR = preprocessor
    _ARTIFACTS_LOADED = True


def _get_or_train_model(model_name: str) -> Any:
    """
    요청된 모델 이름에 해당하는 분류 모델을 메모리에서 가져오거나,
    없으면 data/processed/X_train_processed.pkl, y_train.pkl 기준으로 1회 학습합니다.

    주의:
        - 서비스 환경에서는 별도 model.pkl 로 저장해 두는 것이 이상적이나,
          현재 프로젝트 구조에서는 전처리된 행렬을 재활용해 간단히 재학습하는 패턴을 사용합니다.
    """
    global _MODEL_CACHE

    key = model_name.lower()
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    # 전처리 아티팩트 로딩 (여기서는 preprocessor 외에 X_train, y_train도 재사용)
    from backend.preprocessing_pipeline import load_processed_data as _load_processed_data

    X_train, _, y_train, _, _ = _load_processed_data(save_dir="data/processed")

    model = get_model(name=key, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    _MODEL_CACHE[key] = model
    return model


def _build_input_dataframe(
    user_features: Mapping[str, Any],
) -> pd.DataFrame:
    """
    단일 유저 피처 딕셔너리를 ColumnTransformer 에 들어갈 pandas.DataFrame 형태로 변환합니다.

    - 전처리기에 등록된 숫자/범주형 컬럼 목록을 조회해,
      해당 컬럼들만 1행짜리 DataFrame 으로 생성합니다.
    - 딕셔너리에 없는 컬럼은 NaN 으로 채워 두고, 이후 SimpleImputer 가 처리합니다.
    """
    if _PREPROCESSOR is None:
        raise RuntimeError("전처리기가 아직 로드되지 않았습니다. _load_artifacts_if_needed()를 먼저 호출하세요.")

    # ColumnTransformer 에서 실제로 사용하는 컬럼 이름들만 수집
    used_columns = []
    for name, _, cols in _PREPROCESSOR.transformers_:
        # backend.preprocessing_pipeline.build_preprocessor 에서
        # ("num", numeric_pipeline, numerical_features),
        # ("cat_ohe", categorical_pipeline, categorical_features)
        # 형태로 등록되어 있으므로 이 두 가지 이름만 사용합니다.
        if name in ("num", "cat_ohe"):
            used_columns.extend(list(cols))

    # 중복 제거 + 순서 유지
    seen = set()
    ordered_cols = []
    for c in used_columns:
        if c not in seen:
            seen.add(c)
            ordered_cols.append(c)

    # 유저가 준 피처 딕셔너리에서 값 채우기 (없으면 NaN)
    row: Dict[str, Any] = {}
    for col in ordered_cols:
        row[col] = user_features.get(col, np.nan)

    df = pd.DataFrame([row], columns=ordered_cols)
    return df


def _prob_to_risk_level(prob: float) -> str:
    """
    확률값(0~1)을 간단한 위험도 레벨 문자열로 매핑합니다.

    - 0.30 미만: LOW
    - 0.30 이상 0.60 미만: MEDIUM
    - 0.60 이상: HIGH

    필요 시, models/metrics.json 에 기록된 best_threshold 를 기준으로
    규칙을 조정해도 됩니다.
    """
    if prob < 0.30:
        return "LOW"
    if prob < 0.60:
        return "MEDIUM"
    return "HIGH"


def predict_churn(
    user_features: Mapping[str, Any],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    단일 유저의 피처 딕셔너리를 입력 받아 이탈 확률을 예측합니다.

    Args:
        user_features:
            - key: 학습에 사용된 컬럼 이름 (예: "listening_time", "payment_failure_count" 등)
            - value: 해당 값 (int, float, bool, str 등)
            - 누락된 컬럼은 NaN 으로 채운 뒤, 전처리 파이프라인의 imputer 가 처리합니다.
        model_name:
            - 사용할 모델 이름 (예: "xgb", "rf", "lgbm" 등)
            - None 이면 backend.config.DEFAULT_MODEL_NAME 사용

    Returns:
        {
          "success": bool,
          "model_name": str,
          "churn_prob": float,   # 0.0 ~ 1.0
          "risk_level": str,     # "LOW" | "MEDIUM" | "HIGH"
          "error": Optional[str] # 실패 시 에러 메시지
        }
    """
    try:
        if not isinstance(user_features, Mapping):
            return {
                "success": False,
                "error": "user_features는 dict 형태여야 합니다.",
            }

        # 1) 전처리기 로드
        _load_artifacts_if_needed()

        # 2) 입력 DataFrame 구성
        X_df = _build_input_dataframe(user_features)

        # 3) 전처리(transform)
        X_transformed = _PREPROCESSOR.transform(X_df)

        # 4) 모델 로드/학습
        effective_model_name = (model_name or DEFAULT_MODEL_NAME).lower()
        model = _get_or_train_model(effective_model_name)

        if not hasattr(model, "predict_proba"):
            return {
                "success": False,
                "error": f"모델 '{effective_model_name}' 은 predict_proba를 지원하지 않습니다.",
            }

        # 5) 확률 예측
        proba = float(model.predict_proba(X_transformed)[:, 1][0])
        risk_level = _prob_to_risk_level(proba)

        return {
            "success": True,
            "model_name": effective_model_name,
            "churn_prob": proba,
            "risk_level": risk_level,
        }

    except Exception as e:  # pragma: no cover - 방어적 예외 처리
        return {
            "success": False,
            "error": f"예측 중 오류 발생: {e}",
        }


__all__ = ["predict_churn"]


