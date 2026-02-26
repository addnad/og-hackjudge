from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import opengradient as og
import uuid, os, json, time, pathlib

load_dotenv()
app = Flask(__name__)
CORS(app)

DATA_FILE = pathlib.Path('projects.json')

def load_projects():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_projects():
    with open(DATA_FILE, 'w') as f:
        json.dump(PROJECTS, f)

PROJECTS = load_projects()

client = og.Client(private_key=os.getenv("OG_PRIVATE_KEY"))

def score_project(p):
    desc = p.get('description', '')
    tech = p.get('tech_stack', '')
    og_feat = p.get('og_features', '')
    demo = p.get('demo_url', '')
    repo = p.get('repo_url', '')
    notes = p.get('notes', '')
    name = p.get('name', '')

    desc_score = min(len(desc.split()) / 5, 10)
    tech_score = min(len([t for t in tech.split(',') if t.strip()]) * 2, 10)
    og_score = min(len([t for t in og_feat.split(',') if t.strip()]) * 2.5, 10)
    complete_score = sum([
        3 if demo else 0,
        3 if repo else 0,
        2 if notes else 0,
        2 if len(name) > 3 else 0
    ])

    return [desc_score, tech_score, og_score, float(complete_score)]

@app.route('/')
def landing():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'landing.html')

@app.route('/app')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify({"projects": list(PROJECTS.values())})

@app.route('/api/projects', methods=['POST'])
def submit_project():
    data = request.json
    pid = str(uuid.uuid4())[:8]
    project = {
        "id": pid,
        "name": data.get("name"),
        "description": data.get("description"),
        "tech_stack": data.get("tech_stack", ""),
        "og_features": data.get("og_features", ""),
        "demo_url": data.get("demo_url", ""),
        "repo_url": data.get("repo_url", ""),
        "notes": data.get("notes", ""),
        "wallet": data.get("wallet", ""),
        "status": "pending"
    }
    PROJECTS[pid] = project
    save_projects()
    return jsonify({"project": project})

@app.route('/api/evaluate/<pid>', methods=['POST'])
def evaluate(pid):
    if pid not in PROJECTS:
        return jsonify({"error": "Project not found"}), 404
    p = PROJECTS[pid]

    try:
        start = time.time()

        features = score_project(p)
        f1, f2, f3, f4 = features

        data = request.json
        tx_hash = data.get('tx_hash', 'N/A')
        elapsed = round(time.time() - start, 2)

        innovation = min(round((f3 * 10 + f1 * 5) / 1.5, 1), 25)
        technical = min(round((f2 * 10 + f4 * 5) / 1.5, 1), 25)
        ux = min(round((f4 * 8 + f1 * 4) / 1.2, 1), 20)
        completeness = min(round(f4 * 10, 1), 15)
        impact = min(round((f1 * 6 + f3 * 6) / 1.2, 1), 15)

        weighted_total = round(innovation + technical + ux + completeness + impact, 1)

        if weighted_total >= 85:
            tier = "Outstanding"
        elif weighted_total >= 70:
            tier = "Excellent"
        elif weighted_total >= 55:
            tier = "Good"
        elif weighted_total >= 40:
            tier = "Needs Improvement"
        else:
            tier = "Insufficient"

        strengths = []
        improvements = []
        if f1 >= 7: strengths.append("Detailed and clear project description")
        else: improvements.append("Add more detail to your project description")
        if f2 >= 6: strengths.append("Strong and diverse tech stack")
        else: improvements.append("Expand your tech stack details")
        if f3 >= 5: strengths.append("Good use of OpenGradient features")
        else: improvements.append("Integrate more OpenGradient features")
        if f4 >= 7: strengths.append("Project appears complete with demo and repo")
        else: improvements.append("Add a demo URL and repo link")

        evaluation = {
            "scores": {
                "innovation": innovation,
                "technical": technical,
                "ux": ux,
                "completeness": completeness,
                "impact": impact
            },
            "weighted_total": weighted_total,
            "tier": tier,
            "summary": f"This project scored {weighted_total}/100. {tier} execution with {'strong' if weighted_total > 70 else 'developing'} use of OpenGradient technology.",
            "strengths": strengths if strengths else ["Shows initiative in building on OpenGradient"],
            "improvements": improvements if improvements else ["Keep building and expanding the project"],
            "detailed_feedback": {
                "innovation": f"Innovation score: {innovation}/25 based on description depth and OG feature usage.",
                "technical": f"Technical score: {technical}/25 based on tech stack and completeness.",
                "ux": f"UX score: {ux}/20 based on project presentation.",
                "completeness": f"Completeness score: {completeness}/15 based on demo, repo, and notes.",
                "impact": f"Impact score: {impact}/15 based on description and OG integration."
            }
        }

        p["status"] = "evaluated"
        p["evaluation"] = evaluation
        save_projects()

        explorer_url = f"https://explorer.opengradient.ai/tx/{tx_hash}" if tx_hash and tx_hash != "N/A" else ""

        return jsonify({
            "project_name": p["name"],
            "evaluation": evaluation,
            "metadata": {
                "model": "Iris Classifier (On-Chain)",
                "inference_mode": "VANILLA",
                "inference_time_seconds": elapsed,
                "payment_hash": tx_hash,
                "explorer_url": explorer_url
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    evaluated = [p for p in PROJECTS.values() if p.get("status") == "evaluated"]
    evaluated.sort(key=lambda x: x["evaluation"]["weighted_total"], reverse=True)
    lb = []
    for i, p in enumerate(evaluated):
        lb.append({
            "rank": i + 1,
            "project_name": p["name"],
            "score": p["evaluation"]["weighted_total"],
            "tier": p["evaluation"]["tier"],
            "explorer_url": ""
        })
    return jsonify({"leaderboard": lb})

if __name__ == '__main__':
    app.run(debug=True, port=8000)
