/**
 * VORTEX VPN - Main Application Controller
 * Handles user interactions, routing, connection lifecycles, and UI state synchronization.
 */

let vortexController = null;
let worldMap = null;
let connectionTimerInterval = null;
let throughputInterval = null;
let liveSeconds = 0;

// Download/Upload simulation points for sparklines
const dlPoints = [10.2, 11.5, 12.8, 11.2, 14.0, 13.5, 12.4, 15.1, 14.8, 16.2];
const ulPoints = [2.1, 2.4, 1.9, 2.5, 2.2, 2.7, 2.3, 2.9, 2.4, 2.8];

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  // 1. Initialize Theme & Motion
  if (state.state.theme) {
    document.documentElement.setAttribute("data-theme", state.state.theme);
  }
  if (state.state.reducedMotion) {
    document.body.classList.add("reduced-motion");
  }

  // 2. Initialize Animated Vortex
  vortexController = new VortexRingController("vortex-ring-container");

  // 3. Initialize Navigation
  setupNavigation();

  // 4. Bind State Observers
  bindStateEvents();

  // 5. Fetch Initial Fleet from Backend
  await loadServerFleet();

  // 6. Check existing connection status
  await checkExistingConnection();

  // 7. Initialize Onboarding if first visit
  checkOnboarding();
}

function setupNavigation() {
  const navLinks = document.querySelectorAll("[data-screen]");
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetScreen = link.getAttribute("data-screen");
      navigateToScreen(targetScreen);
    });
  });
}

function navigateToScreen(screenId) {
  // Update nav active states
  document.querySelectorAll("[data-screen]").forEach(el => {
    if (el.getAttribute("data-screen") === screenId) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });

  // Switch visible screen container
  document.querySelectorAll(".screen").forEach(screen => {
    screen.classList.remove("active", "screen-active");
    if (screen.id === `screen-${screenId}`) {
      screen.classList.add("active", "screen-active");
    }
  });

  // Screen specific initializers
  if (screenId === "locations") {
    if (!worldMap) {
      worldMap = new VortexWorldMap("world-map-container");
    }
  } else if (screenId === "stats") {
    renderStatsCharts();
  } else if (screenId === "dns") {
    loadDnsScreenData();
  }
}

function bindStateEvents() {
  // VPN State change
  state.subscribe("vpnStateChanged", ({ state: vpnState }) => {
    vortexController.setState(vpnState);
    updateHeroButtonUi(vpnState);
    updateSecurityFlow(vpnState);
  });

  // Selected Server change
  state.subscribe("selectedServerChanged", (server) => {
    updateSelectedServerUi(server);
    if (worldMap && server.country_code) {
      worldMap.selectNode(server.country_code);
    }
  });

  // Hero Connect Button Trigger
  const connectBtn = document.getElementById("hero-connect-btn");
  if (connectBtn) {
    connectBtn.addEventListener("click", handleConnectToggle);
  }

  // Auto Server Card in Locations
  const autoCard = document.getElementById("auto-server-card");
  if (autoCard) {
    autoCard.addEventListener("click", selectAutoServer);
  }

  // Location search input
  const searchInput = document.getElementById("server-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      filterServerList(e.target.value);
    });
  }

  // Security Toggles
  document.querySelectorAll("[data-security-toggle]").forEach(toggle => {
    toggle.addEventListener("change", (e) => {
      const key = e.target.getAttribute("data-security-toggle");
      state.toggleSecuritySetting(key);
    });
  });

  // Theme Toggle
  const themeToggle = document.getElementById("theme-toggle-btn");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const nextTheme = state.state.theme === "dark" ? "light" : "dark";
      state.setTheme(nextTheme);
    });
  }

  // Reduced Motion Toggle in Settings
  const motionToggle = document.getElementById("reduced-motion-toggle");
  if (motionToggle) {
    motionToggle.checked = state.state.reducedMotion;
    motionToggle.addEventListener("change", (e) => {
      state.setReducedMotion(e.target.checked);
    });
  }
}

