"""
preprocessing.py
Spotify Churn Prediction - Data Preprocessing Pipeline
Author: 윤경은
Team: SKN21 2ND 2TEAM
Date: 2025-11-21

Description:
- This module implements the full preprocessing pipeline for the Spotify churn dataset.
- Includes: missing-value handling, outlier processing, encoding, scaling, and train/test split.
- Based on EDA results from notebooks/eda_add.ipynb
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# =====================================================
# 1. 데이터 로드
# =====================================================
def load_data(path: str):
    """CSV 파일에서 데이터를 불러옵니당"""
    return pd.read_csv(path)


# =====================================================
# 2. 사용하지 않는 칼럼 삭제
# =====================================================
def drop_unused_columns(df):
    """
    모델 학습에 사용하지 않는 컬럼을 제거합니다.
    - user_id: 식별자이므로 제거
    - 파생 변수(FE): engagement_score, songs_per_minute 등 제거
    """
    df = df.copy()
    
    # Drop user_id (identifier)
    if "user_id" in df.columns:
        df = df.drop(columns=["user_id"])
    
    # Drop FE columns (제외된 파생 변수들)
    fe_cols_to_drop = [
        "engagement_score",
        "songs_per_minute", 
        "skip_intensity",
        "skip_rate_cap",
        "ads_pressure"
    ]
    cols_to_drop = [col for col in fe_cols_to_drop if col in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    return df


# =====================================================
# 3. 결측치 처리
# =====================================================
def clean_missing_values(df):
    """
    결측치 처리 규칙에 따라 값을 채웁니다.
    - listening_time, songs_played_per_day → 중앙값으로 대체
    - payment_failure_count, app_crash_count_30d → 0으로 대체
    - customer_support_contact, promotional_email_click → False 또는 0으로 대체
    """
    df = df.copy()

    # 3-1) 핵심 활동 지표 → median fill
    for col in ["listening_time", "songs_played_per_day"]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # 3-2) 문제 관련 지표 → 0
    for col in ["payment_failure_count", "app_crash_count_30d"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 3-4) 이벤트성 boolean → False
    for col in ["customer_support_contact", "promotional_email_click"]:
        if col in df.columns:
            # int 타입인 경우 0으로, bool 타입인 경우 False로
            if df[col].dtype in [int, float]:
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(False)

    return df


# =====================================================
# 4. 이상치 처리 (IQR 기반 Clip)
# =====================================================
def handle_outliers(df):
    """
    IQR 방식(사분위 범위)을 사용해 이상치를 경계값으로 Clip합니다.
    제외: user_id, is_churned
    """
    df = df.copy()

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    numeric_cols = [c for c in numeric_cols if c not in ["user_id", "is_churned"]]

    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df[col] = df[col].clip(lower, upper)

    return df


# =====================================================
# 5. 범주형 변수 인코딩 (One-hot)
# =====================================================
def encode_categorical(df):
    """
    범주형 컬럼(gender, country 등)을 One-hot 인코딩합니다.
    이미 0/1 구조인 컬럼(offline_listening 등)은 변환하지 않습니다.
    """
    df = df.copy()

    # One-hot encode these categorical columns
    categorical_cols = ["gender", "country", "subscription_type", "device_type"]
    cols_to_encode = [col for col in categorical_cols if col in df.columns]
    
    if cols_to_encode:
        df = pd.get_dummies(
            df,
            columns=cols_to_encode,
            drop_first=True
        )

    return df


# =====================================================
# 6. 수치형 변수 스케일링링
# =====================================================
def scale_numeric(df, scaler=None, fit=True):
    """
    표준화(StandardScaler)를 적용해 수치형 컬럼을 스케일링합니다.
    
    Args:
        df: 스케일링할 데이터프레임
        scaler: 기존에 학습된 scaler (테스트 데이터에 사용)
        fit: True면 fit + transform / False면 transform만 수행
    
    Returns:
        df: Scaled DataFrame
        scaler: Fitted StandardScaler object
    """
    df = df.copy()

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    numeric_cols = [c for c in numeric_cols if c not in ["user_id", "is_churned"]]

    if scaler is None:
        scaler = StandardScaler()
    
    if fit:
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    else:
        df[numeric_cols] = scaler.transform(df[numeric_cols])

    return df, scaler


# =====================================================
# 7. Train/Test Split
# =====================================================
def split_data(df, test_size=0.2, random_state=42):
    """
    Split dataset into train and test sets.
    
    Args:
        df: Preprocessed DataFrame
        test_size: Proportion of test set (테스트 데이터 비율)
        random_state: Random seed for reproducibility(재현성을 위한 랜덤 시드)
    
    Returns:
        X_train, X_test, y_train, y_test
    """
    X = df.drop("is_churned", axis=1)
    y = df["is_churned"]

    return train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )


# =====================================================
# 8.  전체 전처리 파이프라인 실행
# =====================================================
def preprocess_pipeline(
    path="data/enhanced_data_not_clean_FE_delete.csv",
    save_output=True,
    output_dir="data/processed",
    test_size=0.2,
    random_state=42
):
    """
    Complete preprocessing pipeline.
    
    Steps:
    1. 데이터 로드
    2. 사용하지 않는 컬럼 제거 (user_id, FE columns)
    3. 결측치 처리
    4. 이상치 처리 (IQR clip)
    5. 범주형 변수 인코딩 (one-hot)
    6. 수치형 변수 스케일링
    7. Train/Test 분리
    
    Args:
        path: CSV 파일 경로입력력
        save_output: 처리된 데이터를 파일로 저장할지 여부
        output_dir: 처리된 데이터를 저장할 디렉토리
        test_size: Proportion of test set(테스트 데이터 비율)
        random_state: Random seed for reproducibility(재현성을 위한 랜덤 시드)
    
    Returns:
        X_train, X_test, y_train, y_test, scaler
    """
    # 1. Load data
    print(f"[1/7] Loading data from: {path}")
    df = load_data(path)
    print(f"      Original shape: {df.shape}")
    
    # 2. Handle missing values (먼저 결측치 처리)
    print("[2/7] Handling missing values...")
    df = clean_missing_values(df)
    # clean_missing_values 내부에서 engagement_score, skip_intensity 재계산 수행
    
    # 3. Drop unused columns (재계산 후 제거)
    print("[3/7] Dropping unused columns...")
    df = drop_unused_columns(df)
    
    # 4. Handle outliers
    print("[4/7] Handling outliers (IQR clip)...")
    df = handle_outliers(df)
    
    # 5. Encode categorical variables
    print("[5/7] Encoding categorical variables (one-hot)...")
    df = encode_categorical(df)
    
    # 6. Scale numeric variables
    print("[6/7] Scaling numeric variables...")
    df, scaler = scale_numeric(df, fit=True)
    
    # 7. Split data
    print("[7/7] Splitting into train/test sets...")
    X_train, X_test, y_train, y_test = split_data(
        df, test_size=test_size, random_state=random_state
    )
    
    # 8. Save output
    if save_output:
        os.makedirs(output_dir, exist_ok=True)
        
        X_train.to_pickle(f"{output_dir}/X_train.pkl")
        X_test.to_pickle(f"{output_dir}/X_test.pkl")
        y_train.to_pickle(f"{output_dir}/y_train.pkl")
        y_test.to_pickle(f"{output_dir}/y_test.pkl")
        
        # Save scaler for later use
        with open(f"{output_dir}/scaler.pkl", "wb") as f:
            pickle.dump(scaler, f)
        
        print(f"      Files saved to: {output_dir}/")
    
    print("\n[SUCCESS] Preprocessing completed!")
    print(f"          Shapes -> X_train: {X_train.shape}, X_test: {X_test.shape}")
    print(f"                      y_train: {y_train.shape}, y_test: {y_test.shape}")
    
    return X_train, X_test, y_train, y_test, scaler


if __name__ == "__main__":
    preprocess_pipeline()
