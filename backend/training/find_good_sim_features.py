import os
import sys
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# 프로젝트 루트 경로를 Python 경로에 추가 (backend 패키지 import 가능하게)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.inference import predict_churn


DATA_PATH = os.path.join("data", "processed", "enhanced_data_not_clean_FE_delete.csv")

# 시뮬레이터 후보 피처들 (전부 다 쓸 게 아니라, 여기서 상위 몇 개를 골라낼 것)
CANDIDATE_FEATURES: List[str] = [
    "payment_failure_count",
    "app_crash_count_30d",
    "listening_time_trend_7d",
    "skip_rate_increase_7d",
    "freq_of_use_trend_14d",
    "days_since_last_login",
    "login_frequency_30d",
    "songs_played_per_day",
]


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {path}")
    df = pd.read_csv(path)
    return df


def score_feature(
    df: pd.DataFrame,
    feature_name: str,
    n_rows: int = 80,
    n_grid: int = 7,
) -> Tuple[float, float, float]:
    """
    단일 피처 하나를 여러 값으로 바꿔가며 예측해 보고,
    - 단조성(스피어만 상관계수)
    - 예측 확률 변화폭(10%~90% 분위수 차이)
    를 기반으로 점수를 계산합니다.

    점수 = |Spearman Corr| * EffectSize
    """
    if feature_name not in df.columns:
        # 데이터에 없는 피처는 스킵
        return 0.0, 0.0, 0.0

    series = df[feature_name].dropna()
    if series.nunique() < 5:
        # 값이 너무 적으면 의미 있는 곡선을 만들기 어려움
        return 0.0, 0.0, 0.0

    # 값 범위를 분위수 기준으로 잡고, 그 안에서 균등 grid 생성
    q10, q50, q90 = np.percentile(series, [10, 50, 90])
    if q10 == q90:
        return 0.0, 0.0, 0.0

    grid = np.linspace(q10, q90, n_grid)

    # 여러 샘플(row)을 뽑아서, 해당 피처만 grid 값으로 바꿔가며 예측
    sample_df = df.sample(min(n_rows, len(df)), random_state=42)

    xs: List[float] = []
    probs: List[float] = []

    for _, row in sample_df.iterrows():
        base = row.to_dict()
        for v in grid:
            base[feature_name] = float(v)
            result = predict_churn(base, model_name="hgb")
            if not result.get("success", True):
                continue
            xs.append(float(v))
            probs.append(float(result["churn_prob"]))

    if len(xs) < 5:
        return 0.0, 0.0, 0.0

    # 단조성: Spearman 상관계수
    from scipy.stats import spearmanr  # type: ignore

    corr, _ = spearmanr(xs, probs)

    # 예측 확률 변화폭
    p10, p90 = np.percentile(probs, [10, 90])
    effect = float(p90 - p10)

    if np.isnan(corr) or np.isnan(effect):
        return 0.0, 0.0, 0.0

    score = abs(float(corr)) * effect
    return score, float(corr), effect


def main() -> None:
    print("✅ 데이터 로드 중...")
    df = load_data(DATA_PATH)
    print(f" - shape: {df.shape}")

    results: List[Dict[str, float]] = []

    print("\n🔥 피처별 반응도 스코어 계산 시작...\n")

    for feat in CANDIDATE_FEATURES:
        try:
            score, corr, effect = score_feature(df, feat)
        except Exception as e:
            print(f"  [SKIP] {feat}: 에러 발생 -> {e}")
            continue

        print(
            f"  {feat:25s} | score={score:6.4f} | corr={corr:6.3f} | effect={effect:6.3f}"
        )
        results.append(
            {
                "feature": feat,
                "score": score,
                "corr": corr,
                "effect": effect,
            }
        )

    if not results:
        print("\n❌ 유효한 결과가 없습니다. 데이터/피처 이름을 확인하세요.")
        return

    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values("score", ascending=False)

    print("\n" + "=" * 70)
    print("📊 시뮬레이터용 \"좋은 피처\" 순위 (상위 6개 추천)")
    print("=" * 70)
    print(res_df.to_string(index=False))

    top_k = res_df.head(6)["feature"].tolist()
    print("\n✅ 추천 입력 피처 조합 (프론트에서 받아 쓰면 좋은 컬럼들):")
    for f in top_k:
        print(f" - {f}")


if __name__ == "__main__":
    main()


