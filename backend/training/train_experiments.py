"""
train_experiments.py
Auth: 신지용
전처리 파이프라인(`backend/preprocessing.py`)을 호출해
모델 학습 + 평가(F1, AUC, Best Threshold)를 수행하는 스크립트.

현재 전처리 로직은 `notebooks/pipeline.ipynb`에서 정의된
sklearn ColumnTransformer 기반 파이프라인을 그대로 옮긴
`preprocess_and_split` 함수를 사용합니다.

역할 분리:
- 전처리 수정        → `backend/preprocessing.py`
- 모델 종류/파라미터 → `backend/models.py`의 `get_model()`
- 데이터 경로/seed/비율 → 아래 CONFIG 상수만 수정
"""

import json
import os
from datetime import datetime

import numpy as np
from sklearn.metrics import (
    f1_score,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    confusion_matrix,
)

from backend.config import (
    DATA_PATH,
    TEST_SIZE,
    RANDOM_STATE,
    DEFAULT_MODEL_NAME,
    THRESH_START,
    THRESH_END,
    THRESH_STEP,
    METRICS_PATH,
)
from backend.models import get_model
from backend.preprocessing_pipeline import preprocess_and_split  # 같은 backend 디렉터리 기준 import


# =========================================================
# 공통 설정 (팀원은 되도록 config.py만 수정)
# =========================================================
MODEL_NAME = DEFAULT_MODEL_NAME  # "rf", "logit", "hgb" 등 backend/models.py에서 지원하는 이름

# 선택: 하이퍼파라미터 override (기본은 빈 dict, 필요할 때만 수정)
MODEL_PARAMS = {
    # 예시) RandomForest/ExtraTrees 튜닝
    # "n_estimators": 400,
    # "max_depth": 8,
    # "min_samples_leaf": 5,
    #
    # 예시) XGBoost / LightGBM 튜닝
    # "learning_rate": 0.05,
    # "n_estimators": 400,
    # "max_depth": 6,
    # "n_estimators": 600,
    # "learning_rate": 0.03,
    # "max_depth": 3,
    # "subsample": 0.8,
    # "colsample_bytree": 0.8,
    # "scale_pos_weight": 3.0,

}


def evaluate_with_best_threshold(
    y_true,
    y_proba,
    thresholds: np.ndarray | None = None,
):
    """
    여러 threshold를 스캔하여 F1이 최대가 되는 지점을 찾고,
    그때의 F1과 전체 AUC를 함께 반환합니다.
    """
    if thresholds is None:
        thresholds = np.arange(THRESH_START, THRESH_END, THRESH_STEP)

    best_f1 = 0.0
    best_th = float(thresholds[0])
    best_precision = 0.0
    best_recall = 0.0

    for th in thresholds:
        y_pred = (y_proba >= th).astype(int)
        f1 = f1_score(y_true, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_th = float(th)
            best_precision = precision_score(y_true, y_pred, zero_division=0)
            best_recall = recall_score(y_true, y_pred, zero_division=0)

    auc = roc_auc_score(y_true, y_proba)
    pr_auc = average_precision_score(y_true, y_proba)
    return best_f1, auc, pr_auc, best_th, best_precision, best_recall


def main():
    # 1) 전처리 파이프라인 실행
    #    - 데이터 경로/비율/seed는 상단 CONFIG를 통해 제어
    #    - notebooks/pipeline.ipynb와 동일한 sklearn ColumnTransformer 파이프라인 사용
    X_train, X_test, y_train, y_test, _ = preprocess_and_split(
        path=DATA_PATH,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # 2) 모델 생성 및 학습
    #    - MODEL_NAME을 "rf", "xgb" 등으로 바꿔가며 실험하고
    #    - MODEL_PARAMS에 원하는 하이퍼파라미터만 선택적으로 넣어 override 가능
    model = get_model(name=MODEL_NAME, random_state=RANDOM_STATE, **MODEL_PARAMS)
    model.fit(X_train, y_train)

    # 3) 예측 및 평가
    y_proba = model.predict_proba(X_test)[:, 1]
    best_f1, auc, pr_auc, best_th, best_precision, best_recall = evaluate_with_best_threshold(
        y_test, y_proba
    )

    # Best threshold 기준 예측 결과 및 혼동 행렬
    y_pred_best = (y_proba >= best_th).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_best).ravel()

    print("📊 Evaluation with sklearn preprocessing pipeline")
    print(f"- Model         : {MODEL_NAME}")
    print(f"- F1 Score      : {best_f1:.4f}")
    print(f"- AUC           : {auc:.4f}")
    print(f"- PR-AUC        : {pr_auc:.4f}")
    print(f"- Best Threshold: {best_th:.2f}")
    print(f"- Precision     : {best_precision:.4f}")
    print(f"- Recall        : {best_recall:.4f}")
    print(f"- Confusion     : TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"- n_train       : {len(y_train)}")
    print(f"- n_test        : {len(y_test)}")

    # 4) 메트릭 자동 저장
    save_metrics(
        model_name=MODEL_NAME,
        best_f1=best_f1,
        auc=auc,
        pr_auc=pr_auc,
        best_th=best_th,
        precision=best_precision,
        recall=best_recall,
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
        n_train=len(y_train),
        n_test=len(y_test),
    )


def save_metrics(
    model_name: str,
    best_f1: float,
    auc: float,
    pr_auc: float,
    best_th: float,
    precision: float,
    recall: float,
    tn: int,
    fp: int,
    fn: int,
    tp: int,
    n_train: int,
    n_test: int,
) -> None:
    """
    실험 결과 메트릭을 JSON 파일로 누적 저장합니다.
    - 저장 위치: config.METRICS_PATH (기본: models/metrics.json)
    - 형식: 실행마다 하나의 dict를 리스트에 append
    """
    # json.dump 시 numpy 타입(np.int64, np.float32 등)을 그대로 넣으면 에러가 나므로
    # 여기서 모두 Python 기본 타입(int, float, str)으로 변환해 둔다.
    run_info = {
        "model": str(model_name),
        "f1": float(best_f1),
        "auc": float(auc),
        "pr_auc": float(pr_auc),
        "best_threshold": float(best_th),
        "precision": float(precision),
        "recall": float(recall),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "n_train": int(n_train),
        "n_test": int(n_test),
        "data_path": str(DATA_PATH),
        "test_size": float(TEST_SIZE),
        "random_state": int(RANDOM_STATE),
        "threshold_range": {
            "start": float(THRESH_START),
            "end": float(THRESH_END),
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    if isinstance(existing, dict):
        # 예전 형식이 dict 하나였다면 리스트로 변환
        existing = [existing]

    existing.append(run_info)

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"💾 Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()