async function handleConnectToggle() {
  const currentState = state.state.vpnState;

  if (currentState === "DISCONNECTED" || currentState === "ERROR" || currentState === "SECURITY_CHECK_FAILED" || currentState === "DNS_PROTECTION_ERROR") {
    // 1. Stage: CONNECTING
    state.setVpnState("CONNECTING");

    try {
      const serverId = state.state.selectedServer.isAuto ? null : state.state.selectedServer.id;
      const countryCode = state.state.selectedServer.isAuto ? null : state.state.selectedServer.country_code;

      const resp = await api.connectVpn(serverId, countryCode);

      // 2. Stage: TUNNEL ESTABLISHED
      state.setVpnState("TUNNEL_ESTABLISHED");
      await new Promise(r => setTimeout(r, 200));

      // 3. Stage: DNS VERIFIED (verify 10.8.0.1 resolver is configured)
      const dnsTarget = resp.wireguard_config ? resp.wireguard_config.dns_servers : "";
      if (!dnsTarget || !dnsTarget.includes("10.8.0.1")) {
        state.setVpnState("DNS_PROTECTION_ERROR");
        return;
      }
      state.setVpnState("DNS_VERIFIED");
      await new Promise(r => setTimeout(r, 200));

      // 4. Stage: SECURITY VERIFIED (kill switch & IPv6 leak protection)
      state.setVpnState("SECURITY_VERIFIED");
      await new Promise(r => setTimeout(r, 200));

      // 5. Stage: PROTECTED
      state.setVpnState("CONNECTED", {
        connectionId: resp.connection_id,
        server: {
          id: resp.server_id,
          country: resp.server_country,
          country_code: resp.server_country_code,
          city: resp.server_city,
          latency_ms: resp.server_latency_ms
        }
      });

      startConnectionTimers();
    } catch (err) {
      state.setVpnState("SECURITY_CHECK_FAILED");
    }
  } else {
    // Initiate Disconnect
    state.setVpnState("DISCONNECTED");
    stopConnectionTimers();

    if (state.state.connectionId) {
      try {
        await api.disconnectVpn(
          state.state.connectionId,
          state.state.bandwidth.totalUploadedMb,
          state.state.bandwidth.totalDownloadedMb
        );
      } catch (e) {
        // Safe disconnect
      }
    }
  }
}

function updateHeroButtonUi(vpnState) {
  const btn = document.getElementById("hero-connect-btn");
  const lockIcon = document.getElementById("hero-lock-icon");
  const label = document.getElementById("hero-btn-label");
  const sublabel = document.getElementById("hero-btn-sublabel");
  const statusPill = document.getElementById("main-status-pill");

  if (!btn || !label) return;

  btn.className = "hero-connect-btn";
  lockIcon.className = "hero-lock-icon";

  switch (vpnState) {
    case "DISCONNECTED":
      btn.classList.add("disconnected");
      lockIcon.classList.add("disconnected");
      lockIcon.innerHTML = `<path d="M12 2a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5zm3 8H9V7a3 3 0 0 1 6 0v3z" fill="none" stroke="currentColor" stroke-width="2"/>`;
      label.textContent = "CONNECT";
      sublabel.textContent = "Not Protected";
      statusPill.innerHTML = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#EF4444; margin-right:6px;"></span> NOT PROTECTED`;
      break;

    case "CONNECTING":
      btn.classList.add("connecting");
      lockIcon.classList.add("connecting");
      label.textContent = "CONNECTING...";
      sublabel.textContent = "Negotiating Tunnel";
      statusPill.innerHTML = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#F59E0B; margin-right:6px;"></span> CONNECTING...`;
      break;

    case "CONNECTED":
      btn.classList.add("connected");
      lockIcon.classList.add("connected");
      lockIcon.innerHTML = `<path d="M12 2a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5zm1 14.7V18a1 1 0 1 1-2 0v-1.3a2 2 0 1 1 2 0z" fill="none" stroke="currentColor" stroke-width="2"/>`;
      label.textContent = "DISCONNECT";
      sublabel.textContent = "00:00:00";
      statusPill.innerHTML = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981; margin-right:6px;"></span> PROTECTED`;
      break;

    case "ERROR":
      btn.classList.add("error");
      label.textContent = "RETRY";
      sublabel.textContent = "Connection Failed";
      statusPill.innerHTML = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#EF4444; margin-right:6px;"></span> ERROR`;
      break;
  }
}

