# 📦 Data Preprocessing Pipeline Design

# 📦 Data Preprocessing Pipeline Design  
프로젝트: 고객 이탈(churn) 예측  
담당: 데이터 분석 + 파이프라인 설계 리더 (1번 역할)

---

## 1. 목표  
원본 데이터를 체계적으로 전처리하여  
모델 학습에 최적화된 형태(X, y)를 생성하는 파이프라인 설계.

---

## 2. 데이터 구조 이해

### ✔ 데이터 구성  
- 총 레코드: 8,000  
- 총 컬럼: 12  
- 타깃 변수: **is_churned (0/1)**

### ✔ 변수 유형  
- **범주형**: gender, country, subscription_type, device_type  
- **수치형**: age, listening_time, songs_played_per_day, skip_rate, ads_listened_per_week, offline_listening  
- **ID 컬럼**: user_id → 모델 학습에서 제외

---

## 3. 데이터 품질 점검

### 🔸 결측치
- listening_time: 240  
- songs_played_per_day: 240  
→ **평균 또는 중앙값으로 대체(Median Impute)**

### 🔸 이상치  
- skip_rate: 0~5 이상치 다수  
- ads_listened_per_week: 30~50 이상의 극단값 존재  

처리 방안:  
- percentile(1%, 99%) 기반 윈저라이징(Winsorizing) 또는 IQR 기반 캡핑  
- 지나치게 왜도 높은 변수는 log 또는 sqrt 변환 고려

---

## 4. Feature 분석 요약 (EDA 기반)

### ✔ 범주형 변수 → 유의미한 Feature  
EDA 결과, 범주형 변수는 churn_rate 차이가 명확:

| 컬럼명 | 인사이트 |
|--------|-----------|
| subscription_type | Family 플랜 이탈률 가장 높음 |
| device_type | Mobile 사용자 이탈률 가장 높음 |
| offline_listening | 1 사용자가 이탈률 더 높음 |

→ **One-Hot Encoding 또는 Target Encoding 필요**

### ✔ 수치형 변수 → 단독 의미 약함, 가공 필요  
- 분포가 churn 여부와 거의 동일  
- corr < 0.02 수준  
→ 가공된 feature가 필요함

수치형 `Feature Engineering` 아이디어:
1. `engagement_score` = listening_time × songs_played_per_day
  : 사용자의 적극성  
2. skip_rate capped (0 ~ 1.5)  
3. listening_time binning (low / mid / high)  
4. `songs_per_minute` = songs_played_per_day / listening_time 비율  
  : 재생곡 수 / 들은 시간
5. `skip_intensity` = skip_rate * songs_played_per_day
  : 스킵 비율 * 재생곡 수 = 실제 스킵한 행동량
6. `ads_pressure` = ads_listened_per_week / listening_time
7. age group화 == young / adult / senior or 알파 / mz / x 세대
8. subsciption_type_level
   - eda에서 Family > Premium > Student > Free 순서였으니까 
   유형별 위험도를 숫자로 매핑
  (ex) "Family":3, "Premium":2, "Student":1, "Free":0
---

## 5. 전처리 파이프라인 설계

### **Step 1. Drop Unused Columns**
- user_id 제거

### **Step 2. 결측치 처리**
- listening_time → median  
- songs_played_per_day → median  

### **Step 3. 이상치 처리**
- skip_rate → 상단값 cap  
- ads_listened_per_week → percentile 기반 윈저라이징

### **Step 4. 범주형 인코딩**
- OneHotEncoding(subscription_type, device_type)  
- gender, country는 cardinality에 따라 처리 결정  
  - country는 grouping 필요 (top-5 + 기타)

### **Step 5. 수치형 스케일링**
- MinMax 또는 StandardScaler  
- Tree 계열 모델(XGBoost, LightGBM) 사용 시 생략 가능

### **Step 6. Feature Engineering(옵션)**
- engagement_score  
- listening_time_bin  
- skip_rate_cap  
- ads_listened_log

---

## 6. 출력 산출물
- **pipeline_design.md (본 문서)**  
- **feature_list.pkl (후보 feature 모음)**  
- **preprocessing.py (팀 2번이 구현할 파이프라인 코드)**  
- **EDA 문서(data_analysis.ipynb + feature_exploration.ipynb)**

---

## 7. 팀 전달 메모
- 범주형 변수는 예측력 높으므로 유지 및 적절히 인코딩할 것  
- 수치형은 단독 영향 약하므로 Feature Engineering을 통해 강화해야 함  
- 파이프라인은 재현성을 위해 함수 형태로 구성 필요 (train/test 동일 처리)
