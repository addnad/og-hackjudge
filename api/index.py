import os
import uuid
import time
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
load_dotenv()

app = Flask(__name__)
CORS(app)

_mongo_client = None
def get_col():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(os.getenv("MONGO_URI"))
    return _mongo_client["og_hackjudge"]["projects"]

_og_client = None
def get_og_client():
    global _og_client
    if _og_client is None:
        import opengradient as og
        _og_client = og.Client(private_key=os.getenv("OG_PRIVATE_KEY"))
    return _og_client

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_prompt(p):
    return f"""You are an expert hackathon judge evaluating projects built on OpenGradient.
Score this project across 5 categories. Respond ONLY with valid JSON, no markdown, no explanation.

Project Name: {p.get("name","")}
Description: {p.get("description","")}
Tech Stack: {p.get("tech_stack","")}
OpenGradient Features Used: {p.get("og_features","")}
Demo URL: {p.get("demo_url","")}
Repo URL: {p.get("repo_url","")}
Notes: {p.get("notes","")}

Respond with this exact JSON structure:
{{
  "weighted_total": <number 0-100>,
  "tier": <"Outstanding"|"Excellent"|"Good"|"Needs Improvement"|"Insufficient">,
  "scores": {{"innovation": <0-25>, "technical": <0-25>, "ux": <0-20>, "completeness": <0-15>, "impact": <0-15>}},
  "summary": "<2 sentence summary>",
  "strengths": ["<strength1>", "<strength2>"],
  "improvements": ["<improvement1>", "<improvement2>"],
  "detailed_feedback": {{"innovation": "<fb>", "technical": "<fb>", "ux": "<fb>", "completeness": "<fb>", "impact": "<fb>"}}
}}"""

def parse_llm_output(output):
    output = output.strip()
    if output.startswith("```"):
        output = output.split("```")[1]
        if output.startswith("json"):
            output = output[4:]
    return json.loads(output.strip())

def fallback_score(p):
    desc = p.get("description",""); tech = p.get("tech_stack","")
    og_features = p.get("og_features",""); demo = p.get("demo_url","")
    repo = p.get("repo_url",""); notes = p.get("notes",""); name = p.get("name","")
    f1=min(len(desc.split())/5,10); f2=min(len([x for x in tech.split(",") if x.strip()])*2,10)
    f3=min(len([x for x in og_features.split(",") if x.strip()])*2.5,10)
    f4=min((1 if demo else 0)+(1 if repo else 0)+(1 if notes else 0)+(1 if name else 0),4)*2.5
    innovation=min((f3*10+f1*5)/1.5,25); technical=min((f2*10+f4*5)/1.5,25)
    ux=min((f4*8+f1*4)/1.2,20); completeness=min(f4*0.625*4,15); impact=min((f1*6+f3*6)/1.2,15)
    total=round(innovation+technical+ux+completeness+impact,1)
    if total>=85: tier="Outstanding"
    elif total>=70: tier="Excellent"
    elif total>=55: tier="Good"
    elif total>=40: tier="Needs Improvement"
    else: tier="Insufficient"
    return {"weighted_total":total,"tier":tier,"scores":{"innovation":round(innovation,1),"technical":round(technical,1),"ux":round(ux,1),"completeness":round(completeness,1),"impact":round(impact,1)},"summary":f"This project scored {total}/100.","strengths":["Shows initiative in building on OpenGradient"],"improvements":["Add more detail to your submission"],"detailed_feedback":{"innovation":"N/A","technical":"N/A","ux":"N/A","completeness":"N/A","impact":"N/A"}}

def score_project(p):
    messages = [{"role": "user", "content": build_prompt(p)}]
    try:
        client = get_og_client()
        result = client.llm.chat(
            model=og.TEE_LLM.CLAUDE_HAIKU_4_5,
            messages=messages,
            max_tokens=800,
            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
        )
        evaluation = parse_llm_output(result.chat_output.get("content", "").strip())
        _sig = getattr(result, "tee_signature", "") or ""
        _ts = getattr(result, "tee_timestamp", "") or ""
        print(f"TEE_SIG_DEBUG: sig={_sig[:20] if _sig else None} ts={_ts}")
        evaluation["_tee_signature"] = _sig
        evaluation["_tee_timestamp"] = _ts
        return evaluation
    except Exception as e:
        print(f"LLM scoring failed: {e}, falling back to algorithmic")
        fb = fallback_score(p)
        fb["_llm_error"] = str(e)
        return fb

@app.route("/")
def landing():
    with open(os.path.join(base, "landing.html"), "r") as f:
        return f.read(), 200, {"Content-Type": "text/html"}

