package com.vortex.vpn

import android.content.Context
import com.wireguard.android.backend.GoBackend
import com.wireguard.android.backend.Tunnel
import com.wireguard.config.Config
import java.io.ByteArrayInputStream
import java.nio.charset.StandardCharsets

class WireGuardManager(private val context: Context) {

    private val backend = GoBackend(context)
    private var currentTunnel: VortexTunnel? = null

    class VortexTunnel(private val tunnelName: String) : Tunnel {
        override fun getName(): String = tunnelName
        override fun onStateChange(newState: Tunnel.State) {}
    }

    fun startTunnel(name: String, rawConfig: String): Tunnel.State {
        val config = Config.parse(ByteArrayInputStream(rawConfig.toByteArray(StandardCharsets.UTF_8)))
        val tunnel = VortexTunnel(name)
        currentTunnel = tunnel
        return backend.setState(tunnel, Tunnel.State.UP, config)
    }

    fun stopTunnel(): Tunnel.State {
        currentTunnel?.let {
            val state = backend.setState(it, Tunnel.State.DOWN, null)
            currentTunnel = null
            return state
        }
        return Tunnel.State.DOWN
    }

    fun getState(): Tunnel.State {
        return currentTunnel?.let { backend.getState(it) } ?: Tunnel.State.DOWN
    }
}
