<<<<<<< HEAD
# import numpy as np
# import pandas as pd

# np.random.seed(42)  # 동일한 결과 유지

# df = pd.read_csv("data/raw_dataset.csv")

# # ---------------------------------------------------
# # 🟡 [결측치 삽입 - 각 3%]
# # listening_time → 3%
# df.loc[df.sample(frac=0.03).index, 'listening_time'] = np.nan

# # songs_played_per_day → 3%
# df.loc[df.sample(frac=0.03).index, 'songs_played_per_day'] = np.nan
# # ---------------------------------------------------

# # ---------------------------------------------------
# # 🔴 [이상치 삽입]
# # skip_rate → 2% (0~1 범위 벗어난 값)
# df.loc[df.sample(frac=0.02).index, 'skip_rate'] = 2.5

# # age → 1% (비현실적인 값)
# df.loc[df.sample(frac=0.01).index, 'age'] = 150
# # ---------------------------------------------------

# # 저장
# df.to_csv("data/raw_dataset_modified_2.csv", index=False)

import pandas as pd

# data/raw_dataset_modified.csv 파일 읽기
df_modified = pd.read_csv("data/raw_dataset_modified_2.csv")

# 각 컬럼별 결측치 개수 출력
print("각 컬럼별 결측치 개수:")
print(df_modified.isnull().sum())

# 전체 결측치 개수 출력
print("전체 결측치 개수:", df_modified.isnull().sum().sum())
# 각 컬럼별 이상치 개수 출력
print("\n각 컬럼별 이상치 개수:")

# 이상치 기준 정의
outlier_conditions = {
    'age': (df_modified['age'] < 0) | (df_modified['age'] > 100),
    'skip_rate': (df_modified['skip_rate'] < 0) | (df_modified['skip_rate'] > 1)
}

for col, cond in outlier_conditions.items():
    print(f"{col}: {cond.sum()}")

# 전체 이상치 개수 출력
total_outliers = sum(cond.sum() for cond in outlier_conditions.values())
print("전체 이상치 개수:", total_outliers)
=======
"""
app.py (Spotify 이용자 이탈 분석)
Auth: 박수빈
Date: 2025-11-18
Description
- Spotify 이용자 이탈 분석 확인 페이지
- 추가 기능 필요?
"""

# -------------------------------------------------------------
# Main Functions
# -------------------------------------------------------------
def test (str):
    """ Test 함수"""
    
    # 2025-11-18 박수빈 : 임시 주석 수정.
    # return false
    pass
>>>>>>> f784a6119fef694e345578216d891e6774a08959
