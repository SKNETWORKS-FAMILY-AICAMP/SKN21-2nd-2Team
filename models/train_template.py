"""
train_template.py (공통 모델 템플릿)
Author: 정세연
Date: 2025-11-20
Description
- 데이터 로딩·전처리·모델 학습·평가·저장을 포함한 공통 Baseline 템플릿!
"""

import argparse
import os
import json
import datetime
import logging
from typing import List, Dict, Tuple, Any

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score


# -----------------------------------------------------------
# 로깅 설정 (기본: INFO, CLI에서 조정 가능)
# -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------
# 1. 기본 설정 (데이터 구조 정의)
# -----------------------------------------------------------

# 타겟 컬럼명
TARGET_COL = "is_churned"

# ID 컬럼 (feature에서 제거)
ID_COLS: List[str] = ["user_id"]

# 숫자형 피처
NUM_FEATURES: List[str] = [
    "age",
    "listening_time",
    "songs_played_per_day",
    "skip_rate",
    "ads_listened_per_week",
    "offline_listening",
]

# 범주형 피처
CAT_FEATURES: List[str] = [
    "gender",
    "country",
    "subscription_type",
    "device_type",
]


# -----------------------------------------------------------
# 2. 데이터 로딩 및 검증
# -----------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    """CSV 파일 로드 및 필수 컬럼 검증"""
    if not os.path.exists(path):
        logger.error(f"Data file not found: {path}")
        raise FileNotFoundError(f"Data file not found: {path}")

    logger.info(f"Loading data from: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # 필수 컬럼 체크
    required_cols = NUM_FEATURES + CAT_FEATURES + [TARGET_COL]
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df


def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """기본적인 데이터 검증 (결측치, 타겟 분포, 숫자형 통계)"""
    logger.info("Validating data...")

    # 결측치 확인
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.warning(f"Missing values found:\n{null_counts[null_counts > 0]}")

    # 타겟 분포 확인
    if TARGET_COL in df.columns:
        target_dist = df[TARGET_COL].value_counts()
        logger.info(f"Target distribution:\n{target_dist}")

    # 숫자형 피처 기본 통계 (DEBUG 레벨로만 출력)
    numeric_cols = [col for col in NUM_FEATURES if col in df.columns]
    if numeric_cols:
        logger.debug(f"Numeric features summary:\n{df[numeric_cols].describe()}")

    return df


def train_valid_split(
    df: pd.DataFrame,
    target_col: str = TARGET_COL,
    valid_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """학습 / 검증 데이터 분리"""
    # 타겟 컬럼 확인
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in dataframe")
        raise ValueError(f"Target column '{target_col}' not found")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_valid, y_train, y_valid = train_test_split(
        X,
        y,
        test_size=valid_size,
        random_state=random_state,
        stratify=y,
    )

    logger.info(f"Train size: {len(X_train)}, Valid size: {len(X_valid)}")
    logger.info(f"Train target distribution:\n{y_train.value_counts()}")
    logger.info(f"Valid target distribution:\n{y_valid.value_counts()}")

    return X_train, X_valid, y_train, y_valid


# -----------------------------------------------------------
# 3. 전처리 + 모델 정의
# -----------------------------------------------------------

def build_preprocessor(
    numeric_features: List[str],
    categorical_features: List[str],
) -> ColumnTransformer:
    """숫자형 + 범주형 전처리 파이프라인 생성"""
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )
    return preprocessor


def build_baseline_model() -> LogisticRegression:
    """
    베이스라인 모델 - Logistic Regression
    다른 모델로 교체 시 이 함수만 수정하면 됩니다.
    """
    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        n_jobs=-1,
    )
    return model


def build_pipeline(
    numeric_features: List[str],
    categorical_features: List[str],
) -> Pipeline:
    """전처리 + Logistic Regression으로 파이프라인 구성"""
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    model = build_baseline_model()

    clf = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )
    return clf


# -----------------------------------------------------------
# 4. 성능 평가 및 저장
# -----------------------------------------------------------

