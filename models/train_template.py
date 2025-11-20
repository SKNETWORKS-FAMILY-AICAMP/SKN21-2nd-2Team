"""
train_template.py (공통 모델 템플릿)
Author: 정세연
Date: 2025-11-20
Description
- 데이터 로딩 · 전처리 · 피처 엔지니어링 · 모델 학습 · 평가 · 저장을 포함한 공통 Baseline 템플릿
"""

import argparse
import os
import json
import datetime
import logging
from typing import List, Dict, Tuple, Any

import joblib
import pandas as pd
import numpy as np

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

# 숫자형 기본 피처
NUM_FEATURES: List[str] = [
    "age",
    "listening_time",
    "songs_played_per_day",
    "skip_rate",
    "ads_listened_per_week",
    "offline_listening",
]

# 범주형 기본 피처
CAT_FEATURES: List[str] = [
    "gender",
    "country",
    "subscription_type",
    "device_type",
]

# 파이프라인 설계 기준 파생 숫자형 피처
ENGINEERED_NUM_FEATURES: List[str] = [
    "engagement_score",
    "songs_per_minute",
    "skip_intensity",
    "ads_pressure",
]

# 파이프라인 설계 기준 파생 범주형 피처
ENGINEERED_CAT_FEATURES: List[str] = [
    "age_group",
    "subscription_type_level",
    "country_grouped",
]

