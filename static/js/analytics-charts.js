/**
 * OptiExam Analytics Charts — Zero-CDN Native Canvas & SVG Renderer
 * Renders grade distribution histograms and item analysis charts
 * using only HTML5 Canvas API. No external dependencies.
 */

(function () {
  'use strict';

  // ─── Color Palette ────────────────────────────────────────────────────────
  const COLORS = {
    A: '#10B981', // success green
    B: '#4F46E5', // primary indigo
    C: '#38BDF8', // sky blue
    D: '#F59E0B', // warning amber
    F: '#EF4444', // danger red
    bar: '#4F46E5',
    barHover: '#7C3AED',
    text: 'rgba(255,255,255,0.75)',
    grid: 'rgba(255,255,255,0.08)',
    bg: 'rgba(0,0,0,0)'
  };

  // ─── Grade Histogram Bar Chart ────────────────────────────────────────────
  function renderGradeHistogram(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const DPR = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight || 220;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    ctx.scale(DPR, DPR);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';

    const labels = Object.keys(data);     // ['A','B','C','D','F']
    const values = Object.values(data);   // [12, 34, 56, 18, 4]
    const maxVal  = Math.max(...values, 1);
    const padL = 42, padR = 16, padT = 16, padB = 40;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;
    const barW   = (chartW / labels.length) * 0.6;
    const gap    = (chartW / labels.length) * 0.4;

    // Draw grid lines
    const gridLines = 5;
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    for (let i = 0; i <= gridLines; i++) {
      const y = padT + (chartH / gridLines) * i;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(padL + chartW, y);
      ctx.stroke();
      // Y-axis label
      const val = Math.round(maxVal - (maxVal / gridLines) * i);
      ctx.fillStyle = COLORS.text;
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(val, padL - 6, y + 4);
    }

    // Draw bars
    labels.forEach(function (label, i) {
      const barH = (values[i] / maxVal) * chartH;
      const x = padL + (chartW / labels.length) * i + gap / 2;
      const y = padT + chartH - barH;

      // Gradient fill
      const grad = ctx.createLinearGradient(x, y, x, padT + chartH);
      const gradeColor = COLORS[label] || COLORS.bar;
      grad.addColorStop(0, gradeColor);
      grad.addColorStop(1, gradeColor + '44');

      ctx.fillStyle = grad;
      const radius = 4;
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + barW - radius, y);
      ctx.quadraticCurveTo(x + barW, y, x + barW, y + radius);
      ctx.lineTo(x + barW, padT + chartH);
      ctx.lineTo(x, padT + chartH);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
      ctx.fill();

      // Value label on bar
      if (values[i] > 0) {
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(values[i], x + barW / 2, y - 6);
      }

      // X-axis label
      ctx.fillStyle = COLORS.text;
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Grade ' + label, x + barW / 2, padT + chartH + 22);
    });
  }

  // ─── Item Analysis Scatter / Dot Plot ─────────────────────────────────────
  function renderItemScatter(canvasId, items) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !items || items.length === 0) return;
    const ctx = canvas.getContext('2d');
    const DPR = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight || 260;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    ctx.scale(DPR, DPR);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';

    const padL = 50, padR = 20, padT = 20, padB = 50;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    // Axes
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 1;
    // X axis
    ctx.beginPath();
    ctx.moveTo(padL, padT + chartH);
    ctx.lineTo(padL + chartW, padT + chartH);
    ctx.stroke();
    // Y axis
    ctx.beginPath();
    ctx.moveTo(padL, padT);
    ctx.lineTo(padL, padT + chartH);
    ctx.stroke();

    // Axis labels
    ctx.fillStyle = COLORS.text;
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Difficulty Index (p-value) →', padL + chartW / 2, H - 8);
    ctx.save();
    ctx.translate(14, padT + chartH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Discrimination (D-index) ↑', 0, 0);
    ctx.restore();

    // Grid ticks
    ctx.strokeStyle = COLORS.grid;
    for (let v = 0; v <= 1; v += 0.2) {
      const xPos = padL + v * chartW;
      const yPos = padT + (1 - v) * chartH;
      ctx.beginPath(); ctx.moveTo(xPos, padT); ctx.lineTo(xPos, padT + chartH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(padL, yPos); ctx.lineTo(padL + chartW, yPos); ctx.stroke();
      ctx.fillStyle = COLORS.text;
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(v.toFixed(1), xPos, padT + chartH + 14);
      ctx.textAlign = 'right';
      ctx.fillText(v.toFixed(1), padL - 4, yPos + 4);
    }

    // Dots
    items.forEach(function (item) {
      const px = padL + (item.p_value || 0) * chartW;
      const py = padT + (1 - Math.max(-1, Math.min(1, item.d_index || 0))) * chartH;
      let color = COLORS.F;
      if ((item.p_value || 0) >= 0.7) color = COLORS.A;
      else if ((item.p_value || 0) >= 0.3) color = COLORS.D;

      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fillStyle = color + 'CC';
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    });
  }

  // ─── Auto-Initialize on DOM Ready ─────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    // Grade Histogram
    const histCanvas = document.getElementById('analytics-histogram');
    if (histCanvas && histCanvas.dataset.grades) {
      try {
        renderGradeHistogram('analytics-histogram', JSON.parse(histCanvas.dataset.grades));
      } catch (e) { console.warn('OptiExam Charts: Histogram parse error', e); }
    }

    // Item Analysis Scatter
    const scatterCanvas = document.getElementById('item-analysis-scatter');
    if (scatterCanvas && scatterCanvas.dataset.items) {
      try {
        renderItemScatter('item-analysis-scatter', JSON.parse(scatterCanvas.dataset.items));
      } catch (e) { console.warn('OptiExam Charts: Scatter parse error', e); }
    }
  });

  // ─── Public API ───────────────────────────────────────────────────────────
  window.OptiExamCharts = {
    renderGradeHistogram: renderGradeHistogram,
    renderItemScatter: renderItemScatter
  };

}());
