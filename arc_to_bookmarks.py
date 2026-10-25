#!/usr/bin/env python3
"""Export Arc's StorableSidebar.json to a standard bookmarks HTML file that
any browser (Chrome, Firefox, Safari, Edge, Brave, etc.) can import.

Place this script next to StorableSidebar.json and run:
    python3 arc_to_bookmarks.py

Or pass explicit paths:
    python3 arc_to_bookmarks.py /path/to/StorableSidebar.json -o bookmarks.html

The output has one top-level folder per Arc Space, named after that Space.
Inside each Space folder, the original folder nesting and order are preserved
exactly as in StorableSidebar.json, with every root container that belongs to
that Space (however many Arc keeps — pinned, regular, etc.) flattened
directly into it, no extra wrapper subfolder.

Arc's "Top Apps" row (shown identically under every Space, shared rather than
owned by any one of them) is collected into its own top-level folder named
"Arc — Shared Pinned". Anything that still can't be tied to a Space or a
folder goes into a final folder named "Arc — отдельные вкладки".
"""

import argparse
import html
import json
from pathlib import Path
from typing import Any

DEFAULT_INPUT_FILE = Path("StorableSidebar.json")
DEFAULT_OUTPUT_FILE = Path("arc_bookmarks.html")
FALLBACK_FOLDER_TITLE = "Arc — отдельные вкладки"
SHARED_PINNED_FOLDER_TITLE = "Arc — Shared Pinned"
DEFAULT_SPACE_TITLE = "Arc Space"


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


def parse_spaces(raw: Any) -> list[dict[str, Any]]:
    """Like records_from_pairs, but also keeps the pairs-list key as "spaceKey".

    A Space's own "id" field and the key Arc uses to reference that Space
    elsewhere (e.g. an itemContainer's containerType.spaceItems._0) can be
    two different values. spaceKey is the one other records actually point to.
    """
    records: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return records

    i = 0
    while i < len(raw):
        if i + 1 < len(raw) and isinstance(raw[i + 1], dict):
            record = dict(raw[i + 1])
            key = raw[i] if isinstance(raw[i], str) else None
            if key:
                record["spaceKey"] = key
                record.setdefault("id", key)
            records.append(record)
            i += 2
        else:
            i += 1
    return records


def collect_container_index(
    items: list[dict[str, Any]],
) -> tuple[list[str], dict[str, list[str]]]:
    """Find Arc's root containers via their own declared type.

    Each root container (pinned row, regular tab tree, Top Apps, ...) is
    itself a record in sidebar.items with data.itemContainer.containerType
    saying what it is. This is more reliable than a Space's
    containerIDs/newContainerIDs lists: the marker words in those ("pinned",
    "unpinned") don't reliably correspond to meaningful categories, and
    containerIDs in particular isn't consistently ordered/paired.

    Returns (topapps_container_ids, {space_key: [container_id, ...]}).
    """
    topapps_ids: list[str] = []
    spaceitems_by_key: dict[str, list[str]] = {}

    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str):
            continue
        data = item.get("data")
        if not isinstance(data, dict):
            continue
        container = data.get("itemContainer")
        if not isinstance(container, dict):
            continue
        container_type = container.get("containerType")
        if not isinstance(container_type, dict):
            continue

        if "topApps" in container_type:
            topapps_ids.append(item_id)

        space_items = container_type.get("spaceItems")
        if isinstance(space_items, dict):
            space_key = space_items.get("_0")
            if isinstance(space_key, str):
                spaceitems_by_key.setdefault(space_key, []).append(item_id)

    return topapps_ids, spaceitems_by_key


def reorder_by_declared_children(
    children_by_parent: dict[str, list[dict[str, Any]]],
    by_id: dict[str, dict[str, Any]],
) -> None:
    """Reorder each parent's children to match that item's own childrenIds.

    childrenIds is Arc's authoritative ordering — the order its own sidebar
    UI shows. The order items happen to appear in sidebar.items (what
    children_by_parent is built from) does not reliably match it, so without
    this, exported folders can come out in a different order than Arc shows.
    Mutates children_by_parent in place.
    """
    for parent_id, children in children_by_parent.items():
        parent_item = by_id.get(parent_id)
        if parent_item is None:
            continue
        declared_ids = parent_item.get("childrenIds")
        if not isinstance(declared_ids, list) or not declared_ids:
            continue

        by_child_id = {
            child["id"]: child for child in children if isinstance(child.get("id"), str)
        }
        declared_id_set = set(declared_ids)
        ordered = [by_child_id[cid] for cid in declared_ids if cid in by_child_id]
        # Anything not listed in childrenIds (shouldn't normally happen) is
        # still exported, just appended after the declared order.
        leftover = [child for child in children if child.get("id") not in declared_id_set]
        children_by_parent[parent_id] = ordered + leftover


