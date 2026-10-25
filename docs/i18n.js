/**
 * Minimal i18n: EN/RU strings for the static page (data-i18n attributes)
 * plus a small t() API that app.js uses for dynamically generated text.
 *
 * The literal folder names arc-converter.js writes into the OUTPUT bookmarks
 * file ("Arc — Shared Pinned", "Arc — отдельные вкладки") are NOT
 * translated here — they match arc_to_chrome.py's output regardless of the
 * page's UI language, so the web and CLI versions always produce identical
 * files.
 */
(function (global) {
  'use strict';

  const STORAGE_KEY = 'arc2chrome-lang';

  const STRINGS = {
    en: {
      subtitle:
        "Turn Arc's <code>StorableSidebar.json</code> into a bookmarks file any browser can import — one folder per Space, nesting and order preserved.",
      privacyNote:
        'Everything happens locally in your browser. Your file is never uploaded anywhere — this page has no server and makes no network requests with your data. (<a href="https://github.com/MrFa1n/ArcToHtml" target="_blank" rel="noopener">source on GitHub</a>, verify for yourself.)',
      dropzoneTitle: 'Drop <code>StorableSidebar.json</code> here or click to choose a file',
      dropzoneHint: "On macOS it's usually at ~/Library/Application Support/Arc/StorableSidebar.json",
      dropzoneAriaLabel: 'Choose or drop StorableSidebar.json',
      howtoSummary: 'How to import the result into Chrome',
      howtoSteps: [
        'Open <code>chrome://bookmarks</code>',
        'Click the ⋮ menu in the top right',
        'Choose <em>Import bookmarks</em> and pick the downloaded file',
        'Your Spaces show up as folders under "Imported"',
      ],
      footer:
        '<a href="https://github.com/MrFa1n/ArcToHtml">ArcToHtml</a> · Apache License 2.0 · runs the same conversion as the <a href="https://github.com/MrFa1n/ArcToHtml/blob/main/arc_to_chrome.py">Python CLI</a>',
      themeToggleLabelToLight: 'Switch to light theme',
      themeToggleLabelToDark: 'Switch to dark theme',
      langToggleLabel: 'Language',

      convertedOk: 'Converted successfully.',
      missingTabs: (n) =>
        `${n} tab(s) couldn’t be placed in the tree and were collected into the "Arc — отдельные вкладки" folder instead.`,
      statItemsParsed: 'Arc items parsed',
      statSpacesFound: 'Spaces found',
      statTabsFound: 'Tabs with a URL',
      statBookmarksExported: 'Bookmarks exported',
      downloadButton: (name) => `Download ${name}`,
      convertAnother: 'Convert another file',
      warnNotJson: 'That doesn’t look like a .json file — trying anyway.',
      errCouldNotRead: 'Could not read that file.',
      errInvalidJson: 'That file isn’t valid JSON. Make sure you picked StorableSidebar.json itself.',
      errUnexpected: (msg) => `Unexpected error while converting: ${msg}`,
      errNotArcFile:
        'This doesn’t look like an Arc StorableSidebar.json file (missing sidebar.containers[1]).',
      errNoItems: 'No Arc items found in this file (sidebar.items is empty).',
    },
    ru: {
      subtitle:
        'Превращает <code>StorableSidebar.json</code> из Arc в файл закладок, который понимает любой браузер — по папке на каждый Space, со всей вложенностью и порядком.',
      privacyNote:
        'Всё происходит локально в браузере. Файл никуда не загружается — у страницы нет сервера, и ваши данные никуда не отправляются по сети. (<a href="https://github.com/MrFa1n/ArcToHtml" target="_blank" rel="noopener">исходный код на GitHub</a> — можно проверить самостоятельно.)',
      dropzoneTitle: 'Перетащите сюда <code>StorableSidebar.json</code> или нажмите, чтобы выбрать файл',
      dropzoneHint: 'На macOS он обычно лежит тут: ~/Library/Application Support/Arc/StorableSidebar.json',
      dropzoneAriaLabel: 'Выбрать или перетащить StorableSidebar.json',
      howtoSummary: 'Как импортировать результат в Chrome',
      howtoSteps: [
        'Откройте <code>chrome://bookmarks</code>',
        'Нажмите на меню ⋮ в правом верхнем углу',
        'Выберите <em>Импортировать закладки</em> и укажите скачанный файл',
        'Ваши Spaces появятся папками внутри «Imported»',
      ],
      footer:
        '<a href="https://github.com/MrFa1n/ArcToHtml">ArcToHtml</a> · Apache License 2.0 · та же логика, что и в <a href="https://github.com/MrFa1n/ArcToHtml/blob/main/arc_to_chrome.py">Python CLI</a>',
      themeToggleLabelToLight: 'Переключить на светлую тему',
      themeToggleLabelToDark: 'Переключить на тёмную тему',
      langToggleLabel: 'Язык',

      convertedOk: 'Готово — конвертация прошла успешно.',
      missingTabs: (n) =>
        `Не удалось вписать в дерево вкладок: ${n} — они помещены в папку «Arc — отдельные вкладки».`,
      statItemsParsed: 'Элементов Arc разобрано',
      statSpacesFound: 'Найдено Spaces',
      statTabsFound: 'Вкладок со ссылкой',
      statBookmarksExported: 'Закладок экспортировано',
      downloadButton: (name) => `Скачать ${name}`,
      convertAnother: 'Конвертировать другой файл',
      warnNotJson: 'Это не похоже на .json-файл — всё равно пробуем.',
      errCouldNotRead: 'Не удалось прочитать файл.',
      errInvalidJson: 'Файл не является корректным JSON. Убедитесь, что выбрали именно StorableSidebar.json.',
      errUnexpected: (msg) => `Неожиданная ошибка при конвертации: ${msg}`,
      errNotArcFile: 'Это не похоже на StorableSidebar.json от Arc (не найден sidebar.containers[1]).',
      errNoItems: 'В файле не найдено элементов Arc (sidebar.items пуст).',
    },
  };

  function detectDefaultLang() {
    const nav = (global.navigator && global.navigator.language) || 'en';
    return nav.toLowerCase().startsWith('ru') ? 'ru' : 'en';
  }

  let currentLang = null;
  const listeners = [];

  function applyStaticStrings(lang) {
    const dict = STRINGS[lang];
    document.documentElement.lang = lang;

    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (Object.prototype.hasOwnProperty.call(dict, key) && typeof dict[key] === 'string') {
        el.innerHTML = dict[key];
      }
    });

    document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
      // format: "attrName:key"
      el.getAttribute('data-i18n-attr')
        .split(',')
        .forEach((pair) => {
          const [attr, key] = pair.split(':').map((s) => s.trim());
          if (dict[key]) el.setAttribute(attr, dict[key]);
        });
    });

    const stepsList = document.getElementById('howtoSteps');
    if (stepsList) {
      stepsList.innerHTML = dict.howtoSteps.map((s) => `<li>${s}</li>`).join('');
    }

    document.querySelectorAll('[data-lang-btn]').forEach((btn) => {
      const isActive = btn.getAttribute('data-lang-btn') === lang;
      btn.setAttribute('aria-pressed', String(isActive));
    });
  }

  function setLanguage(lang) {
    if (!STRINGS[lang]) lang = 'en';
    currentLang = lang;
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) {
      /* ignore (private mode, etc.) */
    }
    applyStaticStrings(lang);
    listeners.forEach((fn) => fn(lang));
  }

  function getLang() {
    return currentLang || detectDefaultLang();
  }

  function t(key, ...args) {
    const dict = STRINGS[getLang()] || STRINGS.en;
    const value = dict[key];
    if (typeof value === 'function') return value(...args);
    return value != null ? value : key;
  }

  function onLanguageChange(fn) {
    listeners.push(fn);
  }

  function init() {
    let stored = null;
    try {
      stored = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      /* ignore */
    }
    setLanguage(stored && STRINGS[stored] ? stored : detectDefaultLang());
  }

  global.I18N = { setLanguage, getLang, t, onLanguageChange, init };
})(typeof window !== 'undefined' ? window : globalThis);
