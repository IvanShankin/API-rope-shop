import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from src.core.config.base import init_env


class Config:
    def __init__(self) -> None:
        init_env()

        self.env: EnvConfig = EnvConfig.build()
        self.db_connection: DbConnectionConfig = DbConnectionConfig.build(self.env)
        self.paths: PathsConfig = PathsConfig.build()
        self.tokens: TokensConfig = TokensConfig.build()
        self.allowed_extensions: AllowedExtensions = AllowedExtensions.build()
        self.cors: CorsConfig = CorsConfig.build()
        self.admin: AdminConfig = AdminConfig.build()


class EnvConfig(BaseModel):
    secret_key: str

    db_host: str
    db_port: str
    db_user: str
    db_password: str
    db_name: str

    mode: str

    @classmethod
    def build(cls) -> "EnvConfig":

        return cls(
            secret_key=os.environ['SECRET_KEY'],
            db_host=os.environ['DB_HOST'],
            db_port=os.environ['DB_PORT'],
            db_user=os.environ['DB_USER'],
            db_password=os.environ['DB_PASSWORD'],
            db_name=os.environ['DB_NAME'],

            mode=os.environ['MODE']
        )



class DbConnectionConfig(BaseModel):
    postgres_server_url: str  # URL для подключения к серверу PostgresSQL без указания конкретной базы данных
    sql_db_url: str
    engine: AsyncEngine
    session_local: sessionmaker

    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Разрешаем произвольные типы
    )

    @classmethod
    def build(cls, conf_env: EnvConfig) -> "DbConnectionConfig":
        sql_db_url = f'postgresql+asyncpg://{conf_env.db_user}:{conf_env.db_password}@{conf_env.db_host}:{conf_env.db_port}/{conf_env.db_name}'
        engine = create_async_engine(sql_db_url)

        return cls(
            postgres_server_url=f'postgresql+asyncpg://{conf_env.db_user}:{conf_env.db_password}@{conf_env.db_host}:{conf_env.db_port}/postgres',
            sql_db_url=sql_db_url,
            engine=engine,
            session_local=sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )
        )


class PathsConfig(BaseModel):
    base: Path
    media: Path
    products: Path
    categories: Path
    splice_types: Path
    work_photos: Path
    charity_photos: Path
    temp: Path

    @classmethod
    def build(cls, postscript: Optional[str] = '') -> "PathsConfig":
        base = Path(__file__).resolve().parents[3]
        media = base / Path("media")
        products = media / Path(f"products{postscript}")
        categories = media / Path(f"categories{postscript}")
        splice_types = media / Path(f"splice_types{postscript}")
        work_photos = media / Path(f"work_photos{postscript}")
        charity_photos = media / Path(f"charity_photos{postscript}")
        temp = media / Path(f"temp{postscript}")

        media.mkdir(exist_ok=True)
        products.mkdir(exist_ok=True)
        categories.mkdir(exist_ok=True)
        splice_types.mkdir(exist_ok=True)
        work_photos.mkdir(exist_ok=True)
        charity_photos.mkdir(exist_ok=True)
        temp.mkdir(exist_ok=True)

        return cls(
            base=base,
            media=media,
            products=products,
            categories=categories,
            splice_types=splice_types,
            work_photos=work_photos,
            charity_photos=charity_photos,
            temp=temp,
        )


class TokensConfig(BaseModel):
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    algorithm: str

    @classmethod
    def build(cls) -> "TokensConfig":
        return cls(
            access_token_expire_minutes=30,
            refresh_token_expire_days=30,
            algorithm="HS256",
        )


class AllowedExtensions(BaseModel):
    for_image: List[str] = ["webp", "jpg", ".jpeg", "gif", ".png", "heic", "heif"]

    @classmethod
    def build(cls) -> "AllowedExtensions":
        return cls(
            for_image=["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif"],
        )


class CorsConfig(BaseModel):
    allow_origins: List[str]
    allow_origin_regex: Optional[str] = None
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]
    expose_headers: List[str] = ["*"]

    @classmethod
    def build(cls) -> "CorsConfig":
        default_origins = [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:4200",
            "http://localhost:5500",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:4200",
            "http://127.0.0.1:5500",
        ]

        env_origins = os.getenv("CORS_ORIGINS")
        origins = (
            [origin.strip() for origin in env_origins.split(",") if origin.strip()]
            if env_origins
            else default_origins
        )

        origin_regex = os.getenv(
            "CORS_ORIGIN_REGEX",
            r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        )

        return cls(
            allow_origins=origins,
            allow_origin_regex=origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )


class AdminConfig(BaseModel):
    email: str
    username: str
    password: str

    @classmethod
    def build(cls) -> "AdminConfig":
        return cls(
            email=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
            username=os.environ.get("ADMIN_USERNAME", "admin"),
            password=os.environ.get("ADMIN_PASSWORD", "admin12345"),
        )
