/**
 * Arc StorableSidebar.json -> Netscape bookmarks HTML, in pure client-side JS.
 *
 * This is a line-for-line port of arc_to_bookmarks.py at the repo root — keep
 * the two in sync. See that file's docstrings for why each step exists
 * (containers identified by data.itemContainer.containerType rather than
 * marker words, childrenIds as the authoritative order, Top Apps handling,
 * the Space pairs-list key vs its own "id" field, etc).
 */
(function (global) {
  'use strict';

  const FALLBACK_FOLDER_TITLE = 'Arc — отдельные вкладки';
  const SHARED_PINNED_FOLDER_TITLE = 'Arc — Shared Pinned';
  const DEFAULT_SPACE_TITLE = 'Arc Space';
  const NO_TITLE = 'Без названия';
  const NO_FOLDER_TITLE = 'Папка Arc';

  function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
  }

  // Arc stores many collections as alternating [key, object, key, object, ...].
  function recordsFromPairs(value) {
    const records = [];
    if (!Array.isArray(value)) return records;
    let i = 0;
    while (i < value.length) {
      if (i + 1 < value.length && isPlainObject(value[i + 1])) {
        const record = Object.assign({}, value[i + 1]);
        if (!record.id && typeof value[i] === 'string') {
          record.id = value[i];
        }
        records.push(record);
        i += 2;
      } else {
        i += 1;
      }
    }
    return records;
  }

  // Like recordsFromPairs, but also keeps the pairs-list key as "spaceKey":
  // a Space's own "id" field and the key Arc uses to reference that Space
  // elsewhere (e.g. an itemContainer's containerType.spaceItems._0) can be
  // two different values. spaceKey is the one other records actually point to.
  function parseSpaces(raw) {
    const records = [];
    if (!Array.isArray(raw)) return records;
    let i = 0;
    while (i < raw.length) {
      if (i + 1 < raw.length && isPlainObject(raw[i + 1])) {
        const record = Object.assign({}, raw[i + 1]);
        const key = typeof raw[i] === 'string' ? raw[i] : null;
        if (key) {
          record.spaceKey = key;
          if (!record.id) record.id = key;
        }
        records.push(record);
        i += 2;
      } else {
        i += 1;
      }
    }
    return records;
  }

  // Find Arc's root containers via their own declared type
  // (data.itemContainer.containerType) rather than a Space's
  // containerIDs/newContainerIDs marker words, which have proven unreliable.
  // Returns { topAppsIds, spaceItemsByKey: Map<spaceKey, containerId[]> }.
  function collectContainerIndex(items) {
    const topAppsIds = [];
    const spaceItemsByKey = new Map();

    for (const item of items) {
      const itemId = item.id;
      if (typeof itemId !== 'string') continue;
      const data = item.data;
      if (!isPlainObject(data)) continue;
      const container = data.itemContainer;
      if (!isPlainObject(container)) continue;
      const containerType = container.containerType;
      if (!isPlainObject(containerType)) continue;

      if (Object.prototype.hasOwnProperty.call(containerType, 'topApps')) {
        topAppsIds.push(itemId);
      }

      const spaceItems = containerType.spaceItems;
      if (isPlainObject(spaceItems)) {
        const spaceKey = spaceItems._0;
        if (typeof spaceKey === 'string') {
          if (!spaceItemsByKey.has(spaceKey)) spaceItemsByKey.set(spaceKey, []);
          spaceItemsByKey.get(spaceKey).push(itemId);
        }
      }
    }

    return { topAppsIds, spaceItemsByKey };
  }

  // childrenIds is Arc's authoritative ordering — the order its own sidebar
  // UI shows. The order items happen to appear in sidebar.items (what
  // childrenByParent is built from) does not reliably match it. Mutates
  // childrenByParent in place.
  function reorderByDeclaredChildren(childrenByParent, byId) {
    for (const [parentId, children] of childrenByParent.entries()) {
      const parentItem = byId.get(parentId);
      if (!parentItem) continue;
      const declaredIds = parentItem.childrenIds;
      if (!Array.isArray(declaredIds) || declaredIds.length === 0) continue;

      const byChildId = new Map();
      for (const child of children) {
        if (typeof child.id === 'string') byChildId.set(child.id, child);
      }
      const declaredSet = new Set(declaredIds);
      const ordered = [];
      for (const cid of declaredIds) {
        if (byChildId.has(cid)) ordered.push(byChildId.get(cid));
      }
      // Anything not listed in childrenIds (shouldn't normally happen) is
      // still exported, just appended after the declared order.
      const leftover = children.filter((child) => !declaredSet.has(child.id));
      childrenByParent.set(parentId, ordered.concat(leftover));
    }
  }

  // Container ids a Space explicitly lists, in source order. Arc mixes
  // marker words ("pinned"/"unpinned") into these lists alongside the
  // actual container ids; rather than rely on their exact pairing (which
  // has proven inconsistent across exports), just keep whichever entries
  // are actually items in sidebar.items.
  function extractDeclaredContainerIds(space, byId) {
    for (const key of ['newContainerIDs', 'containerIDs']) {
      const raw = space[key];
      if (!Array.isArray(raw)) continue;
      const ids = raw.filter((entry) => typeof entry === 'string' && byId.has(entry));
      if (ids.length) return ids;
    }
    return [];
  }

  function getTabData(item) {
    const data = item.data;
    if (!isPlainObject(data)) return {};
    const tab = data.tab;
    return isPlainObject(tab) ? tab : {};
  }

  function getUrl(item) {
    const tab = getTabData(item);
    const url = tab.savedURL;
    if (typeof url !== 'string' || !url.trim()) return null;
    return url.trim();
  }

  function getTitle(item) {
    const tab = getTabData(item);
    const title = tab.savedTitle || item.title || getUrl(item) || NO_TITLE;
    const str = String(title).trim();
    return str || NO_TITLE;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/"/g, '&quot;');
  }

  // `code` is a stable, language-independent identifier the UI can use to
  // show a localized message (see i18n.js); `message` stays in English for
  // anyone using this module directly (console, tests, non-UI contexts).
  class ArcFormatError extends Error {
    constructor(message, code) {
      super(message);
      this.code = code;
    }
  }

  /**
   * @param {object} source - parsed StorableSidebar.json
   * @returns {{html: string, stats: object}}
   */
  function convertArcSidebarToBookmarksHtml(source) {
    const containers =
      (source && source.sidebar && source.sidebar.containers) || [];
    if (!Array.isArray(containers) || containers.length < 2 || !isPlainObject(containers[1])) {
      throw new ArcFormatError(
        'Could not find sidebar.containers[1] — this doesn’t look like an Arc StorableSidebar.json file.',
        'NOT_ARC_FILE'
      );
    }

    const sidebar = containers[1];
    const items = recordsFromPairs(sidebar.items || []);
    const spaces = parseSpaces(sidebar.spaces || []);

    if (!items.length) {
      throw new ArcFormatError('No Arc items found in sidebar.items.', 'NO_ITEMS');
    }

    const byId = new Map();
    for (const item of items) {
      if (typeof item.id === 'string' && item.id) byId.set(item.id, item);
    }

    const { topAppsIds, spaceItemsByKey } = collectContainerIndex(items);

    // Group every item by its raw parentID, regardless of whether that
    // parent is itself a record in sidebar.items — a Space's root
    // containers are often referenced only from sidebar.spaces, not
    // present as their own item.
    const childrenByParent = new Map();
    const roots = [];
    for (const item of items) {
      const parentId = item.parentID;
      if (typeof parentId === 'string' && parentId) {
        if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, []);
        childrenByParent.get(parentId).push(item);
      } else {
        roots.push(item);
      }
    }
    reorderByDeclaredChildren(childrenByParent, byId);

    const lines = [
      '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
      '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
      '<TITLE>Arc bookmarks</TITLE>',
      '<H1>Arc bookmarks</H1>',
      '<DL><p>',
    ];
    const exportedIds = new Set();
    const exportedUrls = new Set();
    const visited = new Set();

    function emitBookmark(item, indent) {
      const url = getUrl(item);
      if (!url) return false;
      const itemId = item.id;
      const title = getTitle(item);
      // Deduplicate by ID first; URL+title is a fallback for records without IDs.
      if (typeof itemId === 'string' && exportedIds.has(itemId)) return false;
      const key = title + '\u0000' + url;
      if (!itemId && exportedUrls.has(key)) return false;
      const prefix = '    '.repeat(indent);
      lines.push(`${prefix}<DT><A HREF="${escapeAttr(url)}">${escapeHtml(title)}</A>`);
      if (typeof itemId === 'string') exportedIds.add(itemId);
      exportedUrls.add(key);
      return true;
    }

    function emitItem(item, indent) {
      const itemId = item.id;
      if (typeof itemId === 'string') {
        if (visited.has(itemId)) return;
        visited.add(itemId);
      }

      if (getUrl(item)) {
        emitBookmark(item, indent);
        // A URL-bearing item is a tab, not a folder; still don't drop any
        // children if an unusual Arc record has both a URL and child IDs.
        const descendants = itemId ? childrenByParent.get(itemId) || [] : [];
        for (const child of descendants) emitItem(child, indent);
        return;
      }

      const descendants = itemId ? childrenByParent.get(itemId) || [] : [];
      const data = item.data;
      const isFolder = descendants.length > 0 || (isPlainObject(data) && isPlainObject(data.list));
      if (isFolder) {
        const title = String(item.title || NO_FOLDER_TITLE);
        const prefix = '    '.repeat(indent);
        lines.push(`${prefix}<DT><H3>${escapeHtml(title)}</H3>`);
        lines.push(`${prefix}<DL><p>`);
        for (const child of descendants) emitItem(child, indent + 1);
        lines.push(`${prefix}</DL><p>`);
      }
    }

    function emitChildren(containerId, indent) {
      visited.add(containerId);
      const children = childrenByParent.get(containerId) || [];
      for (const child of children) emitItem(child, indent);
    }

    // First pass: one top-level folder per Arc Space, so the number of
    // folders under the imported root matches the number of Spaces in Arc.
    // Within each Space folder, every root container belonging to that
    // Space is flattened directly in, preserving each container's own
    // nesting/order as-is.
    const usedSpaceTitles = new Map();
    for (const space of spaces) {
      const spaceTitle = String(space.title || '').trim() || DEFAULT_SPACE_TITLE;
      const seenCount = usedSpaceTitles.get(spaceTitle) || 0;
      usedSpaceTitles.set(spaceTitle, seenCount + 1);
      const displayTitle = seenCount === 0 ? spaceTitle : `${spaceTitle} (${seenCount + 1})`;

      const containerIds = extractDeclaredContainerIds(space, byId);
      const spaceKey = space.spaceKey || space.id;
      if (typeof spaceKey === 'string') {
        for (const containerId of spaceItemsByKey.get(spaceKey) || []) {
          if (!containerIds.includes(containerId)) containerIds.push(containerId);
        }
      }

      lines.push(`    <DT><H3>${escapeHtml(displayTitle)}</H3>`);
      lines.push('    <DL><p>');
      for (const containerId of containerIds) emitChildren(containerId, 2);
      lines.push('    </DL><p>');
    }

    // Second pass: Arc's "Top Apps" row is shown identically under every
    // Space, but it isn't owned by any one of them — give it its own
    // top-level folder instead of letting it leak into the generic
    // fallback folder below.
    for (const containerId of topAppsIds) visited.add(containerId);
    if (topAppsIds.some((cid) => (childrenByParent.get(cid) || []).length > 0)) {
      lines.push(`    <DT><H3>${escapeHtml(SHARED_PINNED_FOLDER_TITLE)}</H3>`);
      lines.push('    <DL><p>');
      for (const containerId of topAppsIds) emitChildren(containerId, 2);
      lines.push('    </DL><p>');
    }

    // Third pass: anything left over at the top level that isn't tied to
    // any Space (e.g. an unusual/legacy record) still keeps its own structure.
    for (const root of roots) {
      const rootId = root.id;
      if (typeof rootId === 'string' && visited.has(rootId)) continue;
      emitItem(root, 1);
    }

    // Fallback pass: export every URL-bearing tab that was not reached by
    // the tree above, so nothing is silently dropped.
    const missingTabs = items.filter(
      (item) => getUrl(item) && !(typeof item.id === 'string' && exportedIds.has(item.id))
    );
    if (missingTabs.length) {
      lines.push(`    <DT><H3>${escapeHtml(FALLBACK_FOLDER_TITLE)}</H3>`);
      lines.push('    <DL><p>');
      for (const item of missingTabs) emitBookmark(item, 2);
      lines.push('    </DL><p>');
    }

    lines.push('</DL><p>');
    const htmlOutput = lines.join('\n') + '\n';

    const totalTabs = items.filter((item) => getUrl(item)).length;
    const exportedCount =
      exportedIds.size + items.filter((item) => !item.id && getUrl(item)).length;

    const stats = {
      totalItems: items.length,
      spacesFound: spaces.length,
      tabsFound: totalTabs,
      exportedCount,
      missingCount: missingTabs.length,
    };

    return { html: htmlOutput, stats };
  }

  const api = { convertArcSidebarToBookmarksHtml, ArcFormatError };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  global.ArcBookmarksConverter = api;
})(typeof window !== 'undefined' ? window : globalThis);
