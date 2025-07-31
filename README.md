# Dueling Quibblers

A fun CLI application that creates debates between fantasy characters using LangGraph and Ollama. This assumes you are running a MacBook with Python 3.9 (or higher).

## Features

- Interactive CLI interface for debate setup (or in the browser with Streamlit frontend)
- Fantasy character debaters with unique personalities and speaking styles
- 3-round debate format with memory of previous arguments
- Powered by Ollama's LLM
- Built with LangGraph for structured conversation flow

## Setup to run locally on your laptop
1a. Install Ollama (which allows you to run a LLM right on your laptop!) at https://ollama.com/. Please go to the website and download the installation file and install it.
1b. Open up a Terminal and download an Ollama LLM model by typing:
```bash
ollama pull llama3.1:8b  # this will take a few minutes since the model is a few GBs
```
1c. Run the Ollama model by typing in the Terminal and leave it on:
```bash
ollama run llama3.1:8b  # you can type questions to the LLM and it will respond!
```

2. Copy this repo to your laptop by either using `git clone` (or manually copy all the files to a folder called `dueling-quibblers/`)
```bash
<<<<<<< Updated upstream
python3 -m venv .venv  # assumes you have a Python 3.11+ environment
=======
git clone https://github.com/eugeneh101/dueling-quibblers.git
```

3a. See what version of Python you have. This code uses Python 3.9 (or higher).
```bash
python3 -V
```
3b. In a new Terminal (keep the previous Terminal running Ollama on), create a Python 3.9+ virtual environment, activate it, and install the dependencies in the virtual environment:
```bash
python3 -m venv .venv  # assumes you have a Python 3.9+ environment
>>>>>>> Stashed changes
source .venv/bin/activate  # if you are on a Mac, it's different if you are on Windows
pip3 install -r requirements.txt
```

4a. Run Dueling Quibblers in the Terminal:
```bash
python3 dueling_quibblers_v4.py
```
4b. Or run Dueling Quibblers in the browser using Streamlit and go to the browser url mentioned in the Terminal (most likely http://localhost:8501):
```bash
streamlit run app_v3.py
```

5. Have fun and be inspired! You can try another Ollama LLM such as phi4-mini and update line 43 in `dueling_quibblers_v4.py` with `OllamaLLM(model="phi4-mini")`.
```bash
ollama pull phi4-mini  # this will take a few minutes since the model is a few GBs
ollama run phi4-mini  # you can type questions to the LLM and it will respond!
```

## Usage

1. Enter the debate topic when prompted
2. Enter the first debater character (e.g., "Harry Potter", "Phoenix Wright")
3. Enter the second debater character
4. Watch as the characters debate with 3 rounds each!
5. Characters are randomly assigned affirmative/negative positions
6. Judge is randomly assigned and will give the verdict!

## Example

```
Topic: Should magic be taught in schools?
Debater 1: Harry Potter
Debater 2: Phoenix Wright

[Debate begins with 3 rounds each...]
