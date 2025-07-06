from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from transformers import pipeline
from fastmcp import FastMCP
import json
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi import Query
from fastapi.responses import RedirectResponse
import random
from collections import defaultdict




affirmations = [
    "You are enough just as you are 🌸",
    "Every day you’re growing stronger 🌱",
    "You bring light to the world 💡",
    "It’s okay to not be okay 🤍",
    "Your feelings are valid, always 💖",
    "You’ve overcome so much already 🌈",
    "Breathe. You’re doing great 🌬️",
    "You deserve love and rest 🫶"
]



# Create FastAPI app
fastapi_app = FastAPI()
fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

app = FastMCP("sentiment-analysis", fastapi_app)

# Load sentiment analysis model
sentiment_model = pipeline("sentiment-analysis")
templates = Jinja2Templates(directory="templates")

JOURNAL_FILE = "journal.json"

# Ensure journal file exists
try:
    with open(JOURNAL_FILE, "x") as f:
        json.dump([], f)
except FileExistsError:
    pass

@fastapi_app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@fastapi_app.post("/analyze", response_class=HTMLResponse)
def analyze(request: Request, user_input: str = Form(...)):
    result = sentiment_model(user_input)[0]
    mood = result["label"]
    confidence = round(result["score"] * 100, 2)

    # Choose quote based on mood and confidence
    quote = ""
    affirmation = random.choice(affirmations)

    if mood.upper() == "POSITIVE":
        quote = "You're unstoppable today! 🎉" if confidence >= 85 else "A little smile goes a long way. 🌤️"
    elif mood.upper() == "NEGATIVE":
        quote = "It's okay to not be okay. Be gentle with yourself. 🫂" if confidence >= 85 else "You're doing your best, even if it doesn't feel like it. 🌧️"
    elif mood.upper() == "NEUTRAL":
        quote = "Steady and calm is a superpower too. 📘" if confidence >= 85 else "It’s okay to just breathe and be. 🌙"
    else:
        quote = "You got this! 💪"

    return templates.TemplateResponse("result.html", {
        "request": request,
        "mood": mood,
        "quote": quote,
        "user_input": user_input,
       "affirmation": affirmation
    })

@fastapi_app.post("/journal", response_class=HTMLResponse)
def journal(request: Request, user_input: str = Form(...), mood: str = Form(...), entry: str = Form(...)):
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "mood": mood,
        "input": user_input,
        "journal": entry
    }
    with open(JOURNAL_FILE, "r+") as f:
        data = json.load(f)
        data.append(new_entry)
        f.seek(0)
        json.dump(data, f, indent=2)

    return templates.TemplateResponse("thankyou.html", {"request": request})

from collections import defaultdict

from collections import Counter

@fastapi_app.get("/journal", response_class=HTMLResponse)
def show_journal(request: Request):
    with open(JOURNAL_FILE, "r") as f:
        entries = json.load(f)

    # Count moods
    mood_counter = Counter(entry["mood"] for entry in entries)

    return templates.TemplateResponse("journal.html", {
        "request": request,
        "entries": entries,
        "mood_data": dict(mood_counter)  # 👈 pass mood data to template
    })


@fastapi_app.get("/edit", response_class=HTMLResponse)
def edit_entry(request: Request, timestamp: str):
    with open(JOURNAL_FILE, "r") as f:
        data = json.load(f)
    entry = next((item for item in data if item["timestamp"] == timestamp), None)
    if not entry:
        return HTMLResponse("Entry not found", status_code=404)
    return templates.TemplateResponse("edit.html", {"request": request, "entry": entry})
@fastapi_app.post("/update", response_class=HTMLResponse)
def update_entry(request: Request, timestamp: str = Form(...), entry: str = Form(...), mood: str = Form(...), user_input: str = Form(...)):
    with open(JOURNAL_FILE, "r+") as f:
        data = json.load(f)
        for item in data:
            if item["timestamp"] == timestamp:
                item["journal"] = entry
                break
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
    return RedirectResponse(url="/journal", status_code=303)

@fastapi_app.post("/delete", response_class=HTMLResponse)
def delete_entry(request: Request, timestamp: str = Form(...)):
    with open(JOURNAL_FILE, "r+") as f:
        data = json.load(f)
        data = [entry for entry in data if entry["timestamp"] != timestamp]
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
    return RedirectResponse(url="/journal", status_code=303)