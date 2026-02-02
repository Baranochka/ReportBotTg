from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class BotConfig(BaseModel):
    token: str = ""
    admin_token: str = "" 


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            ".env.template",
            ".env",
            ".env.dev",
        ),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="TG__",
    )
    bot: BotConfig = BotConfig()



settings = Settings()