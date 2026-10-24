#!/usr/bin/env python3
"""Redact Arc's StorableSidebar.json before sharing it (e.g. in a bug report).

Replaces URLs, titles, and other identifying values (IDs, emails, tokens, ...)
with predictable placeholders, while keeping the JSON structure intact. This
is handy for producing a safe sample fixture for examples/ or for attaching
to an issue.

Usage:
    python3 tools/sanitize_arc.py StorableSidebar.json -o StorableSidebar.sanitized.json

Always double-check the output by hand before sharing it — this is a
best-effort filter, not a guarantee.
"""

import argparse
import json
import re
from pathlib import Path

# Значения этих полей заменяем независимо от регистра ключа.
URL_KEYS = {
    "url", "savedurl", "originalurl", "targeturl",
    "faviconurl", "sourceurl", "canonicalurl",
}
TITLE_KEYS = {
    "title", "savedtitle", "name", "displayname",
    "description", "subtitle",
}
SENSITIVE_KEY_PARTS = {
    "id", "uuid", "guid", "token", "cookie", "password",
    "email", "username", "account", "profile", "path", "device",
}


class Sanitizer:
    """Replaces sensitive values with placeholders.

    The same original value always maps to the same placeholder (per
    category), so structural links such as id -> parentID are preserved in
    the sanitized output instead of being scrambled into mismatched IDs.
    """

    def __init__(self) -> None:
        self._url_map: dict[str, str] = {}
        self._title_map: dict[str, str] = {}
        self._id_map: dict[str, str] = {}

    @property
    def url_counter(self) -> int:
        return len(self._url_map)

    @property
    def title_counter(self) -> int:
        return len(self._title_map)

    @property
    def id_counter(self) -> int:
        return len(self._id_map)

    def _lookup(self, mapping: dict[str, str], value: str, make_placeholder) -> str:
        placeholder = mapping.get(value)
        if placeholder is None:
            placeholder = make_placeholder(len(mapping) + 1)
            mapping[value] = placeholder
        return placeholder

    def sanitize(self, value, key=""):
        normalized = key.lower()

        if isinstance(value, dict):
            return {k: self.sanitize(v, k) for k, v in value.items()}

        if isinstance(value, list):
            result = []
            for index, item in enumerate(value):
                if (
                    isinstance(item, str)
                    and index + 1 < len(value)
                    and isinstance(value[index + 1], dict)
                ):
                    # Arc encodes many collections as alternating
                    # [id, object, id, object, ...] — this string plays the
                    # same role as a dict's "id" field even though it isn't
                    # nested under that key name, so it needs the same
                    # redaction. Without this, these ids inherit the parent
                    # list's own key (e.g. "spaces", "items"), which doesn't
                    # match the sensitive-key check below and leaks through.
                    result.append(
                        self._lookup(self._id_map, item, lambda n: f"REDACTED_VALUE_{n}")
                    )
                else:
                    result.append(self.sanitize(item, key))
            return result

        if not isinstance(value, str):
            return value

        if normalized in URL_KEYS or normalized.endswith("url"):
            return self._lookup(self._url_map, value, lambda n: f"https://example.com/page{n}")

        if normalized in TITLE_KEYS or normalized.endswith("title"):
            return self._lookup(self._title_map, value, lambda n: f"REDACTED_TITLE_{n}")

        if any(part in normalized for part in SENSITIVE_KEY_PARTS):
            return self._lookup(self._id_map, value, lambda n: f"REDACTED_VALUE_{n}")

        # На случай, если URL или email лежит в другом текстовом поле.
        value = re.sub(
            r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
            "REDACTED_EMAIL",
            value,
        )

        value = re.sub(
            r"https?://\S+|www\.\S+",
            "REDACTED_URL",
            value,
            flags=re.IGNORECASE,
        )

        return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the JSON file to sanitize")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Path to write the sanitized JSON file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.source.is_file():
        raise SystemExit(f"Не найден файл: {args.source.resolve()}")

    data = json.loads(args.source.read_text(encoding="utf-8"))
    sanitizer = Sanitizer()
    cleaned = sanitizer.sanitize(data)

    args.output.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Создан файл: {args.output.resolve()}")
    print(f"Заменено URL: {sanitizer.url_counter}")
    print(f"Заменено названий: {sanitizer.title_counter}")
    print(f"Заменено чувствительных значений: {sanitizer.id_counter}")
    print("Перед отправкой проверь файл вручную.")


if __name__ == "__main__":
    main()
