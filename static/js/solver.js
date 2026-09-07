function showTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

function renderResult(targetId, data) {
  const el = document.getElementById(targetId);
  if (!data.ok) {
    el.innerHTML = `<div class="error-box">${data.error || 'Something went wrong.'}</div>`;
    return;
  }
  let html = '';
  if (data.steps && data.steps.length) {
    html += '<div class="steps"><strong>Working:</strong><ol>';
    data.steps.forEach(s => { html += `<li>${s}</li>`; });
    html += '</ol></div>';
  }
  if (typeof data.result === 'string') {
    html += `<div class="result-box">Answer: ${data.result}</div>`;
  } else if (Array.isArray(data.result)) {
    html += '<div class="result-box"><table><tr><th>x</th><th>y</th></tr>';
    data.result.forEach(r => { html += `<tr><td>${r.x}</td><td>${r.y}</td></tr>`; });
    html += '</table></div>';
  } else if (data.result && data.result.image) {
    html += `<img class="plot-img" src="data:image/png;base64,${data.result.image}">`;
    if (data.result.intersection) {
      html += `<div class="result-box">Intersection point(s): ${data.result.intersection}</div>`;
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
    el.innerHTML = `<div class="error-box">Network error: ${e}</div>`;
  }
}
