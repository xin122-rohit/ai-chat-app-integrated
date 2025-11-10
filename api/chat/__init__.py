import logging
import json
import time
import azure.functions as func
from azure.identity import DefaultAzureCredential
import requests

# === UPDATE THESE VALUES ===
PROJECT_NAME = "agent-to-agent-5055"           # e.g., myagentproj
AI_SERVICE_NAME = "agent-to-agent-5055-resource"     # e.g., myai
ASSISTANT_ID = "asst_zQ8ANX9CJfElxVlHKEKiLa5P"                   # from portal
API_VERSION = "2024-07-18"


BASE_URL = f"https://{AI_SERVICE_NAME}.services.ai.azure.com/api/projects/{PROJECT_NAME}"

def get_token():
    credential = DefaultAzureCredential()
    return credential.get_token("https://ai.azure.com").token

def call_api(method, url, json_body=None):
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    }
    resp = requests.request(method, url, headers=headers, json=json_body)
    resp.raise_for_status()
    return resp.json()

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        user_message = req_body.get("message")
        if not user_message:
            return func.HttpResponse(
                json.dumps({"error": "Field 'message' is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # 1. Create new thread
        thread = call_api("POST", f"{BASE_URL}/threads?api-version={API_VERSION}", {})
        thread_id = thread["id"]

        # 2. Add user message
        call_api("POST", f"{BASE_URL}/threads/{thread_id}/messages?api-version={API_VERSION}",
                 {"role": "user", "content": user_message})

        # 3. Start run
        run = call_api("POST", f"{BASE_URL}/threads/{thread_id}/runs?api-version={API_VERSION}",
                       {"assistant_id": ASSISTANT_ID})
        run_id = run["id"]

        # 4. Poll until completed
        while True:
            status_resp = call_api("GET", f"{BASE_URL}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}")
            status = status_resp["status"]
            if status == "completed":
                break
            if status in ["failed", "cancelled"]:
                return func.HttpResponse(
                    json.dumps({"error": f"Run {status}"}),
                    status_code=500,
                    mimetype="application/json"
                )
            time.sleep(1.5)

        # 5. Get reply
        messages = call_api("GET", f"{BASE_URL}/threads/{thread_id}/messages?api-version={API_VERSION}")
        assistant_msg = next((m for m in messages["data"] if m["role"] == "assistant"), None)
        reply = assistant_msg["content"][0]["text"]["value"] if assistant_msg else "No reply"

        return func.HttpResponse(
            json.dumps({"reply": reply}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
