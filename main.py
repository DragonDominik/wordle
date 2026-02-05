from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from datetime import date

from collections import defaultdict
import math

# for speeding up
from concurrent.futures import ProcessPoolExecutor, as_completed

# load words
file_path = os.path.join(os.path.dirname(__file__), "words.txt")
with open(file_path, "r") as f:
    valid_words = set(word.strip().lower() for word in f)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

answer = ""
def get_wordle_answer(date):
    # NYT Wordle API URL
    url = f"https://www.nytimes.com/svc/wordle/v2/{date}.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Check for errors
        data = response.json()
        global answer
        answer = data['solution']
        #solution = "teens"
    except Exception as e:
        return f"Error: {e}"
get_wordle_answer(date.today())

possibleAnswers = valid_words.copy()

@app.post("/set-wordle")
async def set_solution(request: Request):
    data = await request.json()
    date = data.get("date")
    
    if not date:
        return JSONResponse(content={"success": False, "error": "Date is required"})
    
    get_wordle_answer(date)
    
    global possibleAnswers
    possibleAnswers = valid_words.copy()
    
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
    
    result = get_pattern(word, answer)
    
    return JSONResponse(status_code=200, content={"result": result})

# INFORMATION THEORY MODEL

import time

@app.post("/get-entropy")
async def root(request: Request):
    data = await request.json()
    guesses = data.get("guesses")
        
    treshold = 5
    
    doneEntropy = False
    if guesses != []:
        if len(possibleAnswers) > treshold:
            filterSolutions(guesses)
            start = time.time()
            entropy = calculate_entropy()
            print(f"Took {time.time() - start:.2f}s")
        else:
            for guess in guesses:
                possibleAnswers.discard(guess["word"])
        doneEntropy = True
    
    print(len(possibleAnswers))
    if doneEntropy:
        if(len(possibleAnswers) <= treshold):
            return JSONResponse(status_code=200, content={"mode": "remaining" ,"possibleAnswers": list(possibleAnswers)})
        else:
            return JSONResponse(status_code=200, content={"mode": "entropy", "entropies": entropy})
    else: 
        return JSONResponse(status_code=200, content={"mode": "entropy", "entropies": [('tares', 6.159376455792686), ('lares', 6.1147937838751805), ('rales', 6.096830602742281), ('rates', 6.0840618196418355), ('ranes', 6.076799032713865), ('nares', 6.074924674941598), ('reais', 6.049569076778583), ('teras', 6.047397415697396), ('soare', 6.043722976131018), ('tales', 6.0141813239031015)]})


def setFilters(guesses):
    green = {}  # {position: letter}
    yellow = {}  # {letter: forbidden positions}
    gray = set()  # incorrect letters
    letter_count = {}  # {letter: [min, max]}
    
    for guess in guesses:
        word = guess["word"].lower()
        result = guess["result"]
        
        # Count green+yellow letters in this guess
        confirmed = {}  # letter -> count
        for letter, res in zip(word, result):
            if res in ("green", "yellow"):
                confirmed[letter] = confirmed.get(letter, 0) + 1
        
        # Count total occurrences of each letter in the guess
        total_in_word = {}
        for letter in word:
            total_in_word[letter] = total_in_word.get(letter, 0) + 1
        
        # Process each position
        for i, (letter, res) in enumerate(zip(word, result)):
            if res == "green":
                green[i] = letter
            elif res == "yellow":
                if i not in yellow.get(letter, []):
                    yellow.setdefault(letter, []).append(i)
            elif res == "gray":
                # if letter in yellow or green set max
                if letter in confirmed:
                    if letter not in letter_count:
                        letter_count[letter] = [confirmed[letter], confirmed[letter]]
                    else:
                        letter_count[letter][1] = confirmed[letter]
                else:
                    gray.add(letter)
        
        # update min
        for letter, count in confirmed.items():
            if letter not in letter_count:
                letter_count[letter] = [count, 5]
            else:
                letter_count[letter][0] = max(letter_count[letter][0], count)

    for pos, letter in green.items():
        if letter in yellow and pos in yellow[letter]:
            yellow[letter].remove(pos)
    
    return green, yellow, gray, letter_count
    
def filterSolutions(guesses):
    global possibleAnswers
    green_set, yellow_set, gray_set, letter_count = setFilters(guesses)
    
    new_possible = set()
    
    for word in possibleAnswers:
        valid = True
    
        for i, letter in enumerate(word):
            if letter in gray_set:
                valid = False
                break
            if i in green_set and green_set[i] != letter:
                valid = False
                break
            if letter in yellow_set and i in yellow_set[letter]:
                valid = False
                break
        
        # min-max 
        for letter, counts in letter_count.items():
            if word.count(letter) > counts[1] or word.count(letter) < counts[0]:
                valid = False
                break
        
        if valid:
            new_possible.add(word)
    
    possibleAnswers = new_possible

def get_pattern(guess, solution):
    pattern = []
    solution_letters = list(solution)
    
    # GREEN 
    for i in range(5):
        if guess[i] == solution[i]:
            pattern.append('green')
            solution_letters[i] = None
        else:
            pattern.append(None)
    
    # YELLOW
    for i in range(5):
        if pattern[i] is None:
            if guess[i] in solution_letters:
                pattern[i] = 'yellow'
                # remove first occurrence
                solution_letters[solution_letters.index(guess[i])] = None
            else:
                pattern[i] = 'gray' # GRAY
    return tuple(pattern)

# checks all possible guesses against possible answers

# helper for single guess
def entropy_for_guess(guess, possibleAnswers):
    pattern_counts = defaultdict(int)
    for solution in possibleAnswers:
        pattern = get_pattern(guess, solution)
        pattern_counts[pattern] += 1

    total = len(possibleAnswers)
    H = 0
    for count in pattern_counts.values():
        p = count / total
        H -= p * math.log2(p)
    return (guess, H)

def calculate_entropy():
    entropies = []
    guesses = list(valid_words) if len(possibleAnswers) > 100 else list(possibleAnswers)
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(entropy_for_guess, guess, possibleAnswers) for guess in guesses]
        for future in as_completed(futures):
            entropies.append(future.result())
    entropies.sort(key=lambda x: x[1], reverse=True)
    return entropies[:10]