def compute_metrics(
    y_true,
    y_pred,
    y_proba=None,
) -> Dict[str, float]:
    """공통으로 사용하는 성능 평가 함수"""
    metrics: Dict[str, float] = {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
    }

    if y_proba is not None:
        try:
            metrics["roc_auc"] = roc_auc_score(y_true, y_proba)
        except ValueError as e:
            logger.warning(f"Could not compute ROC AUC: {e}")
            metrics["roc_auc"] = float("nan")

    return metrics


def save_metrics(metrics: Dict[str, float], output_path: str = "metrics.json"):
    """메트릭을 JSON 파일로 저장 (NaN 값은 null로 변환)"""
    try:
        # NaN → null로 변환 (표준 JSON 호환)
        clean_metrics: Dict[str, Any] = {}
        for k, v in metrics.items():
            if isinstance(v, float) and pd.isna(v):
                clean_metrics[k] = None
            else:
                clean_metrics[k] = float(v)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(clean_metrics, f, indent=2, ensure_ascii=False)

        logger.info(f"Metrics saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")


def print_metrics(metrics: Dict[str, float]):
    """메트릭을 보기 좋게 출력 (NaN 처리 포함)"""
    print("\n" + "=" * 60)
    print("=== Validation Metrics (Baseline: Logistic Regression) ===")
    print("=" * 60)
    for k, v in metrics.items():
        if isinstance(v, float) and pd.isna(v):
            print(f"{k:>12s}: N/A")
        else:
            print(f"{k:>12s}: {v:.4f}")
    print("=" * 60)


# -----------------------------------------------------------
# 5. 학습 + 평가 + 모델 저장 (메타데이터 포함)
# -----------------------------------------------------------

