"""
inference.py
Auth: 신지용
Date: 2025-11-25

전처리 파이프라인(`backend/preprocessing_pipeline.py`)과
모델 팩토리(`backend/models.py`)를 조합해, 단일 유저의
이탈 확률(churn_prob)을 계산하는 추론 모듈.

**최적화**: 이제 사전 학습된 모델(hgb_final.pkl)을 로드하여 사용합니다.
X_train_processed.pkl이 더 이상 필요하지 않으며, 서버 시작이 훨씬 빨라집니다.

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
    )
"""

from __future__ import annotations

from typing import Any, Dict, Mapping
from pathlib import Path
import joblib

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# 모듈 전역 캐시 (서버 최초 1회만 로딩)
# ---------------------------------------------------------
_ARTIFACTS_LOADED: bool = False
_PREPROCESSOR = None
_MODEL = None


def _load_artifacts_if_needed() -> None:
    """
    models/ 폴더에 저장된 학습된 모델과 전처리기를 로드합니다.
    
    필요 파일:
    - models/hgb_final.pkl: 학습된 HGB 모델
    - models/preprocessor_final.pkl: ColumnTransformer 전처리기
    
    이 파일들은 backend/training/train_and_save_model.py를 실행하여 생성됩니다.
    """
    global _ARTIFACTS_LOADED, _PREPROCESSOR, _MODEL

    if _ARTIFACTS_LOADED and _PREPROCESSOR is not None and _MODEL is not None:
        return

    # 프로젝트 루트 경로
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    models_dir = project_root / "models"
    
    model_path = models_dir / "hgb_final.pkl"
    preprocessor_path = models_dir / "preprocessor_final.pkl"
    
    # 파일 존재 확인
    if not model_path.exists():
        raise FileNotFoundError(
            f"모델 파일을 찾을 수 없습니다: {model_path}\n"
            "먼저 backend/training/train_and_save_model.py를 실행하여 모델을 학습하고 저장하세요."
        )
    
    if not preprocessor_path.exists():
        raise FileNotFoundError(
            f"전처리기 파일을 찾을 수 없습니다: {preprocessor_path}\n"
            "먼저 backend/training/train_and_save_model.py를 실행하여 전처리기를 저장하세요."
        )
    
    # 모델 및 전처리기 로드
    _MODEL = joblib.load(model_path)
    _PREPROCESSOR = joblib.load(preprocessor_path)
    
    _ARTIFACTS_LOADED = True
    print(f"✅ 모델 로드 완료: {model_path.name}")
    print(f"✅ 전처리기 로드 완료: {preprocessor_path.name}")


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
) -> Dict[str, Any]:
    """
    단일 유저의 피처 딕셔너리를 입력 받아 이탈 확률을 예측합니다.

    Args:
        user_features:
            - key: 학습에 사용된 컬럼 이름 (예: "listening_time", "payment_failure_count" 등)
            - value: 해당 값 (int, float, bool, str 등)
            - 누락된 컬럼은 NaN 으로 채운 뒤, 전처리 파이프라인의 imputer 가 처리합니다.

    Returns:
        {
          "success": bool,
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

        # 1) 모델 및 전처리기 로드
        _load_artifacts_if_needed()

        # 2) 입력 DataFrame 구성
        X_df = _build_input_dataframe(user_features)

        # 3) 전처리(transform)
        X_transformed = _PREPROCESSOR.transform(X_df)

        # 4) 확률 예측
        if not hasattr(_MODEL, "predict_proba"):
            return {
                "success": False,
                "error": "모델이 predict_proba를 지원하지 않습니다.",
            }

        proba = float(_MODEL.predict_proba(X_transformed)[:, 1][0])
        risk_level = _prob_to_risk_level(proba)

        return {
            "success": True,
            "churn_prob": proba,
            "risk_level": risk_level,
        }

    except Exception as e:  # pragma: no cover - 방어적 예외 처리
        return {
            "success": False,
            "error": f"예측 중 오류 발생: {e}",
        }


__all__ = ["predict_churn"]
