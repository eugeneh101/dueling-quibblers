#!/usr/bin/env python3
"""
Dueling Quibblers - A CLI app for fantasy character debates using LangGraph and AWS Bedrock
"""

import os
import random
from dataclasses import dataclass, field

import typer
from langchain.schema import HumanMessage
from langchain_aws import ChatBedrock
from langgraph.graph import END, StateGraph
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Initialize Rich console for beautiful output
console = Console()


@dataclass
class DebateState:
    """State for the debate conversation"""

    topic: str
    debater1: str
    debater2: str
    debater1_position: str  # "affirmative" or "negative"
    debater2_position: str
    judge: str = None
    round_number: int = 1
    debate_history: list[dict[str, str]] = field(default_factory=list)
    current_speaker: str = None


class DebateManager:
    """Manages the debate flow and character interactions"""

    def __init__(self):
        # Initialize AWS Bedrock client
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name="us-east-1",
        )

        # Character personality templates
        self.character_personalities = {
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

        # Judge personality templates
        self.judge_personalities = {
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

    def get_character_personality(self, character_name: str) -> dict[str, str]:
        """Get personality template for a character, with fallback for unknown characters"""
        character_lower = character_name.lower()

        # Check for exact matches first
        for known_char, personality in self.character_personalities.items():
            if character_lower in known_char:
                return personality

        # Fallback personality for unknown characters
        return {
            "style": "Unique and distinctive, speaks with their own special flair and mannerisms.",
            "tone": "Distinctive and memorable, with their own personality",
        }

    def get_judge_personality(self, judge_name: str) -> dict[str, str]:
        """Get personality template for a judge, with fallback for unknown judges"""
        judge_lower = judge_name.lower()

        # Check for exact matches first
        for known_judge, personality in self.judge_personalities.items():
            if judge_lower in known_judge:
                return personality

        # Fallback personality for unknown judges
        return {
            "style": "Wise and impartial, speaks with judicial authority and fairness.",
            "tone": "Authoritative and fair, with balanced judgment",
        }

    def create_debate_prompt(self, state: DebateState, speaker: str) -> str:
        """Create a debate prompt for the current speaker"""
        # Determine if speaker is debater1 or debater2
        is_debater1 = speaker == state.debater1

        # Get positions and opponent info
        speaker_position = (
            state.debater1_position if is_debater1 else state.debater2_position
        )
        opponent = state.debater2 if is_debater1 else state.debater1
        opponent_position = (
            state.debater2_position if is_debater1 else state.debater1_position
        )

        personality = self.get_character_personality(speaker)

        # Build context from debate history
        history_context = ""
        if state.debate_history:
            history_context = "\n\nPrevious arguments:\n"
            for entry in state.debate_history:
                history_context += f"- {entry['speaker']}: {entry['argument']}\n"

        prompt = f"""You are {speaker} participating in a formal debate.

Topic: {state.topic}
Your position: {speaker_position}
Opponent: {opponent} (taking the {opponent_position} position)
Current round: {state.round_number} of 3

Your speaking style: {personality['style']}
Your tone: {personality['tone']}

{history_context}

As {speaker}, present your argument for round {state.round_number}. 
- If this is your first argument, present your main case
- If this is a later round, address your opponent's previous arguments and strengthen your position
- Stay in character as {speaker} throughout
- Be engaging and entertaining while making logical points
- Keep your response to 2-3 paragraphs maximum

Speak now as {speaker}:"""

        return prompt

    def generate_debate_response(self, state: DebateState, speaker: str) -> str:
        """Generate a debate response for the current speaker"""
        prompt = self.create_debate_prompt(state, speaker)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content

    def create_judgment_prompt(self, state: DebateState) -> str:
        """Create a prompt for the judge's verdict"""
        personality = self.get_judge_personality(state.judge)

        # Build summary of all arguments
        arguments_summary = ""
        for entry in state.debate_history:
            arguments_summary += f"\n{entry['speaker']} (Round {entry['round']}): {entry['argument'][:200]}...\n"

        prompt = f"""You are {state.judge}, presiding as judge over this debate.

Topic: {state.topic}
Debater 1: {state.debater1} (taking the {state.debater1_position} position)
Debater 2: {state.debater2} (taking the {state.debater2_position} position)

Your speaking style: {personality['style']}
Your tone: {personality['tone']}

All arguments presented:{arguments_summary}

As {state.judge}, you must now deliver your verdict. You should:
1. Announce which debater has won (either {state.debater1} or {state.debater2})
2. Explain your reasoning for the decision
3. Comment on the quality of arguments from both sides
4. Stay completely in character as {state.judge} throughout
5. Be entertaining and memorable in your delivery
6. Keep your verdict to 3-4 paragraphs maximum

Deliver your judgment as {state.judge}:"""

        return prompt

    def generate_judgment(self, state: DebateState) -> str:
        """Generate the judge's verdict"""
        prompt = self.create_judgment_prompt(state)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content

    def create_debate_graph(self) -> StateGraph:
        """Create the LangGraph for the debate flow"""

        workflow = StateGraph(DebateState)

        # Define the debate nodes
        def start_debate(state: DebateState) -> DebateState:
            """Initialize the debate"""
            console.print(
                Panel(
                    f"[bold blue]:performing_arts: DUELING QUIBBLERS :performing_arts:[/bold blue]\n\n"
                    f"[bold]Topic:[/bold] {state.topic}\n"
                    f"[bold]Debater 1:[/bold] {state.debater1} ({state.debater1_position})\n"
                    f"[bold]Debater 2:[/bold] {state.debater2} ({state.debater2_position})\n\n"
                    f"[yellow]Let the debate begin![/yellow]",
                    title="Debate Setup",
                    border_style="blue",
                )
            )
            return state

        def debater1_speaks(state: DebateState) -> DebateState:
            """Debater 1 presents their argument"""
            console.print(
                f"\n[bold cyan]:microphone: {state.debater1} speaks (Round {state.round_number}):[/bold cyan]\n"
            )

            response = self.generate_debate_response(state, state.debater1)

            # Display the response
            console.print(
                Panel(
                    response,
                    title=f"{state.debater1}",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )

            # Update state
            state.debate_history.append(
                {
                    "speaker": state.debater1,
                    "argument": response,
                    "round": state.round_number,
                }
            )
            state.current_speaker = state.debater1

            return state

        def debater2_speaks(state: DebateState) -> DebateState:
            """Debater 2 presents their argument"""
            console.print(
                f"\n[bold magenta]:microphone: {state.debater2} speaks (Round {state.round_number}):[/bold magenta]\n"
            )

            response = self.generate_debate_response(state, state.debater2)

            # Display the response
            console.print(
                Panel(
                    response,
                    title=f"{state.debater2}",
                    border_style="magenta",
                    padding=(1, 2),
                )
            )

            # Update state
            state.debate_history.append(
                {
                    "speaker": state.debater2,
                    "argument": response,
                    "round": state.round_number,
                }
            )
            state.current_speaker = state.debater2

            return state

        def advance_round(state: DebateState) -> DebateState:
            """Advance to the next round or end debate"""
            if state.round_number < 3:
                state.round_number += 1
                console.print(
                    f"\n[bold yellow]:arrows_counterclockwise: Round {state.round_number} begins![/bold yellow]\n"
                )
            return state

        def end_debate(state: DebateState) -> DebateState:
            """End the debate"""
            console.print(
                Panel(
                    f"[bold green]:checkered_flag: Debate concluded![/bold green]\n\n"
                    f"Thank you to our debaters:\n"
                    f"• {state.debater1} ({state.debater1_position})\n"
                    f"• {state.debater2} ({state.debater2_position})\n\n"
                    f"[italic]Now we await the judge's verdict...[/italic]",
                    title="Debate Complete",
                    border_style="green",
                )
            )
            return state

        def judge_verdict(state: DebateState) -> DebateState:
            """Judge delivers the verdict"""
            console.print(
                f"\n[bold yellow]:scales: {state.judge} delivers the verdict:[/bold yellow]\n"
            )

            verdict = self.generate_judgment(state)

            # Display the verdict
            console.print(
                Panel(
                    verdict,
                    title=f":scales: {state.judge}'s Verdict",
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

            return state

        # Add nodes to the graph
        workflow.add_node("start", start_debate)
        workflow.add_node("debater1", debater1_speaks)
        workflow.add_node("debater2", debater2_speaks)
        workflow.add_node("advance_round", advance_round)
        workflow.add_node("end", end_debate)
        workflow.add_node("judge_verdict", judge_verdict)

        # Define the flow
        workflow.set_entry_point("start")

        # Start -> Debater 1
        workflow.add_edge("start", "debater1")

        # Debater 1 -> Debater 2
        workflow.add_edge("debater1", "debater2")

        # Debater 2 -> Check if round complete
        workflow.add_conditional_edges(
            "debater2",
            lambda state: "advance_round" if state.round_number < 3 else "end",
            {"advance_round": "advance_round", "end": "end"},
        )

        # Advance round -> Debater 1 (for next round)
        workflow.add_edge("advance_round", "debater1")

        # End -> Judge Verdict
        workflow.add_edge("end", "judge_verdict")

        # Judge Verdict -> END
        workflow.add_edge("judge_verdict", END)

        return workflow.compile()


def get_user_input() -> tuple[str, str, str]:
    """Get debate setup from user"""
    console.print(
        Panel(
            "[bold blue]:performing_arts: Welcome to Dueling Quibblers! :performing_arts:[/bold blue]\n\n"
            "Two fantasy characters will engage in a spirited debate.\n"
            "Each will present 3 arguments in character.",
            title="Welcome",
            border_style="blue",
        )
    )

    # Get debate topic
    topic = Prompt.ask("\n[bold]What is the debate topic?[/bold]")

    # Get first debater
    debater1 = Prompt.ask(
        "\n[bold]Enter the first debater character[/bold] (e.g., Harry Potter, Phoenix Wright)"
    )

    # Get second debater
    debater2 = Prompt.ask(
        "\n[bold]Enter the second debater character[/bold] (e.g., Gandalf, Sherlock Holmes)"
    )

    return topic, debater1, debater2


def assign_positions() -> tuple[str, str]:
    """Randomly assign affirmative and negative positions"""
    positions = ["affirmative", "negative"]
    random.shuffle(positions)
    return positions[0], positions[1]


def assign_judge() -> str:
    """Randomly assign a judge from the list"""
    judges = [
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
    return random.choice(judges)


def main():
    """Main application entry point"""
    try:
        # Get user input
        topic, debater1, debater2 = get_user_input()

        # Assign positions and judge randomly
        position1, position2 = assign_positions()
        judge = assign_judge()

        # Create debate state
        state = DebateState(
            topic=topic,
            debater1=debater1,
            debater2=debater2,
            debater1_position=position1,
            debater2_position=position2,
            judge=judge,
        )

        # Create and run debate
        debate_manager = DebateManager()
        debate_graph = debate_manager.create_debate_graph()

        # Execute the debate
        debate_graph.invoke(state)

    except KeyboardInterrupt:
        console.print("\n[yellow]Debate interrupted by user. Goodbye![/yellow]")


if __name__ == "__main__":
    typer.run(main)
