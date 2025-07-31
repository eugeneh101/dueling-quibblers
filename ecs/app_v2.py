import json
import os
import random

import streamlit as st

from dueling_quibblers_v3 import DebateManager, console
from utils_v2 import get_character_image

DEBATE_NUM_ROUNDS = json.loads(os.environ.get("DEBATE_NUM_ROUNDS", "3"))
console.quiet = True  # deactivate rich, pretty-print to ECS/Cloudwatch logs

st.set_page_config(page_title="Dueling Quibblers", layout="centered")
st.title("⚔️ Dueling Quibblers 🏆")
st.markdown(
    "Welcome to **Dueling Quibblers**! Enter a debate topic and pick two "
    "fictional characters to battle it out. The characters will be randomly "
    'assigned for ("affirmative") or against ("negative") the motion. '
    f"The judge will decide the winner after {DEBATE_NUM_ROUNDS} rounds!"
)

# --- User Inputs ---
topic = st.text_input("Debate Topic", "Should magic be regulated?")
debater1 = st.text_input("Debater 1 (e.g., Harry Potter)", "Harry Potter")
debater2 = st.text_input("Debater 2 (e.g., Gandalf)", "Gandalf")
judge = st.text_input(
    'Judge (or type "random" to get a surprise judge!)', "Sheldon Cooper"
)
print(f"topic: {topic}", flush=True)  # flush for ECS task -> Cloudwatch logs
print(f"debater1: {debater1}", flush=True)  # flush for ECS task -> Cloudwatch logs
print(f"debater2: {debater2}", flush=True)  # flush for ECS task -> Cloudwatch logs
print(f"judge: {judge}", flush=True)  # flush for ECS task -> Cloudwatch logs

# --- Fetch Images ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(debater1)
    img1 = get_character_image(name=debater1)
    st.image(img1, width=150)
with col2:
    st.subheader("")
    st.image("pics/Street_Fighter_VS_logo.png", width=150)  # hard coded
with col3:
    st.subheader(debater2)
    img2 = get_character_image(name=debater2)
    st.image(img2, width=150)
_, col2, _ = st.columns(3)
with col2:
    st.html("<br>")
    st.subheader(f"**Judge:** {judge}")
    if judge.lower() == "random":
        st.image("pics/mystery_judge.jpg", width=150)  # hard coded
    else:
        imgj = get_character_image(name=judge)
        st.image(imgj, width=150)

# --- Run Debate ---
if st.button("Start Debate!", type="primary"):
    # creating langgraph graph and stream
    debate_manager = DebateManager()
    debate_graph = debate_manager.create_debate_graph(debate_initialized=True)
    positions = ["affirmative", "negative"]
    random.shuffle(positions)
    if judge.lower() == "random":
        judge = random.choice(list(debate_manager.judge_personalities.keys()))
    graph_stream = debate_graph.stream(
        input={
            "topic": topic,
            "debater1": debater1,
            "debater2": debater2,
            "debater1_position": positions[0],
            "debater2_position": positions[1],
            "judge": judge,
        },
        stream_mode="updates",
        # print_mode="updates",
    )

    with st.spinner("Generating debate arguments..."):
        st.markdown("## 🎤 Debate Rounds")
        for event in graph_stream:
            assert len(event) == 1, event
            node, state = event.popitem()
            if node in ("start_debate", "advance_round"):
                st.markdown(f"### Round {state['round_number']}")
            elif node in ("debater1_speaks", "debater2_speaks"):
                # Create a styled container for each speaker
                debater = state["current_debater"]
                position = state["current_position"]
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"**{debater}** ({position})")
                    with col2:
                        # Create an expandable section for the argument
                        with st.expander(f"View {debater}'s argument", expanded=True):
                            st.markdown(state["debate_history"][-1]["argument"])
                if debater == debater2:
                    st.divider()
            elif "end_of_arguments" == node:
                st.markdown("## ⚖️ Judge's Verdict")
            elif "judge_verdict" == node:
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"**Judge:** {judge.title()}")
                    with col2:
                        # Create an expandable section for the argument
                        with st.expander(f"View {debater}'s argument", expanded=True):
                            st.success(
                                f"🏆 **Winner: {state['judge_verdict'].debate_winner}**"
                            )
                            with st.container():
                                st.markdown("### Judge's Explanation")
                                st.info(
                                    state["judge_verdict"].debate_winner_explanation
                                )
            else:
                raise Exception("Unexpected event: {event}".format(event={node: state}))
    # Final celebration
    st.balloons()
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit. Images via DuckDuckGo")
