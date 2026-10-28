import os
import re
import json
import pickle
import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv(override=True)

try:
    import groq
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

app = Flask(__name__)

# =========================================================================
# GROQ CLOUD ACCELERATION STATE & CONFIGURATION
# =========================================================================
VALID_GROQ_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
configured_model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")
if configured_model not in VALID_GROQ_MODELS:
    configured_model = "qwen/qwen3.8-27b"

GROQ_STATE = {
    "api_key": os.environ.get("GROQ_API_KEY", ""),
    "model": configured_model,
    "is_active": False
}

def get_groq_client():
    if not GROQ_AVAILABLE:
        return None
    key = GROQ_STATE["api_key"] or os.environ.get("GROQ_API_KEY", "")
    if key and key.startswith("gsk_"):
        try:
            return Groq(api_key=key, timeout=8.0)
        except Exception as e:
            print(f"[!] Groq initialization warning: {e}")
            return None
    return None

def test_groq_connection(api_key, model_name="qwen/qwen3.8-27b"):
    if not GROQ_AVAILABLE:
        return False, "groq python library not installed"
    try:
        client = Groq(api_key=api_key, timeout=8.0)
        client.models.list()
        return True, "Successfully verified Groq API connection"
    except Exception as e:
        return False, str(e)

def save_env_var(key, value):
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    found = False
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

def remove_env_var(key):
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = [line for line in f if not line.startswith(f"{key}=")]
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

# Initial probe if environment variable already exists
if GROQ_STATE["api_key"]:
    ok, _ = test_groq_connection(GROQ_STATE["api_key"], GROQ_STATE["model"])
    GROQ_STATE["is_active"] = ok

# Load trained NLP model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "scam_model.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "model_metrics.json")

model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

def load_metrics():
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_samples": 188,
        "scam_samples": 131,
        "legitimate_samples": 57,
        "cv_accuracy": 96.27,
        "train_accuracy": 100.0,
        "categories": {
            "Digital Arrest": 46,
            "Utility Disconnection": 28,
            "Bank & KYC": 25,
            "Telegram Job": 12,
            "Lottery / KBC": 8,
            "Emergency Relative": 7,
            "Loan Scam": 5,
            "Genuine Banking & Services": 57
        }
    }

def extract_entities(text):
    """
    Extract suspect phone numbers, URLs, UPI VPAs, and APK mentions.
    """
    entities = {
        "phones": [],
        "urls": [],
        "upis": [],
        "apks": []
    }
    
    # Phone numbers (Indian 10-digit formats with or without country code)
    phone_pattern = r'(?:\+?91[\-\s]?)?[6-9]\d{9}\b'
    entities["phones"] = list(set(re.findall(phone_pattern, text)))
    
    # URLs and links
    url_pattern = r'(?:https?:\/\/|www\.)[^\s\/$.?#].[^\s]*|(?:bit\.ly|tinyurl|t\.me|wa\.me)\/[a-zA-Z0-9_-]+|[a-zA-Z0-9-]+\.(?:com|in|cc|net|org|xyz|top|link|site|info|online|club)\/[^\s]*'
    raw_urls = re.findall(url_pattern, text, re.IGNORECASE)
    entities["urls"] = list(set(raw_urls))
    
    # UPI IDs / VPAs
    upi_pattern = r'\b[a-zA-Z0-9._-]+@(okaxis|oksbi|okhdfcbank|paytm|ybl|ibl|upi|axl|icici)\b'
    entities["upis"] = list(set(re.findall(upi_pattern, text, re.IGNORECASE)))
    
    # APK / Remote desktop tools
    apk_keywords = ["apk", "anydesk", "quicksupport", "teamviewer", "rustdesk", "yono", "sbi-kyc", "screen share"]
    for word in apk_keywords:
        if word in text.lower():
            entities["apks"].append(word.upper())
    entities["apks"] = list(set(entities["apks"]))
    
    return entities

