#!/usr/bin/env python3
"""
Dueling Quibblers - A CLI app for fantasy character debates using LangGraph and Ollama
"""
import json
import operator
import os
import random
from typing import Annotated, Literal, Optional, TypedDict, Union

from langchain.schema import HumanMessage
from langchain_ollama.llms import OllamaLLM
from langgraph.graph import END, StateGraph
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DEBATE_NUM_ROUNDS = json.loads(os.environ.get("DEBATE_NUM_ROUNDS", "3"))
console = Console()  # Initialize Rich console for beautiful output


class DebateState(TypedDict):
    """State for the debate conversation"""

    topic: str
    debater1: str
    debater2: str
    debater1_position: Literal["affirmative", "negative"]
    debater2_position: Literal["affirmative", "negative"]
    current_debater: Optional[str]  # for streamlit
    current_position: Optional[Literal["affirmative", "negative"]]  # for streamlit
    judge: str
    round_number: int
    debate_history: Annotated[list[dict[str, Union[str, int]]], operator.add]
    judge_verdict: str  # for streamlit


class DebateManager:
    """Manages the debate flow and character interactions"""

    def __init__(self):
        self.llm = llm = OllamaLLM(model="llama3.1:8b")  ### can change
        self.character_personalities = {  # Character personality templates
            "harry potter": {
                "style": "Brave, determined, speaks with conviction about justice and doing what's right. Uses phrases like 'I believe', 'We must', 'It's our duty'.",
                "tone": "Passionate and earnest, with a sense of moral responsibility",
            },
            "phoenix wright": {
                "style": "Confident, witty, uses clever wordplay and dramatic flair. Speaks with theatrical gestures and dramatic pauses.",
                "tone": "Charismatic and theatrical, with a touch of mystery",
            },
            "gandalf": {
                "style": "Wise, philosophical, speaks with ancient wisdom and authority. Uses formal language and references to history and lore.",
                "tone": "Sage-like and authoritative, with deep knowledge",
            },
            "sherlock holmes": {
                "style": "Analytical, logical, presents arguments with deductive reasoning and evidence. Uses phrases like 'Elementary', 'The facts clearly indicate'.",
                "tone": "Precise and analytical, with sharp wit",
            },
            "wonder woman": {
                "style": "Strong, compassionate, speaks about truth, justice, and equality. Uses empowering language and references to ancient wisdom.",
                "tone": "Noble and inspiring, with warrior spirit",
            },
            "iron man": {
                "style": "Genius, sarcastic, uses humor and technology references. Speaks with confidence and occasional snark.",
                "tone": "Brilliant and witty, with technological insight",
            },
        }
        self.judge_personalities = {  # Judge personality templates
            "judge dredd": {
                "style": "Authoritarian, speaks with absolute authority and harsh judgment. Uses phrases like 'I am the law', 'Guilty as charged', 'Justice is swift'.",
                "tone": "Harsh and uncompromising, with zero tolerance for weakness",
            },
            "j.a.r.v.i.s.": {
                "style": "Polite, analytical, speaks with British formality and technological precision. Uses phrases like 'If I may', 'Analysis complete', 'I must respectfully disagree'.",
                "tone": "Courteous and precise, with sophisticated AI reasoning",
            },
            "spock": {
                "style": "Logical, emotionless, presents decisions based purely on facts and logic. Uses phrases like 'That is illogical', 'The facts indicate', 'Fascinating'.",
                "tone": "Completely rational and analytical, with Vulcan precision",
            },
            "brainiac": {
                "style": "Superior, condescending, speaks with intellectual arrogance and vast knowledge. Uses phrases like 'Your primitive arguments', 'My superior intellect', 'Obviously'.",
                "tone": "Intellectually superior and dismissive of lesser minds",
            },
            "lex luthor": {
                "style": "Cunning, manipulative, speaks with calculated intelligence and subtle threats. Uses phrases like 'How predictable', 'Your naivety is showing', 'I expected better'.",
                "tone": "Smooth and calculating, with underlying menace",
            },
            "rick sanchez": {
                "style": "Cynical, brilliant, speaks with scientific genius and existential nihilism. Uses phrases like 'Wubba lubba dub dub', 'Your arguments are garbage', 'Science, bitch'.",
                "tone": "Brilliant but cynical, with scientific arrogance",
            },
            "the doctor": {
                "style": "Eccentric, wise, speaks with ancient knowledge and quirky charm. Uses phrases like 'Brilliant', 'Oh, that's clever', 'Time and space'.",
                "tone": "Warm and eccentric, with centuries of wisdom",
            },
            "sheldon cooper": {
                "style": "Pedantic, socially awkward, presents arguments with scientific precision and social obliviousness. Uses phrases like 'Bazinga', 'That's incorrect', 'I have a PhD'.",
                "tone": "Intellectually superior but socially awkward",
            },
            "abed nadir": {
                "style": "Meta-aware, pop-culture obsessed, speaks with TV show references and meta-commentary. Uses phrases like 'This is like that episode of', 'Plot twist', 'Character development'.",
                "tone": "Self-aware and pop-culture savvy, with meta-humor",
            },
        }

    def initialize_debate(self, state: DebateState) -> DebateState:
        console.print(
            Panel(
                "[bold blue]:performing_arts: Welcome to Dueling Quibblers! :performing_arts:[/bold blue]\n\n"
                "Two fantasy characters will engage in a spirited debate.\n"
                f"Each will present {DEBATE_NUM_ROUNDS} arguments in character.",
                title="Welcome",
                border_style="blue",
            )
        )
        topic = Prompt.ask("\n[bold]What is the debate topic?[/bold]")
        debater1 = Prompt.ask(
            "\n[bold]Enter the first debater character[/bold] (e.g., Harry Potter, Phoenix Wright)"
        )
        debater2 = Prompt.ask(
            "\n[bold]Enter the second debater character[/bold] (e.g., Gandalf, Sherlock Holmes)"
        )
        positions = ["affirmative", "negative"]
        random.shuffle(positions)
        judge_list = [
            "Judge Dredd",
            "J.A.R.V.I.S.",
            "Spock",
            "Brainiac",
            "Lex Luthor",
            "The Doctor",
            "Sheldon Cooper",
            "Rick Sanchez",
            "Abed Nadir",
        ]
        judge = random.choice(judge_list)
        return {
            "topic": topic,
            "debater1": debater1,
            "debater2": debater2,
            "debater1_position": positions[0],
            "debater2_position": positions[1],
            "judge": judge,
            "round_number": 1,
            "debate_history": [],
        }

    def start_debate(self, state: DebateState) -> DebateState:
        console.print(
            Panel(
                f"[bold blue]:performing_arts: DUELING QUIBBLERS :performing_arts:[/bold blue]\n\n"
                f"[bold]Topic:[/bold] {state['topic']}\n"
                f"[bold]Debater 1:[/bold] {state['debater1']} ({state['debater1_position']})\n"
                f"[bold]Debater 2:[/bold] {state['debater2']} ({state['debater2_position']})\n\n"
                f"[yellow]Let the debate begin![/yellow]",
                title="Debate Setup",
                border_style="blue",
            )
        )
        return {
            "round_number": state.get("round_number", 1),  # for streamlit
            "debate_history": state.get(
                "debate_history", []
            ),  # initialize attribute if not already
        }

    def get_character_personality(self, character_name: str) -> dict[str, str]:
        """Get personality template for a character, with fallback for unknown characters"""
        for known_char, personality in self.character_personalities.items():
            if character_name.lower() in known_char:
                return personality
        return {  # Fallback personality for unknown characters
            "style": "Unique and distinctive, speaks with their own special flair and mannerisms.",
            "tone": "Distinctive and memorable, with their own personality",
        }

    def create_debate_prompt(self, state: DebateState, speaker: str) -> str:
        """Create a debate prompt for the current speaker"""
        is_debater1 = (
            speaker == state["debater1"]
        )  # Determine if speaker is debater1 or debater2
        speaker_position = (  # Get positions and opponent info
            state["debater1_position"] if is_debater1 else state["debater2_position"]
        )
        opponent = state["debater2"] if is_debater1 else state["debater1"]
        opponent_position = (
            state["debater2_position"] if is_debater1 else state["debater1_position"]
        )
        personality = self.get_character_personality(character_name=speaker)

        history_context = ""  # Build context from debate history
        if state["debate_history"]:
            history_context = "\n\nPrevious arguments:\n"
            for entry in state["debate_history"]:
                history_context += f"- {entry['speaker']}: {entry['argument']}\n"
        prompt = f"""You are {speaker} participating in a formal debate.

Topic: {state["topic"]}
Your position: {speaker_position}
Opponent: {opponent} (taking the {opponent_position} position)
Current round: {state["round_number"]} of {DEBATE_NUM_ROUNDS}

Your speaking style: {personality['style']}
Your tone: {personality['tone']}

{history_context}

As {speaker}, present your argument for round {state["round_number"]}. 
- If this is your first argument, present your main case
- If this is a later round, address your opponent's previous arguments and strengthen your position
- Stay in character as {speaker} throughout
- Be engaging and entertaining while making logical points
- Keep your response to 2-3 paragraphs maximum

Speak now as {speaker}:"""
        return prompt

    def generate_debate_response(self, state: DebateState, speaker: str) -> str:
        """Generate a debate response for the current speaker"""
        prompt = self.create_debate_prompt(state=state, speaker=speaker)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response

    def debater1_speaks(self, state: DebateState) -> DebateState:
        """Debater 1 presents their argument"""
        console.print(
            f"\n[bold cyan]:microphone: {state['debater1']} speaks (Round {state['round_number']}):[/bold cyan]\n"
        )
        response = self.generate_debate_response(state=state, speaker=state["debater1"])
        console.print(
            Panel(
                response,
                title=f"{state['debater1']}",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        return {
            "current_debater": state["debater1"],  # for streamlit
            "current_position": state["debater1_position"],  # for streamlit
            "debate_history": [
                {
                    "speaker": state["debater1"],
                    "argument": response,
                    "round": state["round_number"],
                }
            ],
        }

    def debater2_speaks(self, state: DebateState) -> DebateState:
        """Debater 2 presents their argument"""
        console.print(
            f"\n[bold magenta]:microphone: {state['debater2']} speaks (Round {state['round_number']}):[/bold magenta]\n"
        )
        response = self.generate_debate_response(state=state, speaker=state["debater2"])
        console.print(
            Panel(
                response,
                title=f"{state['debater2']}",
                border_style="magenta",
                padding=(1, 2),
            )
        )
        return {
            "current_debater": state["debater2"],  # for streamlit
            "current_position": state["debater2_position"],  # for streamlit
            "debate_history": [
                {
                    "speaker": state["debater2"],
                    "argument": response,
                    "round": state["round_number"],
                }
            ],
        }

    def advance_round(self, state: DebateState) -> DebateState:
        """Advance to the next round or end debate"""
        round_number = state["round_number"] + 1
        console.print(
            f"\n[bold yellow]:arrows_counterclockwise: Round {round_number} begins![/bold yellow]\n"
        )
        return {
            "current_debater": None,  # not super important
            "current_position": None,  # not super important
            "round_number": round_number,
        }

    def end_of_arguments(self, state: DebateState) -> DebateState:
        """End the debate"""
        console.print(
            Panel(
                f"[bold green]:checkered_flag: Debate concluded![/bold green]\n\n"
                f"Thank you to our debaters:\n"
                f"• {state['debater1']} ({state['debater1_position']})\n"
                f"• {state['debater2']} ({state['debater2_position']})\n\n"
                f"[italic]Now we await the judge's verdict...[/italic]",
                title="Debate Complete",
                border_style="green",
            )
        )
        return {"current_debater": None}  # not super important

    def get_judge_personality(self, judge_name: str) -> dict[str, str]:
        """Get personality template for a judge, with fallback for unknown judges"""
        for known_judge, personality in self.judge_personalities.items():
            if judge_name.lower() in known_judge:
                return personality
        return {  # Fallback personality for unknown judges
            "style": "Wise and impartial, speaks with judicial authority and fairness.",
            "tone": "Authoritative and fair, with balanced judgment",
        }

    def create_judgment_prompt(self, state: DebateState) -> str:
        """Create a prompt for the judge's verdict"""
        personality = self.get_judge_personality(judge_name=state["judge"])
        arguments_summary = ""  # Build summary of all argument
        for entry in state["debate_history"]:
            arguments_summary += f"\n{entry['speaker']} (Round {entry['round']}): {entry['argument'][:200]}...\n"
        prompt = f"""You are {state["judge"]}, presiding as judge over this debate.

Topic: {state["topic"]}
Debater 1: {state["debater1"]} (taking the {state["debater1_position"]} position)
Debater 2: {state["debater2"]} (taking the {state["debater2_position"]} position)

Your speaking style: {personality['style']}
Your tone: {personality['tone']}

All arguments presented:{arguments_summary}

As {state["judge"]}, you must now deliver your verdict. You should:
1. Announce which debater has won (either {state["debater1"]} or {state["debater2"]})
2. Explain your reasoning for the decision
3. Comment on the quality of arguments from both sides
4. Stay completely in character as {state["judge"]} throughout
5. Be entertaining and memorable in your delivery
6. Keep your verdict to 3-4 paragraphs maximum

Deliver your judgment as {state["judge"]}:"""
        return prompt

    def generate_judgment(self, state: DebateState) -> str:
        """Generate the judge's verdict"""
        prompt = self.create_judgment_prompt(state=state)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response

    def judge_verdict(self, state: DebateState) -> DebateState:
        """Judge delivers the verdict"""
        console.print(
            f"\n[bold yellow]:scales: {state['judge']} delivers the verdict:[/bold yellow]\n"
        )
        verdict = self.generate_judgment(state=state)
        console.print(
            Panel(
                verdict,
                title=f":scales: {state['judge']}'s Verdict",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        console.print(
            Panel(
                f"[bold yellow]:trophy: The debate has been judged! :trophy:[/bold yellow]\n\n"
                f"[italic]Thank you for watching Dueling Quibblers![/italic]",
                title="Finale",
                border_style="yellow",
            )
        )
        return {"judge_verdict": verdict}  # for streamlit

    def create_debate_graph(self, debate_initialized=False) -> StateGraph:
        """Create the LangGraph for the debate flow"""
        workflow = StateGraph(DebateState)

        workflow.add_node("start_debate", self.start_debate)
        workflow.add_node("debater1_speaks", self.debater1_speaks)
        workflow.add_node("debater2_speaks", self.debater2_speaks)
        workflow.add_node("advance_round", self.advance_round)
        workflow.add_node("end_of_arguments", self.end_of_arguments)
        workflow.add_node("judge_verdict", self.judge_verdict)

        if not debate_initialized:
            workflow.add_node("initialize_debate", self.initialize_debate)
            workflow.set_entry_point("initialize_debate")
            workflow.add_edge("initialize_debate", "start_debate")
        else:
            workflow.set_entry_point("start_debate")

        workflow.add_edge("start_debate", "debater1_speaks")
        workflow.add_edge("debater1_speaks", "debater2_speaks")
        workflow.add_conditional_edges(
            "debater2_speaks",
            lambda state: (
                "advance_round"
                if state["round_number"] < DEBATE_NUM_ROUNDS
                else "end_of_arguments"
            ),
            {"advance_round": "advance_round", "end_of_arguments": "end_of_arguments"},
        )
        workflow.add_edge("advance_round", "debater1_speaks")
        workflow.add_edge("end_of_arguments", "judge_verdict")
        workflow.add_edge("judge_verdict", END)
        return workflow.compile()


def main():
    """Main application entry point"""
    try:
        debate_manager = DebateManager()
        debate_graph = debate_manager.create_debate_graph(debate_initialized=False)
        debate_graph.invoke({})
    except KeyboardInterrupt:
        console.print("\n[yellow]Debate interrupted by user. Goodbye![/yellow]")


if __name__ == "__main__":
    main()
