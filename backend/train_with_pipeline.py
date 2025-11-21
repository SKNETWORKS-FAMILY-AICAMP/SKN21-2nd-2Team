"""
train_with_pipeline.py

전처리 파이프라인(`backend/preprocessing.py`)을 호출해
모델 학습 + 평가(F1, AUC, Best Threshold)를 수행하는 스크립트.

역할 분리:
- 전처리 수정        → `backend/preprocessing.py`
- 모델 종류/파라미터 → `backend/models.py`의 `get_model()`
- 데이터 경로/seed/비율 → 아래 CONFIG 상수만 수정
"""

import numpy as np
from preprocessing import preprocess_pipeline  # 같은 backend 디렉터리 기준 import
from sklearn.metrics import f1_score, roc_auc_score

from models import get_model


# =========================================================
# 공통 설정 (팀원은 여기만 바꿔도 실험 가능)
# =========================================================
DATA_PATH = "data/enhanced_data_not_clean_FE_delete.csv"
TEST_SIZE = 0.2
RANDOM_STATE = 42
MODEL_NAME = "rf"  # "rf", "logit" 등 backend/models.py에서 지원하는 이름


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
        thresholds = np.arange(0.05, 0.35, 0.01)

    best_f1 = 0.0
    best_th = float(thresholds[0])

    for th in thresholds:
        y_pred = (y_proba >= th).astype(int)
        f1 = f1_score(y_true, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_th = float(th)

    auc = roc_auc_score(y_true, y_proba)
    return best_f1, auc, best_th


def main():
    # 1) 전처리 파이프라인 실행
    #    - 데이터 경로/비율/seed는 상단 CONFIG를 통해 제어
    X_train, X_test, y_train, y_test, _ = preprocess_pipeline(
        path=DATA_PATH,
        save_output=False,  # 모델 테스트용이므로 파일은 저장하지 않음
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # 2) 모델 생성 및 학습
    #    - MODEL_NAME을 "rf" → "logit" 등으로 바꿔가며 실험 가능
    model = get_model(name=MODEL_NAME, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    # 3) 예측 및 평가
    y_proba = model.predict_proba(X_test)[:, 1]
    best_f1, auc, best_th = evaluate_with_best_threshold(y_test, y_proba)

    print("📊 Evaluation with preprocessing pipeline")
    print(f"- F1 Score      : {best_f1:.4f}")
    print(f"- AUC           : {auc:.4f}")
    print(f"- Best Threshold: {best_th:.2f}")
    print(f"- n_train       : {len(y_train)}")
    print(f"- n_test        : {len(y_test)}")


if __name__ == "__main__":
    main()


