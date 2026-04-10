from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Music Parser'
    api_prefix: str = '/api/v1'
    output_dir: str = Field(default='/music')
    omnivore_import_dir: str | None = Field(default='/omnivore/inbox')
    sqlite_path: str = Field(default='app/data/music_parser.db')
    max_history: int = 100

    model_config = {'env_file': 'stack.env', 'extra': 'ignore'}


settings = Settings()
