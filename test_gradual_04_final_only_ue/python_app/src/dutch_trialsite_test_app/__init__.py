from typing import Annotated
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from starlette.responses import HTMLResponse
from pathlib import Path

from .camara import request_qod, get_cluster_names
from .metrics import post_mqtt_metric

app = FastAPI()
root_html = Path("./static/index.html")


@app.get("/")
async def get_root() -> HTMLResponse:
    return HTMLResponse(status_code=200, content=root_html.read_text())


@app.get("/get_cluster_names")
async def get_cluster_names_() -> list[str]:
    return get_cluster_names()


@app.post("/request_qos")
async def request_qod_(addr: Annotated[int, Form()]) -> str:
    ue_ip = f"10.45.0.{addr}"
    return request_qod(ue_ip)


@app.post("/post_mqtt_metric/")
async def post_mqtt_metric_(value: Annotated[int, Form()]):
    post_mqtt_metric(value)
    return PlainTextResponse(
        status_code=200, content=f"Submitted MQTT metric with value: {value}"
    )
