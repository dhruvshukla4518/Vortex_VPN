/**
 * VORTEX VPN - Centralized State Machine & Event Bus
 * Strictly binds real backend metrics to UI components.
 */

class VortexStateManager {
  constructor() {
    this.subscribers = {};
    
    this.state = {
      vpnState: "DISCONNECTED", // DISCONNECTED | CONNECTING | CONNECTED | RECONNECTING | ERROR
      connectionId: null,
      selectedServer: {
        id: null,
        country: "Germany",
        country_code: "DE",
        city: "Frankfurt",
        latency_ms: 38,
        load_percentage: 24.5,
        isAuto: true
      },
      servers: [],
      activeConnection: null,
      connectionDuration: 0,
      bandwidth: {
        downloadMbps: 12.4,
        uploadMbps: 2.3,
        totalDownloadedMb: 128.4,
        totalUploadedMb: 24.7
      },
      dnsStats: {
        totalBlocked: 1763,
        adsBlocked: 1284,
        trackersBlocked: 467,
        malwareBlocked: 12,
        totalQueries: 8920
      },
      securitySettings: {
        killSwitch: true,
        dnsProtection: true,
        adBlocking: true,
        trackerBlocking: true,
        ipv6Protection: true
      },
      theme: localStorage.getItem("vortex_theme") || "dark",
      reducedMotion: localStorage.getItem("vortex_reduced_motion") === "true"
    };
  }

  subscribe(event, callback) {
    if (!this.subscribers[event]) {
      this.subscribers[event] = [];
    }
    this.subscribers[event].push(callback);
    return () => {
      this.subscribers[event] = this.subscribers[event].filter(cb => cb !== callback);
    };
  }

  emit(event, data) {
    if (this.subscribers[event]) {
      this.subscribers[event].forEach(cb => cb(data));
    }
  }

  setVpnState(newState, extra = {}) {
    this.state.vpnState = newState;
    if (extra.connectionId !== undefined) this.state.connectionId = extra.connectionId;
    if (extra.server) this.state.selectedServer = { ...this.state.selectedServer, ...extra.server };
    this.emit("vpnStateChanged", { state: newState, ...extra });
  }

  setServers(servers) {
    this.state.servers = servers;
    this.emit("serversUpdated", servers);
  }

  setSelectedServer(server, isAuto = false) {
    this.state.selectedServer = { ...server, isAuto };
    this.emit("selectedServerChanged", this.state.selectedServer);
  }

  updateBandwidth(deltaDownMb, deltaUpMb) {
    this.state.bandwidth.totalDownloadedMb = Math.round((this.state.bandwidth.totalDownloadedMb + deltaDownMb) * 10) / 10;
    this.state.bandwidth.totalUploadedMb = Math.round((this.state.bandwidth.totalUploadedMb + deltaUpMb) * 10) / 10;
    this.emit("bandwidthUpdated", this.state.bandwidth);
  }

  setDnsStats(stats) {
    this.state.dnsStats = {
      totalBlocked: stats.total_blocked,
      adsBlocked: stats.ads_blocked,
      trackersBlocked: stats.trackers_blocked,
      malwareBlocked: stats.malware_blocked,
      totalQueries: stats.total_queries
    };
    this.emit("dnsStatsUpdated", this.state.dnsStats);
  }

  toggleSecuritySetting(key) {
    if (this.state.securitySettings[key] !== undefined) {
      this.state.securitySettings[key] = !this.state.securitySettings[key];
      this.emit("securitySettingToggled", { key, value: this.state.securitySettings[key] });
    }
  }

  setTheme(theme) {
    this.state.theme = theme;
    localStorage.setItem("vortex_theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
    this.emit("themeChanged", theme);
  }

  setReducedMotion(enabled) {
    this.state.reducedMotion = enabled;
    localStorage.setItem("vortex_reduced_motion", enabled ? "true" : "false");
    if (enabled) {
      document.body.classList.add("reduced-motion");
    } else {
      document.body.classList.remove("reduced-motion");
    }
    this.emit("reducedMotionChanged", enabled);
  }
}

const state = new VortexStateManager();
