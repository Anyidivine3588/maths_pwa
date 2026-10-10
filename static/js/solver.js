// Solver output is small HTML (<sup>, stacked fractions, tables). Only a few safe tags are
// allowed; anything else (scripts, images, event handlers) is turned into plain text.
const _ALLOWED_TAGS = new Set(['B','I','U','SUP','SUB','BR','SPAN','TABLE','TR','TD','TH','THEAD','TBODY','STRONG','EM','SMALL']);
function _walkClean(node) {
  Array.from(node.childNodes).forEach(ch => {
    if (ch.nodeType === 1) {
      if (!_ALLOWED_TAGS.has(ch.tagName)) {
        ch.replaceWith(document.createTextNode(ch.textContent));
        return;
      }
      Array.from(ch.attributes).forEach(a => {
        if (!(a.name === 'class' && /^[\w -]*$/.test(a.value))) ch.removeAttribute(a.name);
      });
      _walkClean(ch);
    } else if (ch.nodeType !== 3) {
      ch.remove();
    }
  });
}
function cleanHtml(html) {
  const t = document.createElement('template');
  t.innerHTML = String(html == null ? '' : html);
  _walkClean(t.content);
  return t.innerHTML;
}

function showTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

function renderResult(targetId, data) {
  const el = document.getElementById(targetId);
  if (!data.ok) {
    el.innerHTML = `<div class="error-box">${cleanHtml(data.error || 'Something went wrong.')}</div>`;
    return;
  }
  let html = '';
  if (data.steps && data.steps.length) {
    html += '<div class="steps"><strong>Working:</strong><ol>';
    data.steps.forEach(s => { html += `<li>${cleanHtml(s)}</li>`; });
    html += '</ol></div>';
  }
  if (typeof data.result === 'string') {
    html += `<div class="result-box">Answer: ${cleanHtml(data.result)}</div>`;
  } else if (Array.isArray(data.result)) {
    html += '<div class="result-box"><table><tr><th>x</th><th>y</th></tr>';
    data.result.forEach(r => { html += `<tr><td>${r.x}</td><td>${r.y}</td></tr>`; });
    html += '</table></div>';
  } else if (data.result && data.result.image) {
    html += `<img class="plot-img" src="data:image/png;base64,${data.result.image}">`;
    if (data.result.intersection) {
      html += `<div class="result-box">Intersection point(s): ${cleanHtml(data.result.intersection)}</div>`;
    }
    if (data.result.text) {
      html += `<div class="result-box">${cleanHtml(data.result.text)}</div>`;
    }
  }
  el.innerHTML = html;
}

async function postSolve(url, payload, targetId) {
  const el = document.getElementById(targetId);
  el.innerHTML = '<p style="color:var(--muted);">Solving…</p>';
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    renderResult(targetId, data);
  } catch (e) {
    el.innerHTML = `<div class="error-box">Network error: ${cleanHtml(String(e))}</div>`;
  }
}

function showGroup(selectId, prefix) {
  const v = document.getElementById(selectId).value;
  document.querySelectorAll('.field-group[data-for="' + selectId + '"]').forEach(g => {
    g.classList.toggle('active', g.dataset.show.split(' ').includes(v));
  });
}
function val(id) { const e = document.getElementById(id); return e ? e.value : ''; }

// ---- generic, form-driven topic pages ----
function initGeneric() {
  document.querySelectorAll('.panel').forEach(panel => {
    const gated = panel.querySelectorAll('.gf[data-showif]');
    const update = () => {
      gated.forEach(g => {
        let rule = {};
        try { rule = JSON.parse(g.getAttribute('data-showif')); } catch (e) {}
        let ok = true;
        Object.keys(rule).forEach(name => {
          const ctl = panel.querySelector('[name="' + name + '"]');
          const want = rule[name];
          const have = ctl ? ctl.value : '';
          if (!(Array.isArray(want) ? want.includes(have) : want === have)) ok = false;
        });
        g.style.display = ok ? '' : 'none';
      });
    };
    panel.querySelectorAll('select').forEach(sel => sel.addEventListener('change', update));
    update();
  });
}

function runGeneric(topic, sub, panelId) {
  const panel = document.getElementById(panelId);
  const payload = {};
  panel.querySelectorAll('.gf').forEach(g => {
    if (g.style.display === 'none') return;
    const ctl = g.querySelector('input, select');
    if (ctl) payload[ctl.name] = ctl.value;
  });
  postSolve('/api/g/' + topic + '/' + sub, payload, panelId + '__out');
}
