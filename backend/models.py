"""
models.py
Auth: 신지용
여러 종류의 모델을 이름으로 선택해서 생성하는 팩토리 모듈.

현재 전처리/학습 로직은 `notebooks/pipeline.ipynb`와
`backend/preprocessing_pipeline.py`에서 정의된 파이프라인 출력을
입력으로 사용합니다.

역할 분리:
- 전처리 수정        → `backend/preprocessing_pipeline.py`
- 모델 종류/파라미터 → 이 모듈의 `MODEL_REGISTRY` 및 `get_model()`
- 데이터 경로/seed/비율 → `backend/config.py`의 상수들

사용 예시:
    from backend.models import get_model
    model = get_model(name="rf", random_state=42)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

try:
    # 선택 설치 모델 (requirements.txt에 xgboost, lightgbm이 있을 경우 사용)
    from xgboost import XGBClassifier  # type: ignore
except ImportError:  # pragma: no cover - 패키지 미설치 시 안전 처리
    XGBClassifier = None  # type: ignore

try:
    from lightgbm import LGBMClassifier  # type: ignore
except ImportError:  # pragma: no cover
    LGBMClassifier = None  # type: ignore


# 팀원들이 문자열로 모델 이름을 넘길 수 있게 단순 str로 정의
ModelName = str


@dataclass(frozen=True)
class ModelSpec:
    """단일 모델에 대한 설정 정보를 담는 데이터 클래스."""

    cls: type
    default_params: Mapping[str, Any]
    supports_random_state: bool = True


# -----------------------------------------------------
#  기본 모델 레지스트리
#  - 새 모델을 추가할 때는 이 딕셔너리에만 항목을 추가하면 됨.
# -----------------------------------------------------
MODEL_REGISTRY: Dict[ModelName, ModelSpec] = {
    "rf": ModelSpec(
        cls=RandomForestClassifier,
        default_params={
            "n_estimators": 300,
            "max_depth": None,
            "min_samples_split": 5,
            "class_weight": "balanced",
            "n_jobs": -1,
            # random_state는 아래 get_model에서 주입
        },
        supports_random_state=True,
    ),
    "logit": ModelSpec(
        cls=LogisticRegression,
        default_params={
            "C": 0.01,          # 규제 강도 (작을수록 규제 강함) → 이 데이터에서는 0.01이 F1 최고
            "penalty": "l2",    # L2 정규화 (기본값)
            "solver": "lbfgs",  # 다차원/연속 피처에 안정적인 해법
            "max_iter": 1000,   # 수렴 여유
            "class_weight": None  # 'balanced'는 이 데이터에서 F1 떨어졌음
        },
        supports_random_state=True,
    ),
    "et": ModelSpec(
        cls=ExtraTreesClassifier,
        default_params={
            "n_estimators": 300,
            "max_depth": None,
            "min_samples_split": 5,
            "class_weight": "balanced",
            "n_jobs": -1,
        },
        supports_random_state=True,
    ),
    "knn": ModelSpec(
        cls=KNeighborsClassifier,
        default_params={
            "n_neighbors": 25,
            "weights": "distance",
            "metric": "minkowski",
            "p": 2,
            "n_jobs": -1,
        },
        supports_random_state=False,
    ),
    "hgb": ModelSpec(
        cls=HistGradientBoostingClassifier,
        default_params={
            "learning_rate": 0.06,
            "max_depth": 3,
            "max_bins": 255,
            "l2_regularization": 0.3,
            "min_samples_leaf": 20,
        },
        supports_random_state=True,
    ),
    # 아래 두 모델은 해당 패키지가 설치된 경우에만 실제로 사용할 수 있습니다.
    # (xgboost, lightgbm 미설치 상태에서 호출하면 get_model()에서 에러가 발생합니다.)
    "xgb": ModelSpec(
        cls=XGBClassifier if XGBClassifier is not None else RandomForestClassifier,
        default_params={
        "n_estimators": 500,
        "learning_rate": 0.06,
        "max_depth": 5,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "scale_pos_weight": 3.0,
        },
        supports_random_state=True,
    ),
    "lgbm": ModelSpec(
        cls=LGBMClassifier if LGBMClassifier is not None else RandomForestClassifier,
        default_params={
            "n_estimators": 700,
            "learning_rate": 0.02,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
        },
        supports_random_state=True,
    ),
}


def get_model(
    name: ModelName = "rf",
    random_state: int = 42,
    **overrides: Any,
):
    """
    모델 이름에 따라 적절한 모델 인스턴스를 반환합니다.

    Args:
        name: "rf", "logit" 등 모델 이름
        random_state: 재현성을 위한 시드 값
        **overrides: 기본 하이퍼파라미터를 덮어쓰는 키워드 인자

    사용 예시:
        model = get_model("rf", random_state=0, n_estimators=500)
    """
    key = name.lower()

    if key not in MODEL_REGISTRY:
        raise ValueError(f"지원하지 않는 모델 이름입니다: {name!r}")

    spec = MODEL_REGISTRY[key]

    # 기본 하이퍼파라미터 복사
    params: Dict[str, Any] = dict(spec.default_params)

    # random_state 지원 모델이라면 주입
    if spec.supports_random_state:
        params["random_state"] = random_state

    # 호출 시 전달한 override 인자로 덮어쓰기
    params.update(overrides)

    return spec.cls(**params)


__all__ = ["get_model", "ModelName", "MODEL_REGISTRY", "ModelSpec"]


