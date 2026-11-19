#!/usr/bin/env python3
"""Create or verify SHA-256 checksums for the three project data matrices.

Run from the repository root:
    python tools/verify_data_checksums.py

After intentionally replacing a source matrix, regenerate the committed
reference only after both collaborators agree on the new source:
    python tools/verify_data_checksums.py --write
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKSUM_FILE = REPOSITORY_ROOT / "data_checksums.sha256"
DATA_FILES = (
    Path("coadread_tcga_pan_can_atlas_2018/data_log2_cna.txt"),
    Path("coadread_tcga_pan_can_atlas_2018/data_mrna_seq_v2_rsem.txt"),
    Path("coadread_tcga_pan_can_atlas_2018/data_methylation_hm450.txt"),
)
CHUNK_SIZE = 1024 * 1024  # 1 MiB


def sha256(path: Path) -> str:
    """Return the SHA-256 digest without reading the whole file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums() -> int:
    """Write checksums for the selected matrices in standard SHA-256 format."""
    lines = []
    for relative_path in DATA_FILES:
        path = REPOSITORY_ROOT / relative_path
        if not path.is_file():
            print(f"MISSING  {relative_path}")
            return 1
        lines.append(f"{sha256(path)}  {relative_path.as_posix()}\n")

    CHECKSUM_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {CHECKSUM_FILE.relative_to(REPOSITORY_ROOT)}")
    return 0


def read_expected_checksums() -> dict[Path, str]:
    """Read and validate the committed checksum manifest."""
    expected: dict[Path, str] = {}
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if (
            not separator
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(f"Invalid checksum entry: {line!r}")
        expected[Path(filename)] = digest

    if set(expected) != set(DATA_FILES):
        raise ValueError("Checksum manifest must contain exactly the three selected data files.")
    return expected


def verify_checksums() -> int:
    """Compare local files with the committed checksum manifest."""
    if not CHECKSUM_FILE.is_file():
        print(f"MISSING  {CHECKSUM_FILE.relative_to(REPOSITORY_ROOT)}")
        return 1

    try:
        expected = read_expected_checksums()
    except ValueError as error:
        print(f"INVALID  {error}")
        return 1

    failures = 0
    for relative_path in DATA_FILES:
        path = REPOSITORY_ROOT / relative_path
        if not path.is_file():
            print(f"MISSING  {relative_path}")
            failures += 1
            continue

        actual = sha256(path)
        if actual == expected[relative_path]:
            print(f"OK       {relative_path}")
        else:
            print(f"MISMATCH {relative_path}")
            failures += 1

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the committed checksum manifest using the local data files",
    )
    args = parser.parse_args()
    return write_checksums() if args.write else verify_checksums()


if __name__ == "__main__":
    raise SystemExit(main())