# -----------------------------------------------------------
# 2. 데이터 로딩 + 검증 + 전처리
# -----------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    """CSV 파일 로드 및 필수 컬럼 검증"""
    if not os.path.exists(path):
        logger.error(f"Data file not found: {path}")
        raise FileNotFoundError(f"Data file not found: {path}")

    logger.info(f"Loading data from: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # 필수 컬럼 체크 (기본 feature + target 기준)
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


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    전처리 + Feature Engineering (파이프라인 설계 기반)

    실제 프로젝트에서는 이 로직을 별도 모듈(fe_pipeline.py 등)로 분리할 수 있습니다.
    여기서는 구조와 흐름을 명확히 하기 위해 간단한 구현만 포함합니다

    Steps:
    1) 사용하지 않는 컬럼 제거 (ID/개인정보 등)
    2) 결측치 처리 (주요 수치형 컬럼 median 대체)
    3) 이상치 처리 / 캡핑 (skip_rate, ads_listened_per_week 등)
    4) 수치형 파생 피처 생성 (engagement_score, songs_per_minute, ...)
    5) 범주형 파생 피처 생성 (age_group, subscription_type_level, country_grouped)
    """
    logger.info("Preprocessing data (v2 pipeline structure)...")
    df = df.copy()

    # 1) 사용하지 않는 컬럼 제거
    drop_candidates = ["user_id", "Name", "Password"]
    drop_cols = [c for c in drop_candidates if c in df.columns]
    if drop_cols:
        logger.info(f"Dropping unused columns: {drop_cols}")
        df = df.drop(columns=drop_cols)

    # 2) 결측치 처리 (주요 수치형)
    numeric_cols_to_impute = [
        "age", "listening_time", "songs_played_per_day",
        "skip_rate", "ads_listened_per_week", "offline_listening"
    ]
    for col in numeric_cols_to_impute:
        if col in df.columns and df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(f"Imputed {col} with median={median_val:.4f}")

    # 3) 이상치 처리 / 캡핑
    # 3-1) skip_rate 상한값 캡핑 (예: 1.5)
    if "skip_rate" in df.columns:
        upper = 1.5
        before_max = df["skip_rate"].max()
        df["skip_rate"] = df["skip_rate"].clip(upper=upper)
        logger.info(f"Capped skip_rate at {upper} (before max={before_max:.4f})")

    # 3-2) ads_listened_per_week 윈저라이징 (99 percentile 기준)
    if "ads_listened_per_week" in df.columns:
        q99 = df["ads_listened_per_week"].quantile(0.99)
        before_max = df["ads_listened_per_week"].max()
        df["ads_listened_per_week"] = df["ads_listened_per_week"].clip(upper=q99)
        logger.info(
            f"Capped ads_listened_per_week at 99th={q99:.2f} (before max={before_max:.2f})"
        )

    # 4) 수치형 파생 피처
    # 0 나누기 방지를 위한 안전한 listening_time (한 번만 계산)
    if "listening_time" in df.columns:
        lt_safe = df["listening_time"].replace(0, np.nan)
        
        if "songs_played_per_day" in df.columns:
            # 4-1) engagement_score = listening_time * songs_played_per_day
            df["engagement_score"] = df["listening_time"] * df["songs_played_per_day"]
            logger.debug("Created engagement_score")
            
            # 4-2) songs_per_minute = songs_played_per_day / listening_time
            df["songs_per_minute"] = (df["songs_played_per_day"] / lt_safe).fillna(0.0)
            logger.debug("Created songs_per_minute")
            
            # 4-3) skip_intensity = skip_rate * songs_played_per_day
            if "skip_rate" in df.columns:
                df["skip_intensity"] = df["skip_rate"] * df["songs_played_per_day"]
                logger.debug("Created skip_intensity")
        
        # 4-4) ads_pressure = ads_listened_per_week / listening_time
        if "ads_listened_per_week" in df.columns:
            df["ads_pressure"] = (df["ads_listened_per_week"] / lt_safe).fillna(0.0)
            logger.debug("Created ads_pressure")

    # 5) 범주형 파생 피처
    # 5-1) age_group (단순 구간화 예시)
    if "age" in df.columns:
        bins = [0, 24, 34, 44, 200]
        labels = ["young", "adult", "middle", "senior"]
        df["age_group"] = pd.cut(
            df["age"], 
            bins=bins, 
            labels=labels, 
            right=True, 
            include_lowest=True
        )
        # NaN 처리 (age가 결측이었던 경우)
        if df["age_group"].isnull().any():
            df["age_group"] = df["age_group"].cat.add_categories("Unknown").fillna("Unknown")
        logger.debug("Created age_group")

    # 5-2) subscription_type_level (위험도 매핑 예시)
    if "subscription_type" in df.columns:
        level_map = {
            "Free": 0,
            "Student": 1,
            "Premium": 2,
            "Family": 3,
        }
        # 매핑되지 않는 값은 -1 (Unknown)
        df["subscription_type_level"] = (
            df["subscription_type"].map(level_map).fillna(-1).astype(int)
        )
        logger.debug("Created subscription_type_level")

    # 5-3) country_grouped (Top-N + Other)
    if "country" in df.columns:
        top_countries = df["country"].value_counts().head(5).index
        df["country_grouped"] = df["country"].where(
            df["country"].isin(top_countries), "Other"
        )
        logger.debug("Created country_grouped")

    # 파생 피처 생성 확인 로그
    created_features = [
        f for f in ENGINEERED_NUM_FEATURES + ENGINEERED_CAT_FEATURES 
        if f in df.columns
    ]
    logger.info(f"Created {len(created_features)} engineered features: {created_features}")
    
    # 예상했던 피처가 생성되지 않았다면 경고
    expected_features = set(ENGINEERED_NUM_FEATURES + ENGINEERED_CAT_FEATURES)
    missing_features = expected_features - set(created_features)
    if missing_features:
        logger.warning(f"Expected features not created: {missing_features}")

    return df


def train_valid_split(
    df: pd.DataFrame,
    target_col: str = TARGET_COL,
    valid_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """학습 / 검증 데이터 분리"""
    # valid_size sanity check (0과 0.5 사이 권장)
    if not 0.0 < valid_size < 0.5:
        raise ValueError(f"valid_size는 0과 0.5 사이로 설정해 주세요. 현재 값: {valid_size}")

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
        shuffle=True,
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
    다른 모델로 교체 시 이 함수만 수정하면 됩니당
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
        clean_metrics: Dict[str, Any] = {}
        for k, v in metrics.items():
            # 숫자형인 경우만 float/NaN 처리
            if isinstance(v, (int, float)):
                if isinstance(v, float) and pd.isna(v):
                    clean_metrics[k] = None
                else:
                    clean_metrics[k] = float(v)
            else:
                # 숫자가 아니면 원래 값 그대로 저장
                clean_metrics[k] = v

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
    numeric_features: List[str],
    categorical_features: List[str],
):
    """
    모델과 메타데이터를 함께 저장.

    model_output_path(.pkl)에는 dict가 저장됩니다.
    {
        'pipeline': sklearn Pipeline 객체,
        'metrics': 학습 시점의 성능 메트릭,
        'timestamp': 저장 시각(ISO 문자열),
        'features': {
            'numeric': 사용된 숫자형 피처 목록,
            'categorical': 사용된 범주형 피처 목록,
        },
        'target_col': 타깃 컬럼명,
    }
    
    로드 예시:
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
            "numeric": numeric_features,
            "categorical": categorical_features,
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
    - 전처리 + Feature Engineering (preprocess_data)
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

        # 2) 기본 검증
        df = validate_data(df)

        # 3) 전처리 + Feature Engineering
        df = preprocess_data(df)

        # 4) ID 컬럼이 남아 있다면 한 번 더 제거
        drop_cols = [col for col in ID_COLS if col in df.columns]
        if drop_cols:
            logger.info(f"Dropping ID columns: {drop_cols}")
            df = df.drop(columns=drop_cols)

        # 5) 최종적으로 사용할 feature 목록 (원본 + 파생 중 실제 존재하는 컬럼만)
        numeric_features = [
            c for c in NUM_FEATURES + ENGINEERED_NUM_FEATURES 
            if c in df.columns
        ]
        categorical_features = [
            c for c in CAT_FEATURES + ENGINEERED_CAT_FEATURES 
            if c in df.columns
        ]

        logger.info(f"Numeric features used ({len(numeric_features)}): {numeric_features}")
        logger.info(f"Categorical features used ({len(categorical_features)}): {categorical_features}")

        # 6) train / valid split
        X_train, X_valid, y_train, y_valid = train_valid_split(
            df,
            target_col=TARGET_COL,
            valid_size=valid_size,
            random_state=random_state,
        )

        # 7) 파이프라인 구성
        logger.info("Building pipeline...")
        pipeline = build_pipeline(numeric_features, categorical_features)

        # 8) 학습
        logger.info("Training model...")
        pipeline.fit(X_train, y_train)
        logger.info("Training completed!")

        # 9) 예측 및 평가
        logger.info("Evaluating model...")
        y_pred = pipeline.predict(X_valid)

        # 확률 예측 가능하면 proba 출력
        y_proba = None
        try:
            if hasattr(pipeline, "predict_proba"):
                y_proba = pipeline.predict_proba(X_valid)[:, 1]
        except Exception as e:
            logger.warning(f"Could not get prediction probabilities: {e}")

        metrics = compute_metrics(y_valid, y_pred, y_proba=y_proba)

        # 10) 성능 출력
        print_metrics(metrics)

        # 11) 메트릭 저장
        save_metrics(metrics, metrics_output_path)

        # 12) 모델 + 메타데이터 저장
        save_model_with_metadata(
            pipeline,
            metrics,
            model_output_path,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
        )

        logger.info("Training process completed successfully!")
        return metrics, model_output_path

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

