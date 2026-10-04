"""
VORTEX VPN - Health Check CLI Utility
Polls the control plane and outputs tabular health diagnostics.
"""
import sys
import httpx

def main():
    api_url = "http://127.0.0.1:8000/api/v1"
    print(f"Connecting to VORTEX VPN control plane at {api_url}...")
    try:
        r = httpx.get(f"{api_url}/health", timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            fleet = data.get("fleet", {})
            print("==================================================")
            print("CONTROL PLANE STATUS: HEALTHY")
            print("==================================================")
            print(f"Total Servers:       {fleet.get('total_servers')}")
            print(f"Online Servers:      {fleet.get('online_servers')}")
            print(f"Fleet Availability:  {fleet.get('availability_percentage')}%")
            print(f"Total Bandwidth:     {fleet.get('total_bandwidth_mbps')} Mbps")
            print(f"Active Tunnels:      {fleet.get('active_connections')}")
            print("==================================================")
        else:
            print(f"[ERROR] Control plane returned status {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[ERROR] Unable to reach control plane: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
