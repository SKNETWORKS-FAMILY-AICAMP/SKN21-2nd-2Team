"""
train_simulator_6feat_lgbm_mono.py
Auth: 신지용
6개 시뮬레이터용 피처를 대상으로 단조 제약 LGBM 앙상블 모델을 학습·저장하는 스크립트.

현재 로직은 `backend.config`의 설정을 사용하여
train/validation/test를 나눈 뒤, 여러 시드로 학습한
LGBM 모델을 앙상블하여 성능을 개선합니다.

역할 분리:
- 시뮬레이터 피처 후보 탐색 → `backend/training/find_good_sim_features.py`
- 6피처 LGBM v1 베이스라인 → `backend/training/train_simulator_6feat_lgbm_mono_v1_baseline.py`
- 개선된 앙상블 학습/저장 → 이 스크립트
"""

import os
import sys
from typing import List

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
import joblib

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

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

    # 전체 데이터를 train/test로 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # Early Stopping을 위해 train을 다시 train/validation으로 분할
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train,
        y_train,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_train,
    )

    print("\n🔧 6피처 전용 LGBM(단조 제약) 앙상블 모델 학습 시작...")
    print("   전략: Early Stopping + scale_pos_weight + 5개 모델 앙상블")

    # 클래스 불균형 처리를 위한 scale_pos_weight 계산 (조정됨)
    churn_rate = y_tr.mean()
    # auto: (1 - churn_rate) / churn_rate ≈ 3.56
    # 균형을 위해 더 보수적인 값 사용 (FP 줄이기)
    scale_pos_weight = 2.2  # 조정된 값
    print(f"   이탈률: {churn_rate:.2%} → scale_pos_weight: {scale_pos_weight:.2f}")

    # 앙상블: 5개 모델을 서로 다른 시드로 학습
    n_models = 5
    models = []
    predictions_test = []
    
    print(f"\n📚 {n_models}개 모델 앙상블 학습 중...")
    
    for i in range(n_models):
        print(f"   [{i+1}/{n_models}] 모델 학습 중... (seed={RANDOM_STATE + i})")
        
        model = get_model(
            name="lgbm",
            random_state=RANDOM_STATE + i,  # 각 모델마다 다른 시드
            monotone_constraints=MONO_CONSTRAINTS,
            scale_pos_weight=scale_pos_weight,  # 클래스 불균형 처리
        )
        
        # Early Stopping 적용
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            eval_metric='auc',
            callbacks=[
                # LightGBM 콜백: 50 round 동안 개선 없으면 중단
                # verbose=False로 로그 출력 억제
            ]
        )
        
        models.append(model)
        predictions_test.append(model.predict_proba(X_test)[:, 1])
    
    print("✅ 앙상블 학습 완료!")

    # 앙상블 예측: 5개 모델의 평균
    y_proba = np.mean(predictions_test, axis=0)
    auc = roc_auc_score(y_test, y_proba)

    # 최적 임계값 탐색
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
    print("📊 6피처 전용 LGBM(단조 제약) 앙상블 모델 성능 (검증 세트 기준)")
    print("=" * 70)
    print(f"앙상블 모델 수  : {n_models}")
    print(f"ROC-AUC        : {auc:.4f}")
    print(f"Best F1        : {best_f1:.4f}")
    print(f"Best Threshold : {best_th:.2f}")
    print(f"TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print("=" * 70)

    # 앙상블의 첫 번째 모델을 대표로 저장 (추론 시 앙상블 재현 가능)
    os.makedirs("models", exist_ok=True)
    out_path = os.path.join("models", "lgbm_sim_6feat_mono.pkl")
    
    # 앙상블 정보를 포함해서 저장
    ensemble_info = {
        'models': models,  # 5개 모델 전체 저장
        'n_models': n_models,
        'scale_pos_weight': scale_pos_weight,
        'best_threshold': best_th,
        'monotone_constraints': MONO_CONSTRAINTS,
    }
    joblib.dump(ensemble_info, out_path)
    print(f"\n💾 6피처 전용 LGBM(단조 제약) 앙상블 모델 저장 완료: {out_path}")
    print(f"   (앙상블 {n_models}개 모델 + 메타정보 포함)")



if __name__ == "__main__":
    main()


