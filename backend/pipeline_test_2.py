from preprocessing import preprocess_pipeline  # ← 여기만 수정
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score

# 1) 파이프라인 실행 (파일 바꾸고 싶으면 path만 바꿔줘)
X_train, X_test, y_train, y_test, scaler = preprocess_pipeline(
    path="data/enhanced_data_not_clean_FE_delete.csv",  # 또는 enhanced_data.csv 등
    save_output=False,  # 테스트니까 파일은 안 저장
    test_size=0.2,
    random_state=42,
)

# 2) 간단한 모델 학습
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    random_state=42,
    class_weight="balanced",
)
model.fit(X_train, y_train)

# 3) F1 / AUC 계산
proba = model.predict_proba(X_test)[:, 1]
pred = (proba >= 0.5).astype(int)   # 간단히 threshold 0.5

f1 = f1_score(y_test, pred)
auc = roc_auc_score(y_test, proba)

print("F1:", f1)
print("AUC:", auc)