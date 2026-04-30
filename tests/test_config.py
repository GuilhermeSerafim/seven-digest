import pytest
from pathlib import Path
from digest_engine.config import load_config, Config


YAML_GOOD = """
project:
  name: "Test Project"
  brand:
    primary_color: "#112233"
    light_color: "#aabbcc"
    logo_path: null
repos:
  - name: backend
    path: "./backend"
    branch: main
    ignore_patterns: ["^chore"]
classification:
  llm_provider: openai
  model: gpt-4o
  audience: "test audience"
  prompt_overrides: null
screenshots:
  enabled: false
delivery:
  whatsapp:
    provider: meta_cloud_api
    phone_number_id: "PHONE_ID"
    template_name: "tpl"
    recipients:
      - { name: "A", phone: "+5511..." }
  archive:
    path: "reports/"
    commit_to_repo: true
"""


def test_load_config_parses_valid_yaml(tmp_path: Path):
    p = tmp_path / "c.yaml"
    p.write_text(YAML_GOOD)
    cfg = load_config(p)
    assert isinstance(cfg, Config)
    assert cfg.project.name == "Test Project"
    assert cfg.repos[0].name == "backend"
    assert cfg.delivery.whatsapp.recipients[0].phone == "+5511..."


def test_load_config_rejects_missing_required(tmp_path: Path):
    bad = YAML_GOOD.replace('name: "Test Project"', "")
    p = tmp_path / "c.yaml"
    p.write_text(bad)
    with pytest.raises(Exception):
        load_config(p)


def test_load_config_substitutes_env_vars(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("META_PHONE_ID", "REAL_ID_123")
    yaml = YAML_GOOD.replace('"PHONE_ID"', '"${META_PHONE_ID}"')
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    cfg = load_config(p)
    assert cfg.delivery.whatsapp.phone_number_id == "REAL_ID_123"
