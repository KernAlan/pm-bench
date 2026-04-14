#!/usr/bin/env python3
"""
tools/hf_push.py
================

Push the prepared PM-Bench JSONL files to a HuggingFace Hub dataset repo.

This tool is documented-but-auth-gated: running it requires an HF token with
write access to the target repo. It does not push automatically as part of CI
or any other pipeline.

Prerequisites
-------------

1. Generate the JSONL files first::

       python huggingface/prepare_hf_dataset.py

   This writes ``huggingface/mcq.jsonl`` and ``huggingface/open-ended.jsonl``.

2. Install the Hub client::

       pip install huggingface_hub

3. Authenticate. Either of:

       export HF_TOKEN=<your hf token>            # preferred for CI
       huggingface-cli login                      # interactive

Usage
-----

       python tools/hf_push.py --repo-id KernAlan/pm-bench
       python tools/hf_push.py --repo-id KernAlan/pm-bench --dry-run
       python tools/hf_push.py --repo-id KernAlan/pm-bench --private

What gets uploaded
------------------

The script uploads:

    huggingface/README.md          -> README.md  (dataset card, YAML + body)
    huggingface/mcq.jsonl          -> mcq.jsonl
    huggingface/open-ended.jsonl   -> open-ended.jsonl
    huggingface/loading_script.py  -> pm_bench.py  (HF expects script named
                                                    after the dataset repo)

If the target repo does not exist the script will create it (unless
``--no-create`` is passed).

Error handling
--------------

If ``huggingface_hub`` is not installed or no token is available, the script
prints a clear message and exits non-zero without touching the network.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HF_DIR = ROOT / "huggingface"

# (local_path, path_in_repo)
UPLOADS = [
    (HF_DIR / "README.md",          "README.md"),
    (HF_DIR / "mcq.jsonl",          "mcq.jsonl"),
    (HF_DIR / "open-ended.jsonl",   "open-ended.jsonl"),
    (HF_DIR / "loading_script.py",  "pm_bench.py"),
]


def _missing_files() -> list[Path]:
    return [p for p, _ in UPLOADS if not p.exists()]


def _resolve_token(cli_token: str | None) -> str | None:
    if cli_token:
        return cli_token
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Push PM-Bench JSONL + card to HuggingFace Hub."
    )
    parser.add_argument("--repo-id", required=True,
                        help="HF repo id, e.g., 'KernAlan/pm-bench'.")
    parser.add_argument("--token", default=None,
                        help="HF token (falls back to $HF_TOKEN).")
    parser.add_argument("--private", action="store_true",
                        help="Create the repo as private if it does not exist.")
    parser.add_argument("--no-create", action="store_true",
                        help="Fail instead of creating the repo if it is missing.")
    parser.add_argument("--commit-message", default="Update PM-Bench dataset",
                        help="Commit message for each upload.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be uploaded without contacting the Hub.")
    args = parser.parse_args()

    missing = _missing_files()
    if missing:
        print("Missing required files (run prepare_hf_dataset.py first):",
              file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] Target repo: {args.repo_id}")
        print(f"[dry-run] Private: {args.private}")
        for src, dst in UPLOADS:
            print(f"[dry-run] upload {src}  ->  {dst}")
        return 0

    token = _resolve_token(args.token)
    if not token:
        print("No HF token found. Set $HF_TOKEN or pass --token.", file=sys.stderr)
        print("  export HF_TOKEN=<your hf token>", file=sys.stderr)
        return 2

    try:
        from huggingface_hub import HfApi, create_repo  # type: ignore
        from huggingface_hub.utils import RepositoryNotFoundError  # type: ignore
    except ImportError:
        print("Install huggingface_hub first:  pip install huggingface_hub",
              file=sys.stderr)
        return 2

    api = HfApi(token=token)

    # Ensure repo exists.
    try:
        api.repo_info(repo_id=args.repo_id, repo_type="dataset")
    except RepositoryNotFoundError:
        if args.no_create:
            print(f"Repo {args.repo_id} does not exist and --no-create was set.",
                  file=sys.stderr)
            return 3
        print(f"Creating dataset repo: {args.repo_id} (private={args.private})")
        create_repo(
            repo_id=args.repo_id,
            repo_type="dataset",
            token=token,
            private=args.private,
            exist_ok=True,
        )
    except Exception as exc:
        print(f"Failed to query repo: {exc}", file=sys.stderr)
        return 4

    # Upload each file.
    for src, dst in UPLOADS:
        print(f"uploading {src.name}  ->  {args.repo_id}:{dst}")
        try:
            api.upload_file(
                path_or_fileobj=str(src),
                path_in_repo=dst,
                repo_id=args.repo_id,
                repo_type="dataset",
                token=token,
                commit_message=args.commit_message,
            )
        except Exception as exc:
            print(f"  upload failed: {exc}", file=sys.stderr)
            return 5

    print(f"\nDone. View at: https://huggingface.co/datasets/{args.repo_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
