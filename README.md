# Dueling Quibblers

A fun CLI application that creates debates between fantasy characters using LangGraph and AWS Bedrock.

## Features

- Interactive CLI interface for debate setup
- Fantasy character debaters with unique personalities and speaking styles
- 3-round debate format with memory of previous arguments
- Powered by AWS Bedrock
- Built with LangGraph for structured conversation flow

## Setup

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

2. Configure AWS credentials:
   - Set up AWS CLI or environment variables
   - Ensure access to AWS Bedrock service
   - Set `AWS_DEFAULT_REGION` environment variable

3. Run the application:
```bash
# Option 1: Using Poetry
poetry run python dueling_quibblers.py

# Option 2: Activate virtual environment first
poetry shell
python dueling_quibblers.py

# Option 3: Using the installed script (after poetry install)
dueling-quibblers
```

## Usage

1. Enter the debate topic when prompted
2. Enter the first debater character (e.g., "Harry Potter", "Phoenix Wright")
3. Enter the second debater character
4. Watch as the characters debate with 3 rounds each!
5. Characters are randomly assigned affirmative/negative positions

## Example

```
Topic: Should magic be taught in schools?
Debater 1: Harry Potter
Debater 2: Phoenix Wright

[Debate begins with 3 rounds each...]
 