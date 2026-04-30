# digest-engine

Automated weekly progress digest. Reads commits from configured repos, translates to business language via LLM, renders branded PDF, delivers via WhatsApp.

## Run locally

```
pip install -e .[dev]
python -m digest_engine --week 2026-W17
```

## Config

Edit `digest.config.yaml`. See spec at `../docs/superpowers/specs/2026-04-29-progress-digest-design.md`.
