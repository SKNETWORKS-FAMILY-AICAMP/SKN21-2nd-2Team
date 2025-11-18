"""
결측치 및 이상치 삽입
신지용
"""

import numpy as np
import pandas as pd

np.random.seed(42) 

df = pd.read_csv("data/raw_dataset.csv")

# ---------------------------------------------------
# 결측치 3%
df.loc[df.sample(frac=0.03).index, 'listening_time'] = np.nan
df.loc[df.sample(frac=0.03).index, 'songs_played_per_day'] = np.nan

# ---------------------------------------------------
# 이상치(값도 랜덤)
# skip_rate → 2% (정상 범위 벗어난 1~5 사이 랜덤)
idx_out_skip = df.sample(frac=0.02).index
df.loc[idx_out_skip, 'skip_rate'] = np.random.uniform(1, 5, size=len(idx_out_skip))

# age → 1% (120~200 사이 랜덤 나이)
idx_out_age = df.sample(frac=0.01).index
df.loc[idx_out_age, 'age'] = np.random.randint(120, 200, size=len(idx_out_age))

# 저장
df.to_csv("data/raw_data.csv", index=False)


"""
결측치 및 이상치 확인
"""

# import pandas as pd

# # data/raw_dataset_modified.csv 파일 읽기
# df_modified = pd.read_csv("data/raw_data.csv")

# # 각 컬럼별 결측치 개수 출력
# print("각 컬럼별 결측치 개수:")
# print(df_modified.isnull().sum())

# # 전체 결측치 개수 출력
# print("전체 결측치 개수:", df_modified.isnull().sum().sum())
# # 각 컬럼별 이상치 개수 출력
# print("\n각 컬럼별 이상치 개수:")

# # 이상치 기준 정의
# outlier_conditions = {
#     'age': (df_modified['age'] < 0) | (df_modified['age'] > 100),
#     'skip_rate': (df_modified['skip_rate'] < 0) | (df_modified['skip_rate'] > 1)
# }

# for col, cond in outlier_conditions.items():
#     print(f"{col}: {cond.sum()}")

# # 전체 이상치 개수 출력
# total_outliers = sum(cond.sum() for cond in outlier_conditions.values())
# print("전체 이상치 개수:", total_outliers)
