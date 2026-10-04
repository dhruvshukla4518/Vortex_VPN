"""
VORTEX VPN - Streamlit Administrative Command Center
Real-time fleet monitoring, server management, telemetry analytics, and Plotly charts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import httpx

st.set_page_config(
    page_title="VORTEX VPN — Admin Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #111318;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

API_BASE = st.sidebar.text_input("Control Plane API URL", "http://127.0.0.1:8000/api/v1")

@st.cache_data(ttl=5)
def fetch_fleet_servers():
    try:
        resp = httpx.get(f"{API_BASE}/servers?only_active=false", timeout=4.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

@st.cache_data(ttl=5)
def fetch_system_health():
    try:
        resp = httpx.get(f"{API_BASE}/health", timeout=4.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

st.title("🛡️ VORTEX VPN — Fleet Management Console")

health_data = fetch_system_health()
servers = fetch_fleet_servers()

if health_data:
    fleet = health_data.get("fleet", {})
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Users", fleet.get("total_users", 0))
    col2.metric("Active Tunnels", fleet.get("active_connections", 0))
    col3.metric("Online Nodes", f"{fleet.get('online_servers', 0)} / {fleet.get('total_servers', 0)}")
    col4.metric("Fleet Bandwidth", f"{fleet.get('total_bandwidth_mbps', 0)} Mbps")
    col5.metric("Availability", f"{fleet.get('availability_percentage', 0)}%")
else:
    st.warning("Control plane offline or unreachable. Please verify FastAPI backend is running.")

st.divider()

# Charts Section
if servers:
    df = pd.DataFrame(servers)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌐 Node Latency Comparison (ms)")
        fig_lat = px.bar(
            df, x="city", y="latency_ms", color="country",
            labels={"city": "Server Location", "latency_ms": "Ping Latency (ms)"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_lat, use_container_width=True)

    with c2:
        st.subheader("⚡ Resource Load Distribution (%)")
        fig_load = px.bar(
            df, x="city", y="load_percentage", color="load_percentage",
            color_continuous_scale="Viridis",
            labels={"city": "Server Location", "load_percentage": "Combined Load (%)"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_load, use_container_width=True)

    st.subheader("📋 Active Server Fleet Directory")
    display_cols = ["country", "country_code", "city", "hostname", "public_ip", "status", "latency_ms", "load_percentage", "active_connections", "capacity"]
    st.dataframe(df[display_cols], use_container_width=True)

# Add Node Form
st.divider()
st.subheader("➕ Deploy New VPN Server Node")
with st.form("add_server_form"):
    f_col1, f_col2, f_col3 = st.columns(3)
    country = f_col1.text_input("Country", "Canada")
    country_code = f_col2.text_input("Country Code (2-letter)", "CA")
    city = f_col3.text_input("City", "Toronto")
    
    hostname = f_col1.text_input("Hostname", "ca-tor-01.vortexvpn.net")
    public_ip = f_col2.text_input("Public IP", "198.51.100.25")
    endpoint = f_col3.text_input("WireGuard Endpoint", "ca-tor-01.vortexvpn.net:51820")
    
    pubkey = f_col1.text_input("WireGuard Public Key", "iAl7zT484VzRfW5BJa5+gOWlJa7O55tmADWb42eP0Q=")
    capacity = f_col2.number_input("Connection Capacity", value=1500, min_value=100)

    submitted = st.form_submit_button("Register Server Node")
    if submitted:
        payload = {
            "country": country,
            "country_code": country_code,
            "city": city,
            "hostname": hostname,
            "public_ip": public_ip,
            "wireguard_endpoint": endpoint,
            "wireguard_port": 51820,
            "wireguard_public_key": pubkey,
            "internal_subnet": "10.8.0.0/24",
            "capacity": int(capacity)
        }
        try:
            r = httpx.post(f"{API_BASE}/admin/servers", json=payload, timeout=5.0)
            if r.status_code == 201:
                st.success(f"Server '{hostname}' registered successfully!")
                st.rerun()
            else:
                st.error(f"Registration failed: {r.text}")
        except Exception as err:
            st.error(f"Error: {err}")
