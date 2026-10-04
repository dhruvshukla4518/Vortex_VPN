package com.vortex.vpn

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import androidx.core.app.NotificationCompat

class VortexVpnService : VpnService() {

    private var vpnInterface: ParcelFileDescriptor? = null
    private val NOTIFICATION_CHANNEL_ID = "vortex_vpn_status"
    private val NOTIFICATION_ID = 1001

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        if (action == ACTION_DISCONNECT) {
            stopVpn()
            return START_NOT_STICKY
        }

        val ipv4 = intent?.getStringExtra(EXTRA_IPV4) ?: "10.8.0.2"
        val ipv6 = intent?.getStringExtra(EXTRA_IPV6) ?: "fd42:42:42::2"
        val dns = intent?.getStringExtra(EXTRA_DNS) ?: "10.8.0.1"
        val serverName = intent?.getStringExtra(EXTRA_SERVER_NAME) ?: "Germany · Frankfurt"

        startForeground(NOTIFICATION_ID, buildNotification("Connected to $serverName"))
        establishTunnel(ipv4, ipv6, dns)

        return START_STICKY
    }

    private fun establishTunnel(ipv4: String, ipv6: String, dns: String) {
        try {
            vpnInterface?.close()

            val builder = Builder()
                .setSession("VORTEX VPN")
                .addAddress(ipv4.split("/")[0], 32)
                .addAddress(ipv6.split("/")[0], 128)
                .addDnsServer(dns)
                .addRoute("0.0.0.0", 0)
                .addRoute("::", 0)
                .setBlocking(true) // Enforces fail-closed Kill Switch

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                builder.setMetered(false)
            }

            vpnInterface = builder.establish()
        } catch (e: Exception) {
            stopVpn()
        }
    }

    private fun stopVpn() {
        try {
            vpnInterface?.close()
            vpnInterface = null
        } catch (e: Exception) {}
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        stopVpn()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "VPN Status",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows live VORTEX VPN connection state"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(text: String): Notification {
        val launchIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, launchIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("VORTEX VPN — Protected")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    companion object {
        const val ACTION_CONNECT = "com.vortex.vpn.CONNECT"
        const val ACTION_DISCONNECT = "com.vortex.vpn.DISCONNECT"
        const val EXTRA_IPV4 = "extra_ipv4"
        const val EXTRA_IPV6 = "extra_ipv6"
        const val EXTRA_DNS = "extra_dns"
        const val EXTRA_SERVER_NAME = "extra_server_name"
    }
}
