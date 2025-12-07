import os
from aiohttp import web

async def healthz(request):
    return web.Response(text="OK", status=200)

async def readyz(request):
    # Here you would check DB/Redis connectivity
    # For now, always ready
    return web.Response(text="READY", status=200)

async def metrics(request):
    # Example metrics output
    metrics = """
# HELP kokoromichi_requests_total Total requests
# TYPE kokoromichi_requests_total counter
kokoromichi_requests_total 42
# HELP kokoromichi_pending_tx_total Pending transactions
# TYPE kokoromichi_pending_tx_total gauge
kokoromichi_pending_tx_total 3
"""
    return web.Response(text=metrics, content_type="text/plain")

app = web.Application()
app.router.add_get('/healthz', healthz)
app.router.add_get('/readyz', readyz)
app.router.add_get('/metrics', metrics)

if __name__ == "__main__":
    port = int(os.getenv("METRICS_PORT", "8000"))
    web.run_app(app, host="0.0.0.0", port=port)
