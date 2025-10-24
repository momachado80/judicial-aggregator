from fastapi import APIRouter
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
INGESTED_ITEMS = Counter("datajud_ingested_items_total", "Total items ingested", ["tribunal", "tipo"])
NOTIF_SENT = Counter("notifications_sent_total", "Total notifications sent", ["channel", "relevance"])
INGEST_DURATION = Histogram("datajud_ingest_duration_seconds", "Ingest duration", ["tribunal"])
API_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "endpoint"])

metrics_router = APIRouter()

@metrics_router.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
