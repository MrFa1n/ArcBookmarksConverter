#!/usr/bin/env python3
"""Export Arc's StorableSidebar.json to Chrome-importable bookmarks HTML.

Place this script next to StorableSidebar.json and run:
    python3 arc_to_chrome.py

Or pass explicit paths:
    python3 arc_to_chrome.py /path/to/StorableSidebar.json -o bookmarks.html

Regular Arc folders are preserved where the parent/child relationships are available.
Any tabs missed by the folder traversal (including pinned tabs that are not inside a
folder) are collected into a final folder named "Arc — отдельные и закреплённые вкладки".
"""

import argparse
import html
import json
from pathlib import Path
from typing import Any

DEFAULT_INPUT_FILE = Path("StorableSidebar.json")
DEFAULT_OUTPUT_FILE = Path("arc_bookmarks.html")
FALLBACK_FOLDER_TITLE = "Arc — отдельные и закреплённые вкладки"


def records_from_pairs(value: Any) -> list[dict[str, Any]]:
    """Arc stores many collections as alternating [key, object, key, object, ...]."""
    records: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return records

    i = 0
    while i < len(value):
        if i + 1 < len(value) and isinstance(value[i + 1], dict):
            record = dict(value[i + 1])
            if not record.get("id") and isinstance(value[i], str):
                record["id"] = value[i]
            records.append(record)
            i += 2
        else:
            i += 1
    return records


def get_tab_data(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data")
    if not isinstance(data, dict):
        return {}
    tab = data.get("tab")
    return tab if isinstance(tab, dict) else {}


def get_url(item: dict[str, Any]) -> str | None:
    tab = get_tab_data(item)
    url = tab.get("savedURL")
    if not isinstance(url, str) or not url.strip():
        return None
    return url.strip()


def get_title(item: dict[str, Any]) -> str:
    tab = get_tab_data(item)
    title = tab.get("savedTitle") or item.get("title") or get_url(item) or "Без названия"
    return str(title).strip() or "Без названия"


def escape_attr(value: str) -> str:
    return html.escape(value, quote=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help=f"Path to Arc's StorableSidebar.json (default: {DEFAULT_INPUT_FILE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Path to write the Netscape bookmarks HTML file (default: {DEFAULT_OUTPUT_FILE})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_file: Path = args.input
    output_file: Path = args.output

    if not input_file.exists():
        raise SystemExit(
            f"Не найден файл {input_file}. Положи StorableSidebar.json рядом со скриптом "
            "или укажи путь явно: arc_to_chrome.py /путь/к/StorableSidebar.json"
        )

    with input_file.open("r", encoding="utf-8") as file:
        source = json.load(file)

    containers = source.get("sidebar", {}).get("containers", [])
    if len(containers) < 2 or not isinstance(containers[1], dict):
        raise SystemExit("Не удалось найти sidebar.containers[1] в StorableSidebar.json.")

    sidebar = containers[1]
    items = records_from_pairs(sidebar.get("items", []))
    spaces = records_from_pairs(sidebar.get("spaces", []))

    if not items:
        raise SystemExit("В sidebar.items не найдены элементы Arc.")

    by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            by_id[item_id] = item

    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    roots: list[dict[str, Any]] = []
    for item in items:
        parent_id = item.get("parentID")
        if isinstance(parent_id, str) and parent_id in by_id:
            children_by_parent.setdefault(parent_id, []).append(item)
        else:
            roots.append(item)

    # Use space/container names where parent IDs correspond to a space container.
    container_to_space: dict[str, str] = {}
    for space in spaces:
        space_title = str(space.get("title") or "Arc")
        for container_id in space.get("containerIDs", []):
            if isinstance(container_id, str):
                container_to_space[container_id] = space_title

    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Arc bookmarks</TITLE>",
        "<H1>Arc bookmarks</H1>",
        "<DL><p>",
    ]
    exported_ids: set[str] = set()
    exported_urls: set[tuple[str, str]] = set()
    visited: set[str] = set()

    def emit_bookmark(item: dict[str, Any], indent: int) -> bool:
        url = get_url(item)
        if not url:
            return False
        item_id = item.get("id")
        title = get_title(item)
        # Deduplicate by ID first; URL+title is a fallback for records without IDs.
        if isinstance(item_id, str) and item_id in exported_ids:
            return False
        key = (title, url)
        if not item_id and key in exported_urls:
            return False
        prefix = "    " * indent
        lines.append(f'{prefix}<DT><A HREF="{escape_attr(url)}">{html.escape(title)}</A>')
        if isinstance(item_id, str):
            exported_ids.add(item_id)
        exported_urls.add(key)
        return True

    def emit_item(item: dict[str, Any], indent: int = 1) -> None:
        item_id = item.get("id")
        if isinstance(item_id, str):
            if item_id in visited:
                return
            visited.add(item_id)

        if get_url(item):
            emit_bookmark(item, indent)
            # A URL-bearing item is a tab, not a folder; still don't drop any children
            # if an unusual Arc record has both a URL and child IDs.
            descendants = children_by_parent.get(str(item_id), []) if item_id else []
            if descendants:
                for child in descendants:
                    emit_item(child, indent)
            return

        descendants = children_by_parent.get(str(item_id), []) if item_id else []
        is_folder = bool(descendants) or isinstance(item.get("data", {}).get("list"), dict)
        if is_folder:
            title = str(item.get("title") or "Папка Arc")
            prefix = "    " * indent
            lines.append(f"{prefix}<DT><H3>{html.escape(title)}</H3>")
            lines.append(f"{prefix}<DL><p>")
            for child in descendants:
                emit_item(child, indent + 1)
            lines.append(f"{prefix}</DL><p>")

    # First pass: preserve the hierarchy represented by parentID.
    for root in roots:
        emit_item(root)

    # Fallback pass: export every URL-bearing tab that was not reached by the tree.
    # This is what captures pinned/standalone tabs whose parent is a virtual Arc
    # container rather than another record in sidebar.items.
    missing_tabs = [
        item for item in items
        if get_url(item)
        and not (isinstance(item.get("id"), str) and item.get("id") in exported_ids)
    ]
    if missing_tabs:
        lines.append(f'    <DT><H3>{html.escape(FALLBACK_FOLDER_TITLE)}</H3>')
        lines.append("    <DL><p>")
        for item in missing_tabs:
            emit_bookmark(item, 2)
        lines.append("    </DL><p>")

    lines.append("</DL><p>")
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    total_tabs = sum(1 for item in items if get_url(item))
    print(f"Элементов Arc в списке: {len(items)}")
    print(f"Вкладок со ссылкой найдено: {total_tabs}")
    print(f"Закладок экспортировано: {len(exported_ids) + sum(1 for item in items if not item.get('id') and get_url(item))}")
    print(f"Не вошло в основное дерево и добавлено в отдельную папку: {len(missing_tabs)}")
    print(f"Файл создан: {output_file.resolve()}")
    print("Импорт в Chrome: Диспетчер закладок → меню ⋮ → Импортировать закладки → arc_bookmarks.html")


if __name__ == "__main__":
    main()
