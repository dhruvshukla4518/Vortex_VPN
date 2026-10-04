/**
 * VORTEX VPN - REST API Client
 * Manages communication with FastAPI backend endpoints, JWT tokens, and auto-refresh.
 */

const API_BASE = "/api/v1";

class VortexApiClient {
  constructor() {
    this.token = localStorage.getItem("vortex_access_token") || null;
    this.refreshToken = localStorage.getItem("vortex_refresh_token") || null;
  }

  setTokens(accessToken, refreshToken) {
    this.token = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem("vortex_access_token", accessToken);
    localStorage.setItem("vortex_refresh_token", refreshToken);
  }

  clearTokens() {
    this.token = null;
    this.refreshToken = null;
    localStorage.removeItem("vortex_access_token");
    localStorage.removeItem("vortex_refresh_token");
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    try {
      let response = await fetch(url, { ...options, headers });

      // Handle 401 Unauthorized by attempting token refresh
      if (response.status === 401 && this.refreshToken && !endpoint.includes("/auth/")) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          headers["Authorization"] = `Bearer ${this.token}`;
          response = await fetch(url, { ...options, headers });
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.warn(`[VortexApi] ${endpoint} error:`, err.message);
      throw err;
    }
  }

  async refreshAccessToken() {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });
      if (res.ok) {
        const data = await res.json();
        this.setTokens(data.access_token, data.refresh_token);
        return true;
      }
    } catch (e) {
      this.clearTokens();
    }
    return false;
  }

  // Auth Endpoints
  async register(email, username, password) {
    const data = await this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, password })
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async login(emailOrUsername, password) {
    const data = await this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email_or_username: emailOrUsername, password })
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  // Server Fleet
  async getServers() {
    return await this.request("/servers");
  }

  async getFastestServer(countryCode = null) {
    const query = countryCode ? `?country_code=${encodeURIComponent(countryCode)}` : "";
    return await this.request(`/servers/auto/fastest${query}`);
  }

  // VPN Connection Lifecycle
  async connectVpn(serverId = null, countryCode = null) {
    return await this.request("/vpn/connect", {
      method: "POST",
      body: JSON.stringify({ server_id: serverId, country_code: countryCode })
    });
  }

  async disconnectVpn(connectionId, bytesUp = 0, bytesDown = 0) {
    return await this.request("/vpn/disconnect", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId,
        bytes_uploaded_mb: bytesUp,
        bytes_downloaded_mb: bytesDown
      })
    });
  }

  async getVpnStatus() {
    return await this.request("/vpn/status");
  }

  async getDiagnostics() {
    return await this.request("/vpn/diagnostics");
  }

  // DNS Shield & Statistics
  async getDnsStats() {
    return await this.request("/dns/statistics");
  }

  async getDnsActivity() {
    return await this.request("/dns/activity");
  }

  async getCustomRules() {
    return await this.request("/dns/custom-rules");
  }

  async addCustomRule(domain, action = "block", category = "custom") {
    return await this.request("/dns/custom-rules", {
      method: "POST",
      body: JSON.stringify({ domain, action, category })
    });
  }

  async deleteCustomRule(ruleId) {
    return await this.request(`/dns/custom-rules/${ruleId}`, {
      method: "DELETE"
    });
  }
}

const api = new VortexApiClient();
