import os
import joblib
from loguru import logger
from app.core.config import settings

class ModelStorage:
    def __init__(self):
        self.local_path = settings.MODEL_STORAGE_PATH
        os.makedirs(self.local_path, exist_ok=True)

    def save_model(self, model, name: str):
        """Guarda modelo localmente o sube a la nube si S3 está configurado."""
        file_path = os.path.join(self.local_path, f"{name}.pkl")
        joblib.dump(model, file_path)
        logger.info(f"Modelo {name} guardado en {file_path}")
        
        # TODO: Implementar upload a S3 si AWS_ACCESS_KEY está presente

    def load_model(self, name: str):
        """Carga modelo desde disco o descarga desde S3."""
        file_path = os.path.join(self.local_path, f"{name}.pkl")
        if not os.path.exists(file_path):
            logger.error(f"Modelo {name} no encontrado en {file_path}")
            return None
        return joblib.load(file_path)

model_storage = ModelStorage()
