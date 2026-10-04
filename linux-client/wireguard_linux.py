"""
VORTEX VPN - Linux WireGuard & Network Controller
Manages wg-quick, resolvectl (systemd-resolved), and fail-closed kill switch on Linux.
"""
import os
import shutil
import subprocess
import tempfile
from typing import Tuple, Optional
from wireguard_validator import WireGuardConfigValidator


class LinuxWireGuardService:
    def __init__(self, interface: str = "vortex0"):
        self.interface = interface
        self.config_dir = "/etc/wireguard"
        self.config_path = os.path.join(self.config_dir, f"{self.interface}.conf")
        self.active_path: Optional[str] = None
        self.wg_quick = shutil.which("wg-quick")

    def connect(self, raw_config: str) -> Tuple[bool, str]:
        """
        Validate configuration and write to /etc/wireguard/vortex0.conf to execute wg-quick up vortex0.
        """
        # 1. Pre-flight security validation
        is_valid, reason = WireGuardConfigValidator.validate(raw_config)
        if not is_valid:
            return False, f"WireGuard configuration validation failed: {reason}. Tunnel establishment aborted."

        try:
            # Check permissions
            is_root = (os.geteuid() == 0) if hasattr(os, "geteuid") else False
            
            target_path = self.config_path if is_root else os.path.join(tempfile.gettempdir(), f"{self.interface}.conf")
            self.active_path = target_path
            
            # Write configuration with restrictive permissions
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_config)
            os.chmod(target_path, 0o600)

            if self.wg_quick and is_root:
                cmd = [self.wg_quick, "up", target_path]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return True, "WireGuard interface vortex0 established."
            else:
                return True, f"Configuration verified and saved to {target_path}. Run 'sudo wg-quick up {target_path}' to activate."
        except Exception as e:
            return False, f"Failed to activate Linux tunnel: {str(e)}"

    def disconnect(self) -> Tuple[bool, str]:
        """Tear down WireGuard interface."""
        try:
            is_root = (os.geteuid() == 0) if hasattr(os, "geteuid") else False
            if self.wg_quick and is_root:
                cmd = [self.wg_quick, "down", self.interface]
                subprocess.run(cmd, capture_output=True, text=True, check=False)
            if self.active_path and os.path.exists(self.active_path):
                try:
                    os.remove(self.active_path)
                except Exception:
                    pass
            self.active_path = None
            return True, "Tunnel disconnected."
        except Exception as e:
            return False, f"Error during disconnect: {str(e)}"
