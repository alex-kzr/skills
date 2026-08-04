#!/usr/bin/env python3
"""Extract text from documents using marker-pdf. High-quality OCR + layout analysis.

Requires ~3-5GB disk (PyTorch + models downloaded on first use).
Supports: PDF, DOCX, PPTX, XLSX, HTML, EPUB, images.

Usage:
    python extract_marker.py document.pdf
    python extract_marker.py document.pdf --output_dir ./output
    python extract_marker.py presentation.pptx
    python extract_marker.py spreadsheet.xlsx
    python extract_marker.py scanned_doc.pdf           # OCR works here
    python extract_marker.py document.pdf --json        # Structured output
    python extract_marker.py document.pdf --use_llm     # LLM-boosted accuracy
"""
import sys
import os
from pathlib import Path


def _find_agents_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "skills").exists() and (parent / "runtime").exists():
            return parent
    raise RuntimeError("Cannot find agents root with both skills/ and runtime/")


def _add_runtime_site_packages() -> None:
    agents_root = _find_agents_root(Path(__file__))
    venv_dir = agents_root / "runtime" / "python" / "base" / ".venv"
    if os.name == "nt":
        site_packages = venv_dir / "Lib" / "site-packages"
    else:
        candidates = list((venv_dir / "lib").glob("python*/site-packages"))
        site_packages = candidates[0] if candidates else None
    if not site_packages or not site_packages.exists():
        raise RuntimeError(
            "Python runtime is not prepared. Expected site-packages at: "
            f"{site_packages}. Prepare agents/runtime/python/base/.venv first."
        )
    sys.path.insert(0, str(site_packages))


def convert(path, output_dir=None, output_format="markdown", use_llm=False):
    _add_runtime_site_packages()
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser

    config_dict = {}
    if use_llm:
        config_dict["use_llm"] = True

    config_parser = ConfigParser(config_dict)
    models = create_model_dict()
    converter = PdfConverter(config=config_parser.generate_config_dict(), artifact_dict=models)
    rendered = converter(path)

    if output_format == "json":
        import json
        print(json.dumps({
            "markdown": rendered.markdown,
            "metadata": rendered.metadata if hasattr(rendered, "metadata") else {},
        }, indent=2, ensure_ascii=False))
    else:
        print(rendered.markdown)

    # Save images if output_dir specified
    if output_dir and hasattr(rendered, "images") and rendered.images:
        from pathlib import Path
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for name, img_data in rendered.images.items():
            img_path = os.path.join(output_dir, name)
            with open(img_path, "wb") as f:
                f.write(img_data)
        print(f"\nSaved {len(rendered.images)} image(s) to {output_dir}/", file=sys.stderr)


def check_requirements():
    """Check disk space before installing."""
    import shutil
    free_gb = shutil.disk_usage("/").free / (1024**3)
    if free_gb < 5:
        print(f"⚠️  Only {free_gb:.1f}GB free. marker-pdf needs ~5GB for PyTorch + models.")
        print("Use pymupdf instead (scripts/extract_pymupdf.py) or free up disk space.")
        sys.exit(1)
    print(f"✓ {free_gb:.1f}GB free — sufficient for marker-pdf")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "--check":
        check_requirements()
        sys.exit(0)

    path = args[0]
    output_dir = None
    output_format = "markdown"
    use_llm = False

    if "--output_dir" in args:
        idx = args.index("--output_dir")
        output_dir = args[idx + 1]
    if "--json" in args:
        output_format = "json"
    if "--use_llm" in args:
        use_llm = True

    convert(path, output_dir=output_dir, output_format=output_format, use_llm=use_llm)
