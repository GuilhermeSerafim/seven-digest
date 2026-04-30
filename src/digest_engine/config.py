from pathlib import Path
import os
import re
import yaml
from pydantic import BaseModel, Field


class BrandConfigYaml(BaseModel):
    primary_color: str
    light_color: str
    logo_path: str | None = None


class ProjectConfig(BaseModel):
    name: str
    brand: BrandConfigYaml


class RepoConfig(BaseModel):
    name: str
    path: str
    branch: str = "main"
    ignore_patterns: list[str] = Field(default_factory=list)


class ClassificationConfig(BaseModel):
    llm_provider: str = "openai"
    model: str = "gpt-4o"
    audience: str
    prompt_overrides: str | None = None


class ScreenshotsConfig(BaseModel):
    enabled: bool = False


class Recipient(BaseModel):
    name: str
    phone: str


class WhatsAppConfig(BaseModel):
    provider: str
    phone_number_id: str
    template_name: str
    recipients: list[Recipient]


class ArchiveConfig(BaseModel):
    path: str = "reports/"
    commit_to_repo: bool = True


class DeliveryConfig(BaseModel):
    whatsapp: WhatsAppConfig
    archive: ArchiveConfig


class Config(BaseModel):
    project: ProjectConfig
    repos: list[RepoConfig]
    classification: ClassificationConfig
    screenshots: ScreenshotsConfig
    delivery: DeliveryConfig


_ENV_VAR_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


def _substitute_env(text: str) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1)
        return os.environ.get(name, m.group(0))
    return _ENV_VAR_RE.sub(repl, text)


def load_config(path: str | Path) -> Config:
    raw = Path(path).read_text(encoding="utf-8")
    raw = _substitute_env(raw)
    data = yaml.safe_load(raw)
    return Config.model_validate(data)
