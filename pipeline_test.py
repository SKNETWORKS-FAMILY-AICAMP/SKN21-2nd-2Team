"""
pipteline_test.py
Auth: 박수빈
Date: 2025-11-20
Description
- 데이터 로드
- 역할별 컬럼 정의
- 결측치 처리
- 파생변수 생성
- 이상치 처리
- 수치형 스케일링
- 범주형 인코딩 (OneHotEncoder)
- ColumnTransformer 기반 전체 파이프라인 생성
"""

import pandas as pd
import numpy as np

# 모델링용 전처리 도구
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


# =========================================================
# 1) 데이터 로드 함수
# =========================================================
def load_data(path: str) -> pd.DataFrame:
    """
    CSV 데이터를 로드하는 함수
    - path: csv 파일 경로
    """
    df = pd.read_csv(path)
    return df


# =========================================================
# 2) 컬럼 역할 정의
# =========================================================
def define_columns(df: pd.DataFrame):
    """
    데이터셋의 역할별 컬럼을 정의하는 함수
    반환:
        id_cols, cat_cols, num_cols, target_col
    """
    id_cols = ["user_id"]
    cat_cols = ["gender", "country", "subscription_type", "device_type"]
    num_cols = [
        "age",
        "listening_time",
        "songs_played_per_day",
        "skip_rate",
        "ads_listened_per_week",
        "offline_listening",
    ]
    target_col = "is_churned"

    return id_cols, cat_cols, num_cols, target_col


# =========================================================
# 3) 결측치 처리 + 기본 클리닝
# =========================================================
def clean_missing_values(df: pd.DataFrame, num_cols: list) -> pd.DataFrame:
    """
    수치형 컬럼의 결측치를 중앙값으로 대체합니다.
    범주형 컬럼은 결측치가 거의 없으므로 별도 처리하지 않습니다.
    """
    df = df.copy()
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df[c].fillna(df[c].median(), inplace=True)

    return df


# =========================================================
# 4) 이상치 처리 + 파생 변수 생성
# =========================================================
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    파생 변수 생성 및 이상치 처리
    - skip_rate 이상치 cap
    - listening_time binning
    - engagement_score 생성
    """
    df = df.copy()

    # skip_rate cap (0~1)
    df["skip_rate_capped"] = df["skip_rate"].clip(0, 1)

    # listening_time 구간화
    try:
        df["listening_time_bin"] = pd.qcut(
            df["listening_time"], q=4, labels=["very_low", "low", "medium", "high"]
        )
    except:
        # unique 값이 적어서 qcut이 불가능할 경우 fallback
        bins = [-1, 20, 60, 120, df["listening_time"].max()]
        df["listening_time_bin"] = pd.cut(
            df["listening_time"], bins=bins, labels=["very_low", "low", "medium", "high"]
        )

    # engagement_score = 청취시간 + 재생곡수 (정규화)
    lt_norm = df["listening_time"] / (df["listening_time"].max() + 1)
    sp_norm = df["songs_played_per_day"] / (df["songs_played_per_day"].max() + 1)

    df["engagement_score"] = lt_norm + sp_norm

    return df


# =========================================================
# 5) ColumnTransformer 구성
# =========================================================
def build_preprocessing_pipeline(cat_cols: list, num_cols: list):
    """
    전처리 파이프라인을 생성하고 ColumnTransformer로 묶습니다.
    - 범주형: OneHotEncoder
    - 수치형: StandardScaler
    """

    # 범주형 인코더
    cat_transformer = Pipeline(
        steps=[
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    # 수치형 스케일링
    num_transformer = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
        ]
    )

    # ColumnTransformer 결합
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", cat_transformer, cat_cols),
            ("num", num_transformer, num_cols),
        ],
        remainder="drop",   # id_cols 제거
    )

    return preprocessor


# =========================================================
# 6) 전체 데이터 처리 + Train/Test 분리
# =========================================================
def prepare_dataset(path: str):
    """
    전체 파이프라인을 수행하여 전처리와 train/test split까지 마친 후 반환합니다.
    반환:
        X_train, X_test, y_train, y_test, preprocessor
    """
    df = load_data(path)
    id_cols, cat_cols, num_cols, target_col = define_columns(df)

    # 결측치 처리
    df = clean_missing_values(df, num_cols)

    # 파생 변수 추가
    df = feature_engineering(df)

    # 최종 모델 입력 컬럼 정의 (id 제외)
    feature_cols = cat_cols + num_cols + [
        "skip_rate_capped",
        "listening_time_bin",
        "engagement_score",
    ]

    # 타깃 분리
    X = df[feature_cols]
    y = df[target_col]

    # train/test 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 전처리 파이프라인 구성
    preprocessor = build_preprocessing_pipeline(
        cat_cols=cat_cols + ["listening_time_bin"],   # listening_time_bin도 범주형
        num_cols=num_cols + ["skip_rate_capped", "engagement_score"]
    )

    return X_train, X_test, y_train, y_test, preprocessor


# =========================================================
# 모듈 테스트
# =========================================================
if __name__ == "__main__":
    path = "data/raw_data.csv"

    X_train, X_test, y_train, y_test, preprocessor = prepare_dataset(path)

    print("전처리 파이프라인 준비 완료")
    print("X_train shape:", X_train.shape)
    print("X_test shape:", X_test.shape)
