import kagglehub
import os
import shutil

print("Descargando dataset desde Kaggle...")
path = kagglehub.dataset_download("bharathreddybollu/hospital-wait-time-data")
print(f"Dataset descargado en: {path}")

# Copiar el archivo CSV a la carpeta del proyecto para fácil acceso
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.csv'):
            origen = os.path.join(root, file)
            destino = os.path.join(os.getcwd(), 'data', file)
            os.makedirs('data', exist_ok=True)
            shutil.copy(origen, destino)
            print(f"Archivo copiado a: {destino}")
            break