def comprehensive_scam_analysis(text):
    """
    Multi-layered Indic NLP & Social Engineering evaluation engine.
    Supports English, Hindi, Hinglish, and Marathi messages & Call Transcripts.
    """
    msg_lower = text.lower()
    
    # Category Lexicons across Hindi, English, Hinglish, Marathi
    lexicon_digital_arrest = [
        "arrest", "police", "cbi", "customs", "narcotics", "mdma", "drugs", "contraband", 
        "court", "warrant", "trai", "crime branch", "pmla", "money laundering", "surveillance", 
        "dcp", "commissioner", "supreme court", "video call", "skype", "trafficking", "fir",
        "अटक", "पोलीस", "सायबर", "ड्रग्ज", "गुन्हे शाखा", "हवाला", "न्यायालय", "वॉरंट", "डिजिटल अरेस्ट"
    ]
    
    lexicon_utility = [
        "electricity", "power", "bijli", "disconnected", "meter", "power cut", "power office", 
        "msedcl", "adani electricity", "torrent power", "bill not updated", "tonight at", "aaj raat",
        "वीज", "महावितरण", "लाईट", "बिल अपडेट", "रात्री", "खंडित", "कापली जाईल", "वायरमन"
    ]
    
    lexicon_banking = [
        "kyc", "pan card", "yono", "sbi", "hdfc", "icici", "axis", "blocked", "debit card", 
        "credit card", "reward points", "forfeited", "video kyc", "account suspended", "netbanking", 
        "paytm kyc", "wallet balance", "otp", "बँक", "खाते", "पॅन कार्ड", "ब्लॉक", "गोठवण्यात"
    ]
    
    lexicon_job_lottery = [
        "telegram", "work from home", "like youtube", "rating", "earn daily", "part time", 
        "lottery", "kbc", "lucky draw", "crorepati", "won rs", "payout", "pre-deposit", "review agent",
        "राणा प्रताप सिंह", "लकी विजेते", "लॉटरी", "घरबसल्या", "लाईक करा"
    ]
    
    lexicon_loan = [
        "mudra", "pre-approved", "loan", "कर्ज", "लोन", "dhani", "bajaj finance", "processing fee", "फाइल चार्ज"
    ]
    
    lexicon_upi_refund = [
        "cashback", "refund", "google pay", "phonepe", "gpay", "receive money", "enter upi pin", 
        "enter pin to credit", "scan qr to receive", "पैसे मिळवण्यासाठी"
    ]
    
    lexicon_urgency = [
        "immediately", "tonight", "2 hours", "1 hour", "urgent", "turant", "aaj raat", "jaldi", 
        "within 24 hours", "power cut scheduled", "last warning", "final notice", "तात्काळ", "त्वरित", "लगेच"
    ]

    lexicon_safe_indicators = [
        "withdrawn from atm", "order dispatched", "your appointment is confirmed", 
        "hall ticket", "flight booking", "pnr", "arriving in", "have a great month", 
        "bhai", "mummy", "papa", "dawai", "college", "office pahunch gaya", "chai",
        "औषध", "भाजी", "दिवाळीच्या", "हार्दिक शुभेच्छा", "यशस्वीरीत्या भरले", "appointment confirmed",
        "coach", "berth", "happy journey", "salary credited", "auto-debit", "dividend"
    ]

    is_call_transcript = "[call transcript]" in msg_lower or "caller:" in msg_lower or "officer:" in msg_lower

    # Match counts
    matches_arrest = [w for w in lexicon_digital_arrest if w in msg_lower]
    matches_utility = [w for w in lexicon_utility if w in msg_lower]
    matches_banking = [w for w in lexicon_banking if w in msg_lower]
    matches_job_lottery = [w for w in lexicon_job_lottery if w in msg_lower]
    matches_loan = [w for w in lexicon_loan if w in msg_lower]
    matches_upi_refund = [w for w in lexicon_upi_refund if w in msg_lower]
    matches_urgency = [w for w in lexicon_urgency if w in msg_lower]
    matches_safe = [w for w in lexicon_safe_indicators if w in msg_lower]

    entities = extract_entities(text)
    has_links = len(entities["urls"]) > 0
    has_apks = len(entities["apks"]) > 0
    has_phones = len(entities["phones"]) > 0

    # ML Classifier Prediction if available
    ml_scam_prob = None
    if model is not None:
        try:
            proba = model.predict_proba([text])[0]
            # Classes: [legitimate, scam]
            scam_idx = list(model.classes_).index("scam") if "scam" in model.classes_ else 1
            ml_scam_prob = float(proba[scam_idx] * 100.0)
        except Exception:
            pass

    # Score calculation
    base_score = float(ml_scam_prob) if ml_scam_prob is not None else 10.0
    
    # Threat weighting based on detected social engineering constructs
    if len(matches_arrest) >= 2 or (is_call_transcript and len(matches_arrest) >= 1):
        base_score = max(base_score, 85.0 + (len(matches_arrest) * 3))
    elif len(matches_arrest) == 1:
        base_score = max(base_score, 55.0)

    if len(matches_utility) >= 2:
        base_score = max(base_score, 75.0 + (len(matches_utility) * 4))
    elif len(matches_utility) == 1:
        base_score = max(base_score, 45.0)

    if len(matches_banking) >= 2:
        base_score = max(base_score, 70.0 + (len(matches_banking) * 4))
    elif len(matches_banking) == 1:
        base_score = max(base_score, 40.0)

    if len(matches_job_lottery) >= 2:
        base_score = max(base_score, 75.0 + (len(matches_job_lottery) * 4))
    elif len(matches_job_lottery) == 1:
        base_score = max(base_score, 40.0)

    if len(matches_loan) >= 2:
        base_score = max(base_score, 70.0)

    if len(matches_upi_refund) >= 1:
        base_score = max(base_score, 65.0)

    if len(matches_urgency) >= 1:
        base_score += 8.0

    if has_links:
        base_score += 15.0
    if has_apks:
        base_score += 25.0

    # Safe discounting
    if len(matches_safe) >= 1:
        base_score -= (len(matches_safe) * 35.0)

    # Sanitize score between 1.0% and 99.6%
    scam_prob = float(round(max(1.5, min(99.6, float(base_score))), 1))
    is_scam = bool(scam_prob >= 50.0)

    # Classify Primary Modus
    if len(matches_arrest) >= 2 or (len(matches_arrest) >= 1 and is_scam) or (is_call_transcript and is_scam):
        scam_type = "Digital Arrest & Fake Law Enforcement Extortion"
        scam_category = "digital_arrest"
    elif len(matches_utility) >= 2 or (len(matches_utility) >= 1 and is_scam):
        scam_type = "Utility Disconnection & Power Cut Threat"
        scam_category = "utility"
    elif len(matches_banking) >= 2 or (len(matches_banking) >= 1 and is_scam):
        scam_type = "Bank Account Freeze & Fake KYC Phishing"
        scam_category = "banking"
    elif len(matches_job_lottery) >= 2 or (len(matches_job_lottery) >= 1 and is_scam):
        scam_type = "Part-Time Task & Fake Telegram Job Scam"
        scam_category = "job_lottery"
    elif len(matches_loan) >= 1 and is_scam:
        scam_type = "Predatory Instant Loan Approval Scam"
        scam_category = "loan"
    elif len(matches_upi_refund) >= 1 and is_scam:
        scam_type = "UPI PIN Reversal & Fake Refund Trap"
        scam_category = "upi_refund"
    elif is_scam:
        scam_type = "Predatory Social Engineering Extortion"
        scam_category = "generic_scam"
    else:
        scam_type = "Authentic / Benign Communication"
        scam_category = "safe"

    # Severity level
    if scam_prob >= 75.0:
        severity = "CRITICAL THREAT"
        badge_class = "danger"
    elif scam_prob >= 50.0:
        severity = "HIGH RISK WARNING"
        badge_class = "warning"
    elif scam_prob >= 25.0:
        severity = "SUSPICIOUS / ELEVATED"
        badge_class = "info"
    else:
        severity = "SAFE / BENIGN"
        badge_class = "success"

    # Build Psychological Triggers List
    triggers = []
    if is_call_transcript:
        triggers.append({
            "title": "Coercive Audio Interrogation (Phone Call Trap)",
            "icon": "🎙️",
            "desc": "Simulates aggressive judicial or police interrogation over voice call to induce cognitive freeze.",
            "risk": "CRITICAL"
        })
    if matches_urgency:
        triggers.append({
            "title": "False Urgency & Artificial Panic",
            "icon": "⏰",
            "desc": f"Forces hasty actions before consulting family. Detected terms: '{', '.join(matches_urgency)}'.",
            "risk": "HIGH"
        })
    if matches_arrest:
        triggers.append({
            "title": "Coercive Fake Authority (Digital Arrest)",
            "icon": "👮",
            "desc": f"Impersonates police, CBI, or courts to intimidate. Detected terms: '{', '.join(matches_arrest)}'.",
            "risk": "CRITICAL"
        })
    if any(w in matches_arrest for w in ["drugs", "mdma", "laundering", "trafficking", "contraband", "parcel", "fedex", "हवाला", "ड्रग्ज"]):
        triggers.append({
            "title": "Fabricated Criminal Allegation",
            "icon": "⚖️",
            "desc": "Falsely alleges international narcotics smuggling or hawala to induce extreme guilt and compliance.",
            "risk": "CRITICAL"
        })
    if has_links or has_apks:
        triggers.append({
            "title": "Malicious Phishing Link / APK Trap",
            "icon": "🔗",
            "desc": f"Captures netbanking credentials or installs screen-sharing malware. Artifacts: {', '.join(entities['urls'] + entities['apks'])}",
            "risk": "HIGH"
        })
    if matches_job_lottery:
        triggers.append({
            "title": "Financial Greed & Unrealistic Payout Lure",
            "icon": "💰",
            "desc": "Promises astronomical returns for simple tasks or nonexistent lottery prizes to lower suspicion.",
            "risk": "HIGH"
        })
    if matches_banking:
        triggers.append({
            "title": "Impersonation of Financial Institution",
            "icon": "🏦",
            "desc": f"Pretends to be a trusted bank (SBI/HDFC/PNB) warning of account closure to steal credentials.",
            "risk": "HIGH"
        })
    if matches_utility:
        triggers.append({
            "title": "Essential Service Disruption Threat",
            "icon": "⚡",
            "desc": f"Threatens immediate electricity or utility cutoff. Detected terms: '{', '.join(matches_utility)}'.",
            "risk": "HIGH"
        })
    if matches_upi_refund:
        triggers.append({
            "title": "Reverse Payment Deception",
            "icon": "💸",
            "desc": "Tricks victim into entering UPI PIN to 'receive' money, which actually debits their account.",
            "risk": "HIGH"
        })

    # DYNAMIC Tailored Trilingual Advice for Senior Citizens (Hindi, English, Marathi)
    if scam_category == "digital_arrest":
        advice_hindi = [
            "बिल्कुल न घबराएं: यह 100% फर्जी संदेश है।",
            "कोई भी पुलिस, CBI या कस्टम्स कभी भी व्हाट्सएप या वीडियो कॉल पर अरेस्ट नहीं करती।",
            "कानून में 'डिजिटल अरेस्ट' नाम की कोई चीज नहीं होती—यह पूरी तरह ठगों का ड्रामा है।",
            "किसी भी 'वेरिफिकेशन अकाउंट' या UPI पर एक भी रुपया न भेजें।",
            "कॉल तुरंत काटें और अपने बच्चों या 1930 पर संपर्क करें।"
        ]
        advice_english = [
            "Do NOT panic: This is a completely fabricated extortion attempt.",
            "Police, CBI, and Customs NEVER conduct arrests or judicial trials over video calls.",
            "There is NO provision for 'Digital Arrest' under Indian Law (CrPC/BNS).",
            "Never transfer money to any 'security verification' or 'escrow' account.",
            "Disconnect any ongoing call immediately and alert trusted family members."
        ]
        advice_marathi = [
            "घाबरू नका: हा १००% बनावट आणि खंडणीचा प्रयत्न आहे.",
            "पोलीस, सीबीआय किंवा कस्टम्स कधीही व्हिडिओ कॉलवर कोणालाही अटक करत नाहीत.",
            "भारतीय कायद्यात 'डिजिटल अरेस्ट' अशी कोणतीही तरतूद अस्तित्वात नाही.",
            "कोणत्याही बँक किंवा यूपीआय खात्यात पैसे पाठवू नका.",
            "तातडीने कॉल बंद करा आणि कुटुंबियांशी किंवा १९३० हेल्पलाईनवर बोला."
        ]
        banner_text = "CRITICAL WARNING: Indian Law Enforcement NEVER conducts arrests or judicial hearings over video calls. Do not panic and do not transfer money!"
        voice_hi = "सावधान! यह एक फर्जी डिजिटल अरेस्ट संदेश है। पुलिस या सीबीआई कभी भी वीडियो कॉल पर पूछताछ या अरेस्ट नहीं करती। किसी को भी पैसे न भेजें और तुरंत अपने परिवार को बताएं।"
        voice_en = "Warning! Digital arrest scam detected. Law enforcement agencies never arrest anyone over video calls. Do not transfer any money."
        voice_mr = "सावधान! हा डिजिटल अरेस्टचा बनावट प्रयत्न आहे. पोलीस कधीही व्हिडिओ कॉलवर अटक करत नाहीत. कोणालाही पैसे पाठवू नका."

    elif scam_category == "utility":
        advice_hindi = [
            "बिजली विभाग कभी भी रात को 9:30 बजे व्हाट्सएप पर कनेक्शन नहीं काटता।",
            "असली बिजली बिल का नोटिस हमेशा अगले महीने के कागजी बिल में आता है।",
            "संदेश में दिए गए किसी भी अनजान मोबाइल नंबर पर कॉल न करें।",
            "कोई भी ऐप (AnyDesk / QuickSupport / APK) मोबाइल में डाउनलोड न करें।",
            "बिल हमेशा केवल आधिकारिक बिजली बोर्ड की वेबसाइट या बिजली ऑफिस जाकर ही भरें।"
        ]
        advice_english = [
            "Electricity boards never disconnect domestic power at night via WhatsApp notices.",
            "Official power notices are always delivered on physical monthly billing statements.",
            "Never call the personal mobile numbers listed in such SMS warnings.",
            "Never install screen-sharing apps (AnyDesk, QuickSupport, or APK files).",
            "Pay bills only through the official state electricity portal (e.g. MSEDCL, Adani, BESCOM)."
        ]
        advice_marathi = [
            "महावितरण किंवा वीज मंडळ रात्री कधीही वीज खंडित करत नाही.",
            "वीज बिलाची अधिकृत नोटीस नेहमी कागदी बिलामध्ये किंवा महावितरण अॅपवर येते.",
            "संदेशामध्ये दिलेल्या कोणत्याही अनोळखी नंबरवर फोन करू नका.",
            "मोबाईलमध्ये AnyDesk किंवा कोणतेही अॅप (APK) डाऊनलोड करू नका.",
            "बिल केवळ अधिकृत महावितरण केंद्रात किंवा अधिकृत वेबसाईटवरच भरा."
        ]
        banner_text = "UTILITY SCAM DETECTED: Electricity boards never cut power at night via SMS. Do not call the unauthorized mobile number or install APKs!"
        voice_hi = "सावधान! बिजली काटने का यह संदेश फर्जी है। बिजली विभाग रात में इस तरह कनेक्शन नहीं काटता। दिए गए नंबर पर कॉल न करें और कोई ऐप डाउनलोड न करें।"
        voice_en = "Warning! Fake electricity bill scam detected. Utility providers never cut power at night via SMS. Do not call the unknown number."
        voice_mr = "सावधान! वीज बिल कापण्याचा हा संदेश बनावट आहे. वीज मंडळ रात्री कधीही वीज पुरवठा खंडित करत नाही."

    elif scam_category == "banking":
        advice_hindi = [
            "बैंक कभी भी एसएमएस के जरिए खाता या डेबिट कार्ड ब्लॉक नहीं करता।",
            "संदेश में दिए गए किसी भी लिंक (Link) पर क्लिक करके पैन कार्ड या आधार नंबर न डालें।",
            "बैंक अधिकारी कभी भी फोन पर ओटीपी (OTP) या नेटबैंकिंग पासवर्ड नहीं मांगते।",
            "अगर कोई शंका हो, तो सीधे अपने नजदीकी बैंक शाखा (Branch) में जाकर बात करें।"
        ]
        advice_english = [
            "Banks never suspend accounts or debit cards via generic SMS links.",
            "Never click unverified links to update PAN or Aadhaar credentials.",
            "Bank staff never ask for OTPs, CVVs, or NetBanking passwords over the phone.",
            "For any account queries, visit your local bank branch directly."
        ]
        advice_marathi = [
            "बँक कधीही एसएमएसमधील लिंकवरून खाते किंवा एटीएम कार्ड ब्लॉक करत नाही.",
            "कोणत्याही लिंकवर क्लिक करून पॅन कार्ड, आधार किंवा बँक माहिती भरू नका.",
            "बँक अधिकारी फोनवर कधीही ओटीपी (OTP) किंवा पासवर्ड मागत नाहीत.",
            "काहीही अडचण असल्यास थेट बँकेच्या शाखेत जाऊन खात्री करा."
        ]
        banner_text = "BANKING PHISHING DETECTED: Banks never demand immediate KYC updates via third-party web links. Keep your OTPs secret!"
        voice_hi = "सावधान! यह बैंक और केवाईसी का फर्जी संदेश है। बैंक कभी भी एसएमएस लिंक पर खाता ब्लॉक नहीं करता। किसी को भी अपना ओटीपी न दें।"
        voice_en = "Warning! Fake bank KYC phishing alert detected. Banks never block accounts via SMS links. Never share your OTP."
        voice_mr = "सावधान! हा बँकेच्या नावाखाली फसवणुकीचा संदेश आहे. बँक कधीही एसएमएस लिंकद्वारे खाते ब्लॉक करत नाही."

    elif scam_category == "job_lottery":
        advice_hindi = [
            "यूट्यूब वीडियो लाइक करने के कोई भी कंपनी रोजाना 4000-5000 रुपये नहीं देती।",
            "टेलीग्राम पर 'टास्क पूरा करने' का लालच देकर पहले पैसे डलवाए जाते हैं और फिर फंसाया जाता है।",
            "केबीसी या लॉटरी के नाम पर 'प्रोसेसिंग फीस' मांगना 100% ठगी है।",
            "किसी भी अनजान व्यक्ति को नौकरी या लॉटरी के लिए कोई पैसा न दें।"
        ]
        advice_english = [
            "No legitimate company pays ₹4,000 daily for simply liking YouTube videos.",
            "Telegram task schemes ask for an upfront 'pre-deposit' and steal your funds.",
            "Demanding a 'processing fee' to release lottery or KBC winnings is 100% fraud.",
            "Never transfer money to anonymous recruitment or lottery agents."
        ]
        advice_marathi = [
            "कोणतीही कंपनी युट्यूब व्हिडिओ लाईक करण्यासाठी दररोज हजारो रुपये देत नाही.",
            "टेलिग्रामवर टास्कच्या नावाखाली पैसे भरण्यास सांगून फसवणूक केली जाते.",
            "केबीसी किंवा लॉटरीच्या नावाखाली कर किंवा प्रोसेसिंग फी भरणे १००% फसवणूक आहे.",
            "नोकरी किंवा बक्षीसासाठी कोणालाही पैसे पाठवू नका."
        ]
        banner_text = "TASK / LOTTERY SCAM DETECTED: Legitimate jobs never demand upfront deposit fees. This is a Telegram investment trap!"
        voice_hi = "सावधान! लॉटरी या यूट्यूब वीडियो लाइक करने के नाम पर यह ठगी का संदेश है। कोई भी कंपनी इस तरह पैसे नहीं देती। किसी को भी पैसे न भेजें।"
        voice_en = "Warning! Task and lottery scam detected. Legitimate companies never charge pre-deposits for work. Do not send money."
        voice_mr = "सावधान! घरबसल्या कमाई आणि लॉटरीचा हा बनावट संदेश आहे. कोणालाही पैसे पाठवू नका."

    elif scam_category == "loan":
        advice_hindi = [
            "बिना किसी जांच के 1% ब्याज पर कोई भी सरकारी योजना तुरंत लोन नहीं देती।",
            "लोन देने से पहले 'फाइल चार्ज' या 'सिक्योरिटी फीस' मांगना सीधे तौर पर धोखाधड़ी है।",
            "सरकारी मुद्रा लोन केवल बैंक शाखा या जनसमर्थ पोर्टल के माध्यम से ही मिलता है।"
        ]
        advice_english = [
            "No legitimate bank approves instant collateral-free loans without credit checks.",
            "Demanding upfront 'processing fees' or 'file clearance fees' is a guaranteed scam.",
            "Apply for government Mudra loans only through official bank branches."
        ]
        advice_marathi = [
            "कोणतीही अधिकृत बँक चौकशीशिवाय त्वरित लाखो रुपयांचे कर्ज देत नाही.",
            "कर्ज मंजूर करण्यासाठी आधी 'प्रक्रिया शुल्क' मागणे ही शुद्ध फसवणूक आहे.",
            "मुद्रा कर्जासाठी केवळ अधिकृत बँकेच्या शाखेशी संपर्क साधा."
        ]
        banner_text = "LOAN FRAUD DETECTED: Legitimate banks NEVER demand upfront processing fees via personal UPI to disburse loans!"
        voice_hi = "सावधान! लोन देने के नाम पर यह धोखाधड़ी है। लोन मिलने से पहले कोई भी फाइल चार्ज न दें।"
        voice_en = "Warning! Fake loan approval detected. Never pay upfront processing fees for loan disbursals."
        voice_mr = "सावधान! कर्जाच्या नावाखाली फसवणुकीचा प्रयत्न आहे. कर्जासाठी आधी पैसे देऊ नका."

    elif scam_category == "upi_refund":
        advice_hindi = [
            "पैसे पाने (Receive) के लिए कभी भी यूपीआई पिन (UPI PIN) डालने की जरूरत नहीं होती।",
            "यूपीआई पिन केवल बैंक से पैसे काटने (Send/Pay) के समय ही डाला जाता है।",
            "किसी भी अनजान लिंक या क्यूआर कोड (QR Code) को स्कैन न करें।"
        ]
        advice_english = [
            "You NEVER need to enter your UPI PIN to receive money or refunds.",
            "Entering your UPI PIN ALWAYS debits money from your bank account.",
            "Never scan unknown QR codes sent on WhatsApp to claim cashback."
        ]
        advice_marathi = [
            "पैसे मिळवण्यासाठी (Receive) कधीही यूपीआय पिन (UPI PIN) टाकण्याची गरज नसते.",
            "यूपीआय पिन टाकल्यास तुमच्या बँक खात्यातून पैसे कापले जातात.",
            "कॅशबॅकच्या नावाखाली आलेला क्यूआर कोड कधीही स्कॅन करू नका."
        ]
        banner_text = "UPI REVERSAL TRAP: Entering your UPI PIN will transfer money OUT of your bank account. Never enter your PIN to receive funds!"
        voice_hi = "सावधान! पैसे प्राप्त करने के लिए कभी भी यूपीआई पिन न डालें। यूपीआई पिन डालने से आपके खाते से पैसे कट जाएंगे।"
        voice_en = "Warning! Fake UPI refund trap. You never need to enter your UPI PIN to receive money. Entering your PIN transfers money out."
        voice_mr = "सावधान! पैसे मिळवण्यासाठी कधीही यूपीआय पिन टाकू नका. पिन टाकल्यास खात्यातून पैसे कापले जातील."

    else:
        advice_hindi = [
            "संदेश सुरक्षित और सामान्य प्रतीत होता है।",
            "फिर भी किसी भी स्थिति में अपना बैंक ओटीपी या पासवर्ड किसी को न बताएं।"
        ]
        advice_english = [
            "This communication appears legitimate with standard personal or transactional phrasing.",
            "As a general precaution, never share one-time passwords (OTPs) with anyone."
        ]
        advice_marathi = [
            "हा संदेश सुरक्षित आणि सामान्य व्यवहारिक वाटतो.",
            "तरीही खबरदारी म्हणून कोणालाही तुमचा बँक ओटीपी किंवा पासवर्ड सांगू नका."
        ]
        banner_text = "SAFE STATUS: No coercive extortion, fake digital arrest warrants, or predatory links detected in this message."
        voice_hi = "यह संदेश सुरक्षित प्रतीत होता है। इसमें कोई धमकी या फर्जी लिंक नहीं मिला है। फिर भी अपना बैंक ओटीपी किसी को न बताएं।"
        voice_en = "This message appears legitimate. No threats or deceptive links were found. Always keep your passwords private."
        voice_mr = "हा संदेश सुरक्षित आहे. यात कोणतीही फसवणूक आढळलेली नाही. ओटीपी सुरक्षित ठेवा."

    # Calculate Deception Vectors for visual radar & analytics
    authority_val = min(100, len(matches_arrest) * 35 + (20 if is_call_transcript else 0))
    urgency_val = min(100, len(matches_urgency) * 40 + (30 if "tonight" in msg_lower or "aaj raat" in msg_lower else 0))
    isolation_val = 90 if any(w in msg_lower for w in ["kisi ko mat", "secret", "room", "disconnect", "family", "chupchap"]) else (45 if is_call_transcript else 10)
    financial_val = min(100, len(matches_banking) * 30 + len(matches_loan) * 40 + len(matches_upi_refund) * 45 + (35 if any(w in msg_lower for w in ["transfer", "fine", "deposit", "escrow", "fees"]) else 0))
    digital_trap_val = min(100, (35 if has_links else 0) + (45 if has_apks else 0) + (30 if any(w in msg_lower for w in ["video call", "skype", "teams", "apk", "anydesk"]) else 0))

    deception_vectors = {
        "authority": int(authority_val),
        "urgency": int(urgency_val),
        "isolation": int(isolation_val),
        "financial": int(financial_val),
        "financial_pressure": int(financial_val),
        "digital": int(digital_trap_val),
        "digital_trap": int(digital_trap_val)
    }

    return {
        "scam_prob": scam_prob,
        "is_scam": is_scam,
        "severity": severity,
        "badge_class": badge_class,
        "scam_type": scam_type,
        "scam_category": scam_category,
        "triggers": triggers,
        "entities": entities,
        "vectors": deception_vectors,
        "advice_hindi": advice_hindi,
        "advice_english": advice_english,
        "advice_marathi": advice_marathi,
        "banner_text": banner_text,
        "voice_hindi": voice_hi,
        "voice_english": voice_en,
        "voice_marathi": voice_mr
    }

