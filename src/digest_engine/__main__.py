import argparse
import os
import sys
from pathlib import Path
from .config import load_config
from .iso_week import current_iso_week
from .orchestrator import RunContext, run_pipeline
from .git_collector import collect_commits
from .llm_client import OpenAIClient
from .delivery.whatsapp import WhatsAppDeliverer


def main() -> int:
    p = argparse.ArgumentParser(prog="digest")
    p.add_argument("--week", default=current_iso_week(),
                   help="ISO week id (YYYY-Www). Defaults to current.")
    p.add_argument("--config", default="digest.config.yaml")
    p.add_argument("--reports-dir", default="reports")
    p.add_argument("--cache-dir", default=".cache/classifier")
    p.add_argument("--dry-run", action="store_true",
                   help="Skip WhatsApp send and git push.")
    p.add_argument("--report-url", default=os.environ.get("REPORT_URL", ""),
                   help="Public URL where the PDF will be served.")
    args = p.parse_args()

    cfg = load_config(args.config)

    llm = OpenAIClient(model=cfg.classification.model,
                       api_key=os.environ["OPENAI_API_KEY"])

    whatsapp: WhatsAppDeliverer | None = None
    if not args.dry_run and cfg.delivery.whatsapp.recipients:
        whatsapp = WhatsAppDeliverer(
            config=cfg.delivery.whatsapp,
            access_token=os.environ["META_ACCESS_TOKEN"])

    ctx = RunContext(
        config=cfg, week_id=args.week,
        reports_dir=Path(args.reports_dir),
        cache_dir=Path(args.cache_dir),
        collect_fn=collect_commits, llm=llm, whatsapp=whatsapp,
        report_url=args.report_url, dry_run=args.dry_run)

    result = run_pipeline(ctx)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
