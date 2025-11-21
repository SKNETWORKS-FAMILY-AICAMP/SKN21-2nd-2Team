"""
모델 생성/선택을 담당하는 모듈.

다른 팀원은:
- config.py의 MODEL_NAME을 바꾸거나
- 아래에 새로운 create_XXX 함수를 추가하고 get_model 분기만 늘리면
쉽게 모델을 교체/추가할 수 있다.
"""

from typing import Literal

from sklearn.ensemble import RandomForestClassifier

from .config import MODEL_NAME, RF_PARAMS


def create_rf() -> RandomForestClassifier:
    """
    RandomForest 베이스라인 모델 생성.

    하이퍼파라미터는 전부 config.RF_PARAMS에서 관리하므로,
    팀원은 코드 수정 없이 config만 바꿔 실험할 수 있다.
    """
    return RandomForestClassifier(**RF_PARAMS)


def get_model(model_name: Literal["rf"] | None = None):
    """
    MODEL_NAME에 따라 적절한 모델 인스턴스를 반환한다.

    현재는 "rf"만 지원하지만, 추후 XGBoost/LightGBM 등을
    아래에 추가할 수 있다.
    """
    name = (model_name or MODEL_NAME).lower()

    if name == "rf":
        return create_rf()

    # 예시) 추후 확장
    # elif name == "xgb":
    #     from xgboost import XGBClassifier
    #     from .config import XGB_PARAMS
    #     return XGBClassifier(**XGB_PARAMS)
    #
    # elif name == "lgbm":
    #     from lightgbm import LGBMClassifier
    #     from .config import LGBM_PARAMS
    #     return LGBMClassifier(**LGBM_PARAMS)

    raise ValueError(f"Unknown model name: {name!r}")


__all__ = ["create_rf", "get_model"]