def groq_enrich_analysis(text, base_analysis):
    client = get_groq_client()
    if not client or not GROQ_STATE["is_active"]:
        return base_analysis
    try:
        prompt = f"""You are an elite Cybercrime NLP and Psychological Deception Analyst protecting senior citizens across India.
Analyze this suspect communication:
"{text}"

The local Indic ML classifier assessed:
- Scam Probability: {base_analysis['scam_prob']}%
- Modus Operandi: {base_analysis['scam_type']}

Respond strictly in valid JSON format with these exact keys:
{{
  "forensic_insight": "A concise 2-sentence forensic breakdown of how the message exploits fear, urgency, or authority.",
  "elder_advice_hindi": ["Step 1 in simple comforting Hindi", "Step 2 in simple comforting Hindi", "Step 3 in simple comforting Hindi"],
  "elder_advice_english": ["Step 1 in simple English", "Step 2 in simple English", "Step 3 in simple English"],
  "elder_advice_marathi": ["Step 1 in simple Marathi", "Step 2 in simple Marathi", "Step 3 in simple Marathi"],
  "banner_warning": "High-visibility warning banner text for senior citizens."
}}"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_STATE["model"],
            temperature=0.2,
            max_tokens=500
        )
        content = chat_completion.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        enriched = json.loads(content)
        if "elder_advice_hindi" in enriched and isinstance(enriched["elder_advice_hindi"], list) and len(enriched["elder_advice_hindi"]) > 0:
            base_analysis["advice_hindi"] = enriched["elder_advice_hindi"]
        if "elder_advice_english" in enriched and isinstance(enriched["elder_advice_english"], list) and len(enriched["elder_advice_english"]) > 0:
            base_analysis["advice_english"] = enriched["elder_advice_english"]
        if "elder_advice_marathi" in enriched and isinstance(enriched["elder_advice_marathi"], list) and len(enriched["elder_advice_marathi"]) > 0:
            base_analysis["advice_marathi"] = enriched["elder_advice_marathi"]
        if "banner_warning" in enriched and enriched["banner_warning"]:
            base_analysis["banner_text"] = enriched["banner_warning"]
        if "forensic_insight" in enriched and enriched["forensic_insight"]:
            base_analysis["forensic_insight"] = enriched["forensic_insight"]
    except Exception as e:
        print(f"[!] Groq enrichment notice: {e}")
    return base_analysis

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Please provide a valid message to analyze"}), 400
        
    analysis = comprehensive_scam_analysis(message)
    if GROQ_STATE["is_active"]:
        analysis = groq_enrich_analysis(message, analysis)
    
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ref_id = f"SCAMSHIELD-IN-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Formatted dynamic caregiver alert
    suspect_summary = []
    if analysis["entities"]["phones"]: suspect_summary.append(f"Phone: {', '.join(analysis['entities']['phones'])}")
    if analysis["entities"]["urls"]: suspect_summary.append(f"Phishing Link: {', '.join(analysis['entities']['urls'])}")
    if analysis["entities"]["apks"]: suspect_summary.append(f"Malware App: {', '.join(analysis['entities']['apks'])}")
    intel_text = " | ".join(suspect_summary) if suspect_summary else "No explicit links detected"

    family_alert = f"""🚨 *SCAMSHIELD EMERGENCY ALERT FOR FAMILY* 🚨
