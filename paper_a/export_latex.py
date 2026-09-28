#!/usr/bin/env python3
"""Export a flat Elsevier/JISA source package without private experiment data."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    original = (ROOT / "paper_a.tex").read_text()
    files = {}

    def flatten(match):
        relative = Path(match.group(2))
        source = (ROOT / relative).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError(f"Invalid figure: {relative}")
        if relative.name in files:
            raise ValueError(f"Duplicate flattened filename: {relative.name}")
        files[relative.name] = source.read_bytes()
        return match.group(1) + "{" + relative.name + "}"

    manuscript = re.sub(
        r"(\\includegraphics(?:\[[^\]]*\])?)\{([^}]+)\}",
        flatten,
        original,
    )
    files["paper_a.tex"] = manuscript.encode()

    bbl = (ROOT / "paper_a.bbl").read_text()
    required_bibitems = ("Imam2025JISA", "Wang2025JISA")
    missing_bibitems = [
        key for key in required_bibitems if ("\\bibitem{" + key + "}") not in bbl
    ]
    if missing_bibitems:
        raise RuntimeError(
            "paper_a.bbl is stale; recompile with BibTeX before export. "
            f"Missing bibitems: {missing_bibitems}"
        )

    highlights = [
        line.strip()[2:].strip()
        for line in (ROOT / "highlights.txt").read_text().splitlines()
        if line.strip().startswith("- ")
    ]
    if not 3 <= len(highlights) <= 5:
        raise RuntimeError("Elsevier highlights must contain 3--5 bullet points")
    too_long = [(item, len(item)) for item in highlights if len(item) > 85]
    if too_long:
        raise RuntimeError(f"Highlights exceed 85 characters: {too_long}")

    for name in (
        "references.bib",
        "paper_a.bbl",
        "elsarticle.cls",
        "elsarticle-num.bst",
        "highlights.txt",
    ):
        files[name] = (ROOT / name).read_bytes()

    package_readme = """JISA LaTeX source package.
Target: Journal of Information Security and Applications (JISA).
Publisher template: Elsevier elsarticle numeric submission layout; CTAN 3.5 baseline.
All source files are flattened to one directory for Editorial Manager.
Data/code availability information is included in the manuscript.
Compile: latexmk -pdf -interaction=nonstopmode -halt-on-error paper_a.tex
Highlights follow Elsevier's 3--5 bullet, <=85-character guidance.
No private experiment data, private keys, or reviewer correspondence are included.
"""
    files["README.txt"] = package_readme.encode()

    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files["MANIFEST.json"] = json.dumps(
        {"files": hashes, "target_journal": "Journal of Information Security and Applications"},
        indent=2,
    ).encode()

    output = ROOT / "paper_a_jisa_submission.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)

    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all("/" not in name for name in archive.namelist())

    print(f"{output}: {len(files)} flat submission-source files")


if __name__ == "__main__":
    main()
