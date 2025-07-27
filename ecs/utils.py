import requests
import streamlit as st
from ddgs import DDGS

# Import from local dueling_quibblers_v3.py since we're in the same repo
from dueling_quibblers_v3 import run_debate_streamlit


@st.cache_data(show_spinner=False)
def get_character_image(name: str) -> tuple[str, str | None]:
    queries = [
        f'"{name}" movie still portrait',
        f'"{name}" headshot',
        f'"{name}" character close-up',
        f'site:static.wikia.nocookie.net "{name}"',
    ]
    bad = {"logo", "symbol", "poster", "banner", "wallpaper", "funko"}

    for q in queries:
        try:
            # Pass *q* as the FIRST positional argument
            for hit in DDGS().images(
                q,
                region="us-en",
                safesearch="moderate",
                size="Large",
                type_image="photo",
                max_results=20,
            ):
                url = hit["image"]
                if any(tok in url.lower() for tok in bad) or hit.get("width", 0) < 400:
                    continue
                return url, None
        except Exception as e:
            st.warning(f"DDGS failed on '{q}': {e}")

    # --- Wikipedia fallback ---
    api = (
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '%20')}"
    )
    try:
        img = requests.get(api, timeout=5).json().get("thumbnail", {}).get("source")
        if img:
            return img, "DuckDuckGo gave no suitable photo; used Wikipedia."
    except Exception:
        pass

    return (
        f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
        "Showing placeholder avatar.",
    )


def get_debate_progress(
    topic: str, debater1: str, debater2: str, judge: str
) -> tuple[list, str, str]:
    """
    Get detailed debate progress for Streamlit display.
    Returns (debate_progress, winner, reason):
      - debate_progress: list of dicts with round info, speaker, and arguments
      - winner: name of the winning debater
      - reason: judge's explanation
    """
    debate_progress, _, winner, reason = run_debate_streamlit(
        topic=topic,
        debater1=debater1,
        debater2=debater2,
        judge=judge,
        verbose=True,  # hard coded
    )
    return debate_progress, winner, reason


def run_debate(topic: str, debater1: str, debater2: str) -> list[tuple[str, str]]:
    """
    Run a 3-round debate using advanced logic. Returns a list of (debater1_speech, debater2_speech) tuples.
    """
    debate_progress, debate_log, _, _ = run_debate_streamlit(
        topic=topic,
        debater1=debater1,
        debater2=debater2,
        judge="Sheldon Cooper",  # take a look
        verbose=False,  # hard coded
    )
    return debate_log


def judge_debate(
    debate_log: list[tuple[str, str]], debater1: str, debater2: str, judge: str
) -> tuple[str, str]:
    """
    Judge the debate and return (winner, reason) using advanced logic.
    """
    # Re-run the debate to get the winner and reason (since state is not preserved)
    _, _, winner, reason = run_debate_streamlit(
        topic="",
        debater1=debater1,
        debater2=debater2,
        judge=judge,
        verbose=False,  # hard coded
    )
    return winner, reason


