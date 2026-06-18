import os
from supabase import create_client, Client
from app.core.config import settings

# Cliente de Supabase para Auth y Storage
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

class CloudStorage:
    """Implementación gratuita usando Supabase Storage."""
    
    BUCKET_NAME = "models"

    @classmethod
    async def upload_model(cls, local_file_path: str, model_name: str):
        with open(local_file_path, 'rb') as f:
            supabase.storage.from_(cls.BUCKET_NAME).upload(
                path=f"{model_name}.pkl",
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"}
            )

    @classmethod
    async def download_model(cls, model_name: str, destination_path: str):
        with open(destination_path, 'wb+') as f:
            res = supabase.storage.from_(cls.BUCKET_NAME).download(f"{model_name}.pkl")
            f.write(res)

# Auth Middleware: Verifica el token de Supabase
async def get_current_user(token: str):
    user = supabase.auth.get_user(token)
    return user