# -----------------------------------------------------------
# 6. CLI 인터페이스 + 실행 가이드
# -----------------------------------------------------------

# --------------------------------------------------------------
# [실행 예시 1] 기본 실행
#
#   python train_template.py --data_path ../data/raw_dataset.csv
#
# [실행 예시 2] 출력 경로 지정
#
#   python train_template.py \
#       --data_path ../data/raw_dataset.csv \
#       --model_output_path models/model_v2.pkl \
#       --metrics_output_path results/metrics_v2.json
#
# [실행 예시 3] validation 비율 조정
#
#   python train_template.py \
#       --data_path ../data/raw_dataset.csv \
#       --valid_size 0.25 \
#       --random_state 123
#
# [실행 예시 4] 상세 로그 보기
#
#   python train_template.py \
#       --data_path ../data/raw_dataset.csv \
#       --log_level DEBUG
# --------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="공통 Baseline 학습 템플릿 (v2.0 with Feature Engineering)"
    )
    parser.add_argument(
        "--data_path",
        type=str,
        required=True,
        help="학습에 사용할 CSV 데이터 경로",
    )
    parser.add_argument(
        "--model_output_path",
        type=str,
        default="model_lk.pkl",
        help="학습된 모델 저장 경로 (.pkl)",
    )
    parser.add_argument(
        "--metrics_output_path",
        type=str,
        default="metrics.json",
        help="평가 메트릭 저장 파일명",
    )
    parser.add_argument(
        "--valid_size",
        type=float,
        default=0.2,
        help="검증 데이터 비율 (0~1 사이, 기본: 0.2)",
    )
    parser.add_argument(
        "--random_state",
        type=int,
        default=42,
        help="랜덤시드 (기본: 42)",
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
    logger.info("Starting training process (v2.0 with Feature Engineering)...")
    logger.info("=" * 60)

    try:
        metrics, model_path = train_and_evaluate(
            data_path=args.data_path,
            model_output_path=args.model_output_path,
            metrics_output_path=args.metrics_output_path,
            valid_size=args.valid_size,
            random_state=args.random_state,
        )

        print(f"\nModel saved to: {model_path}")
        print(f"Metrics saved to: {args.metrics_output_path}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Training process failed: {e}")
        raise


if __name__ == "__main__":
    main()