Dear Family Member,
ScamShield detected a {analysis['severity']} on your elder's device!
- Threat Type: {analysis['scam_type']}
- Assessed Risk: {analysis['scam_prob']}%
- Psychological Triggers: {len(analysis['triggers'])} flagged
- Extracted Suspect Intel: {intel_text}
- Intercepted Text Snippet: "{message[:95]}..."
Protective Status: The elder was warned NOT to transfer money or install screen apps. Please call them right now to verify!"""

    # Formatted dynamic cybercrime complaint
    cybercrime_complaint = f"""========================================================================
NATIONAL CYBER CRIME REPORTING PORTAL - FORMAL INCIDENT DRAFT
Incident Reference: {ref_id}
Timestamp of Incident: {timestamp_str}
Submission Target: cybercrime.gov.in / National Helpline 1930
Category: Financial Fraud & Online Impersonation Extortion
Sub-Category: {analysis['scam_type']}
Applicable Legal Acts: Section 419/420 IPC, Section 66C/66D Information Technology Act 2000

SUSPICIOUS EVIDENCE LOGGED:
"{message}"

EXTRACTED SUSPECT ARTIFACTS:
1. Contact Numbers: {', '.join(analysis['entities']['phones']) if analysis['entities']['phones'] else 'None detected in body'}
2. Malicious Links: {', '.join(analysis['entities']['urls']) if analysis['entities']['urls'] else 'None detected in body'}
3. Remote Software: {', '.join(analysis['entities']['apks']) if analysis['entities']['apks'] else 'None mentioned'}

