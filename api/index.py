import os
from dotenv import load_dotenv

import opengradient as og




import uuid
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

def llm_score_project(project):
    try:
        description = project.get("description", "")
        tech_stack = project.get("tech_stack", "")
        repo_url = project.get("repo_url", "")
        demo_url = project.get("demo_url", "")

        prompt = f"""
You are an expert hackathon judge. Evaluate this project strictly and quantitatively.

Project description: {description}
Tech stack: {tech_stack}
Repo: {repo_url}
Demo: {demo_url}

Score each category 1-10:
- Innovation
- Technical Implementation
- User Experience / Design
- Completeness / Functionality
- Impact / Usefulness

Calculate weighted total score out of 100: Innovation 25%, Tech 30%, UX 20%, Completeness 15%, Impact 10%.

Tier: "S" (90+), "A" (80-89), "B" (70-79), "C" (60-69), "D" (<60)

Output **ONLY** valid JSON, no explanations, no markdown, no code blocks, nothing else:
{{
  "scores": {{
    "innovation": integer,
    "technical": integer,
    "ux": integer,
    "completeness": integer,
    "impact": integer
  }},
  "weighted_total": float,
  "tier": string,
  "summary": string,
  "strengths": string,
  "improvements": string
}}
"""

        result = og_client.llm.chat(
            model=og.TEE_LLM.CLAUDE_SONNET_4_5,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.6,
            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
        )

        output = result.chat_output["content"]
        tx_hash = result.transaction_hash if hasattr(result, "transaction_hash") else "external"

        import json
        import re

        eval_data = json.loads(output)

        eval_data["tx_hash"] = tx_hash
        eval_data["inference_time_seconds"] = 5.0  # placeholder
        eval_data["payment_hash"] = tx_hash

        return eval_data

    except Exception as e:
        return {"error": str(e), "weighted_total": 0, "tier": "D"}




load_dotenv()

try:
    og_client = og.Client(private_key=os.getenv("OG_PRIVATE_KEY"))
    print("OpenGradient client initialized successfully!")
except Exception as e:
    print(f"Error initializing client: {e}")

try:
    approval = og_client.llm.ensure_opg_approval(opg_amount=5.0)
    if hasattr(approval, "transaction_hash") and approval.transaction_hash:
        print(f"Approval transaction sent: {approval.transaction_hash}")
    else:
        print("OPG approval already sufficient or not needed.")
except Exception as e:
    print(f"Approval check failed (may be ok if already approved): {e}")


app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['og_hackjudge']
projects_col = db['projects']

