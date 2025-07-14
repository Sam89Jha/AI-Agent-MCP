from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import importlib
import sys
import os
import json

# Ensure lambda-functions is in the path for imports
sys.path.append(os.path.dirname(__file__))

from send_message import lambda_handler as send_message_handler
from get_message import lambda_handler as get_message_handler
from make_call import lambda_handler as make_call_handler

app = FastAPI(title="Local Lambda API Gateway Emulator")

@app.post("/lambda/send_message")
async def send_message(request: Request):
    event = await request.json()
    result = send_message_handler({"body": json.dumps(event)}, None)
    body = result.get("body", "{}")
    try:
        content = json.loads(body)
    except Exception:
        content = {"error": "Invalid response from Lambda handler", "raw": body}
    return JSONResponse(status_code=result.get("statusCode", 200), content=content)

@app.get("/lambda/get_message")
async def get_message(booking_code: str, limit: int = 50, start_key: str = ""):
    event = {"booking_code": booking_code, "limit": limit}
    if start_key:
        event["start_key"] = start_key
    result = get_message_handler(event, None)
    body = result.get("body", "{}")
    try:
        content = json.loads(body)
    except Exception:
        content = {"error": "Invalid response from Lambda handler", "raw": body}
    return JSONResponse(status_code=result.get("statusCode", 200), content=content)

@app.post("/lambda/make_call")
async def make_call(request: Request):
    event = await request.json()
    result = make_call_handler({"body": json.dumps(event)}, None)
    body = result.get("body", "{}")
    try:
        content = json.loads(body)
    except Exception:
        content = {"error": "Invalid response from Lambda handler", "raw": body}
    return JSONResponse(status_code=result.get("statusCode", 200), content=content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000) 