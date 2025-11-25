"""
test_scenario_lgbm.py
Auth: 신지용
6피처 LGBM 단조 제약 모델에 대해,
소수의 대표 시나리오를 통해 직관적인 동작 여부를 빠르게 점검하는 스크립트.

현재 로직은 `backend.inference_sim_6feat_lgbm.predict_churn_6feat_lgbm`을 호출해
10개 전형적인 사용 패턴에 대한 위험도(L/M/H)를 확인합니다.

역할 분리:
- 모델 학습/저장        → `backend/training/train_simulator_6feat_lgbm_mono.py`
- 6피처 추론           → `backend.inference_sim_6feat_lgbm`
- 간단 시나리오 스모크 테스트 → 이 스크립트
"""

import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.inference_sim_6feat_lgbm import predict_churn_6feat_lgbm

# 1. 평범한 유저 (Clean)
scenario_1_clean = {
    "app_crash_count_30d": 0,
    "skip_rate_increase_7d": 0.0,
    "days_since_last_login": 1,
    "listening_time_trend_7d": 0.0,
    "freq_of_use_trend_14d": 0.0,
    "login_frequency_30d": 20,
}

# 2. 스킵만 늘어난 유저 (Quality only)
scenario_2_skip_only = {
    "app_crash_count_30d": 0,
    "skip_rate_increase_7d": 30.0,
    "days_since_last_login": 3,
    "listening_time_trend_7d": 0.0,
    "freq_of_use_trend_14d": 0.0,
    "login_frequency_30d": 20,
}

# 3. 크래시만 많은 유저 (Crash only)
scenario_3_crash_only = {
    "app_crash_count_30d": 3,
    "skip_rate_increase_7d": 0.0,
    "days_since_last_login": 3,
    "listening_time_trend_7d": 0.0,
    "freq_of_use_trend_14d": 0.0,
    "login_frequency_30d": 20,
}

# 4. 잠수만 심한 유저 (Inactive only)
scenario_4_days_only = {
    "app_crash_count_30d": 0,
    "skip_rate_increase_7d": 0.0,
    "days_since_last_login": 21,
    "listening_time_trend_7d": 0.0,
    "freq_of_use_trend_14d": 0.0,
    "login_frequency_30d": 10,
}

# 5. 사용량 급감만 있는 유저 (Trend only)
scenario_5_trend_only = {
    "app_crash_count_30d": 0,
    "skip_rate_increase_7d": 0.0,
    "days_since_last_login": 3,
    "listening_time_trend_7d": -20.0,
    "freq_of_use_trend_14d": -10.0,
    "login_frequency_30d": 15,
}

# 6. 중간 위험 (Medium 후보) - 여러 악재가 살짝씩 있는 상태
scenario_6_medium_combo = {
    "app_crash_count_30d": 2,
    "skip_rate_increase_7d": 10.0,
    "days_since_last_login": 7,
    "listening_time_trend_7d": -10.0,
    "freq_of_use_trend_14d": -6.0,
    "login_frequency_30d": 12,
}

# 7. 고위험 (Crash + 잠수)
scenario_7_high_crash_days = {
    "app_crash_count_30d": 3,
    "skip_rate_increase_7d": 5.0,
    "days_since_last_login": 21,
    "listening_time_trend_7d": -5.0,
    "freq_of_use_trend_14d": -4.0,
    "login_frequency_30d": 8,
}

# 8. 고위험 (잠수 + 사용량 급감)
scenario_8_high_days_trend = {
    "app_crash_count_30d": 1,
    "skip_rate_increase_7d": 5.0,
    "days_since_last_login": 21,
    "listening_time_trend_7d": -20.0,
    "freq_of_use_trend_14d": -10.0,
    "login_frequency_30d": 5,
}

# 9. 매우 안전 (High engagement)
scenario_9_very_safe = {
    "app_crash_count_30d": 0,
    "skip_rate_increase_7d": 0.0,
    "days_since_last_login": 0,
    "listening_time_trend_7d": 10.0,
    "freq_of_use_trend_14d": 8.0,
    "login_frequency_30d": 30,
}

# 10. 엣지 (값 범위 극단 조합)
scenario_10_edge = {
    "app_crash_count_30d": 4,
    "skip_rate_increase_7d": 35.0,
    "days_since_last_login": 30,
    "listening_time_trend_7d": -20.0,
    "freq_of_use_trend_14d": -16.0,
    "login_frequency_30d": 1,
}


scenarios = {
    "1. 평범 (Clean)": scenario_1_clean,
    "2. 스킵만 증가 (Quality only)": scenario_2_skip_only,
    "3. 크래시만 많음 (Crash only)": scenario_3_crash_only,
    "4. 잠수만 심함 (Days only)": scenario_4_days_only,
    "5. 사용량 급감 (Trend only)": scenario_5_trend_only,
    "6. 중간 위험 (Combo)": scenario_6_medium_combo,
    "7. 고위험 (Crash + Days)": scenario_7_high_crash_days,
    "8. 고위험 (Days + Trend)": scenario_8_high_days_trend,
    "9. 매우 안전 (High engagement)": scenario_9_very_safe,
    "10. 엣지 (Extreme combo)": scenario_10_edge,
}


for name, feats in scenarios.items():
    print(f"\n--- [{name}] 예측 (LGBM 단조제약) ---")
    result = predict_churn_6feat_lgbm(feats)
    print(f"입력 피처: {feats}")
    if result.get("success"):
        print(f"이탈 확률: {result['churn_prob']:.4f} ({result['risk_level']})")
    else:
        print(f"에러: {result.get('error')}")


