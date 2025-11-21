"""
Baseline 모델 학습/평가를 한 번에 실행하는 엔트리포인트 스크립트.

위치는 backend/ 아래에 두지만,
실제 ML 로직(데이터 로딩, 모델, 학습/평가)은 모두 src/ 패키지에 모듈화되어 있다.

사용 방법 (프로젝트 루트에서):
    python backend/run_baseline.py

다른 팀원은:
- src/config.py의 MODEL_NAME, 하이퍼파라미터(dict)만 수정해서
  동일한 코드 구조로 다양한 모델/파라미터 조합을 시험할 수 있다.
"""

from pathlib import Path
import sys

# ---------------------------------------------------------------------------
# PYTHONPATH에 프로젝트 루트(src 패키지가 있는 위치)를 강제로 추가
# - 사용자 실행 위치와 관계없이 항상 src를 import할 수 있게 하기 위함.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_PATH, MODEL_NAME
from src.data_loader import load_data
from src.models import get_model
from src.train_eval import train_and_evaluate


def main() -> None:
    print("=" * 80)
    print("📁 Baseline 실행 정보")
    print("=" * 80)
    print(f"- DATA_PATH : {DATA_PATH}")
    print(f"- MODEL_NAME: {MODEL_NAME}")

    # 1) 데이터 로드 (여기서는 이미 clean된 CSV를 사용)
    X, y = load_data()
    print("\n[데이터 요약]")
    print(f"- 샘플 수      : {X.shape[0]}")
    print(f"- 피처 수      : {X.shape[1]}")

    # 2) 모델 생성
    model = get_model()
    print(f"\n[모델 생성 완료] 타입: {type(model).__name__}")

    # 3) 학습 및 평가
    print("\n[학습 및 평가 진행 중...]")
    metrics, trained_model = train_and_evaluate(model, X, y)

    # 4) 결과 출력
    print("\n" + "=" * 80)
    print("📊 평가 결과 (Baseline)")
    print("=" * 80)
    print(f"- F1 Score      : {metrics['F1']:.4f}")
    print(f"- AUC           : {metrics['AUC']:.4f}")
    print(f"- Best Threshold: {metrics['best_threshold']:.2f}")
    print(f"- 샘플 수       : {metrics['n_samples']}")
    print(f"- Threshold 개수: {metrics['n_thresholds']}")
    print("=" * 80)

    # TODO:
    # - 추후 여기에서 모델을 pickle/joblib으로 저장하거나
    #   feature importance, confusion matrix 등을 추가로 출력할 수 있다.


if __name__ == "__main__":
    main()


