import httpx
import base64
import json
from .qod_content import get_qod_content

AF_ENDPOINT = "http://af-service-pool.open5gs:8000"
CLIENT_ID = "opencaller"
CLIENT_SECRET = "envelope"
AUTH_HEADER_DATA = base64.b64encode(
    f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
).decode()


def request_token(scope: str) -> str:
    print("Requesting access token for $CLIENT_ID")
    # For multiple scopes, use space seperation
    form_data = {
        "grant_type": "client_credentials",
        "scope": scope,
    }
    print(f"{AF_ENDPOINT}/oauth2/token")
    token_rsp = httpx.post(
        f"{AF_ENDPOINT}/oauth2/token",
        headers={"Authorization": f"Basic {AUTH_HEADER_DATA}"},
        data=form_data,
    ).text

    print(f"Got auth token: {token_rsp}")
    return json.loads(token_rsp)["access_token"]


def get_cluster_names() -> list[str]:
    token = request_token("ec-clusters-read")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    clusters_rsp = httpx.get(
        f"{AF_ENDPOINT}/edgecloud/v0/clusters",
        headers=headers,
    ).text
    print("Clusters response:")
    print(clusters_rsp)
    return [c["name"] for c in json.loads(clusters_rsp)]


def request_qod(ue_ip: str) -> str:
    token = request_token("qod-sessions-write")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    qod_rsp = httpx.post(
        f"{AF_ENDPOINT}/quality-on-demand/v0/sessions",
        content=get_qod_content(ue_ip),
        headers=headers,
    ).text
    return qod_rsp
