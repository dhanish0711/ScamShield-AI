# 🛡️ ScamShield AI: Elder Fraud Defense & Indic Deception Classification System

[![IBM SkillsBuild](https://img.shields.io/badge/IBM%20SkillsBuild-AICTE%20Internship-blue?style=for-the-badge&logo=ibm)](https://skillsbuild.org/)
[![UN SDG 16](https://img.shields.io/badge/UN%20SDG%2016-Peace%2C%20Justice%20%26%20Strong%20Institutions-blue?style=for-the-badge)](https://sdgs.un.org/goals/goal16)
[![UN SDG 10](https://img.shields.io/badge/UN%20SDG%2010-Reduced%20Inequalities-orange?style=for-the-badge)](https://sdgs.un.org/goals/goal10)
[![Python Flask](https://img.shields.io/badge/Backend-Python%20Flask-green?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Groq Cloud](https://img.shields.io/badge/Groq%20Cloud-LPU%20Inference-orange?style=for-the-badge&logo=fastapi)](https://groq.com/)
[![Accessibility](https://img.shields.io/badge/WCAG%202.1-AA%20Compliant-brightgreen?style=for-the-badge)](https://www.w3.org/WAI/standards-guidelines/wcag/)

> **Internship Track:** AI & Machine Learning Specialization  
> **Host Organization:** Edunet Foundation in collaboration with IBM SkillsBuild for Academia & AICTE  
> **Deliverable Phase:** Deliverable 2 (Working Prototype & Core Codebase)  
> **Local Web URL:** `http://127.0.0.1:5000`

---

## 📌 Executive Summary

**ScamShield AI** is an assistive cyber fraud defense and machine learning platform engineered specifically to safeguard **senior citizens** across India against predatory digital extortion schemes. By combining **Indic Natural Language Processing (Hindi, English, Hinglish, Marathi)**, a **3-Agent Autonomous Swarm**, an **Interactive Call Interceptor Simulator**, and an **OSINT Threat Intelligence Lookup**, ScamShield bridges the generational technology divide and provides actionable reassurance before irreversible financial loss occurs.

---

## 🌟 Key Functional Pillars & 5-View Architecture

ScamShield AI features an accessible, tabbed 5-view user interface compliant with **WCAG 2.1 AA** standards and **Jakob Nielsen's 10 Usability Heuristics**:

### 1. 📡 Live Indic Deception Scanner & Autonomous 3-Agent Swarm
- **Hybrid NLP Classification Engine:** Analyzes suspicious WhatsApp forwards, SMS messages, electricity cut threats, and fake bank notifications.
- **📁 Voice Note & Call Audio Scanner:** Drag-and-drop or upload `.mp3`, `.wav`, and `.m4a` recordings, transcribing voice notes via **Groq Whisper Large v3** and analyzing them for deception.
- **Deception Vectors Breakdown:** Quantifies predatory psychological manipulation across 5 dimensions:
  - 👮 **Authority Coercion** (Fake police, CBI, court summons)
  - ⏰ **False Urgency & Panic** (Immediate disconnections, 2-hour arrest deadlines)
  - 🔒 **Secrecy & Family Isolation Pressure** (Demands to lock room, stay silent)
  - 💸 **Financial Siphoning / Escrow Lure** ("RBI clearance accounts", UPI traps)
  - 🔗 **Malicious APK / Web Trap** (Remote access Trojans like AnyDesk, phishing URLs)
- **Autonomous Multi-Agent Swarm:**
  - **Agent 1 (Deception Forensics):** Dissects coercive cognitive triggers.
  - **Agent 2 (Elder Reassurance & Caregiver Dispatch):** Provides calming step-by-step guidance in Hindi, English, and Marathi, with one-click WhatsApp emergency alert dispatch to designated family members.
  - **Agent 3 (National Cybercrime Incident Drafter):** Compiles evidence-backed legal complaints formatted under Sections 419/420 IPC and Section 66D IT Act for direct submission to **`cybercrime.gov.in`** and the **1930 Helpline**. Includes a print-ready legal docket.

### 2. 🚨 Virtual Voice Call Interceptor Simulator
- Interactive phone call demonstration simulating a real-world **Digital Arrest** interrogation from a spoofed Mumbai Crime Branch officer.
- Web Audio API tone synthesis simulating telephone chimes and real-time audio streams.
- Live streaming transcript with automatic ScamShield background interception ribbons warning the elder to hang up before funds are transferred.

### 3. 🔍 Indian Cyber Threat OSINT Lookup Tool
- Real-time search repository referencing blacklisted numbers, phishing URLs, fake APKs, and official helplines (Chakshu & I4C dataset).
- Instantly verifies suspect contacts (e.g., `9820192831`, `sbi-kyc-portal.net`, `1930`) with threat severity ratings and citizen grievance counts.

### 4. 🎓 Elder Defense Practice Lab (Interactive Awareness Quiz)
- 5 real-world interactive scenarios teaching seniors how to spot digital arrests, night electricity cuts, and UPI PIN scams.
- Live scoring, instant educational feedback, and a printable **Certified Cyber-Aware Citizen Certificate**.

### 5. 💬 Ask ScamShield AI Companion (Elder Reassurance Chatbot)
- Conversational cyber defense assistant tailored for Indian senior citizens.
- Answers questions in natural, gentle language in **Hindi, Marathi, English, or Hinglish**.
- Powered by **Groq Cloud LPU Acceleration** (with intelligent local fallback if offline).
- Includes one-click audio playback ("Listen Aloud") to read advice to seniors.

---

## ⚡ Groq Cloud LPU Acceleration (Dual-Engine Architecture)

ScamShield AI features a **Dual-Engine Architecture**:
1. **Local Indic Machine Learning Model:** Runs 100% offline using a Hybrid Word + Char N-Gram TF-IDF Vectorizer and Calibrated Classifier with **96.27% cross-validation accuracy**.
2. **Groq Cloud Acceleration (Optional):** When a Groq API Key is configured via the in-app **"Groq AI Setup (⚡)"** modal or `.env`:
   - **Cognitive Reasoning:** Accelerated by `qwen/qwen3.8-27b`, `openai/gpt-oss-120b`, or `openai/gpt-oss-20b`.
   - **Voice Note Transcription:** Accelerated by `whisper-large-v3`.
   - **Zero Dependency Fallback:** If offline or if the key is removed, the entire platform continues functioning locally without interruption.

---

## ♿ Elder-Centric Accessibility Features

- 🔊 **Trilingual Voice Audio (Web Speech API):** Paced audio playback in **Hindi (हिंदी)**, **English**, and **Marathi (मराठी)**.
- 🎙️ **Speech-to-Text Microphone Dictation:** Allows seniors with tremors or limited typing skills to dictate suspicious messages verbally.
- 👁️ **One-Click Font Rescaling:** Adjust text magnification up to 128% with single-click buttons.
- 🌓 **High Contrast AAA Mode:** Optimized for elders with cataracts or low-vision conditions.
- 🚨 **Panic Distress Button:** Emits an immediate audio siren and surfaces national emergency numbers (`1930` and `112`).

---

## 🔬 Machine Learning Model Specifications

| Parameter | Specification |
| :--- | :--- |
| **Model Type** | Hybrid Word + Character N-Gram (3–5) TF-IDF Vectorizer + Calibrated Logistic Regression |
| **Dataset Corpus** | 188 curated Indic scam & legitimate messages |
| **Linguistic Coverage** | Hindi, English, Hinglish, Marathi |
| **Cross-Validation (5-Fold)** | **96.27% Accuracy** |
| **Training Precision / Recall** | **1.00 / 1.00 (100%)** |
| **Target Classes** | Binary (Scam vs. Benign) + Multi-Class Modus Operandi (Digital Arrest, Utility Cut, Bank KYC, Task Scam, Lottery) |

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- Python 3.9+ with `pip`
- Modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox)

### Installation

1. **Clone or navigate to the repository directory:**
   ```bash
   git clone <your-repo-url>
   cd scamshield-ai
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Configure Groq API Key for Cloud Acceleration:**
   Copy the example environment file and add your key:
   ```bash
   cp .env.example .env
   ```
   *(Or enter your key directly in the web dashboard by clicking `Groq AI Setup ⚡`)*

4. **Start the Application Server:**
   ```bash
   python server.py
   ```

5. **Access the Web Dashboard:**
   Open your browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## 📁 Repository Structure

```text
├── server.py                 # Core Flask backend, NLP pipeline, OSINT search & API endpoints
├── train_advanced_model.py   # Machine learning training pipeline & cross-validation script
├── scam_dataset.csv          # Curated dataset of 188 Indic scam & benign messages
├── scam_model.pkl            # Serialized trained scikit-learn model pipeline
├── model_metrics.json        # Stored empirical validation metrics (96.27% accuracy)
├── templates/
│   └── index.html            # 5-view accessible semantic HTML5 dashboard
├── static/
│   ├── css/
│   │   └── style.css         # WCAG 2.1 AA stylesheet, high contrast & print docket styles
│   └── js/
│       └── app.js            # Controller engine (Speech API, Groq, OSINT & Call Interceptor)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore configuration (excludes secrets & cache)
└── README.md                 # Project documentation
```

---

## 👥 Alignment with UN Sustainable Development Goals

- **UN SDG 16 (Peace, Justice and Strong Institutions):** Combats organized transnational cyber extortion networks exploiting vulnerable citizens and automates reporting to statutory law enforcement agencies (`cybercrime.gov.in` / 1930).
- **UN SDG 10 (Reduced Inequalities):** Eradicates digital inequality by empowering elderly citizens with assistive, multilingual, voice-enabled cyber defense tools.

---

© 2026 ScamShield AI. Built for the **IBM SkillsBuild for Academia / AICTE Internship Capstone Evaluation**.
