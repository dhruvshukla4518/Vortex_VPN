# VORTEX VPN — Android Client Architecture & Build Guide

## 1. Overview
The Android client integrates the official WireGuard Android tunnel library (`com.wireguard.android:tunnel`) alongside an Android `VpnService` bridge and a hardware-accelerated Material 3 user interface.

---

## 2. Directory Structure
```
android/
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       └── java/com/vortex/vpn/
│           ├── MainActivity.kt        # UI container, permission handler & JS bridge
│           ├── VortexVpnService.kt    # Android VpnService implementation & Kill Switch
│           └── WireGuardManager.kt    # Tunnel lifecycle controller
├── build.gradle.kts
└── settings.gradle.kts
```

---

## 3. Building with Android Studio or CLI

### Prerequisites
- JDK 17+
- Android SDK with API 34 platform and build-tools installed
- Android device or emulator running Android 8.0+ (API 26+)

### Build Debug APK
```bash
cd android
./gradlew assembleDebug
```
The output APK will be located at:
`android/app/build/outputs/apk/debug/app-debug.apk`

---

## 4. Key Mechanisms

### Kill Switch Enforcement
When the tunnel is established in `VortexVpnService.kt`:
```kotlin
val builder = Builder()
    .setSession("VORTEX VPN")
    .addAddress(ipv4, 32)
    .addAddress(ipv6, 128)
    .addDnsServer("10.8.0.1")
    .addRoute("0.0.0.0", 0)
    .addRoute("::", 0)
    .setBlocking(true) // Enforces fail-closed Kill Switch
```
Setting `setBlocking(true)` ensures that all app packets are held or dropped if tunnel connectivity is interrupted, preventing cleartext network leaks.

### JavaScript Bridge
`MainActivity.kt` registers `AndroidBridge` into the WebView DOM:
- Calling `window.AndroidBridge.connect(ipv4, ipv6, dns)` requests system VPN permission via `VpnService.prepare()` and establishes the tunnel.
- Calling `window.AndroidBridge.disconnect()` safely terminates the tunnel.
