import streamlit as st
from utils import get_character_image, get_debate_progress

st.set_page_config(page_title="Dueling Quibblers", layout="centered")
st.title("⚔️ Dueling Quibblers 🏆")

st.markdown("""
Welcome to **Dueling Quibblers**! Enter a debate topic and pick two fictional characters to battle it out. The judge (default: Sheldon Cooper) will decide the winner after 3 rounds!
""")

# --- User Inputs ---
topic = st.text_input("Debate Topic", "Should magic be regulated?")
debater1 = st.text_input("Debater 1 (e.g., Harry Potter)", "Harry Potter")
debater2 = st.text_input("Debater 2 (e.g., Gandalf)", "Gandalf")
judge = st.text_input("Judge (default: Sheldon Cooper)", "Sheldon Cooper")

# --- Fetch Images ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(debater1)
    img1, err1 = get_character_image(debater1)
    st.image(img1, width=150)
    if err1:
        st.warning(err1)
with col2:
    st.subheader("VS")
with col3:
    st.subheader(debater2)
    img2, err2 = get_character_image(debater2)
    st.image(img2, width=150)
    if err2:
        st.warning(err2)
st.markdown(f"**Judge:** {judge}")
imgj, errj = get_character_image(judge)
st.image(imgj, width=100)
if errj:
    st.warning(errj)

# --- Debate Rounds ---
if st.button("Start Debate!", type="primary"):
    with st.spinner("Generating debate arguments..."):
        debate_progress, winner, reason = get_debate_progress(topic, debater1, debater2, judge)
    
    # Display debate progress
    st.markdown("## 🎤 Debate Rounds")
    
    # Group by rounds
    rounds = {}
    for entry in debate_progress:
        round_num = entry["round"]
        if round_num not in rounds:
            rounds[round_num] = []
        rounds[round_num].append(entry)
    
    # Display each round
    for round_num in sorted(rounds.keys()):
        st.markdown(f"### Round {round_num}")
        
        for entry in rounds[round_num]:
            speaker = entry["speaker"]
            argument = entry["argument"]
            position = entry["position"]
            
            # Create a styled container for each speaker
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    if speaker == debater1:
                        st.markdown(f"**{speaker}** ({position})")
                        st.markdown("🎭")
                    else:
                        st.markdown(f"**{speaker}** ({position})")
                        st.markdown("🎭")
                
                with col2:
                    # Create an expandable section for the argument
                    with st.expander(f"View {speaker}'s argument", expanded=True):
                        st.markdown(argument)
        
        st.divider()
    
    # Display the verdict
    st.markdown("## ⚖️ Judge's Verdict")
    
    # Winner announcement
    st.success(f"🏆 **Winner: {winner}**")
    
    # Judge's reasoning
    with st.container():
        st.markdown("### Judge's Explanation")
        st.info(reason)
    
    # Final celebration
    st.balloons()
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit. Images via DuckDuckGo and Wikipedia.")
