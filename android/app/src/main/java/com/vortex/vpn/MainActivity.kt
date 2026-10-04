package com.vortex.vpn

import android.app.Activity
import android.content.Intent
import android.net.VpnService
import android.os.Bundle
import android.webkit.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val vpnPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            startVpnService()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        setContentView(webView)

        setupWebView()
    }

    private fun setupWebView() {
        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.setSupportZoom(false)

        webView.addJavascriptInterface(VortexBridge(), "AndroidBridge")
        // Load the local VORTEX VPN control plane or bundled assets
        webView.loadUrl("http://10.0.2.2:8000/")
    }

    private fun requestVpnPermission() {
        val intent = VpnService.prepare(this)
        if (intent != null) {
            vpnPermissionLauncher.launch(intent)
        } else {
            startVpnService()
        }
    }

    private fun startVpnService(ipv4: String = "10.8.0.2/32", ipv6: String = "fd42:42:42::2/128", dns: String = "10.8.0.1") {
        val intent = Intent(this, VortexVpnService::class.java).apply {
            action = VortexVpnService.ACTION_CONNECT
            putExtra(VortexVpnService.EXTRA_IPV4, ipv4)
            putExtra(VortexVpnService.EXTRA_IPV6, ipv6)
            putExtra(VortexVpnService.EXTRA_DNS, dns)
        }
        startService(intent)
    }

    private fun stopVpnService() {
        val intent = Intent(this, VortexVpnService::class.java).apply {
            action = VortexVpnService.ACTION_DISCONNECT
        }
        startService(intent)
    }

    inner class VortexBridge {
        @JavascriptInterface
        fun connect(ipv4: String, ipv6: String, dns: String) {
            runOnUiThread {
                requestVpnPermission()
            }
        }

        @JavascriptInterface
        fun disconnect() {
            runOnUiThread {
                stopVpnService()
            }
        }
    }
}
