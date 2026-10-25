(function () {
  'use strict';

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const statusEl = document.getElementById('status');
  const themeToggle = document.getElementById('themeToggle');

  const THEME_KEY = 'arcbm-theme';

  // --- theme --------------------------------------------------------

  function currentTheme() {
    const stored = document.documentElement.getAttribute('data-theme');
    if (stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  function applyThemeLabel() {
    const key = currentTheme() === 'dark' ? 'themeToggleLabelToLight' : 'themeToggleLabelToDark';
    themeToggle.setAttribute('aria-label', window.I18N.t(key));
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {
      /* ignore */
    }
    applyThemeLabel();
  }

  function initTheme() {
    let stored = null;
    try {
      stored = localStorage.getItem(THEME_KEY);
    } catch (e) {
      /* ignore */
    }
    if (stored === 'light' || stored === 'dark') {
      document.documentElement.setAttribute('data-theme', stored);
    }
    applyThemeLabel();
  }

  themeToggle.addEventListener('click', () => {
    setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
  });

  // --- language -------------------------------------------------------

  document.querySelectorAll('[data-lang-btn]').forEach((btn) => {
    btn.addEventListener('click', () => {
      window.I18N.setLanguage(btn.getAttribute('data-lang-btn'));
    });
  });

  // --- conversion flow --------------------------------------------------

  let lastResult = null; // { fileBaseName, html, stats } — re-rendered on language change

  function clearStatus() {
    statusEl.innerHTML = '';
    lastResult = null;
  }

  function showMessage(kind, text) {
    const div = document.createElement('div');
    div.className = `msg ${kind}`;
    div.textContent = text;
    statusEl.appendChild(div);
  }

  function statRow(label, value) {
    return `<tr><td>${label}</td><td>${value}</td></tr>`;
  }

  function renderResult(fileBaseName, html, stats) {
    statusEl.innerHTML = '';
    const t = window.I18N.t;

    if (stats.missingCount > 0) {
      showMessage('warn', t('missingTabs', stats.missingCount));
    } else {
      showMessage('ok', t('convertedOk'));
    }

    const table = document.createElement('table');
    table.className = 'stats';
    table.innerHTML = [
      statRow(t('statItemsParsed'), stats.totalItems.toLocaleString()),
      statRow(t('statSpacesFound'), stats.spacesFound.toLocaleString()),
      statRow(t('statTabsFound'), stats.tabsFound.toLocaleString()),
      statRow(t('statBookmarksExported'), stats.exportedCount.toLocaleString()),
    ].join('');
    statusEl.appendChild(table);

    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const baseName = fileBaseName.replace(/\.json$/i, '').trim();
    const outName = (baseName ? `${baseName}_bookmarks` : 'arc_bookmarks') + '.html';

    const actions = document.createElement('div');
    actions.className = 'actions';

    const downloadLink = document.createElement('a');
    downloadLink.className = 'btn';
    downloadLink.href = url;
    downloadLink.download = outName;
    downloadLink.textContent = t('downloadButton', outName);
    actions.appendChild(downloadLink);

    const resetBtn = document.createElement('button');
    resetBtn.className = 'btn btn-secondary';
    resetBtn.type = 'button';
    resetBtn.textContent = t('convertAnother');
    resetBtn.addEventListener('click', () => {
      clearStatus();
      fileInput.value = '';
    });
    actions.appendChild(resetBtn);

    statusEl.appendChild(actions);
  }

  function showResult(fileBaseName, html, stats) {
    lastResult = { fileBaseName, html, stats };
    renderResult(fileBaseName, html, stats);
  }

  window.I18N.onLanguageChange(() => {
    applyThemeLabel();
    if (lastResult) {
      renderResult(lastResult.fileBaseName, lastResult.html, lastResult.stats);
    }
  });

  function handleFile(file) {
    clearStatus();
    if (!file) return;
    const t = window.I18N.t;

    if (!/\.json$/i.test(file.name)) {
      showMessage('warn', t('warnNotJson'));
    }

    const reader = new FileReader();
    reader.onerror = () => {
      showMessage('err', t('errCouldNotRead'));
    };
    reader.onload = () => {
      let source;
      try {
        source = JSON.parse(reader.result);
      } catch (err) {
        showMessage('err', t('errInvalidJson'));
        return;
      }

      try {
        const { html, stats } = window.ArcBookmarksConverter.convertArcSidebarToBookmarksHtml(source);
        showResult(file.name, html, stats);
      } catch (err) {
        if (err instanceof window.ArcBookmarksConverter.ArcFormatError) {
          const key = err.code === 'NO_ITEMS' ? 'errNoItems' : 'errNotArcFile';
          showMessage('err', t(key));
        } else {
          showMessage('err', t('errUnexpected', err.message));
          console.error(err);
        }
      }
    };
    reader.readAsText(file);
  }

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', () => {
    handleFile(fileInput.files[0]);
  });

  ['dragenter', 'dragover'].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });
  dropzone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    handleFile(file);
  });

  initTheme();
  window.I18N.init();
})();
