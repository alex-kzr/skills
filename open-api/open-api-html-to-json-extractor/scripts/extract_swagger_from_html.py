#!/usr/bin/env python3

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_swagger_data(html_text: str) -> dict[str, Any]:
    pattern = r'<script\s+id=["\\\']swagger-data["\\\']\s+type=["\\\']application/json["\\\']\s*>(.*?)</script>'
    match = re.search(pattern, html_text, flags=re.DOTALL | re.IGNORECASE)

    if not match:
        raise ValueError(
            'Could not find <script id="swagger-data" type="application/json">...</script>'
        )

    raw_json = html.unescape(match.group(1)).strip()
    data = json.loads(raw_json)

    if isinstance(data, dict) and "spec" in data:
        return data["spec"]

    if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
        return data

    raise ValueError("JSON was found, but it does not contain an OpenAPI/Swagger spec")


def print_summary(spec: dict[str, Any]) -> None:
    info = spec.get("info", {})
    components = spec.get("components", {})
    schemas = components.get("schemas", {})

    print("Extracted OpenAPI spec")
    print(f"Version: {spec.get('openapi') or spec.get('swagger') or 'unknown'}")
    print(f"Title: {info.get('title', 'unknown')}")
    print(f"Paths: {len(spec.get('paths', {}))}")
    print(f"Schemas: {len(schemas)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract OpenAPI/Swagger JSON from Swagger UI HTML"
    )
    parser.add_argument("input_html", help="Path to Swagger UI HTML file")
    parser.add_argument(
        "output_json",
        nargs="?",
        default="openapi.json",
        help="Output JSON file path. Default: openapi.json",
    )

    args = parser.parse_args()

    input_path = Path(args.input_html)
    output_path = Path(args.output_json)

    html_text = load_text(input_path)
    spec = extract_swagger_data(html_text)

    output_path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print_summary(spec)
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