@app.route("/app")
def index():
    with open(os.path.join(base, "index.html"), "r") as f:
        return f.read(), 200, {"Content-Type": "text/html"}

@app.route("/api/projects", methods=["GET"])
def get_projects():
    projects = list(get_col().find({}, {"_id": 0}).sort("created_at", -1))
    return jsonify({"projects": projects})

@app.route("/api/projects", methods=["POST"])
def submit_project():
    data = request.json
    project = {"id": str(uuid.uuid4())[:8], "name": data.get("name", ""), "description": data.get("description", ""), "tech_stack": data.get("tech_stack", ""), "og_features": data.get("og_features", ""), "demo_url": data.get("demo_url", ""), "repo_url": data.get("repo_url", ""), "notes": data.get("notes", ""), "wallet": data.get("wallet", ""), "status": "pending", "created_at": time.time()}
    get_col().insert_one(project)
    project.pop("_id", None)
    return jsonify({"project": project})

@app.route("/api/evaluate/<pid>", methods=["POST"])
def evaluate(pid):
    p = get_col().find_one({"id": pid}, {"_id": 0})
    if not p:
        return jsonify({"error": "Project not found"}), 404
    try:
        data_check = request.json or {}
        if p.get("status") == "evaluated":
            return jsonify({"error": "This project has already been evaluated."}), 400
        submitter_wallet = p.get("wallet", "").lower()
        evaluator_wallet = data_check.get("wallet", "").lower()
        if submitter_wallet and evaluator_wallet and submitter_wallet != evaluator_wallet:
            return jsonify({"error": "Only the project owner can evaluate this project."}), 403
        start = time.time()
        evaluation = score_project(p)
        elapsed = round(time.time() - start, 2)
        tee_sig = evaluation.pop("_tee_signature", "") or ""
        tee_ts = evaluation.pop("_tee_timestamp", "") or ""
        get_col().update_one({"id": pid}, {"$set": {"evaluation": evaluation, "tee_signature": tee_sig, "tee_timestamp": tee_ts, "status": "evaluated"}})
        return jsonify({"project_name": p["name"], "evaluation": evaluation, "metadata": {"model": "Claude Haiku 4.5 (TEE-verified via x402)", "inference_mode": "TEE", "inference_time_seconds": elapsed, "tee_signature": tee_sig, "tee_timestamp": tee_ts, "payment_hash": "x402-opg"}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/projects/<pid>", methods=["PUT"])
def edit_project(pid):
    try:
        data = request.json or {}
        p = get_col().find_one({"id": pid}, {"_id": 0})
        if not p:
            return jsonify({"error": "Project not found"}), 404
        if p.get("status") == "evaluated":
            return jsonify({"error": "Cannot edit an evaluated project."}), 400
        submitter_wallet = p.get("wallet", "").lower()
        editor_wallet = data.get("wallet", "").lower()
        if submitter_wallet and editor_wallet and submitter_wallet != editor_wallet:
            return jsonify({"error": "Only the project owner can edit this project."}), 403
        update = {k: data[k] for k in ["name","description","tech_stack","og_features","demo_url","repo_url","notes"] if k in data}
        get_col().update_one({"id": pid}, {"$set": update})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/clear", methods=["DELETE"])
def clear_projects():
    if request.headers.get("X-Admin-Key") != "og-hackjudge-clear-2024":
        return jsonify({"error": "Unauthorized"}), 401
    result = get_col().delete_many({})
    return jsonify({"deleted": result.deleted_count})

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    all_evaluated = list(get_col().find({"status": "evaluated"}, {"_id": 0}))
    valid = [p for p in all_evaluated if p.get("evaluation") and isinstance(p["evaluation"].get("weighted_total"), (int, float))]
    valid = sorted(valid, key=lambda x: x["evaluation"]["weighted_total"], reverse=True)
    lb = [{"rank": i+1, "project_name": p["name"], "description": p.get("description",""), "tech_stack": p.get("tech_stack",""), "og_features": p.get("og_features",""), "demo_url": p.get("demo_url",""), "repo_url": p.get("repo_url",""), "wallet": p.get("wallet",""), "score": p["evaluation"]["weighted_total"], "tier": p["evaluation"]["tier"], "scores": p["evaluation"].get("scores",{}), "summary": p["evaluation"].get("summary",""), "strengths": p["evaluation"].get("strengths",[]), "improvements": p["evaluation"].get("improvements",[]), "tee_signature": p.get("tee_signature","")} for i, p in enumerate(valid)]
    return jsonify({"leaderboard": lb})

if __name__ == "__main__":
    app.run(debug=True, port=8000)
