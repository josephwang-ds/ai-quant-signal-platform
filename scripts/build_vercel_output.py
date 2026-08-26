"""Package only public HTML into Vercel's prebuilt static-output format."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from company_lens.web.ask import ASK_EVIDENCE_VERSION, build_ask_evidence

DEFAULT_ASK_FUNCTION = Path("ops/vercel/ask/index.js")


def build_vercel_output(
    source: Path,
    output_root: Path,
    *,
    ask_function_source: Path = DEFAULT_ASK_FUNCTION,
) -> Path:
    source = Path(source)
    output_root = Path(output_root)
    html_files = sorted(source.glob("*.html"))
    if not html_files or not (source / "index.html").exists() or not (source / "404.html").exists():
        raise ValueError(f"source is not a complete Company Lens site: {source}")

    build_output = output_root / ".vercel" / "output"
    temporary = output_root / ".vercel" / ".output.next"
    if temporary.exists():
        shutil.rmtree(temporary)
    static = temporary / "static"
    static.mkdir(parents=True)
    for path in html_files:
        shutil.copy2(path, static / path.name)
    _build_ask_function(source, temporary, ask_function_source)
    config = {
        "version": 3,
        "routes": [
            {"src": "/", "dest": "/index.html"},
            {"handle": "filesystem"},
            {"src": "/.*", "dest": "/404.html", "status": 404},
        ],
    }
    (temporary / "config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )

    if build_output.exists():
        shutil.rmtree(build_output)
    temporary.replace(build_output)
    return build_output


def _build_ask_function(
    source: Path,
    output: Path,
    function_source: Path,
) -> None:
    companies = {}
    for path in sorted(source.glob("*.json")):
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(snapshot, dict) or not {
            "ticker",
            "benchmark",
            "performance",
            "profile",
        }.issubset(snapshot):
            continue
        companies[str(snapshot["ticker"]).upper()] = build_ask_evidence(snapshot)
    if not companies:
        return
    if not function_source.is_file():
        raise ValueError(f"Company Lens ask function is missing: {function_source}")

    function = output / "functions" / "api" / "ask.func"
    function.mkdir(parents=True)
    shutil.copy2(function_source, function / "index.js")
    (function / "evidence.json").write_text(
        json.dumps(
            {
                "schema_version": ASK_EVIDENCE_VERSION,
                "companies": companies,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    (function / ".vc-config.json").write_text(
        json.dumps(
            {
                "runtime": "nodejs22.x",
                "handler": "index.js",
                "maxDuration": 45,
                "memory": 512,
                "launcherType": "Nodejs",
                "shouldAddHelpers": True,
            }
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/build/company_pages"))
    parser.add_argument(
        "--out", type=Path, default=Path("data/build/vercel_frontend")
    )
    parser.add_argument(
        "--ask-function-source",
        type=Path,
        default=DEFAULT_ASK_FUNCTION,
    )
    args = parser.parse_args()
    output = build_vercel_output(
        args.source,
        args.out,
        ask_function_source=args.ask_function_source,
    )
    files = list((output / "static").glob("*.html"))
    functions = list((output / "functions").glob("**/*.func"))
    size = sum(path.stat().st_size for path in files)
    print(
        f"Vercel frontend: {len(files)} HTML files, {len(functions)} function, "
        f"{size / 1024 / 1024:.1f} MB -> {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
