"""
test_comprehensive_scenarios.py
Auth: 신지용
6피처 LGBM 단조 제약 앙상블 모델에 대해,
사람이 정의한 다양한 유저 페르소나 시나리오를 종합적으로 테스트하는 스크립트.

현재 로직은 `backend.inference_sim_6feat_lgbm.predict_churn_6feat_lgbm`을 호출해
20개 시나리오에 대한 이탈 확률 및 위험도 분포를 점검합니다.

역할 분리:
- 모델 학습/저장     → `backend/training/train_simulator_6feat_lgbm_mono.py`
- 6피처 추론        → `backend.inference_sim_6feat_lgbm`
- 시나리오 기반 점검 → 이 스크립트
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.inference_sim_6feat_lgbm import predict_churn_6feat_lgbm


# ==============================================================================
# 📱 유저 페르소나 기반 시나리오 (20가지)
# ==============================================================================

scenarios = {
    # ===== 매우 안전 그룹 (Super Active Users) =====
    "1. 파워 유저 (매일 접속, 사용량 증가)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": -5.0,  # 스킵률 감소!
        "days_since_last_login": 0,
        "listening_time_trend_7d": 15.0,  # 청취시간 15% 증가
        "freq_of_use_trend_14d": 10.0,    # 사용빈도 10% 증가
        "login_frequency_30d": 30,
    },
    
    "2. 충성 고객 (꾸준한 사용)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 0.0,
        "days_since_last_login": 1,
        "listening_time_trend_7d": 5.0,
        "freq_of_use_trend_14d": 3.0,
        "login_frequency_30d": 25,
    },
    
    "3. 열성 신규 유저 (최근 가입, 매우 활발)": {
        "app_crash_count_30d": 1,  # 신규라 기능 탐색 중 가끔 크래시
        "skip_rate_increase_7d": 2.0,  # 취향 찾는 중
        "days_since_last_login": 0,
        "listening_time_trend_7d": 20.0,  # 급증!
        "freq_of_use_trend_14d": 15.0,
        "login_frequency_30d": 20,
    },
    
    # ===== 안전 그룹 (Normal Active Users) =====
    "4. 일반 유저 (주 3-4회 접속)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 0.0,
        "days_since_last_login": 2,
        "listening_time_trend_7d": 0.0,
        "freq_of_use_trend_14d": 0.0,
        "login_frequency_30d": 15,
    },
    
    "5. 출퇴근 유저 (규칙적 사용)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 1.0,
        "days_since_last_login": 1,
        "listening_time_trend_7d": 2.0,
        "freq_of_use_trend_14d": 1.0,
        "login_frequency_30d": 22,  # 주 5일 출퇴근
    },
    
    "6. 주말 유저 (주말에만 집중 사용)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 0.0,
        "days_since_last_login": 4,  # 주중엔 안 들어옴
        "listening_time_trend_7d": 5.0,
        "freq_of_use_trend_14d": 3.0,
        "login_frequency_30d": 8,   # 월 8회 (주말만)
    },
    
    # ===== 경고 단계 (Warning Signs) =====
    "7. 음질 불만 유저 (스킵률만 급증)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 25.0,  # 추천 알고리즘 불만
        "days_since_last_login": 2,
        "listening_time_trend_7d": 0.0,
        "freq_of_use_trend_14d": 0.0,
        "login_frequency_30d": 18,
    },
    
    "8. 기술적 문제 경험 유저 (크래시 빈발)": {
        "app_crash_count_30d": 5,  # 심각한 크래시 문제
        "skip_rate_increase_7d": 3.0,
        "days_since_last_login": 3,
        "listening_time_trend_7d": -5.0,  # 조금 감소
        "freq_of_use_trend_14d": -3.0,
        "login_frequency_30d": 15,
    },
    
    "9. 관심 감소 유저 (사용량 서서히 감소)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 5.0,
        "days_since_last_login": 5,
        "listening_time_trend_7d": -8.0,
        "freq_of_use_trend_14d": -6.0,
        "login_frequency_30d": 12,
    },
    
    "10. 바쁜 직장인 (최근 접속 빈도 감소)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 0.0,
        "days_since_last_login": 10,  # 바쁜 일주일
        "listening_time_trend_7d": -5.0,
        "freq_of_use_trend_14d": -4.0,
        "login_frequency_30d": 10,
    },
    
    # ===== 중간 위험 그룹 (Medium Risk) =====
    "11. 경쟁 서비스 탐색 중 (여러 악재)": {
        "app_crash_count_30d": 2,
        "skip_rate_increase_7d": 15.0,
        "days_since_last_login": 7,
        "listening_time_trend_7d": -12.0,
        "freq_of_use_trend_14d": -8.0,
        "login_frequency_30d": 10,
    },
    
    "12. 불만족 유저 (크래시 + 스킵 증가)": {
        "app_crash_count_30d": 4,
        "skip_rate_increase_7d": 20.0,
        "days_since_last_login": 5,
        "listening_time_trend_7d": -8.0,
        "freq_of_use_trend_14d": -5.0,
        "login_frequency_30d": 12,
    },
    
    "13. 흥미 상실 초기 단계 (서서히 멀어짐)": {
        "app_crash_count_30d": 1,
        "skip_rate_increase_7d": 10.0,
        "days_since_last_login": 9,
        "listening_time_trend_7d": -15.0,
        "freq_of_use_trend_14d": -10.0,
        "login_frequency_30d": 8,
    },
    
    # ===== 고위험 그룹 (High Risk) =====
    "14. 장기 미접속 유저 (3주 이상)": {
        "app_crash_count_30d": 1,
        "skip_rate_increase_7d": 5.0,
        "days_since_last_login": 25,
        "listening_time_trend_7d": -18.0,
        "freq_of_use_trend_14d": -12.0,
        "login_frequency_30d": 3,
    },
    
    "15. 크래시 피해 유저 (나쁜 경험)": {
        "app_crash_count_30d": 6,
        "skip_rate_increase_7d": 12.0,
        "days_since_last_login": 14,
        "listening_time_trend_7d": -15.0,
        "freq_of_use_trend_14d": -10.0,
        "login_frequency_30d": 5,
    },
    
    "16. 거의 탈퇴 직전 (모든 지표 나쁨)": {
        "app_crash_count_30d": 3,
        "skip_rate_increase_7d": 30.0,
        "days_since_last_login": 20,
        "listening_time_trend_7d": -25.0,
        "freq_of_use_trend_14d": -20.0,
        "login_frequency_30d": 2,
    },
    
    # ===== 매우 고위험 (Critical Risk) =====
    "17. 완전 이탈 (한 달 미접속)": {
        "app_crash_count_30d": 2,
        "skip_rate_increase_7d": 10.0,
        "days_since_last_login": 30,
        "listening_time_trend_7d": -20.0,
        "freq_of_use_trend_14d": -15.0,
        "login_frequency_30d": 1,
    },
    
    "18. 최악의 경험 유저 (극단적 악재)": {
        "app_crash_count_30d": 8,
        "skip_rate_increase_7d": 40.0,
        "days_since_last_login": 28,
        "listening_time_trend_7d": -30.0,
        "freq_of_use_trend_14d": -25.0,
        "login_frequency_30d": 1,
    },
    
    # ===== 특수 케이스 (Edge Cases) =====
    "19. 복귀 유저 (오랜만에 재접속, 사용량 회복 중)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 0.0,
        "days_since_last_login": 15,  # 오랜만에 접속
        "listening_time_trend_7d": 10.0,  # 다시 사용 증가!
        "freq_of_use_trend_14d": 8.0,
        "login_frequency_30d": 5,  # 최근엔 적지만 회복 중
    },
    
    "20. 시험 기간 학생 (일시적 감소)": {
        "app_crash_count_30d": 0,
        "skip_rate_increase_7d": 0.0,
        "days_since_last_login": 12,  # 시험 기간 2주
        "listening_time_trend_7d": -10.0,
        "freq_of_use_trend_14d": -8.0,
        "login_frequency_30d": 8,  # 평소엔 활발했음
    },
}


# ==============================================================================
# 테스트 실행 및 결과 분석
# ==============================================================================

def run_comprehensive_test():
    print("=" * 80)
    print("🧪 LGBM 앙상블 모델 포괄적 시나리오 테스트")
    print("=" * 80)
    print(f"총 {len(scenarios)}개 시나리오 테스트\n")
    
    results = {
        "LOW": [],
        "MEDIUM": [],
        "HIGH": [],
        "ERROR": []
    }
    
    for idx, (name, features) in enumerate(scenarios.items(), 1):
        print(f"\n{'='*80}")
        print(f"[{idx}/{len(scenarios)}] {name}")
        print(f"{'='*80}")
        
        # 피처 출력 (보기 좋게)
        print("📊 입력 피처:")
        print(f"  • 크래시 횟수 (30일):      {features['app_crash_count_30d']}")
        print(f"  • 스킵률 증가 (7일):       {features['skip_rate_increase_7d']:+.1f}%")
        print(f"  • 마지막 로그인:           {features['days_since_last_login']}일 전")
        print(f"  • 청취시간 추세 (7일):     {features['listening_time_trend_7d']:+.1f}%")
        print(f"  • 사용빈도 추세 (14일):    {features['freq_of_use_trend_14d']:+.1f}%")
        print(f"  • 로그인 횟수 (30일):      {features['login_frequency_30d']}")
        
        # 예측 수행
        result = predict_churn_6feat_lgbm(features)
        
        if result.get("success"):
            churn_prob = result['churn_prob']
            risk_level = result['risk_level']
            ensemble_size = result.get('ensemble_size', 1)
            
            print(f"\n🎯 예측 결과:")
            print(f"  ✓ 이탈 확률: {churn_prob:.4f} ({churn_prob*100:.2f}%)")
            print(f"  ✓ 위험도: {risk_level}")
            print(f"  ✓ 앙상블 크기: {ensemble_size}개 모델")
            
            # 위험도별 이모지
            emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
            print(f"\n  {emoji.get(risk_level, '⚪')} {risk_level} 위험군")
            
            results[risk_level].append({
                "name": name,
                "prob": churn_prob,
                "features": features
            })
        else:
            print(f"\n❌ 에러: {result.get('error')}")
            results["ERROR"].append(name)
    
    # 최종 요약
    print("\n\n" + "=" * 80)
    print("📈 테스트 결과 요약")
    print("=" * 80)
    print(f"🟢 LOW 위험군:    {len(results['LOW'])}건")
    print(f"🟡 MEDIUM 위험군: {len(results['MEDIUM'])}건")
    print(f"🔴 HIGH 위험군:   {len(results['HIGH'])}건")
    if results["ERROR"]:
        print(f"❌ 에러:          {len(results['ERROR'])}건")
    
    # 각 그룹별 상세 정보
    for risk_level in ["LOW", "MEDIUM", "HIGH"]:
        if results[risk_level]:
            print(f"\n{'='*80}")
            print(f"{risk_level} 위험군 상세 ({len(results[risk_level])}건)")
            print(f"{'='*80}")
            
            # 확률 기준으로 정렬
            sorted_results = sorted(results[risk_level], key=lambda x: x['prob'])
            
            for item in sorted_results:
                print(f"  • {item['name'][:40]:<40} | 이탈 확률: {item['prob']:.4f}")
    
    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    run_comprehensive_test()
