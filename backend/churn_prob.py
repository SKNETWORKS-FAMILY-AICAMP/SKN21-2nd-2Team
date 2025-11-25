"""
churn_prob.py
Auth: 신지용
학습에 사용한 CSV 전체에 대해 이탈 확률 분포를 확인하는 오프라인 스크립트.

현재 로직은 `data/processed/enhanced_data_not_clean_FE_delete.csv`를 로드해
`backend.inference.predict_churn`을 호출하여 각 유저의 이탈 확률과
위험도 레벨을 계산하고, 간단한 통계와 함께 CSV로 저장합니다.

역할 분리:
- 전처리/파이프라인 저장 → `backend/preprocessing_pipeline.py`
- 모델 정의/선택        → `backend/models.py`
- 배치 예측(분포 확인)  → 이 스크립트

사용 방법:
    python backend/churn_prob.py
"""

import os
import sys

import pandas as pd

# 프로젝트 루트 경로를 Python 경로에 추가 (backend 패키지 import 가능하게)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.inference import predict_churn


# 1) 학습에 사용했던 CSV 불러오기
df = pd.read_csv("data/processed/enhanced_data_not_clean_FE_delete.csv")
n_total = len(df)
print(f"총 {n_total}개 샘플에 대해 이탈 확률 계산 시작...")

# 2) 전체 행에 대해 이탈 확률 계산
probs = []
risk_levels = []

for i, (_, row) in enumerate(df.iterrows(), start=1):
    features = row.to_dict()
    result = predict_churn(user_features=features, model_name="hgb")
    if not result.get("success", False):
        raise RuntimeError(result.get("error"))
    probs.append(result["churn_prob"])
    risk_levels.append(result["risk_level"])

    # 진행도 로그 (500행 단위로 출력)
    if i % 500 == 0 or i == n_total:
        print(f"[진행도] {i}/{n_total} 행 처리 완료")

df["churn_prob"] = probs
df["risk_level"] = risk_levels

# 3) 전체 데이터 기준 이탈률/예측 통계 출력
n = len(df)
actual_churn_rate = df["is_churned"].mean() if "is_churned" in df.columns else None
mean_pred_prob = df["churn_prob"].mean()

th = 0.5
pred_churn_rate = (df["churn_prob"] >= th).mean()

print(f"총 샘플 수: {n}")
if actual_churn_rate is not None:
    print(f"실제 이탈률 (is_churned 평균): {actual_churn_rate:.4f}")
print(f"예측 확률 평균 (churn_prob 평균): {mean_pred_prob:.4f}")
print(f"threshold={th:.2f} 기준 예측 이탈률: {pred_churn_rate:.4f}")

# 상위 50개 샘플만 미리보기 출력 (index 리셋 + user_id 기준 정렬)
print("\n▶ 전체 샘플 (user_id, is_churned, churn_prob, risk_level):")
cols_to_show = [c for c in ["user_id", "is_churned", "churn_prob", "risk_level"] if c in df.columns]
preview = df[cols_to_show].sort_values("user_id").reset_index(drop=True)
print(preview.to_string(index=False))

# 4) churn_prob / risk_level 이 포함된 CSV 저장
output_path = "data/processed/enhanced_data_with_lgbm_churn_prob.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n예측 결과 저장 완료: {output_path}")