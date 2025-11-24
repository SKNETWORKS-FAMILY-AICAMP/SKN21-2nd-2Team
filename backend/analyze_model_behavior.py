import sys
import os
import pandas as pd
import numpy as np

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.inference import predict_churn

# 기준 유저 (모든 값이 평균적이거나 0인 상태)
base_user = {
    "payment_failure_count": 0,
    "listening_time_trend_7d": 0.0,
    "skip_rate_increase_7d": 0.0,    # [NEW]
    "app_crash_count_30d": 0,
    "days_since_last_login": 1,      # [NEW]
    
    # 기본값
    "songs_played_per_day": 30,
    "customer_support_contact": 0,
    "subscription_type": "Premium",
    "age": 30,
    "listening_time": 60,
    "skip_rate": 0.2
}

def test_feature_impact(feature_name, test_values):
    print(f"\n📊 [{feature_name}] 변화에 따른 이탈 확률 추이")
    print(f"{'입력값':^10} | {'이탈 확률 (%)':^15} | {'위험 레벨':^10}")
    print("-" * 45)
    
    for val in test_values:
        user = base_user.copy()
        user[feature_name] = val
        
        result = predict_churn(user, model_name="hgb")
        prob = result['churn_prob'] * 100
        level = result['risk_level']
        
        print(f"{str(val):^10} | {prob:^15.2f} | {level:^10}")

# 1. [필수] 결제 실패 (0~3)
test_feature_impact("payment_failure_count", [0, 1, 2, 3])

# 2. [필수] 양적 변화: 사용량 추세 (-50% ~ +50%)
test_feature_impact("listening_time_trend_7d", [-50, -20, -10, 0, 10, 50])

# 3. [NEW] 질적 변화: 스킵률 증가 (0% ~ 50%)
# - 값이 클수록(스킵 많이 함) 위험해야 정상
test_feature_impact("skip_rate_increase_7d", [0, 10, 20, 30, 50])

# 4. [보조] 기술적 불만: 앱 오류 (0~5)
test_feature_impact("app_crash_count_30d", [0, 1, 3, 5])

# 5. [보조] 접속 성실도: 미접속 일수 (1일 ~ 30일)
# - 길수록 위험
test_feature_impact("days_since_last_login", [1, 7, 14, 30])


# ==============================================================================
# 🧪 [최종] 5대 요소 시나리오 검증
# ==============================================================================
def test_scenario_validation():
    print("\n" + "="*60)
    print("🧪 [최종 검증] 5대 핵심 요소 시나리오 테스트")
    print("="*60)
    
    scenarios = {
        "1. 평범 (Clean)": {
            "payment_failure_count": 0, "listening_time_trend_7d": 0.0,
            "skip_rate_increase_7d": 0.0, "app_crash_count_30d": 0, "days_since_last_login": 1
        },
        "2. 질적 불만 (스킵 증가)": {
            # 사용량은 그대로인데 스킵만 늘어난 경우 -> "지루함"
            "payment_failure_count": 0, "listening_time_trend_7d": 0.0,
            "skip_rate_increase_7d": 30.0, "app_crash_count_30d": 0, "days_since_last_login": 3
        },
        "3. 복합 위험 (결제+감소+잠수)": {
            # 돈 안 내고, 덜 듣고, 잠수 탐 -> "이탈 임박"
            "payment_failure_count": 1, "listening_time_trend_7d": -10.0,
            "skip_rate_increase_7d": 10.0, "app_crash_count_30d": 1, "days_since_last_login": 14
        },
        "4. 최악 (모든 악재)": {
            "payment_failure_count": 2, "listening_time_trend_7d": -30.0,
            "skip_rate_increase_7d": 50.0, "app_crash_count_30d": 3, "days_since_last_login": 30
        }
    }
    
    print(f"{'시나리오 명':<20} | {'확률 (%)':^10} | {'레벨':^10}")
    print("-" * 45)

    for name, features in scenarios.items():
        user = base_user.copy()
        user.update(features)
        
        result = predict_churn(user, model_name="hgb")
        prob = result['churn_prob'] * 100
        level = result['risk_level']
        
        print(f"{name:<20} | {prob:^10.2f} | {level:^10}")

test_scenario_validation()
