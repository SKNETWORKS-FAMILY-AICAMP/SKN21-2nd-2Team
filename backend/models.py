"""
models.py

여러 종류의 모델을 이름으로 선택해서 생성하는 팩토리 모듈.

사용 예시:
    from models import get_model
    model = get_model(name="rf", random_state=42)

지원 이름:
- "rf"     : RandomForestClassifier
- "logit"  : LogisticRegression (baseline 비교용)
"""

from typing import Literal

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression


ModelName = Literal["rf", "logit"]


def get_model(
    name: ModelName = "rf",
    random_state: int = 42,
):
    """
    모델 이름에 따라 적절한 모델 인스턴스를 반환합니다.

    Args:
        name: "rf", "logit" 등 모델 이름
        random_state: 재현성을 위한 시드 값
    """
    name = name.lower()

    if name == "rf":
        # 기본 실험용 RandomForest
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=5,
            class_weight="balanced",
            n_jobs=-1,
            random_state=random_state,
        )

    if name == "logit":
        # 비교용 Logistic Regression (baseline)
        return LogisticRegression(
            max_iter=1000,
            n_jobs=-1,
            random_state=random_state,
        )

    raise ValueError(f"지원하지 않는 모델 이름입니다: {name!r}")


__all__ = ["get_model", "ModelName"]



