"""
학습/평가 로직을 담당하는 모듈.

⚠ 최종 전처리 파이프라인이 sklearn Pipeline 형태로 제공될 경우,
   - (전처리가 피처 레벨에서 이뤄진다면) train_test_split 이후,
   - (원본 df 전체를 다루는 경우라면) data_loader 쪽에서
   해당 파이프라인을 적용하면 된다.
"""

from typing import Dict, Tuple

import numpy as np
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .config import RANDOM_STATE, TEST_SIZE


def train_and_evaluate(
    model,
    X,
    y,
    thresholds: np.ndarray | None = None,
) -> Tuple[Dict, object]:
    """
    단일 모델에 대해 train/test split → 학습 → threshold 튜닝 → F1/AUC 계산까지 수행.

    - thresholds가 None이면 [0.05, 0.35) 구간을 0.01 간격으로 스캔해
      F1이 최대가 되는 best threshold를 찾는다.

    반환:
        metrics (dict): F1, AUC, best_threshold 등
        trained_model: 학습이 끝난 모델 인스턴스
    """
    if thresholds is None:
        thresholds = np.arange(0.05, 0.35, 0.01)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # ------------------------------------------------------------------
    # 🔌 [최종 전처리 파이프라인 훅 (HOOK)]
    #
    # 만약 다른 팀원이 sklearn.Pipeline 형태의 전처리/모델 파이프라인을
    # 제공한다면, 사용 방식에 따라 두 가지 패턴이 있을 수 있다.
    #
    # 1) "전처리 + 모델"이 하나의 Pipeline인 경우:
    #       - 이 함수에서 model 대신 pipeline을 받으면 됨.
    #       - 아래 fit / predict_proba 호출은 그대로 사용 가능.
    #
    # 2) "전처리 Pipeline"과 "모델"이 분리되어 있는 경우:
    #       from pipelines import final_pipeline
    #       X_train = final_pipeline.fit_transform(X_train)
    #       X_test = final_pipeline.transform(X_test)
    #
    #   위와 같이 이 위치에서 X_train/X_test에 파이프라인을 적용하면 된다.
    # ------------------------------------------------------------------

    # 모델 학습
    model.fit(X_train, y_train)

    # 예측 확률
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
    else:
        # 일부 모델은 decision_function만 제공할 수 있으므로,
        # 그 경우를 대비한 fallback 로직
        if hasattr(model, "decision_function"):
            scores = model.decision_function(X_test)
            # scores를 0~1 확률 비슷하게 스케일링 (간단한 min-max)
            scores_min = scores.min()
            scores_max = scores.max()
            if scores_max > scores_min:
                y_proba = (scores - scores_min) / (scores_max - scores_min)
            else:
                y_proba = np.zeros_like(scores, dtype=float)
        else:
            raise ValueError("모델이 predict_proba나 decision_function을 지원하지 않습니다.")

    # AUC 계산
    auc = roc_auc_score(y_test, y_proba)

    # 최적 threshold 탐색
    best_f1 = 0.0
    best_th = float(thresholds[0])

    for th in thresholds:
        y_pred_th = (y_proba >= th).astype(int)
        f1_th = f1_score(y_test, y_pred_th)
        if f1_th > best_f1:
            best_f1 = f1_th
            best_th = float(th)

    metrics = {
        "F1": best_f1,
        "AUC": auc,
        "best_threshold": best_th,
        "n_thresholds": len(thresholds),
        "n_samples": len(y),
    }

    return metrics, model


__all__ = ["train_and_evaluate"]


