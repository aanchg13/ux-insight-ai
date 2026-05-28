from fastapi import FastAPI, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import anthropic
from dotenv import load_dotenv
import PyPDF2
import pandas as pd
import io
import json

load_dotenv()

app = FastAPI()
client = anthropic.Anthropic()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

def run_analysis(combined: str):
    prompt = f"""You are an expert UX researcher. Analyze the following user interview transcripts and extract structured insights.

Return ONLY a valid JSON object with this exact structure, no other text before or after:
{{
  "themes": [
    {{
      "name": "theme name",
      "description": "brief description",
      "quotes": ["exact quote from transcript"],
      "frequency": 1,
      "severity": "high/medium/low"
    }}
  ],
  "pain_points": ["pain point 1", "pain point 2"],
  "user_needs": ["need 1", "need 2"],
  "summary": "2-3 sentence executive summary"
}}

Keep quotes short (under 15 words each). Maximum 3 quotes per theme. Be concise throughout.

Transcripts:
{combined}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text.strip())

@app.post("/analyze")
async def analyze(files: list[UploadFile] = File(...)):
    texts = []
    for file in files:
        content = await file.read()
        if file.filename.endswith(".txt"):
            texts.append(content.decode("utf-8"))
        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            texts.append("\n".join([page.extract_text() for page in reader.pages]))
        elif file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
            texts.append(df.to_string())

    combined = "\n\n---NEW TRANSCRIPT---\n\n".join(texts)
    insights = run_analysis(combined)
    return JSONResponse(content=insights)

@app.post("/sample")
async def sample():
    texts = []
    for filename in ["banking_sarah.txt", "banking_marcus.txt", "banking_priya.txt"]:
        with open(filename, "r") as f:
            texts.append(f.read())

    combined = "\n\n---NEW TRANSCRIPT---\n\n".join(texts)
    insights = run_analysis(combined)
    return JSONResponse(content=insights)