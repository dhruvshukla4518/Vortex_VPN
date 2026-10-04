/**
 * VORTEX VPN - Interactive Server World Map
 * Minimalist dark vector map with pulsing server nodes and animated connection line.
 */

const SERVER_COORDINATES = {
  "DE": { name: "Frankfurt", country: "Germany", x: 500, y: 155, flag: "🇩🇪", latency: 38 },
  "US": { name: "New York", country: "United States", x: 260, y: 180, flag: "🇺🇸", latency: 68 },
  "IN": { name: "Mumbai", country: "India", x: 670, y: 235, flag: "🇮🇳", latency: 22 },
  "GB": { name: "London", country: "United Kingdom", x: 475, y: 145, flag: "🇬🇧", latency: 45 },
  "SG": { name: "Singapore", country: "Singapore", x: 745, y: 285, flag: "🇸🇬", latency: 48 },
  "NL": { name: "Amsterdam", country: "Netherlands", x: 490, y: 148, flag: "🇳🇱", latency: 41 }
};

class VortexWorldMap {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.activeCode = "DE";
    this.render();
  }

  render() {
    if (!this.container) return;

    let nodesHtml = "";
    for (const [code, info] of Object.entries(SERVER_COORDINATES)) {
      const isConnected = code === this.activeCode;
      const markerColor = isConnected ? "#10B981" : "#00E5FF";
      
      nodesHtml += `
        <g class="map-node" data-code="${code}" style="cursor: pointer;">
          <!-- Outer Pulsing Ring -->
          <circle cx="${info.x}" cy="${info.y}" r="${isConnected ? 12 : 7}" fill="none" stroke="${markerColor}" stroke-width="1.5" opacity="0.6">
            <animate attributeName="r" values="${isConnected ? '8;18;8' : '5;12;5'}" dur="2.5s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.8;0;0.8" dur="2.5s" repeatCount="indefinite"/>
          </circle>
          <!-- Center Solid Dot -->
          <circle cx="${info.x}" cy="${info.y}" r="5" fill="${markerColor}" />
          <!-- Label -->
          <text x="${info.x + 8}" y="${info.y + 4}" fill="#F8FAFC" font-size="10" font-weight="600" font-family="-apple-system, sans-serif">
            ${info.flag} ${info.name} (${info.latency}ms)
          </text>
        </g>
      `;
    }

    this.container.innerHTML = `
      <div style="position: relative; width: 100%; border-radius: var(--radius-md); overflow: hidden; background: #08090C; border: 1px solid var(--border-subtle);">
        <svg viewBox="0 0 1000 480" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: auto; display: block;">
          <!-- Stylized World Map Continents Outline (Geometric Minimalist) -->
          <path d="M150,120 Q220,100 280,130 Q330,160 300,240 Q250,290 200,220 Z" fill="#141820" opacity="0.7"/>
          <path d="M220,270 Q300,290 310,380 Q270,440 230,360 Z" fill="#141820" opacity="0.7"/>
          <path d="M460,110 Q540,100 560,170 Q510,210 460,160 Z" fill="#141820" opacity="0.7"/>
          <path d="M470,200 Q560,210 550,340 Q490,390 460,260 Z" fill="#141820" opacity="0.7"/>
          <path d="M580,100 Q800,80 840,190 Q760,270 630,220 Z" fill="#141820" opacity="0.7"/>
          <path d="M720,320 Q840,310 820,410 Q730,420 710,350 Z" fill="#141820" opacity="0.7"/>

          <!-- Grid Lines -->
          <line x1="0" y1="160" x2="1000" y2="160" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
          <line x1="0" y1="320" x2="1000" y2="320" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
          <line x1="333" y1="0" x2="333" y2="480" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
          <line x1="666" y1="0" x2="666" y2="480" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>

          <!-- Nodes -->
          ${nodesHtml}
        </svg>
      </div>
    `;

    // Bind click events on server nodes
    this.container.querySelectorAll(".map-node").forEach(nodeEl => {
      nodeEl.addEventListener("click", () => {
        const code = nodeEl.getAttribute("data-code");
        this.selectNode(code);
      });
    });
  }

  selectNode(countryCode) {
    this.activeCode = countryCode;
    this.render();
    const info = SERVER_COORDINATES[countryCode];
    if (info && window.state) {
      window.state.setSelectedServer({
        country: info.country,
        country_code: countryCode,
        city: info.name,
        latency_ms: info.latency,
        load_percentage: 28.0
      }, false);
    }
  }
}
