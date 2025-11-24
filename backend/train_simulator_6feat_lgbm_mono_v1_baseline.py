import os
import sys
from typing import List

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
import joblib

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import (
    DATA_PATH,
    TEST_SIZE,
    RANDOM_STATE,
    THRESH_START,
    THRESH_END,
    THRESH_STEP,
)
from backend.models import get_model


# 시뮬레이터용 6개 피처
SIM_FEATURES: List[str] = [
    "app_crash_count_30d",
    "skip_rate_increase_7d",
    "days_since_last_login",
    "listening_time_trend_7d",
    "freq_of_use_trend_14d",
    "login_frequency_30d",
]

# 단조 제약 방향
#  +1: 값이 증가할수록 이탈 확률이 "증가"해야 함
#  -1: 값이 증가할수록 이탈 확률이 "감소"해야 함
MONO_CONSTRAINTS = [
    +1,  # app_crash_count_30d        (크래시 많을수록 위험 ↑)
    +1,  # skip_rate_increase_7d      (스킵률 증가할수록 위험 ↑)
    +1,  # days_since_last_login      (오래 안 들어올수록 위험 ↑)
    -1,  # listening_time_trend_7d    (값이 커질수록 사용량 증가 → 위험 ↓)
    -1,  # freq_of_use_trend_14d      (사용 빈도 증가 → 위험 ↓)
    -1,  # login_frequency_30d        (로그인 자주 할수록 위험 ↓)
]


def main() -> None:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    if "is_churned" not in df.columns:
        raise ValueError("'is_churned' 타깃 컬럼을 찾을 수 없습니다.")

    print(f"✅ 데이터 로드 완료: {df.shape}")
    print(f"   이탈률: {df['is_churned'].mean():.2%}")

    X = df[SIM_FEATURES].copy()
    y = df["is_churned"].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print("\n🔧 6피처 전용 LGBM(단조 제약) 기본 모델 학습 시작...")

    # 기본 모델 - 단조 제약만 적용
    model = get_model(
        name="lgbm",
        random_state=RANDOM_STATE,
        monotone_constraints=MONO_CONSTRAINTS,
    )
    model.fit(X_train, y_train)
    print("✅ 학습 완료!")

    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    thresholds = np.arange(THRESH_START, THRESH_END, THRESH_STEP)
    best_f1 = 0.0
    best_th = 0.5

    for th in thresholds:
        y_pred = (y_proba >= th).astype(int)
        f1 = f1_score(y_test, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_th = float(th)

    y_best = (y_proba >= best_th).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, y_best).ravel()

    print("\n" + "=" * 70)
    print("📊 6피처 전용 LGBM(단조 제약) 기본 모델 성능 (검증 세트 기준)")
    print("=" * 70)
    print(f"ROC-AUC        : {auc:.4f}")
    print(f"Best F1        : {best_f1:.4f}")
    print(f"Best Threshold : {best_th:.2f}")
    print(f"TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print("=" * 70)

    os.makedirs("models", exist_ok=True)
    out_path = os.path.join("models", "lgbm_sim_6feat_mono_v1_baseline.pkl")
    joblib.dump(model, out_path)
    print(f"\n💾 6피처 전용 LGBM(단조 제약) 기본 모델 저장 완료: {out_path}")
    print("   (v1 기본 버전 - 단조 제약만 적용)")


if __name__ == "__main__":
    main()
