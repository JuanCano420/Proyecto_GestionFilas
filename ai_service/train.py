import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.dummy import DummyRegressor

# 1. Cargar dataset
# Buscamos en la carpeta data/, pero si lo dejaste en la raíz, también lo encontrará
csv_path = 'data/hospital_wait_time.csv'
if not os.path.exists(csv_path):
    csv_path = 'hospital-wait-time-data.csv' # Nombre por defecto de Kaggle en la raíz
    if not os.path.exists(csv_path):
        print("Error: No se encuentra el CSV. Asegúrate de tener el archivo de datos en tu proyecto.")
        exit()

df = pd.read_csv(csv_path)

# 2. Preprocesamiento
# Convertir automáticamente la categoría de texto a números (0, 1, 2...)
df['Urgency_Num'] = df['TriageCategory'].astype('category').cat.codes

# Convertir las columnas de texto a formato de fecha/hora (evitando warnings)
df['CheckInTime'] = pd.to_datetime(df['CheckInTime'], dayfirst=True, errors='coerce')
df['ProviderStartTime'] = pd.to_datetime(df['ProviderStartTime'], dayfirst=True, errors='coerce')

# Calcular la diferencia en minutos para obtener el tiempo real de espera
df['Total Wait Time (min)'] = (df['ProviderStartTime'] - df['CheckInTime']).dt.total_seconds() / 60

# Eliminar filas que no tengan datos válidos de tiempo
df = df.dropna(subset=['Total Wait Time (min)'])

# Selección de features y variable objetivo
features = ['Urgency_Num']
target = 'Total Wait Time (min)'

# Llenar cualquier vacío residual con 0
X = df[features].fillna(0)
y = df[target]

# 3. Split (División de datos para entrenamiento y prueba)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Baseline (Modelo básico de referencia)
baseline = DummyRegressor(strategy="mean")
baseline.fit(X_train, y_train)
baseline_preds = baseline.predict(X_test)
baseline_mae = mean_absolute_error(y_test, baseline_preds)
print(f"Baseline MAE (media histórica): {baseline_mae:.2f} min")

# 5. Modelo Final (Random Forest)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
print(f"Random Forest MAE: {mae:.2f} min")

# 6. Guardar modelo
os.makedirs('ai_service', exist_ok=True)
joblib.dump(model, 'ai_service/model.pkl')
print("Modelo guardado exitosamente en ai_service/model.pkl")