def extract_declared_container_ids(
    space: dict[str, Any], by_id: dict[str, Any]
) -> list[str]:
    """Container ids a Space explicitly lists, in source order.

    Arc mixes marker words ("pinned"/"unpinned") into these lists alongside
    the actual container ids. Rather than rely on their exact pairing (which
    has proven inconsistent across exports), just keep whichever entries are
    actually items in sidebar.items.
    """
    for key in ("newContainerIDs", "containerIDs"):
        raw = space.get(key)
        if not isinstance(raw, list):
            continue
        ids = [entry for entry in raw if isinstance(entry, str) and entry in by_id]
        if ids:
            return ids
    return []


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
            "или укажи путь явно: arc_to_bookmarks.py /путь/к/StorableSidebar.json"
        )

    with input_file.open("r", encoding="utf-8") as file:
        source = json.load(file)

    containers = source.get("sidebar", {}).get("containers", [])
    if len(containers) < 2 or not isinstance(containers[1], dict):
        raise SystemExit("Не удалось найти sidebar.containers[1] в StorableSidebar.json.")

    sidebar = containers[1]
    items = records_from_pairs(sidebar.get("items", []))
    spaces = parse_spaces(sidebar.get("spaces", []))

    if not items:
        raise SystemExit("В sidebar.items не найдены элементы Arc.")

    by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            by_id[item_id] = item

    topapps_container_ids, spaceitems_by_key = collect_container_index(items)

    # Group every item by its raw parentID, regardless of whether that parent
    # is itself a record in sidebar.items — a Space's root containers (e.g. the
    # container holding all of a Space's regular top-level tabs) are often
    # referenced only from sidebar.spaces, not present as their own item.
    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    roots: list[dict[str, Any]] = []
    for item in items:
        parent_id = item.get("parentID")
        if isinstance(parent_id, str) and parent_id:
            children_by_parent.setdefault(parent_id, []).append(item)
        else:
            roots.append(item)
    reorder_by_declared_children(children_by_parent, by_id)

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

    def emit_item(item: dict[str, Any], indent: int) -> None:
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

    def emit_children(container_id: str, indent: int) -> None:
        visited.add(container_id)
        for child in children_by_parent.get(container_id, []):
            emit_item(child, indent)

    # First pass: one top-level folder per Arc Space, so the number of folders
    # under the imported root matches the number of Spaces in Arc. Within each
    # Space folder, every root container belonging to that Space is flattened
    # directly in, preserving each container's own nesting/order as-is.
    used_space_titles: dict[str, int] = {}
    for space in spaces:
        space_title = str(space.get("title") or "").strip() or DEFAULT_SPACE_TITLE
        seen_count = used_space_titles.get(space_title, 0)
        used_space_titles[space_title] = seen_count + 1
        display_title = space_title if seen_count == 0 else f"{space_title} ({seen_count + 1})"

        container_ids = extract_declared_container_ids(space, by_id)
        space_key = space.get("spaceKey") or space.get("id")
        if isinstance(space_key, str):
            for container_id in spaceitems_by_key.get(space_key, []):
                if container_id not in container_ids:
                    container_ids.append(container_id)

        lines.append(f'    <DT><H3>{html.escape(display_title)}</H3>')
        lines.append("    <DL><p>")
        for container_id in container_ids:
            emit_children(container_id, 2)
        lines.append("    </DL><p>")

    # Second pass: Arc's "Top Apps" row is shown identically under every
    # Space, but it isn't owned by any one of them (it's a single shared
    # container, not referenced from any Space's own container list) — give
    # it its own top-level folder instead of letting it leak into the
    # generic fallback folder below.
    for container_id in topapps_container_ids:
        visited.add(container_id)
    if any(children_by_parent.get(cid) for cid in topapps_container_ids):
        lines.append(f'    <DT><H3>{html.escape(SHARED_PINNED_FOLDER_TITLE)}</H3>')
        lines.append("    <DL><p>")
        for container_id in topapps_container_ids:
            emit_children(container_id, 2)
        lines.append("    </DL><p>")

    # Third pass: anything left over at the top level that isn't tied to any
    # Space (e.g. an unusual/legacy record) still keeps its own structure.
    for root in roots:
        root_id = root.get("id")
        if isinstance(root_id, str) and root_id in visited:
            continue
        emit_item(root, 1)

    # Fallback pass: export every URL-bearing tab that was not reached by the
    # tree above, so nothing is silently dropped.
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
    print(f"Spaces найдено: {len(spaces)}")
    print(f"Вкладок со ссылкой найдено: {total_tabs}")
    print(f"Закладок экспортировано: {len(exported_ids) + sum(1 for item in items if not item.get('id') and get_url(item))}")
    print(f"Не вошло в основное дерево и добавлено в отдельную папку: {len(missing_tabs)}")
    print(f"Файл создан: {output_file.resolve()}")
    print("Импорт: в диспетчере закладок твоего браузера выбери «Импортировать закладки» и укажи arc_bookmarks.html")


if __name__ == "__main__":
    main()
