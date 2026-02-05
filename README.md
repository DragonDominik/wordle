This is the recreation of the popular game WORDLE with an additional feature to suggests the best next guess based on **information theory (entropy)**.  
It supports fetching the Wordle solution from the NYT API, checking words, evaluating patterns, and calculating entropy-based recommendations.

---

## Stack

- **Backend:** Python + FastAPI  
- **Frontend:** JavaScript + Tailwind CSS  

## Features

- Fetches today's (or any days) Wordle solution from the NYT API  
- Checks if a word is valid  
- Evaluates a word against the solution with **green/yellow/gray feedback**  
- Suggests the next best guess using **information-theoretic entropy**  
- Filters possible solutions based on previous guesses  

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DragonDominik/wordle.git
cd wordle
```
2. Create a virtual environment
```
python -m venv .venv
```
3. Activate the virtual enviroment
```
Windows
.\.venv\Scripts\activate
Linux/Mac
source .venv/bin/activate
```
4. Install dependacies
```
pip install -r requirements.txt
```

---

## Usage

Start the FastAPI server
```
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Credits

Huge thanks to dracos for the valid wordle word list!
[@dracos](https://github.com/dracos).  
