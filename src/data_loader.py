"""
데이터 로드 및 피처/타깃 분리를 담당하는 모듈.

⚠ 최종 전처리 파이프라인 함수(예: preprocess(df) 또는 sklearn Pipeline)는
   아직 다른 팀원으로부터 전달받지 못했으므로,
   아래에 "최종 전처리 파이프라인 훅" 위치를 주석으로 표시해 둔다.
"""

from typing import Tuple

import pandas as pd

from .config import (
    DATA_PATH,
    TARGET_COL,
    ID_COLS,
    NUM_FEATURE_COLS,
    USE_EXTERNAL_PIPELINE,
    PIPELINE_MODULE,
    PIPELINE_FUNC_NAME,
)


def load_raw_dataframe() -> pd.DataFrame:
    """
    CSV에서 원본 DataFrame을 그대로 로드한다.

    - 여기서는 파일 경로/인코딩 등만 책임진다.
    - 실제 전처리/스케일링/인코딩 등은 추후 '최종 전처리 파이프라인'이 담당.
    """
    df = pd.read_csv(DATA_PATH)
    return df


def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    학습/평가용 X, y를 반환한다.

    1. CSV 로드
    2. (TODO) 최종 전처리 파이프라인 적용 위치
    3. ID, 타깃 컬럼 분리
    """
    df = load_raw_dataframe()

    # ------------------------------------------------------------------
    # 🔌 [최종 전처리 파이프라인 훅 (HOOK)]
    #
    # 예시: backend/pipeline.ipynb 에서 정의된 것처럼
    #   def run_preprocessing(df, scale_type=\"standard\", feature_eng=True): ...
    # 형태의 함수를 외부에서 제공받는 경우,
    # config.USE_EXTERNAL_PIPELINE 을 True로 바꾸고
    # PIPELINE_MODULE / PIPELINE_FUNC_NAME 을 해당 함수에 맞게 설정한 뒤
    # 아래 블록이 실행되도록 하면 된다.
    # ------------------------------------------------------------------
    if USE_EXTERNAL_PIPELINE:
        import importlib

        module = importlib.import_module(PIPELINE_MODULE)
        preprocess_func = getattr(module, PIPELINE_FUNC_NAME)
        df = preprocess_func(df)

    # 타깃 분리
    y = df[TARGET_COL]

    # ID 컬럼 및 타깃 컬럼을 제외한 나머지를 피처로 사용하되,
    # NUM_FEATURE_COLS가 정의되어 있으면 그 목록만 사용한다.
    if NUM_FEATURE_COLS:
        missing = sorted(set(NUM_FEATURE_COLS) - set(df.columns))
        if missing:
            raise ValueError(f"NUM_FEATURE_COLS에 정의된 컬럼이 데이터에 없습니다: {missing}")
        X = df[NUM_FEATURE_COLS]
    else:
        drop_cols = list(ID_COLS) + [TARGET_COL]
        X = df.drop(columns=drop_cols)

    return X, y


__all__ = ["load_raw_dataframe", "load_data"]