def save_model_with_metadata(
    pipeline: Pipeline,
    metrics: Dict[str, float],
    model_output_path: str,
):
    """
    모델과 메타데이터를 함께 저장.

    NOTE:
    - model_output_path(.pkl)에는 dict가 저장됩니다.
      {
        'pipeline': sklearn Pipeline 객체,
        'metrics': 학습 시점의 성능 메트릭,
        'timestamp': 저장 시각(ISO 문자열),
        'features': {
            'numeric': NUM_FEATURES,
            'categorical': CAT_FEATURES
        },
        'target_col': TARGET_COL
      }

    - 로드 예시:
      >>> import joblib
      >>> model_info = joblib.load("model_lk.pkl")
      >>> pipeline = model_info["pipeline"]
      >>> y_pred = pipeline.predict(X_new)
    """
    model_info = {
        "pipeline": pipeline,
        "metrics": metrics,
        "timestamp": datetime.datetime.now().isoformat(),
        "features": {
            "numeric": NUM_FEATURES,
            "categorical": CAT_FEATURES,
        },
        "target_col": TARGET_COL,
    }

    try:
        joblib.dump(model_info, model_output_path)
        logger.info(f"Model with metadata saved to: {model_output_path}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        raise


def train_and_evaluate(
    data_path: str,
    model_output_path: str = "model_lk.pkl",
    metrics_output_path: str = "metrics.json",
    valid_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[Dict[str, float], str]:
    """
    공통 학습 함수
    - 데이터 로드 및 검증
    - train/valid split
    - 파이프라인 학습
    - 성능 평가 후 출력 및 저장
    - 모델 저장 (.pkl with metadata)

    Returns:
        Tuple[Dict[str, float], str]: (메트릭 딕셔너리, 모델 저장 경로)
    """
    try:
        # 1) 데이터 로드
        df = load_data(data_path)

        # 2) 데이터 검증
        df = validate_data(df)

        # 3) ID 컬럼 제거
        drop_cols = [col for col in ID_COLS if col in df.columns]
        if drop_cols:
            logger.info(f"Dropping ID columns: {drop_cols}")
            df = df.drop(columns=drop_cols)

        # 4) train/valid 분리
        X_train, X_valid, y_train, y_valid = train_valid_split(
            df,
            target_col=TARGET_COL,
            valid_size=valid_size,
            random_state=random_state,
        )

        # 5) 파이프라인 구성
        logger.info("Building pipeline...")
        pipeline = build_pipeline(NUM_FEATURES, CAT_FEATURES)

        # 6) 학습
        logger.info("Training model...")
        pipeline.fit(X_train, y_train)
        logger.info("Training completed!")

        # 7) 예측 및 평가
        logger.info("Evaluating model...")
        y_pred = pipeline.predict(X_valid)

        y_proba = None
        if hasattr(pipeline, "predict_proba"):
            y_proba = pipeline.predict_proba(X_valid)[:, 1]

        metrics = compute_metrics(y_valid, y_pred, y_proba=y_proba)

        # 8) 메트릭 저장
        save_metrics(metrics, metrics_output_path)

        # 9) 모델 저장 (메타데이터 포함)
        save_model_with_metadata(pipeline, metrics, model_output_path)

        return metrics, model_output_path

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


# -----------------------------------------------------------
# 6. CLI 인터페이스 + 실행 가이드
# -----------------------------------------------------------

# -----------------------------------------------------------
# [프로젝트 데이터 파일 안내]
#
# 기본으로 사용하는 학습용 데이터:
#   - raw_dataset.csv
#
# → baseline 및 공통 템플릿 기준으로는 raw_dataset.csv 사용 권장
# → 다른 파일로 학습하려면 실행 시 --data_path 로 경로만 변경!!
#
# -----------------------------------------------------------
# [실행 예시 1] 프로젝트 루트에서 실행
#
#   python model/train_template.py \
#       --data_path data/raw_dataset.csv \
#       --model_output model/model_lk.pkl \
#       --metrics_output model/metrics.json
#
# [실행 예시 2] model 폴더에서 실행
#
#   cd model
#   python train_template.py \
#       --data_path ../data/raw_dataset.csv \
#       --model_output model_lk.pkl \
#       --metrics_output metrics.json
#
# [실행 예시 3] 상세 로그 보기 (DEBUG 레벨)
#
#   python train_template.py --data_path ../data/raw_dataset.csv --log_level DEBUG
#
# ※ 기본값은 model 폴더에서 실행을 기준으로 설정됨
# -----------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="공통 Baseline 학습 템플릿 (Logistic Regression, Final Version)"
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default="../data/raw_dataset.csv",
        help="학습에 사용할 CSV 경로 (예: ../data/raw_dataset.csv 또는 data/raw_dataset.csv)",
    )
    parser.add_argument(
        "--model_output",
        type=str,
        default="model_lk.pkl",
        help="저장할 모델 파일명(.pkl) (예: model_lk.pkl 또는 model/model_lk.pkl)",
    )
    parser.add_argument(
        "--metrics_output",
        type=str,
        default="metrics.json",
        help="저장할 메트릭 파일명(.json) (예: metrics.json 또는 model/metrics.json)",
    )
    parser.add_argument(
        "--valid_size",
        type=float,
        default=0.2,
        help="검증 데이터 비율 (기본: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="train/valid split용 random seed",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 설정 (기본: INFO)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 로그 레벨 설정 (루트 + 모듈 로거 둘 다 반영)
    log_level_name = args.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.getLogger().setLevel(log_level)
    logger.setLevel(log_level)

    logger.info("=" * 60)
    logger.info("Starting training process...")
    logger.info("=" * 60)

    try:
        metrics, model_path = train_and_evaluate(
            data_path=args.data_path,
            model_output_path=args.model_output,
            metrics_output_path=args.metrics_output,
            valid_size=args.valid_size,
            random_state=args.seed,
        )

        # 메트릭 출력
        print_metrics(metrics)
        print(f"Model saved to: {model_path}")
        print(f"Metrics saved to: {args.metrics_output}")
        print("=" * 60)

        logger.info("Training process completed successfully!")

    except Exception as e:
        logger.error(f"Training process failed: {e}")
        raise


if __name__ == "__main__":
    main()
