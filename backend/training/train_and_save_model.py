"""
train_and_save_model.py
Author: 신지용

HGB 모델을 학습하고 pkl 파일로 저장하는 스크립트.
이 스크립트를 한 번 실행하면 models/ 폴더에 학습된 모델이 저장되고,
inference.py에서 바로 로드하여 사용할 수 있습니다.
"""

import sys
from pathlib import Path
import joblib
import numpy as np

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.preprocessing_pipeline import preprocess_and_split
from backend.models import get_model
from backend.config import RANDOM_STATE, THRESH_START, THRESH_END, THRESH_STEP
from sklearn.metrics import f1_score, roc_auc_score, classification_report, precision_score, recall_score


def find_best_threshold(y_true, y_proba):
    """
    여러 threshold를 스캔하여 F1이 최대가 되는 지점을 찾습니다.
    train_experiments.py와 동일한 로직 사용.
    """
    thresholds = np.arange(THRESH_START, THRESH_END, THRESH_STEP)
    
    best_f1 = 0.0
    best_th = 0.5
    best_precision = 0.0
    best_recall = 0.0
    
    for th in thresholds:
        y_pred = (y_proba >= th).astype(int)
        f1 = f1_score(y_true, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_th = float(th)
            best_precision = precision_score(y_true, y_pred, zero_division=0)
            best_recall = recall_score(y_true, y_pred, zero_division=0)
    
    return best_f1, best_th, best_precision, best_recall


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("HGB Model Training and Saving")
    print("="*60)
    
    # 1. 데이터 전처리
    print("\n[1/4] Preprocessing data...")
    X_train, X_test, y_train, y_test, preprocessor = preprocess_and_split()
    
    # 2. 모델 학습
    print("\n[2/4] Training HGB model...")
    model = get_model("hgb", random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    print("Training completed!")
    
    # 3. 성능 평가 (Best Threshold 스캔)
    print("\n[3/4] Evaluating model...")
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Best threshold 찾기 (train_experiments.py와 동일)
    best_f1, best_th, best_precision, best_recall = find_best_threshold(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)
    
    # Best threshold로 예측
    y_pred = (y_prob >= best_th).astype(int)
    
    print(f"\n{'='*60}")
    print("Model Performance (with Best Threshold)")
    print(f"{'='*60}")
    print(f"F1 Score: {best_f1:.4f}")
    print(f"ROC-AUC: {auc:.4f}")
    print(f"Best Threshold: {best_th:.2f}")
    print(f"Precision: {best_precision:.4f}")
    print(f"Recall: {best_recall:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Not Churned', 'Churned'])}")
    
    # 4. 모델 및 전처리기 저장
    print("\n[4/4] Saving model and preprocessor...")
    
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / "hgb_final.pkl"
    preprocessor_path = models_dir / "preprocessor_final.pkl"
    
    joblib.dump(model, model_path)
    joblib.dump(preprocessor, preprocessor_path)
    
    print(f"\n✅ Model saved to: {model_path}")
    print(f"✅ Preprocessor saved to: {preprocessor_path}")
    
    print(f"\n{'='*60}")
    print("Training and saving completed successfully!")
    print(f"{'='*60}")
    print("\n다음 단계:")
    print("1. Flask 서버를 재시작하세요")
    print("2. 이제 예측이 훨씬 빨라집니다!")
    print("3. X_train_processed.pkl은 더 이상 필요하지 않습니다")


if __name__ == "__main__":
    main()
