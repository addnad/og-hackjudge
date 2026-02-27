import os
import uuid
import time
import json
import pathlib
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = pathlib.Path('projects.json')

def load_projects():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_projects(projects):
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f)

PROJECTS = load_projects()

def score_project(p):
    desc = p.get('description', '')
    tech = p.get('tech_stack', '')
    og = p.get('og_features', '')
    demo = p.get('demo_url', '')
    repo = p.get('repo_url', '')
    notes = p.get('notes', '')
    name = p.get('name', '')
    f1 = min(len(desc.split()) / 5, 10)
    f2 = min(len([x for x in tech.split(',') if x.strip()]) * 2, 10)
    f3 = min(len([x for x in og.split(',') if x.strip()]) * 2.5, 10)
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
    strengths, improvements = [], []
    if f2 >= 6: strengths.append("Strong and diverse tech stack")
    if f3 >= 5: strengths.append("Good use of OpenGradient features")
    if f1 >= 6: strengths.append("Detailed project description")
    if demo and repo: strengths.append("Complete project with demo and repo")
    if not strengths: strengths.append("Shows initiative in building on OpenGradient")
    if f1 < 6: improvements.append("Add more detail to your project description")
    if f2 < 6: improvements.append("Expand your tech stack details")
    if f3 < 5: improvements.append("Integrate more OpenGradient features")
    if not demo or not repo: improvements.append("Add a demo URL and repo link")
    return {
        "weighted_total": total, "tier": tier,
        "scores": {"innovation": round(innovation,1), "technical": round(technical,1), "ux": round(ux,1), "completeness": round(completeness,1), "impact": round(impact,1)},
        "summary": f"This project scored {total}/100. {tier} execution with strong use of OpenGradient technology.",
        "strengths": strengths, "improvements": improvements,
        "detailed_feedback": {
            "innovation": f"Innovation score: {round(innovation,1)}/25 based on description depth and OG feature usage.",
            "technical": f"Technical score: {round(technical,1)}/25 based on tech stack and completeness.",
            "ux": f"UX score: {round(ux,1)}/20 based on project presentation.",
            "completeness": f"Completeness score: {round(completeness,1)}/15 based on demo, repo, and notes.",
            "impact": f"Impact score: {round(impact,1)}/15 based on description and OG integration."
        }
    }

@app.route("/")
def landing():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "landing.html"), "r") as f:
        return f.read(), 200, {"Content-Type": "text/html"}

@app.route("/app")
def index():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "index.html"), "r") as f:
        return f.read(), 200, {"Content-Type": "text/html"}

@app.route("/api/projects", methods=["GET"])
def get_projects():
    return jsonify({"projects": list(PROJECTS.values())})

@app.route("/api/projects", methods=["POST"])
def submit_project():
    data = request.json
    pid = uuid.uuid4().hex[:8]
    project = {"id": pid, "name": data.get("name",""), "description": data.get("description",""), "tech_stack": data.get("tech_stack",""), "og_features": data.get("og_features",""), "demo_url": data.get("demo_url",""), "repo_url": data.get("repo_url",""), "notes": data.get("notes",""), "wallet": data.get("wallet",""), "status": "pending"}
    PROJECTS[pid] = project
    save_projects(PROJECTS)
    return jsonify({"project": project})

@app.route("/api/evaluate/<pid>", methods=["POST"])
def evaluate(pid):
    p = PROJECTS.get(pid)
    if not p:
        return jsonify({"error": "Project not found"}), 404
    try:
        data_check = request.json
        submitter_wallet = p.get("wallet", "").lower()
        evaluator_wallet = data_check.get("wallet", "").lower()
        if submitter_wallet and evaluator_wallet and submitter_wallet != evaluator_wallet:
            return jsonify({"error": "Only the project owner can evaluate this project."}), 403
        tx_hash = data_check.get("tx_hash", "")
        start = time.time()
        evaluation = score_project(p)
        elapsed = round(time.time() - start, 2)
        PROJECTS[pid]["evaluation"] = evaluation
        PROJECTS[pid]["status"] = "evaluated"
        save_projects(PROJECTS)
        return jsonify({"project_name": p["name"], "evaluation": evaluation, "metadata": {"model": "HackJudge Scorer (On-Chain)", "inference_mode": "VANILLA", "inference_time_seconds": elapsed, "payment_hash": tx_hash, "explorer_url": f"https://explorer.opengradient.ai/tx/{tx_hash}"}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    evaluated = [p for p in PROJECTS.values() if p.get("status") == "evaluated"]
    evaluated = sorted(evaluated, key=lambda x: x["evaluation"]["weighted_total"], reverse=True)
    lb = []
    for i, p in enumerate(evaluated):
        lb.append({"rank": i+1, "project_name": p["name"], "description": p.get("description",""), "tech_stack": p.get("tech_stack",""), "og_features": p.get("og_features",""), "demo_url": p.get("demo_url",""), "repo_url": p.get("repo_url",""), "wallet": p.get("wallet",""), "score": p["evaluation"]["weighted_total"], "tier": p["evaluation"]["tier"], "scores": p["evaluation"]["scores"], "summary": p["evaluation"]["summary"], "strengths": p["evaluation"]["strengths"], "improvements": p["evaluation"]["improvements"], "explorer_url": ""})
    return jsonify({"leaderboard": lb})

if __name__ == "__main__":
    app.run(debug=True, port=8000)
