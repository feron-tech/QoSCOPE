QOD_CONTENT = """
{
  "device": {
    "ipv4Address": {
      "privateAddress": "{{ UE_IP }}"
    }
  },
  "applicationServer": {
    "ipv4Address": "10.45.0.1"
  },
  "applicationServerPorts": {
    "ranges": null,
    "ports": [
      5202
    ]
  },
  "qosProfile": "qos_20",
  "webhook": {
    "notificationUrl": "/gohaveasnack",
    "notificationAuthToken": "wowsosecretwowsosecretwowsosecret"
  },
  "duration": 45
}
"""


def get_qod_content(ue_ip: str) -> str:
    return QOD_CONTENT.replace("{{ UE_IP }}", ue_ip)
