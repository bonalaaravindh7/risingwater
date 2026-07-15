"""
Rising Waters - Model Training Script
Regenerates floods.save (classifier) and transform.save (scaler).
Run this inside retrain_env (numpy==1.26.4, scikit-learn==1.5.0, etc.)
"""

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ---------------------------------------------------------------------
# 1. Load dataset
# ---------------------------------------------------------------------
DATA_PATH = "dataset/flood dataset.xlsx"
df = pd.read_excel(DATA_PATH)

print("Columns found in dataset:")
print(list(df.columns))
print(df.head())

# ---------------------------------------------------------------------
# 2. IMPORTANT: update this list to match your ACTUAL column names exactly
#    (must be in the same order app.py uses to build the input DataFrame)
# ---------------------------------------------------------------------
FEATURE_COLUMNS = [
    "Temp",
    "Humidity",
    "Cloud Cover",
    "ANNUAL",
    "Jan-Feb",
    "Mar-May",
    "Jun-Sep",
    "Oct-Dec",
    "avgjune",
    "sub",
]
TARGET_COLUMN = "flood"

missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
if missing:
    raise ValueError(
        f"These columns were not found in the dataset: {missing}\n"
        f"Update FEATURE_COLUMNS / TARGET_COLUMN in this script to match "
        f"the printed column list above."
    )

# ---------------------------------------------------------------------
# 3. Clean missing values
# ---------------------------------------------------------------------
df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN]

# ---------------------------------------------------------------------
# 4. Train/test split
# ---------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------------------------------------------------------------
# 5. Scale features
# ---------------------------------------------------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ---------------------------------------------------------------------
# 6. Train and compare models
# ---------------------------------------------------------------------
models = {
    "Decision Tree": DecisionTreeClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "Gradient Boosting": GradientBoostingClassifier(random_state=42),
}

results = {}
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    preds = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, preds)
    results[name] = (acc, model)
    print(f"\n{'=' * 50}\n{name}  |  Accuracy: {acc:.4f}")
    print(confusion_matrix(y_test, preds))
    print(classification_report(y_test, preds))

# ---------------------------------------------------------------------
# 7. Select best model
# ---------------------------------------------------------------------
best_name, (best_acc, best_model) = max(results.items(), key=lambda kv: kv[1][0])
print(f"\n{'=' * 50}\nBest model: {best_name}  |  Accuracy: {best_acc:.4f}")

# ---------------------------------------------------------------------
# 8. Save model + scaler
# ---------------------------------------------------------------------
joblib.dump(best_model, "floods.save")
joblib.dump(scaler, "transform.save")
print("\nSaved floods.save and transform.save successfully.")