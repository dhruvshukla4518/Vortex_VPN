/**
 * VORTEX VPN - GPU-Accelerated Vortex Ring Controller
 * Manages the animated circular concentric rings and state-dependent effects.
 */

class VortexRingController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.ringOuter = null;
    this.ringInner = null;
    this.aura = null;
    this.currentState = "DISCONNECTED";
    this.init();
  }

  init() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="vortex-aura disconnected" id="vortex-aura"></div>
      <svg class="vortex-rings-svg" viewBox="0 0 260 260" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="vortexGradCyan" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#00E5FF" stop-opacity="0.8"/>
            <stop offset="50%" stop-color="#4F46E5" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="#00E5FF" stop-opacity="0.1"/>
          </linearGradient>
          <linearGradient id="vortexGradGreen" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#10B981" stop-opacity="0.9"/>
            <stop offset="60%" stop-color="#059669" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.1"/>
          </linearGradient>
        </defs>

        <!-- Outer Decorative Orbit Ring -->
        <circle id="ring-outer" cx="130" cy="130" r="110" 
                fill="none" stroke="url(#vortexGradCyan)" stroke-width="2" 
                stroke-dasharray="14 10 32 12" stroke-linecap="round"
                class="animate-spin-slow" />

        <!-- Inner Counter-Rotating Ring -->
        <circle id="ring-inner" cx="130" cy="130" r="96" 
                fill="none" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1.5" 
                stroke-dasharray="8 14 20 8" stroke-linecap="round"
                class="animate-spin-reverse" />
      </svg>
    `;

    this.ringOuter = document.getElementById("ring-outer");
    this.ringInner = document.getElementById("ring-inner");
    this.aura = document.getElementById("vortex-aura");
  }

  setState(vpnState) {
    this.currentState = vpnState;
    if (!this.aura || !this.ringOuter) return;

    // Reset classes
    this.aura.className = "vortex-aura";
    this.ringOuter.className.baseVal = "";
    this.ringInner.className.baseVal = "";

    switch (vpnState) {
      case "DISCONNECTED":
        this.aura.classList.add("disconnected");
        this.ringOuter.setAttribute("stroke", "rgba(100, 116, 139, 0.3)");
        this.ringOuter.classList.add("animate-spin-slow");
        this.ringInner.classList.add("animate-spin-reverse");
        break;

      case "CONNECTING":
      case "RECONNECTING":
        this.aura.classList.add("connecting");
        this.ringOuter.setAttribute("stroke", "var(--status-connecting)");
        this.ringOuter.classList.add("animate-connecting-spin");
        this.ringInner.classList.add("animate-connecting-spin");
        break;

      case "CONNECTED":
        this.aura.classList.add("connected");
        this.ringOuter.setAttribute("stroke", "url(#vortexGradGreen)");
        this.ringOuter.classList.add("animate-spin-slow");
        this.ringInner.classList.add("animate-spin-reverse");
        break;

      case "ERROR":
        this.aura.classList.add("error");
        this.ringOuter.setAttribute("stroke", "var(--status-error)");
        break;
    }
  }
}
