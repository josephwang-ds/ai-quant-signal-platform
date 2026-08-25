"""Package only public HTML into Vercel's prebuilt static-output format."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def build_vercel_output(source: Path, output_root: Path) -> Path:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/build/company_pages"))
    parser.add_argument(
        "--out", type=Path, default=Path("data/build/vercel_frontend")
    )
    args = parser.parse_args()
    output = build_vercel_output(args.source, args.out)
    files = list((output / "static").glob("*.html"))
    size = sum(path.stat().st_size for path in files)
    print(f"Vercel frontend: {len(files)} HTML files, {size / 1024 / 1024:.1f} MB -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
