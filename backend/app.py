import asyncio
import os
import time
from collections import deque

import psutil
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Intelligent Load Balancer Backend")

SERVER_ID = os.getenv("SERVER_ID", "server-unknown")
STARTED_AT = time.time()

SIMULATED_OVERLOAD = False

#REquest metrics
active_requests = 0
response_times = deque(maxlen=100)
#Prime CPU measurement so subsequent readings are meaningful.
psutil.cpu_percent(interval= None)
class OverloadRequest(BaseModel):
    enabled: bool

@app.middleware("http")
async def collect_request_metrics(request, call_next):
    global active_requests
    active_requests += 1
    started = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        elapsed_ms  = (time.perf_counter() - started) * 1000
        response_times.append(elapsed_ms)
        active_requests -=1
        
@app.get("/")
async def home():
    return {
        "server_id":SERVER_ID,
        "message":"Request handled successfully",
        "overloaded": SIMULATED_OVERLOAD
    }

@app.get("/health")
async def health():
    if SIMULATED_OVERLOAD:
        return JSONResponse(
            status_code = 503,
            content = {
                "server_id": SERVER_ID,
                "status": "overloaded",
            }
        )
    return {
        "server_id": SERVER_ID,
        "status": "healthy",
        "uptime_seconds": round(time.time() - STARTED_AT, 2),
    }

@app.get("/metrics")
async def metrics():
    memory = psutil.virtual_memory()
    avg_response_time = (
        sum(response_times) / len(response_times)
        if response_times
        else 0.0
    )
    return {
        "server_id": SERVER_ID,
        "healthy": not SIMULATED_OVERLOAD,
        "overloaded": SIMULATED_OVERLOAD,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent":memory.percent,
        "active_requests":active_requests,
        "avg_response_time_ms" : round(avg_response_time, 2),
        "uptime_seconds": round(time.time() - STARTED_AT, 2)
    }
@app.get("/work")
async def work(
    delay: float = Query(default=0, ge=0, le=10)
):
    #Simulate a slow request for load-testing experiments
    if SIMULATED_OVERLOAD:
        raise HTTPException(
            status_code = 503,
            detail = "Server is overloaded"
        )
    await asyncio.sleep(delay)
    return {
        "server_id": SERVER_ID,
        "processing_delay_seconds": delay,
        "status": "completed"
    }
    
@app.post("/admin/overload")
async def set_overload(request: OverloadRequest):
    #"demo endpoint to simulate a server becoming overloaded"
    global SIMULATED_OVERLOAD
    SIMULATED_OVERLOAD = request.enabled
    return {
        "server_id": SERVER_ID,
        "overloaded": SIMULATED_OVERLOAD,
    }