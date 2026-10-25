(function () {
  'use strict';

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const statusEl = document.getElementById('status');

  function clearStatus() {
    statusEl.innerHTML = '';
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

  function showResult(fileBaseName, html, stats) {
    clearStatus();

    if (stats.missingCount > 0) {
      showMessage(
        'warn',
        `${stats.missingCount} tab(s) couldn't be placed in the tree and were collected into the "Arc — отдельные вкладки" folder instead.`
      );
    } else {
      showMessage('ok', 'Converted successfully.');
    }

    const table = document.createElement('table');
    table.className = 'stats';
    table.innerHTML = [
      statRow('Arc items parsed', stats.totalItems.toLocaleString()),
      statRow('Spaces found', stats.spacesFound.toLocaleString()),
      statRow('Tabs with a URL', stats.tabsFound.toLocaleString()),
      statRow('Bookmarks exported', stats.exportedCount.toLocaleString()),
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
    downloadLink.textContent = `Download ${outName}`;
    actions.appendChild(downloadLink);

    const resetBtn = document.createElement('button');
    resetBtn.className = 'btn btn-secondary';
    resetBtn.type = 'button';
    resetBtn.textContent = 'Convert another file';
    resetBtn.addEventListener('click', () => {
      clearStatus();
      fileInput.value = '';
    });
    actions.appendChild(resetBtn);

    statusEl.appendChild(actions);
  }

  function handleFile(file) {
    clearStatus();
    if (!file) return;

    if (!/\.json$/i.test(file.name)) {
      showMessage('warn', 'That doesn’t look like a .json file — trying anyway.');
    }

    const reader = new FileReader();
    reader.onerror = () => {
      showMessage('err', 'Could not read that file.');
    };
    reader.onload = () => {
      let source;
      try {
        source = JSON.parse(reader.result);
      } catch (err) {
        showMessage('err', 'That file isn’t valid JSON. Make sure you picked StorableSidebar.json itself.');
        return;
      }

      try {
        const { html, stats } = window.ArcToChrome.convertArcSidebarToBookmarksHtml(source);
        showResult(file.name, html, stats);
      } catch (err) {
        if (err instanceof window.ArcToChrome.ArcFormatError) {
          showMessage('err', err.message);
        } else {
          showMessage('err', `Unexpected error while converting: ${err.message}`);
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
})();