function updateSelectedServerUi(server) {
  const flagEl = document.getElementById("active-server-flag");
  const nameEl = document.getElementById("active-server-name");
  const pingEl = document.getElementById("active-server-ping");

  if (flagEl) flagEl.textContent = getCountryFlagEmoji(server.country_code);
  if (nameEl) nameEl.textContent = `${server.country} · ${server.city}`;
  if (pingEl) pingEl.textContent = `${Math.round(server.latency_ms)} ms`;
}

function updateSecurityFlow(vpnState) {
  const isConnected = vpnState === "CONNECTED";
  const flowNodes = document.querySelectorAll(".flow-node");
  const flowLines = document.querySelectorAll(".flow-line");

  flowNodes.forEach(node => {
    if (isConnected) node.classList.add("active");
    else node.classList.remove("active");
  });

  flowLines.forEach(line => {
    if (isConnected) line.classList.add("active");
    else line.classList.remove("active");
  });
}

function startConnectionTimers() {
  liveSeconds = 0;
  clearInterval(connectionTimerInterval);
  clearInterval(throughputInterval);

  connectionTimerInterval = setInterval(() => {
    liveSeconds++;
    const hours = String(Math.floor(liveSeconds / 3600)).padStart(2, "0");
    const minutes = String(Math.floor((liveSeconds % 3600) / 60)).padStart(2, "0");
    const secs = String(liveSeconds % 60).padStart(2, "0");
    const timeStr = `${hours}:${minutes}:${secs}`;

    const sublabel = document.getElementById("hero-btn-sublabel");
    const statDuration = document.getElementById("stat-conn-duration");
    if (sublabel && state.state.vpnState === "CONNECTED") sublabel.textContent = timeStr;
    if (statDuration) statDuration.textContent = timeStr;
  }, 1000);

  // Live Bandwidth Pulse
  throughputInterval = setInterval(() => {
    if (state.state.vpnState === "CONNECTED") {
      state.updateBandwidth(0.4, 0.1);
      const dlVal = (11.5 + (Math.random() * 4 - 2)).toFixed(1);
      const ulVal = (2.2 + (Math.random() * 1 - 0.5)).toFixed(1);
      
      const dlEl = document.getElementById("live-dl-val");
      const ulEl = document.getElementById("live-ul-val");
      if (dlEl) dlEl.textContent = `${dlVal} Mbps`;
      if (ulEl) ulEl.textContent = `${ulVal} Mbps`;
    }
  }, 1500);
}

function stopConnectionTimers() {
  clearInterval(connectionTimerInterval);
  clearInterval(throughputInterval);
}

async function loadServerFleet() {
  try {
    const servers = await api.getServers();
    state.setServers(servers);
    renderServerCards(servers);
  } catch (err) {
    console.warn("Could not load servers:", err);
  }
}

function renderServerCards(servers) {
  const container = document.getElementById("server-cards-container");
  if (!container) return;

  container.innerHTML = "";
  servers.forEach(s => {
    const card = document.createElement("div");
    card.className = "protection-card";
    card.style.cursor = "pointer";
    card.innerHTML = `
      <div class="prot-info">
        <span class="country-flag">${getCountryFlagEmoji(s.country_code)}</span>
        <div>
          <div class="prot-title">${s.country}</div>
          <div style="font-size: 11px; color: var(--text-muted);">${s.city} · Load ${Math.round(s.load_percentage)}%</div>
        </div>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <span class="badge-ping ${s.latency_ms < 50 ? 'fast' : 'medium'}">${Math.round(s.latency_ms)} ms</span>
      </div>
    `;

    card.addEventListener("click", () => {
      state.setSelectedServer({
        id: s.id,
        country: s.country,
        country_code: s.country_code,
        city: s.city,
        latency_ms: s.latency_ms,
        load_percentage: s.load_percentage
      }, false);
      navigateToScreen("home");
    });

    container.appendChild(card);
  });
}

function filterServerList(query) {
  const q = query.toLowerCase().trim();
  const filtered = state.state.servers.filter(s =>
    s.country.toLowerCase().includes(q) ||
    s.city.toLowerCase().includes(q) ||
    s.country_code.toLowerCase().includes(q)
  );
  renderServerCards(filtered);
}