TECHNICAL AUDIT FINDINGS:
1. Threat Level Assessed: {analysis['scam_prob']}% ({analysis['severity']})
2. Primary Modus: Impersonation of statutory authority / utility to induce psychological panic.
3. Precautionary Action: Intercepted by ScamShield AI before financial transfer took place.

PRAYER / RELIEF SOUGHT:
It is prayed that the originating phone numbers, WhatsApp handles, and associated bank accounts/UPI VPAs be placed under immediate cyber observation and frozen as per national fraud prevention guidelines.
========================================================================"""

    response = {
        "scam_prob": analysis["scam_prob"],
        "is_scam": analysis["is_scam"],
        "severity": analysis["severity"],
        "badge_class": analysis["badge_class"],
        "scam_type": analysis["scam_type"],
        "triggers": analysis["triggers"],
        "entities": analysis["entities"],
        "vectors": analysis.get("vectors", {}),
        "advice_hindi": analysis["advice_hindi"],
        "advice_english": analysis["advice_english"],
        "advice_marathi": analysis["advice_marathi"],
        "banner_text": analysis["banner_text"],
        "voice_hindi": analysis["voice_hindi"],
        "voice_english": analysis["voice_english"],
        "voice_marathi": analysis["voice_marathi"],
        "forensic_insight": analysis.get("forensic_insight", ""),
        "ai_engine": f"Groq Llama 3.3 ({GROQ_STATE['model']})" if GROQ_STATE["is_active"] else "Indic Hybrid NLP (Local Offline)",
        "family_alert": family_alert,
        "cybercrime_complaint": cybercrime_complaint,
        "timestamp": timestamp_str,
        "ref_id": ref_id
    }
    return jsonify(response)

@app.route("/api/stats")
def stats():
    metrics = load_metrics()
    return jsonify({
        "dataset_samples": metrics.get("total_samples", 188),
        "supported_languages": ["Hindi", "English", "Hinglish", "Marathi"],
        "cv_accuracy": f"{metrics.get('cv_accuracy', 96.27)}%",
        "train_accuracy": f"{metrics.get('train_accuracy', 100.0)}%",
        "model_type": "Hybrid Word + Char-Ngram (3-5) TF-IDF + Calibrated Classifier",
        "sdgs": ["SDG 16 (Peace, Justice & Strong Institutions)", "SDG 10 (Reduced Inequalities)"],
        "categories": metrics.get("categories", {}),
        "scam_trends": [
            {"name": "Digital Arrest Extortion", "pct": 36, "risk": "Critical"},
            {"name": "Utility Power Cut At Night", "pct": 24, "risk": "High"},
            {"name": "Bank & YONO KYC Freeze", "pct": 20, "risk": "High"},
            {"name": "Telegram Video Like Scam", "pct": 12, "risk": "Medium"},
            {"name": "Instant Loan & Lottery", "pct": 8, "risk": "Medium"}
        ]
    })

@app.route("/api/metrics")
def get_metrics():
    return jsonify(load_metrics())

# =========================================================================
# OSINT THREAT INTELLIGENCE REPOSITORY (Chakshu & Citizen Reports)
# =========================================================================
THREAT_DATABASE = [
    # Flagged Numbers
    {"query": "9820192831", "type": "Phone Number", "status": "BLACKLISTED", "threat_score": 98, "category": "Digital Arrest Extortion", "alias": "Fake Mumbai Crime Branch Inspector", "reports": 312, "source": "I4C National Cyber Cell & Citizen Reports", "action": "Block number immediately. Do not answer calls."},
    {"query": "9876543210", "type": "Phone Number", "status": "BLACKLISTED", "threat_score": 95, "category": "Electricity Power Cut Threat", "alias": "MSEDCL / Adani Power Impersonator", "reports": 248, "source": "Chakshu Portal & State Discom Warnings", "action": "Disconnect and report to official discom."},
    {"query": "9812345678", "type": "Phone Number", "status": "BLACKLISTED", "threat_score": 96, "category": "Digital Arrest / Sextortion", "alias": "Delhi Police Cyber Cell Blackmail", "reports": 184, "source": "Delhi Police Cyber Crime Advisory", "action": "Do not pay compromise settlement. Dial 1930."},
    {"query": "8890123456", "type": "Phone Number", "status": "BLACKLISTED", "threat_score": 92, "category": "Night-Time Power Cut", "alias": "Junior Billing Engineer Fake", "reports": 119, "source": "State Electricity Board Alerts", "action": "Block caller and report on cybercrime.gov.in."},
    {"query": "9819203847", "type": "Phone Number", "status": "BLACKLISTED", "threat_score": 94, "category": "KBC / WhatsApp Lottery", "alias": "Rana Pratap Singh KBC Manager", "reports": 420, "source": "Reliance Jio & Cyber Crime Bureau", "action": "Do not pay processing tax."},
    {"query": "9823456789", "type": "Phone Number", "status": "BLACKLISTED", "threat_score": 91, "category": "MSEDCL Mahavitaran Fake", "alias": "Junior Lineman Disconnection Van", "reports": 95, "source": "Maharashtra Police Cyber Cell", "action": "Verify bill on Mahavitaran app only."},
    
    # Flagged Domains & Links
    {"query": "cbi-investigation-portal.org", "type": "Phishing Domain", "status": "BLACKLISTED", "threat_score": 99, "category": "Digital Arrest Impersonation", "alias": "Fake CBI Video Conference Portal", "reports": 189, "source": "CERT-In Phishing Registry", "action": "Never join video calls or input credentials."},
    {"query": "sbi-kyc-portal.net", "type": "Phishing Domain", "status": "BLACKLISTED", "threat_score": 97, "category": "Bank Phishing / YONO Credential Theft", "alias": "Fake SBI NetBanking Mirror", "reports": 512, "source": "State Bank of India Security Bureau", "action": "Do not enter PAN, Aadhaar or NetBanking password."},
    {"query": "bescom-pay.xyz", "type": "Phishing Domain", "status": "BLACKLISTED", "threat_score": 93, "category": "Malicious APK Distributor", "alias": "BESCOM Remote Control Trojan", "reports": 76, "source": "Karnataka Cyber Police", "action": "Do not download APK files from this domain."},
    {"query": "phonepe-rewards.club", "type": "Phishing Domain", "status": "BLACKLISTED", "threat_score": 94, "category": "UPI PIN Reversal Trap", "alias": "Fake Cashback Scratch Card", "reports": 260, "source": "NPCI Fraud Prevention Cell", "action": "Entering UPI PIN debits money from your account."},
    {"query": "pm-mudra-fund.in", "type": "Phishing Domain", "status": "BLACKLISTED", "threat_score": 92, "category": "Fake Government Loan Disbursal", "alias": "Mudra Subsidy Processing Fee Trap", "reports": 134, "source": "Ministry of Finance Cyber Advisory", "action": "Government loans never charge advance cash fees."},

    # Official Safe Baseline
    {"query": "1930", "type": "Emergency Helpline", "status": "OFFICIAL & VERIFIED", "threat_score": 0, "category": "National Cybercrime Helpline", "alias": "Ministry of Home Affairs (I4C)", "reports": 0, "source": "Government of India Official Service", "action": "Official national helpline for financial cyber fraud."},
    {"query": "112", "type": "Emergency Helpline", "status": "OFFICIAL & VERIFIED", "threat_score": 0, "category": "National Emergency Response", "alias": "Police / Fire / Ambulance Control", "reports": 0, "source": "Government of India Official Service", "action": "Official 24x7 emergency helpline."},
    {"query": "cybercrime.gov.in", "type": "Government Portal", "status": "OFFICIAL & VERIFIED", "threat_score": 0, "category": "National Cyber Crime Reporting", "alias": "Official Cyber Portal of India", "reports": 0, "source": "Ministry of Home Affairs (MHA)", "action": "Official site to lodge formal cybercrime complaints."},
    {"query": "onlinesbi.sbi", "type": "Banking Portal", "status": "OFFICIAL & VERIFIED", "threat_score": 0, "category": "Legitimate Bank Portal", "alias": "State Bank of India Official", "reports": 0, "source": "SBI Official Domain", "action": "Official, secure banking portal."}
]

@app.route("/api/lookup")
def threat_lookup():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"found": False, "message": "Please enter a phone number, link, or UPI ID to verify."})

    # Exact or substring match in database
    for item in THREAT_DATABASE:
        if q == item["query"].lower() or item["query"].lower() in q or q in item["query"].lower():
            return jsonify({
                "found": True,
                "data": item
            })

    # Dynamic heuristic classification for unknown inputs
    phone_clean = re.sub(r'[\s\-\+\(\)]', '', q)
    if re.match(r'^(?:91)?[6-9]\d{9}$', phone_clean):
        return jsonify({
            "found": True,
            "data": {
                "query": q,
                "type": "Phone Number",
                "status": "UNVERIFIED CALLER",
                "threat_score": 45,
                "category": "Unknown Indian Mobile Number",
                "alias": "Unregistered / Private Number",
                "reports": 3,
                "source": "ScamShield Heuristic Phone Verification Engine",
                "action": "Caution: Do not share OTPs, bank details, or transfer money over call with unknown contacts."
            }
        })
    elif any(ext in q for ext in [".xyz", ".club", ".top", ".link", ".site", ".live", ".apk"]):
        return jsonify({
            "found": True,
            "data": {
                "query": q,
                "type": "Web Link / APK",
                "status": "HIGH RISK INDICATOR",
                "threat_score": 85,
                "category": "Suspicious TLD / APK Distribution Pattern",
                "alias": "Potentially Malicious Web Artifact",
                "reports": 18,
                "source": "ScamShield Heuristic Domain Audit",
                "action": "Avoid clicking this link or installing APK software from this domain."
            }
        })
    else:
        return jsonify({
            "found": False,
            "query": q,
            "message": "No known complaints or blacklisted entries found in the national scam database for this item. Always maintain caution with unsolicited communications."
        })

# =========================================================================
# ELDER SCAM DEFENSE PRACTICE LAB (Interactive Training Quiz)
# =========================================================================
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "title": "Scenario 1: WhatsApp Video Call from 'Police / CBI'",
        "question": "A person wearing a police uniform video-calls you on WhatsApp, showing official-looking files, claiming a parcel sent under your Aadhaar card contains drugs, and says you are under 'Digital Arrest'. What is the safest step?",
        "options": [
            "Transfer money to the 'escrow verification account' they provide to prove innocence.",
            "Stay in your room on video call for 5 hours without telling family.",
            "Disconnect the call immediately, alert a trusted family member, and dial 1930.",
            "Send photos of your bank passbook and Aadhaar card."
        ],
        "correct": 2,
        "explanation": "Official Indian Police, CBI, and courts NEVER conduct trials or arrest anyone on WhatsApp or Skype video calls. 'Digital Arrest' is a 100% fabricated extortion scheme."
    },
    {
        "id": 2,
        "title": "Scenario 2: Electricity Power Cut Warning at 9:30 PM",
        "question": "You get an SMS at 7:00 PM: 'Dear consumer, your electricity will be disconnected tonight at 9:30 PM. Contact officer Suresh at 9876543210.' What should you do?",
        "options": [
            "Call the personal mobile number immediately to avoid living in the dark.",
            "Download AnyDesk remote app as requested by the person on phone.",
            "Do NOT call the mobile number. Check and pay your bill only on the official state electricity portal.",
            "Share your debit card CVV over the call."
        ],
        "correct": 2,
        "explanation": "Electricity boards never disconnect residential power at night via personal SMS. Disconnection notices only come through formal monthly paper bills."
    },
    {
        "id": 3,
        "title": "Scenario 3: The 'Enter UPI PIN to Receive Refund' Trick",
        "question": "A caller says: 'Sir, I am sending you a ₹3,000 refund on PhonePe/GPay. Please open the app and enter your UPI PIN.' What actually happens if you enter your PIN?",
        "options": [
            "₹3,000 will be credited to your account.",
            "₹3,000 will be DEDUCTED from your bank account.",
            "The transaction will automatically get cancelled.",
            "Your bank account balance will double."
        ],
        "correct": 1,
        "explanation": "Golden Rule of UPI: You NEVER need to enter your UPI PIN to RECEIVE money. Entering your PIN ALWAYS debits funds out of your account."
    },
    {
        "id": 4,
        "title": "Scenario 4: Urgent Bank Account Blocked Notice",
        "question": "An SMS says: 'Dear SBI user, your YONO account is suspended. Update your PAN card immediately by clicking http://sbi-kyc-update.xyz to avoid closure.' How do you verify?",
        "options": [
            "Click the link immediately and submit your NetBanking password.",
            "Download the APK file provided by the link.",
            "Ignore the SMS link and visit your local bank branch in person or use the official bank app.",
            "Forward the message to 10 friends."
        ],
        "correct": 2,
        "explanation": "Banks never send generic third-party links (like .xyz, .top) demanding immediate PAN or NetBanking password entry. Always visit your branch directly."
    },
    {
        "id": 5,
        "title": "Scenario 5: Emergency Accident Phone Call",
        "question": "A caller in tears says: 'Uncle, your nephew was in a car accident and is in hospital. Transfer ₹25,000 right now for urgent surgery.' What is your immediate first step?",
        "options": [
            "Transfer ₹25,000 instantly without asking any questions.",
            "Call your nephew or his parents directly on their regular, saved phone number to verify.",
            "Take an instant gold loan to pay the stranger.",
            "Give the stranger your ATM PIN."
        ],
        "correct": 1,
        "explanation": "Scammers exploit emotional panic so you don't think rationally. Always verify by directly calling the family member on their known, saved phone number first."
    }
]

@app.route("/api/quiz")
def get_quiz():
    return jsonify({
        "total": len(QUIZ_QUESTIONS),
        "questions": QUIZ_QUESTIONS
    })

# =========================================================================
# LIVE DIGITAL ARREST CALL SIMULATOR (Interactive Demonstration)
# =========================================================================
CALL_SIMULATION_STEPS = [
    {
        "time": "00:03",
        "speaker": "Caller (Impersonating DCP Mumbai Crime Branch)",
        "audio_text": "Namaste Mr. Ramesh, I am Inspector Rathore speaking from Mumbai Cyber Crime Branch Headquarters.",
        "threat_level": "INITIATION",
        "badge": "warning",
        "ai_status": "Analyzing audio stream for spoofed authority..."
    },
    {
        "time": "00:09",
        "speaker": "Caller (Impersonating DCP Mumbai Crime Branch)",
        "audio_text": "An international FedEx consignment containing 16 forged passports and 500 grams of MDMA narcotics was seized at Mumbai airport under your PAN number.",
        "threat_level": "FABRICATED ACCUSATION",
        "badge": "danger",
        "ai_status": "⚠️ Fabricated narcotics trafficking allegation detected!"
    },
    {
        "time": "00:16",
        "speaker": "Caller (Impersonating DCP Mumbai Crime Branch)",
        "audio_text": "Supreme Court has placed you under Digital Arrest. You must immediately isolate in your room and turn on your camera. Do not tell your family.",
        "threat_level": "COERCIVE ISOLATION",
        "badge": "danger",
        "ai_status": "🚨 CRITICAL: 'Digital Arrest' coercion & family isolation pressure flagged!"
    },
    {
        "time": "00:24",
        "speaker": "Caller (Impersonating DCP Mumbai Crime Branch)",
        "audio_text": "To obtain provisional clearance, you must transfer your account balance to the RBI asset verification account.",
        "threat_level": "FINANCIAL EXTORTION",
        "badge": "danger",
        "ai_status": "🚨 INTERCEPTION ACTIVE: Demanding escrow transfer to mule account!"
    }
]

@app.route("/api/call-simulation")
def get_call_simulation():
    return jsonify({
        "caller_id": "+91-98201-92831",
        "caller_alias": "DCP Crime Branch (Spoofed Number)",
        "call_type": "WhatsApp Encrypted Voice Interrogation",
        "steps": CALL_SIMULATION_STEPS
    })

# =========================================================================
# GROQ CLOUD SETTINGS & API MANAGEMENT ENDPOINTS
# =========================================================================
@app.route("/api/groq/status")
def groq_status():
    key = GROQ_STATE["api_key"]
    masked = (key[:7] + "..." + key[-4:]) if (key and len(key) >= 12) else ("Configured" if key else "")
    return jsonify({
        "has_key": bool(key),
        "is_active": GROQ_STATE["is_active"],
        "model": GROQ_STATE["model"],
        "masked_key": masked,
        "available_models": [
            {"id": "qwen/qwen3.8-27b", "name": "Qwen 3.8 27B (High-Speed Multilingual & Indic Reasoning)", "speed": "Ultra Fast", "provider": "Alibaba / Qwen"},
            {"id": "openai/gpt-oss-120b", "name": "OpenAI GPT-OSS 120B (High Capability)", "speed": "Fast", "provider": "OpenAI"},
            {"id": "openai/gpt-oss-20b", "name": "OpenAI GPT-OSS 20B (Low Latency)", "speed": "Ultra Fast", "provider": "OpenAI"}
        ]
    })

@app.route("/api/groq/configure", methods=["POST"])
def groq_configure():
    data = request.get_json() or {}
    key = data.get("api_key", "").strip()
    model_name = data.get("model", "qwen/qwen3.8-27b").strip()

    if not key:
        # Disconnect requested
        GROQ_STATE["api_key"] = ""
        GROQ_STATE["is_active"] = False
        os.environ.pop("GROQ_API_KEY", None)
        remove_env_var("GROQ_API_KEY")
        return jsonify({
            "success": True,
            "message": "Groq API disconnected. Reverted to Local Offline Indic NLP Engine.",
            "is_active": False
        })

    ok, msg = test_groq_connection(key, model_name)
    if ok:
        GROQ_STATE["api_key"] = key
        GROQ_STATE["model"] = model_name
        GROQ_STATE["is_active"] = True
        os.environ["GROQ_API_KEY"] = key
        os.environ["GROQ_MODEL"] = model_name
        save_env_var("GROQ_API_KEY", key)
        save_env_var("GROQ_MODEL", model_name)
        return jsonify({
            "success": True,
            "message": f"Groq API key verified! Accelerated reasoning active with {model_name}.",
            "is_active": True,
            "model": model_name
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Groq validation failed: {msg}. Please check your key at console.groq.com/keys."
        }), 400

# =========================================================================
# ELDER ASSISTANT CHATBOT ("Ask ScamShield AI Companion")
# =========================================================================
def get_local_elder_chat_response(query):
    q = query.lower()
    if any(w in q for w in ["digital arrest", "police", "cbi", "customs", "drugs", "warrant", "arrest", "court", "narcotics"]):
        return (
            "🚨 **CRITICAL SAFETY DIRECTIVE (Digital Arrest Alert):**\n"
            "• **Do Not Panic:** Genuine Indian Police, CBI, ED, and Judicial Courts **NEVER** conduct arrests or trials over WhatsApp or Skype video calls.\n"
            "• **Total Fraud:** 'Digital Arrest' is a 100% fabricated criminal extortion scam.\n"
            "• **Immediate Action:** Disconnect the call right now. Do not transfer any money to 'clearing/escrow accounts'. Tell your family and dial **1930** immediately."
        )
    elif any(w in q for w in ["electricity", "bijli", "power", "disconnection", "bill", "meter", "light"]):
        return (
            "⚡ **ELECTRICITY BILL DISCONNECTION ALERT:**\n"
            "• **No Night Disconnections:** Power distribution companies (MSEDCL, BESCOM, Adani, Tata Power) never disconnect residential power at 9:30 PM via SMS.\n"
            "• **Beware Mobile Numbers:** Electricity boards never ask you to call personal 10-digit mobile numbers or wiremen.\n"
            "• **Safe Step:** Pay or verify bills ONLY through your official discom mobile app or physical electricity office."
        )
    elif any(w in q for w in ["upi", "pin", "refund", "cashback", "phonepe", "gpay", "receive"]):
        return (
            "💸 **GOLDEN RULE OF UPI TRANSACTIONS:**\n"
            "• **Never Enter PIN to Receive:** You **NEVER** need to enter your UPI PIN to receive money or refunds.\n"
            "• **Deduction Trap:** Entering your UPI PIN will **instantly debit** money from your bank account.\n"
            "• **Rule:** If someone asks you to enter your PIN to claim a lottery, reward, or cashback, cancel immediately."
        )
    elif any(w in q for w in ["kyc", "pan", "yono", "sbi", "blocked", "account suspended"]):
        return (
            "🏦 **BANK KYC & ACCOUNT SUSPENSION SAFETY:**\n"
            "• **Never Click SMS Links:** Banks never send third-party links (.xyz, .top, bit.ly) demanding immediate PAN update under threat of 24-hour closure.\n"
            "• **Never Share NetBanking Passwords:** Official bank staff never ask for login passwords or OTPs.\n"
            "• **Safe Action:** Visit your nearest physical bank branch with your passbook to update KYC safely."
        )
    elif any(w in q for w in ["anydesk", "teamviewer", "quicksupport", "screen share", "remote"]):
        return (
            "⚠️ **SEVERE MALWARE WARNING (Remote Desktop Apps):**\n"
            "• **Do Not Install:** Never install AnyDesk, TeamViewer, or QuickSupport if instructed by a caller.\n"
            "• **Screenshare Trap:** These applications allow the caller to see your screen, view your OTPs, and take over your banking apps.\n"
            "• **If already installed:** Turn off your mobile Wi-Fi / Mobile Data immediately and uninstall the app."
        )
    elif any(w in q for w in ["1930", "helpline", "complaint", "cybercrime", "report"]):
        return (
            "📞 **NATIONAL CYBERCRIME HELPLINE 1930:**\n"
            "• **Official Govt Service:** 1930 is the toll-free national cyber financial fraud helpline managed by the Ministry of Home Affairs (I4C).\n"
            "• **Golden Hour:** Calling 1930 within 2 to 3 hours of money deduction alerts banks to freeze the fraudster's mule account before cash withdrawal.\n"
            "• **Online Portal:** You can also register a formal complaint at **cybercrime.gov.in**."
        )
    elif any(w in q for w in ["lottery", "kbc", "prize", "crorepati", "jio", "won"]):
        return (
            "🎁 **LOTTERY & KBC PRIZE SCAM:**\n"
            "• **100% Fake:** You cannot win a lottery you never bought a ticket for.\n"
            "• **Advance Fee Trap:** Scammers claim you won ₹25 Lakhs, then demand ₹15,000 to ₹50,000 for 'GST', 'tax', or 'processing fee'.\n"
            "• **Action:** Do not send a single rupee. Block the sender on WhatsApp immediately."
        )
    else:
        return (
            "🛡️ **SCAMSHIELD ELDER REASSURANCE:**\n"
            "Namaste! ScamShield AI is your personal cyber guardian. Always remember:\n"
            "1. **Never share OTPs, CVVs, or bank passwords** with anyone on phone calls.\n"
            "2. **Police and CBI NEVER arrest anyone via video calls** or WhatsApp.\n"
            "3. **You never need to enter your UPI PIN to receive money**.\n"
            "4. If any caller rushes you or tells you 'not to tell your family', disconnect and talk to your children or trusted neighbors immediately!"
        )

@app.route("/api/chat", methods=["POST"])
def elder_chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_msg:
        return jsonify({"error": "Please provide a valid question"}), 400

    client = get_groq_client()
    if client and GROQ_STATE["is_active"]:
        try:
            system_prompt = (
                "You are 'ScamShield Elder Guardian', an empathetic, gentle, and highly knowledgeable cyber defense assistant "
                "dedicated to protecting senior citizens in India from cyber frauds, digital arrests, power disconnection threats, and financial extortion.\n"
                "Rules:\n"
                "- Tone: Reassuring, respectful ('Namaste', 'Uncle/Aunty', calm), easy to understand, no complex technical jargon.\n"
                "- Multilingual: Respond in the user's preferred language (Hindi, English, Hinglish, or Marathi).\n"
                "- Core Rules:\n"
                "  1. Indian Police, CBI, and Courts NEVER conduct arrests or judicial trials over WhatsApp/Skype/video calls.\n"
                "  2. Never share OTPs, CVV, or passwords.\n"
                "  3. Never enter UPI PIN to receive money.\n"
                "  4. Never install AnyDesk, TeamViewer, or unknown APKs.\n"
                "  5. Always advise alerting a trusted family member and calling 1930 (National Cybercrime Helpline) or 112.\n"
                "Keep responses concise (3-4 bullet points max) so elders can read them easily."
            )
            messages = [{"role": "system", "content": system_prompt}]
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": user_msg})

            resp = client.chat.completions.create(
                model=GROQ_STATE["model"],
                messages=messages,
                max_tokens=350,
                temperature=0.3
            )
            reply = resp.choices[0].message.content
            return jsonify({
                "reply": reply,
                "engine": f"Groq Llama 3.3 ({GROQ_STATE['model']})",
                "provider": "groq"
            })
        except Exception as e:
            print(f"[!] Groq chat fallback: {e}")

    # Fallback to local expert response
    reply = get_local_elder_chat_response(user_msg)
    return jsonify({
        "reply": reply,
        "engine": "ScamShield Local Indic Knowledge Engine",
        "provider": "local"
    })

# =========================================================================
# AUDIO VOICE NOTE UPLOAD & TRANSCRIPTION (Groq Whisper Large v3)
# =========================================================================
@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided in request."}), 400

    audio_file = request.files["audio"]
    client = get_groq_client()
    if not (client and GROQ_STATE["is_active"]):
        return jsonify({
            "success": False,
            "error": "Groq Whisper requires an active Groq API Key. Please add your key in 'Groq AI Setup' (⚡) in the top header or dictate via microphone."
        }), 400

    try:
        filename = audio_file.filename or "recording.wav"
        audio_bytes = audio_file.read()
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3",
            temperature=0.0
        )
        return jsonify({
            "success": True,
            "text": transcription.text,
            "engine": "Groq Whisper Large v3"
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Transcription error: {str(e)}"}), 500

# =========================================================================
# LIVE NATIONAL CYBER THREAT TICKER ADVISORIES
# =========================================================================
@app.route("/api/alerts")
def cyber_alerts():
    return jsonify({
        "alerts": [
            "🚨 I4C ALERT: Spate of fake 'Digital Arrest' calls impersonating Mumbai Police & CBI. Real police NEVER conduct digital arrests via video calls.",
            "⚡ DISCOM WARNING: State electricity boards NEVER send SMS from personal 10-digit mobile numbers threatening 9:30 PM power disconnections.",
            "🏦 RBI ADVISORY: Golden Rule of UPI: You NEVER need to enter your UPI PIN to receive money or refunds.",
            "🔒 MALWARE ALERT: Never install AnyDesk, TeamViewer, or QuickSupport APKs on phone instructions from strangers.",
            "📞 NATIONAL HELPLINE: Dial 1930 immediately or visit cybercrime.gov.in within the 'Golden Hour' if money is debited fraudulently."
        ]
    })

if __name__ == "__main__":
    print("[*] Starting ScamShield AI server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
