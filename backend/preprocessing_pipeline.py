"""
preprocessing.py

Spotify Churn Prediction - Sklearn Pipeline Version
---------------------------------------------------
이 모듈은 `notebooks/pipeline.ipynb`에서 구현한 전처리 방식을
백엔드에서 재사용할 수 있도록 모듈화한 버전입니다.

주요 단계:
- 결측치 처리
- IQR 기반 이상치 처리
- 수치/범주형 분리 후 ColumnTransformer + OneHotEncoder 파이프라인 구성
- Train/Test Split
- (선택) 전처리된 결과 및 preprocessor 객체 저장/로딩
"""

from __future__ import annotations

import os
import pickle
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# =====================================================
# 1. 데이터 로드
# =====================================================
def load_data(path: str) -> pd.DataFrame:
    """CSV 파일에서 데이터를 불러옵니다."""
    return pd.read_csv(path)


# =====================================================
# 2. 결측치 처리 (노트북 로직 기반)
# =====================================================
def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    결측치 처리 규칙 (notebooks/pipeline.ipynb 기준):
    - listening_time, songs_played_per_day → 중앙값으로 대체
    - payment_failure_count, app_crash_count_30d → 0으로 대체
    - customer_support_contact, promotional_email_click → False로 대체
    """
    df = df.copy()

    # 2-1) 핵심 활동 지표 → median fill
    for col in ["listening_time", "songs_played_per_day"]:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    # 2-2) 문제 관련 지표 → 0
    for col in ["payment_failure_count", "app_crash_count_30d"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 2-3) 이벤트성 boolean → False
    for col in ["customer_support_contact", "promotional_email_click"]:
        if col in df.columns:
            df[col] = df[col].fillna(False)

    return df


# =====================================================
# 3. 이상치 처리 (IQR 기반 Clip, 노트북 로직 기반)
# =====================================================
def handle_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """
    IQR 방식(사분위 범위)을 사용해 이상치를 경계값으로 Clip합니다.
    - 대상: 숫자형 컬럼
    - 제외: user_id, is_churned
    """
    df = df.copy()

    num_cols = [
        col
        for col in df.columns
        if df[col].dtype in ["int64", "float64"]
        and col not in ["user_id", "is_churned"]
    ]

    for col in num_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df[col] = df[col].clip(lower, upper)

    return df


# =====================================================
# 4. ColumnTransformer 기반 전처리기 구성
# =====================================================
def build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    """
    notebooks/pipeline.ipynb의 전처리 구성을 그대로 옮긴 함수.

    - numerical_features: 숫자형 컬럼 (is_churned, user_id 제외)
    - categorical_features: gender, device_type, subscription_type, country
    """
    numerical_features = [
        col
        for col in df.columns
        if df[col].dtype in ["int64", "float64"]
        and col not in ["is_churned", "user_id"]
    ]

    base_categorical = ["gender", "device_type", "subscription_type", "country"]
    categorical_features = [c for c in base_categorical if c in df.columns]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numerical_features),
            ("cat_ohe", categorical_pipeline, categorical_features),
        ]
    )

    return preprocessor


# =====================================================
# 5. 전처리 + Train/Test Split (주요 진입점 함수)
# =====================================================
def preprocess_and_split(
    path: str = "data/enhanced_data_not_clean_FE_delete.csv",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, pd.Series, pd.Series, ColumnTransformer]:
    """
    notebooks/pipeline.ipynb의 흐름을 그대로 따르는 메인 함수.

    Steps:
    1. CSV 로드
    2. 결측치 처리
    3. IQR 기반 이상치 처리
    4. ColumnTransformer 전처리기 구성
    5. Train/Test Split
    6. 전처리 fit/transform

    Returns:
        X_train_processed, X_test_processed, y_train, y_test, preprocessor
    """
    # 1) 데이터 로드
    print(f"[1/6] Loading data from: {path}")
    df = load_data(path)
    print(f"      Original shape: {df.shape}")

    # 2) 결측치 처리
    print("[2/6] Handling missing values...")
    df = clean_missing_values(df)

    # 3) 이상치 처리
    print("[3/6] Handling outliers (IQR clip)...")
    df = handle_outliers_iqr(df)

    # 4) 전처리기 구성
    print("[4/6] Building ColumnTransformer preprocessor...")
    preprocessor = build_preprocessor(df)

    # 5) Train/Test Split
    print("[5/6] Train/Test split...")
    X = df.drop(columns=["is_churned"])
    y = df["is_churned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    # 6) 전처리 적용
    print("[6/6] Fitting preprocessor and transforming data...")
    X_train_processed = preprocessor.fit_transform(X_train, y_train)
    X_test_processed = preprocessor.transform(X_test)

    print("\n[SUCCESS] Preprocessing (sklearn pipeline) completed!")
    print(f"          X_train_processed: {X_train_processed.shape}")
    print(f"          X_test_processed : {X_test_processed.shape}")
    print(f"          y_train          : {y_train.shape}")
    print(f"          y_test           : {y_test.shape}")

    return X_train_processed, X_test_processed, y_train, y_test, preprocessor


# =====================================================
# 6. 전처리 결과/객체 저장 & 로딩 (협업용 유틸)
# =====================================================
def save_processed_data(
    X_train,
    X_test,
    y_train,
    y_test,
    preprocessor: ColumnTransformer,
    save_dir: str = "data",
) -> None:
    """
    notebooks/pipeline.ipynb의 save 로직을 백엔드 유틸로 옮긴 버전.
    """
    os.makedirs(save_dir, exist_ok=True)

    with open(os.path.join(save_dir, "X_train_processed.pkl"), "wb") as f:
        pickle.dump(X_train, f)

    with open(os.path.join(save_dir, "X_test_processed.pkl"), "wb") as f:
        pickle.dump(X_test, f)

    with open(os.path.join(save_dir, "y_train.pkl"), "wb") as f:
        pickle.dump(y_train, f)

    with open(os.path.join(save_dir, "y_test.pkl"), "wb") as f:
        pickle.dump(y_test, f)

    with open(os.path.join(save_dir, "preprocessor.pkl"), "wb") as f:
        pickle.dump(preprocessor, f)

    print(f"✅ 전처리 데이터 및 preprocessor 저장 완료: {save_dir}")


def load_processed_data(
    save_dir: str = "data",
) -> Tuple[np.ndarray, np.ndarray, pd.Series, pd.Series, ColumnTransformer]:
    """
    notebooks/pipeline.ipynb의 load 로직을 백엔드 유틸로 옮긴 버전.
    """
    with open(os.path.join(save_dir, "X_train_processed.pkl"), "rb") as f:
        X_train = pickle.load(f)

    with open(os.path.join(save_dir, "X_test_processed.pkl"), "rb") as f:
        X_test = pickle.load(f)

    with open(os.path.join(save_dir, "y_train.pkl"), "rb") as f:
        y_train = pickle.load(f)

    with open(os.path.join(save_dir, "y_test.pkl"), "rb") as f:
        y_test = pickle.load(f)

    with open(os.path.join(save_dir, "preprocessor.pkl"), "rb") as f:
        preprocessor = pickle.load(f)

    print(f"✅ 전처리 데이터 및 preprocessor 로드 완료: {save_dir}")
    return X_train, X_test, y_train, y_test, preprocessor


__all__ = [
    "load_data",
    "clean_missing_values",
    "handle_outliers_iqr",
    "build_preprocessor",
    "preprocess_and_split",
    "save_processed_data",
    "load_processed_data",
]


if __name__ == "__main__":
    X_train_p, X_test_p, y_train_p, y_test_p, preproc = preprocess_and_split()
    save_processed_data(X_train_p, X_test_p, y_train_p, y_test_p, preproc)