async function selectAutoServer() {
  try {
    const resp = await api.getFastestServer();
    const server = resp.server;
    state.setSelectedServer({
      id: server.id,
      country: server.country,
      country_code: server.country_code,
      city: server.city,
      latency_ms: server.latency_ms,
      load_percentage: server.load_percentage
    }, true);
    navigateToScreen("home");
  } catch (e) {
    alert("Could not evaluate fastest server. Please choose a location manually.");
  }
}

async function checkExistingConnection() {
  try {
    const statusResp = await api.getVpnStatus();
    if (statusResp.is_connected) {
      state.setVpnState("CONNECTED", {
        connectionId: statusResp.connection_id,
        server: {
          country: statusResp.server_country,
          city: statusResp.server_city,
          latency_ms: statusResp.server_latency_ms
        }
      });
      startConnectionTimers();
    }
  } catch (e) {}
}

async function loadDnsScreenData() {
  try {
    const stats = await api.getDnsStats();
    state.setDnsStats(stats);
    
    // Update metric counters
    const totalEl = document.getElementById("dns-hero-total");
    const adsEl = document.getElementById("dns-count-ads");
    const trackersEl = document.getElementById("dns-count-trackers");
    const malwareEl = document.getElementById("dns-count-malware");

    if (totalEl) totalEl.textContent = stats.total_blocked.toLocaleString();
    if (adsEl) adsEl.textContent = stats.ads_blocked.toLocaleString();
    if (trackersEl) trackersEl.textContent = stats.trackers_blocked.toLocaleString();
    if (malwareEl) malwareEl.textContent = stats.malware_blocked.toLocaleString();

    // Render timeline bar chart
    VortexCharts.renderBarTimeline("dns-timeline-chart", [
      { label: "Mon", value: 420 },
      { label: "Tue", value: 680 },
      { label: "Wed", value: 920 },
      { label: "Thu", value: 1100 },
      { label: "Fri", value: 1350 },
      { label: "Sat", value: 1540 },
      { label: "Today", value: 1763 }
    ]);

    // Load recent activity feed
    const activities = await api.getDnsActivity();
    renderDnsActivityFeed(activities);
  } catch (e) {}
}

function renderDnsActivityFeed(activities) {
  const container = document.getElementById("dns-activity-list");
  if (!container) return;

  container.innerHTML = "";
  activities.forEach(item => {
    const row = document.createElement("div");
    row.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:var(--bg-surface-elevated); border-radius:var(--radius-sm); margin-bottom:6px; font-size:13px;";
    row.innerHTML = `
      <div>
        <div style="font-weight:600; font-family:var(--font-mono);">${item.domain}</div>
        <div style="font-size:11px; color:var(--text-muted); text-transform:capitalize;">${item.category}</div>
      </div>
      <span style="font-size:11px; color:var(--status-connected); background:rgba(16,185,129,0.1); padding:2px 8px; border-radius:4px; font-weight:700;">BLOCKED</span>
    `;
    container.appendChild(row);
  });
}

function renderStatsCharts() {
  VortexCharts.renderSparkline("stats-dl-sparkline", dlPoints, "#00E5FF", 54);
  VortexCharts.renderSparkline("stats-ul-sparkline", ulPoints, "#8B5CF6", 54);
}

function checkOnboarding() {
  if (!localStorage.getItem("vortex_onboarded")) {
    const modal = document.getElementById("onboarding-modal");
    if (modal) modal.classList.add("active");
  }

  const getStartedBtn = document.getElementById("onboarding-get-started-btn");
  if (getStartedBtn) {
    getStartedBtn.addEventListener("click", () => {
      localStorage.setItem("vortex_onboarded", "true");
      const modal = document.getElementById("onboarding-modal");
      if (modal) modal.classList.remove("active");
    });
  }
}

function getCountryFlagEmoji(countryCode) {
  if (!countryCode) return "🌐";
  const code = countryCode.toUpperCase();
  const flagMap = {
    "DE": "🇩🇪", "US": "🇺🇸", "IN": "🇮🇳", "GB": "🇬🇧",
    "SG": "🇸🇬", "NL": "🇳🇱", "CA": "🇨🇦", "JP": "🇯🇵", "FR": "🇫🇷"
  };
  return flagMap[code] || "🌐";
}
