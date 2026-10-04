/**
 * VORTEX VPN - Zero-Dependency SVG Charts & Sparklines
 * High-performance, low-memory visualizer for network bandwidth and DNS threat timelines.
 */

class VortexCharts {
  static renderSparkline(containerId, points, color = "#00E5FF", height = 48) {
    const container = document.getElementById(containerId);
    if (!container || !points || points.length < 2) return;

    const width = container.clientWidth || 240;
    const min = Math.min(...points);
    const max = Math.max(...points) || 1;
    const range = (max - min) || 1;

    const stepX = width / (points.length - 1);
    const coords = points.map((val, i) => {
      const x = i * stepX;
      const y = height - ((val - min) / range) * (height - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    const pathData = `M ${coords.join(" L ")}`;
    const areaData = `M 0,${height} L ${coords.join(" L ")} L ${width},${height} Z`;

    container.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: ${height}px; overflow: visible;">
        <defs>
          <linearGradient id="grad_${containerId}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${color}" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="${color}" stop-opacity="0.0"/>
          </linearGradient>
        </defs>
        <path d="${areaData}" fill="url(#grad_${containerId})" />
        <path d="${pathData}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    `;
  }

  static renderBarTimeline(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const maxVal = Math.max(...data.map(d => d.value), 10);
    let barsHtml = "";

    data.forEach(item => {
      const pct = Math.round((item.value / maxVal) * 100);
      barsHtml += `
        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;">
          <div style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted);">${item.value}</div>
          <div style="width: 100%; max-width: 24px; height: 100px; background: var(--bg-surface-elevated); border-radius: 4px; display: flex; align-items: flex-end; overflow: hidden;">
            <div style="width: 100%; height: ${pct}%; background: linear-gradient(180deg, var(--accent-cyan), #4F46E5); border-radius: 4px; transition: height 0.4s ease;"></div>
          </div>
          <div style="font-size: 10px; color: var(--text-secondary); font-weight: 500;">${item.label}</div>
        </div>
      `;
    });

    container.innerHTML = `
      <div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; width: 100%; padding: 12px 0;">
        ${barsHtml}
      </div>
    `;
  }
}
