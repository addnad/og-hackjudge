# OG HackJudge 🏆

> **Tamper-proof hackathon evaluations on decentralized AI. Every score is cryptographically provable on-chain.**

**Live App:** [og-hackjudge.vercel.app](https://og-hackjudge.vercel.app)  
**Built by:** [@1stBernice](https://x.com/1st_Bernice0)  
**Powered by:** [OpenGradient](https://opengradient.ai)

---

## What is OG HackJudge?

OG HackJudge is a verifiable AI-powered hackathon judging platform built on OpenGradient's decentralized inference infrastructure. Instead of opaque, centralized judging, every project evaluation is:

- **Scored by an on-chain AI model** deployed on the OpenGradient testnet
- **Cryptographically proven** — each evaluation produces a real blockchain transaction signed by the submitter's wallet
- **Tamper-proof** — scores are recorded on-chain and verifiable on the OpenGradient explorer
- **Transparent** — anyone can verify any evaluation at any time

---

## Features

| Feature | Description |
|---|---|
| 🔍 Verifiable AI Scoring | On-chain inference via OpenGradient's Model Hub |
| 📊 5-Category Breakdown | Innovation, Technical, UX, Completeness, Impact |
| 🏅 Live Leaderboard | Real-time rankings with tier badges |
| 👛 Wallet-Connected | Users sign evaluation transactions with their own wallet |
| ⛽ Zero Gas Fees | OpenGradient testnet is completely free |
| 🔓 Open & Transparent | Every score verifiable on the OG explorer |

---

## How It Works

### 1. Connect Wallet
Connect Rabby or MetaMask. The app automatically switches you to the OpenGradient testnet (Chain ID: 10740).

### 2. Submit Your Project
Fill in your project name, description, tech stack, OpenGradient features used, demo URL, and repo link.

### 3. AI Evaluates On-Chain
Click **⚡ Evaluate with AI**. Your wallet sends a transaction on the OpenGradient testnet as cryptographic proof. The scoring model evaluates your project across 5 categories:

| Category | Weight | What's Measured |
|---|---|---|
| Innovation | 25% | Description depth + OG feature usage |
| Technical | 25% | Tech stack breadth + completeness |
| UX & Design | 20% | Project presentation quality |
| Completeness | 15% | Demo URL, repo link, notes |
| Impact | 15% | Description depth + OG integration |

### 4. Get Your Tier

| Score | Tier |
|---|---|
| 85–100 | 🥇 Outstanding |
| 70–84 | 🥈 Excellent |
| 55–69 | 🥉 Good |
| 40–54 | ⚠️ Needs Improvement |
| 0–39 | ❌ Insufficient |

---

## Tech Stack

**Frontend**
- Vanilla HTML/CSS/JS — single page app with tab navigation
- MetaMask / Rabby wallet integration via `window.ethereum`
- Auto network switching to OpenGradient testnet

**Backend**
- Python + Flask
- OpenGradient Python SDK
- JSON file-based persistence
- Deployed on Vercel serverless functions

**Blockchain**
- OpenGradient Alpha Testnet (Chain ID: 10740)
- RPC: `https://ogevmdevnet.opengradient.ai`
- On-chain inference via OpenGradient Model Hub (Iris Classifier — ONNX)
- Each evaluation sends a signed transaction from the user's wallet as proof

---

## Getting Started Locally

### Prerequisites
- Python 3.10+
- MetaMask or Rabby wallet browser extension
- OPG testnet tokens from [faucet.opengradient.ai](https://faucet.opengradient.ai)

### Installation

```bash
git clone https://github.com/addnad/og-hackjudge.git
cd og-hackjudge

python3 -m venv venv
source venv/bin/activate

pip install flask flask-cors python-dotenv opengradient
```

### Environment Variables

Create a `.env` file:

```env
OG_PRIVATE_KEY=your_private_key_here
OG_MODEL_CID=your_model_cid_here
```

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### Run Locally

```bash
python app.py
```

Visit `http://127.0.0.1:5000`

---

## Project Structure

```
og-hackjudge/
├── app.py              # Flask backend + scoring logic
├── api/
│   └── index.py        # Vercel serverless entry point
├── index.html          # Main app (single page)
├── landing.html        # Landing page
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel deployment config
└── .gitignore
```

---

## OpenGradient Integration

OG HackJudge uses OpenGradient in two ways:

1. **Model Hub** — An ONNX iris classifier model deployed on the OpenGradient Model Hub serves as the on-chain inference engine. Project metadata is mapped into a 4-feature vector and run through the model on-chain.

2. **On-chain Proof** — Every evaluation triggers a real transaction on the OpenGradient testnet (Chain ID: 10740), creating an immutable record of the score that anyone can verify on the explorer.

---

## License

MIT

---

<p align="center">Built with ❤️ by <a href="https://x.com/1st_Bernice0">1stBernice</a> on <a href="https://opengradient.ai">OpenGradient</a></p>
