# OG HackJudge

> Tamper-proof hackathon evaluations powered by verifiable AI. Every score is TEE-attested via x402 on OpenGradient.

**Live App:** https://og-hackjudge.vercel.app
**Built by:** @1stBernice (https://x.com/1st_Bernice0)
**Powered by:** OpenGradient (https://opengradient.ai)

---

## What is OG HackJudge?

OG HackJudge is a verifiable AI-powered hackathon judging platform built on OpenGradient x402 inference infrastructure. Every project evaluation is:

- Scored by Claude Haiku 4.5 running inside a Trusted Execution Environment (TEE) on OpenGradient
- Paid via x402 — inference payments settle automatically in OPG on Base Sepolia
- TEE-attested — each evaluation produces a cryptographic attestation signature from the TEE node
- Tamper-proof — one evaluation per project, owner-only, scores are final

---

## Features

- TEE-Verified AI Scoring: Claude Haiku 4.5 runs inside a TEE via OpenGradient x402
- 5-Category Breakdown: Innovation, Technical, UX, Completeness, Impact
- Live Leaderboard: Real-time rankings with search and tier badges
- Tamper-Proof: One evaluation per project, owner-only, TEE-signed
- Free for Users: x402 payments handled server-side via OPG on Base Sepolia
- Open and Transparent: TEE attestation signatures prove inference integrity

---

## How It Works

1. Connect Wallet — Connect MetaMask or Rabby to identify yourself as the project submitter.
2. Submit Project — Fill in your project name, description, tech stack, OG features, demo and repo URLs.
3. AI Evaluates — The server sends an x402 inference request to OpenGradient. Claude Haiku 4.5 runs inside a TEE and scores your project. A cryptographic attestation signature is returned as proof.
4. Claim Your Rank — Your TEE-attested score is saved. One evaluation per project, tamper-proof.

Scoring categories: Innovation (25%), Technical (25%), UX (20%), Completeness (15%), Impact (15%)

Tiers: Outstanding (85-100), Excellent (70-84), Good (55-69), Needs Improvement (40-54), Insufficient (0-39)

---

## Tech Stack

Frontend: Vanilla HTML/CSS/JS, MetaMask/Rabby wallet, live leaderboard search
Backend: Python, Flask, Vercel serverless, MongoDB Atlas
AI: Claude Haiku 4.5 via OpenGradient TEE LLM
Payment: x402 protocol, OPG token on Base Sepolia (Chain ID: 84532)

---

## Project Structure

og-hackjudge/
├── api/
│   └── index.py        # Flask backend — routes, scoring, x402 inference
├── index.html          # Main app (submit, projects, leaderboard)
├── landing.html        # Landing page
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel deployment config
└── .gitignore

---

## OpenGradient x402 Integration

result = client.llm.chat(
    model=og.TEE_LLM.CLAUDE_HAIKU_4_5,
    messages=messages,
    max_tokens=800,
    x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
)
# result.tee_signature — cryptographic proof of TEE execution
# result.tee_timestamp — timestamp of inference

---

## Local Development

git clone https://github.com/addnad/og-hackjudge.git
cd og-hackjudge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Create .env:
OG_PRIVATE_KEY=your_private_key_here
MONGO_URI=your_mongodb_uri_here

Run: python api/index.py

---

## License

MIT — Built by 1stBernice on OpenGradient
