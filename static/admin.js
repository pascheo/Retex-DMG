/* ── Admin dashboard JS ── */

/* ---------- Radar Chart ---------- */
function drawRadar(canvas, labels, values, maxVal) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const cx = W / 2;
  const cy = H / 2;
  const radius = Math.min(cx, cy) - 50;
  const n = labels.length;
  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2;

  const angleFor = i => startAngle + i * angleStep;

  // Draw grid (5 rings)
  for (let ring = 1; ring <= 4; ring++) {
    const r = (radius * ring) / 4;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const a = angleFor(i);
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = ring === 4 ? '#c0c8e0' : '#e0e4f0';
    ctx.lineWidth = ring === 4 ? 1.5 : 1;
    ctx.stroke();

    // Ring label (value)
    ctx.fillStyle = '#999';
    ctx.font = '11px Arial';
    ctx.textAlign = 'center';
    ctx.fillText((ring).toString(), cx, cy - r + 4);
  }

  // Draw axes
  for (let i = 0; i < n; i++) {
    const a = angleFor(i);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + radius * Math.cos(a), cy + radius * Math.sin(a));
    ctx.strokeStyle = '#c0c8e0';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Draw data polygon
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const v = values[i] !== null ? values[i] : 0;
    const r = (radius * v) / maxVal;
    const a = angleFor(i);
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(0, 49, 137, 0.18)';
  ctx.fill();
  ctx.strokeStyle = '#003189';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Data points
  for (let i = 0; i < n; i++) {
    const v = values[i] !== null ? values[i] : 0;
    const r = (radius * v) / maxVal;
    const a = angleFor(i);
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#003189';
    ctx.fill();
  }

  // Labels
  for (let i = 0; i < n; i++) {
    const a = angleFor(i);
    const labelR = radius + 38;
    const x = cx + labelR * Math.cos(a);
    const y = cy + labelR * Math.sin(a);

    ctx.fillStyle = '#003189';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const shortLabel = labels[i].length > 18 ? labels[i].slice(0, 16) + '…' : labels[i];
    const val = values[i] !== null ? values[i].toFixed(2) : 'N/A';
    ctx.fillText(shortLabel, x, y - 7);
    ctx.font = '11px Arial';
    ctx.fillStyle = '#4a6bbf';
    ctx.fillText(val + ' / 4', x, y + 9);
  }
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('radarCanvas');
  if (!canvas) return;

  const rawLabels = JSON.parse(canvas.dataset.labels || '[]');
  const rawValues = JSON.parse(canvas.dataset.values || '[]');

  // Set canvas size
  const size = Math.min(500, canvas.parentElement.clientWidth - 32);
  canvas.width = size;
  canvas.height = size;

  drawRadar(canvas, rawLabels, rawValues, 4);
});

/* ---------- Service filter (instant) ---------- */
const filterInput = document.getElementById('service-filter');
const tableBody  = document.getElementById('respondents-body');

if (filterInput && tableBody) {
  filterInput.addEventListener('input', () => {
    const term = filterInput.value.toLowerCase().trim();
    tableBody.querySelectorAll('tr').forEach(tr => {
      const service = (tr.dataset.service || '').toLowerCase();
      tr.style.display = (!term || service.includes(term)) ? '' : 'none';
    });
  });
}
