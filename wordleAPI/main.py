from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from datetime import date
import logging

# Szavak betöltése
file_path = os.path.join(os.path.dirname(__file__), "words.txt")
with open(file_path, "r") as f:
    valid_words = set(word.strip().lower() for word in f)

app = FastAPI()

# CORS engedélyezése
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

solutionMap = {}
def get_wordle_answer(date):
    # NYT Wordle API URL
    url = f"https://www.nytimes.com/svc/wordle/v2/{date}.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Check for errors
        data = response.json()
        solutionFormatter(data['solution'])
        return data['solution']
    except Exception as e:
        return f"Error: {e}"
def solutionFormatter(solution):
    global solutionMap 
    solutionMap = {}
    for i, letter in enumerate(solution):
        if letter not in solutionMap:
            solutionMap[letter] = []
        solutionMap[letter].append(i)
solution = get_wordle_answer(date.today())


@app.post("/set-wordle")
async def set_solution(request: Request):
    data = await request.json()
    date = data.get("date")
    
    if not date:
        return JSONResponse(content={"success": False, "error": "Date is required"})
    
    solution = get_wordle_answer(date)
    
    return JSONResponse(content={"success": True})
    

@app.post("/check-word")
async def check_word(request: Request):
    data = await request.json()
    word = data.get("word", "").lower()
    found = word in valid_words
    return JSONResponse(status_code=200, content={"found": found})

@app.post("/eval")
async def evaluate(request: Request):
    data = await request.json()
    word = data.get("word", "").lower()
    
    result = ["gray"] * 5
    print(word)
    print("teszt")
    
    # number of occurrences
    letterCounter = {}
    for letter, occurrences in solutionMap.items():
        letterCounter[letter] = len(occurrences)
    
    # GREEN
    for i, letter in enumerate(word):
        if letter in solutionMap and i in solutionMap[letter]:
            result[i] = "green"
            letterCounter[letter] -= 1
    
    # YELLOW
    for i, letter in enumerate(word):
        if letter in solutionMap and result[i] == "gray" and letterCounter[letter] > 0:
            result[i] = "yellow"
            letterCounter[letter] -= 1
    
    return JSONResponse(status_code=200, content={"result": result})
    