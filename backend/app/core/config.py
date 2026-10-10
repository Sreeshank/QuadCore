from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT.parent / '.env', ROOT / '.env'), extra='ignore')
    app_env: str = 'development'
    demo_mode: bool = True
    database_url: str = f'sqlite:///{(ROOT / "data/taxready.db").as_posix()}'
    storage_dir: Path = ROOT / 'data/private'
    storage_backend: str = 'local'
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    supabase_url: str = ''
    supabase_anon_key: str = ''
    supabase_service_role_key: str = ''
    supabase_bucket: str = 'taxready-private'
    llm_api_key: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_model: str = 'gpt-4.1-mini'
    tesseract_cmd: str = ''
    max_upload_mb: int = 10
    max_pdf_pages: int = 30
    rate_limit: int = 120

    @field_validator('database_url')
    @classmethod
    def postgres_driver(cls, value):
        if value.startswith('postgresql://'):
            return value.replace('postgresql://', 'postgresql+psycopg://', 1)
        if value.startswith('postgres://'):
            return value.replace('postgres://', 'postgresql+psycopg://', 1)
        return value

    def validate_runtime(self):
        if self.app_env == 'production':
            if self.demo_mode:
                raise RuntimeError('DEMO_MODE must be false in production.')
            if not self.supabase_url or not self.supabase_anon_key:
                raise RuntimeError('Production requires Supabase authentication.')
            if not self.supabase_url.startswith('https://'):
                raise RuntimeError('Production authentication must use HTTPS.')
            if self.storage_backend != 'supabase' or not self.supabase_service_role_key:
                raise RuntimeError('Production requires private Supabase storage.')
            if '*' in self.cors_origins:
                raise RuntimeError('Production requires explicit CORS origins.')
        if self.storage_backend not in {'local', 'supabase'}:
            raise RuntimeError('Unknown storage backend.')


settings = Settings()