def score_project(p):
    import opengradient as og_sdk
    import json as json_mod

    desc = p.get('description', '')
    tech = p.get('tech_stack', '')
    og_features = p.get('og_features', '')
    demo = p.get('demo_url', '')
    repo = p.get('repo_url', '')
    notes = p.get('notes', '')
    name = p.get('name', '')

    prompt = f"""You are an expert hackathon judge evaluating projects built on OpenGradient.
Score this project across 5 categories. Respond ONLY with valid JSON, no markdown, no explanation.

Project Name: {name}
Description: {desc}
Tech Stack: {tech}
OpenGradient Features Used: {og_features}
Demo URL: {demo}
Repo URL: {repo}
Notes: {notes}

Respond with this exact JSON structure:
{{
  "weighted_total": <number 0-100>,
  "tier": <"Outstanding"|"Excellent"|"Good"|"Needs Improvement"|"Insufficient">,
  "scores": {{
    "innovation": <number 0-25>,
    "technical": <number 0-25>,
    "ux": <number 0-20>,
    "completeness": <number 0-15>,
    "impact": <number 0-15>
  }},
  "summary": "<2 sentence summary>",
  "strengths": ["<strength1>", "<strength2>"],
  "improvements": ["<improvement1>", "<improvement2>"],
  "detailed_feedback": {{
    "innovation": "<feedback>",
    "technical": "<feedback>",
    "ux": "<feedback>",
    "completeness": "<feedback>",
    "impact": "<feedback>"
  }}
}}"""

    try:
        og_client = og_sdk.Client(private_key=os.getenv("OG_PRIVATE_KEY"))
        result = og_client.llm.chat(
            model=og_sdk.TEE_LLM.CLAUDE_HAIKU_4_5,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            x402_settlement_mode=og_sdk.x402SettlementMode.SETTLE_BATCH
        )
        output = result.chat_output.get('content', '')
        # Strip markdown if present
        output = output.strip()
        if output.startswith('```'):
            output = output.split('```')[1]
            if output.startswith('json'):
                output = output[4:]
        evaluation = json_mod.loads(output.strip())
        return evaluation
    except Exception as e:
        # Fallback to algorithmic scoring if LLM fails
        print(f"LLM scoring failed: {e}, falling back to algorithmic scoring")
        f1 = min(len(desc.split()) / 5, 10)
        f2 = min(len([x for x in tech.split(',') if x.strip()]) * 2, 10)
        f3 = min(len([x for x in og_features.split(',') if x.strip()]) * 2.5, 10)
        f4 = min((1 if demo else 0) + (1 if repo else 0) + (1 if notes else 0) + (1 if name else 0), 4) * 2.5
        innovation = min((f3 * 10 + f1 * 5) / 1.5, 25)
        technical = min((f2 * 10 + f4 * 5) / 1.5, 25)
        ux = min((f4 * 8 + f1 * 4) / 1.2, 20)
        completeness = min(f4 * 0.625 * 4, 15)
        impact = min((f1 * 6 + f3 * 6) / 1.2, 15)
        total = round(innovation + technical + ux + completeness + impact, 1)
        if total >= 85: tier = "Outstanding"
        elif total >= 70: tier = "Excellent"
        elif total >= 55: tier = "Good"
        elif total >= 40: tier = "Needs Improvement"
        else: tier = "Insufficient"
        return {
            "weighted_total": total, "tier": tier,
            "scores": {"innovation": round(innovation,1), "technical": round(technical,1), "ux": round(ux,1), "completeness": round(completeness,1), "impact": round(impact,1)},
            "summary": f"This project scored {total}/100. {tier} execution.",
            "strengths": ["Shows initiative in building on OpenGradient"],
            "improvements": ["Add more detail to your submission"],
            "detailed_feedback": {"innovation": "N/A", "technical": "N/A", "ux": "N/A", "completeness": "N/A", "impact": "N/A"}
        }

@app.route("/")
def landing():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "landing.html"), "r") as f:
        return f.read(), 200, {"Content-Type": "text/html"}

@app.route("/app")
def index():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "index.html"), "r") as f:
        return f.read(), 200, {"Content-Type": "text/html"}

@app.route("/api/projects", methods=["GET"])
def get_projects():
    projects = list(projects_col.find({}, {'_id': 0}).sort('created_at', -1))

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)

@app.route("/api/evaluate/<pid>", methods=["POST"])
def evaluate(pid):
    p = projects_col.find_one({"id": pid}, {'_id': 0})
    if not p:
        return jsonify({"error": "Project not found"}), 404

    evaluation = llm_score_project(p)

    projects_col.update_one(
        {"id": pid},
        {"$set": {"evaluation": evaluation, "status": "evaluated"}}
    )

    return jsonify({
        "project_name": p["name"],
        "evaluation": evaluation,
        "metadata": {
            "model": "Claude Sonnet 4.5 (TEE LLM)",
            "inference_mode": "x402 Paid",
            "inference_time_seconds": evaluation.get("inference_time_seconds", 0),
            "payment_hash": evaluation.get("payment_hash", "external"),
            "explorer_url": f"https://sepolia.basescan.org/tx/{evaluation.get('tx_hash', 'external')}"
        }
    })

