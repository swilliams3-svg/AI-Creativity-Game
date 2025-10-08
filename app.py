import streamlit as st
import random
import time
from openai import OpenAI

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🎲 AI Creativity Challenge", layout="centered")

st.title("🎲 AI Creativity Challenge")
st.markdown("Choose a game mode, get a creative challenge, and test your imagination against AI!")

# --------------------------
# OpenAI client
# --------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------
# Session State Setup
# --------------------------
defaults = {
    "prompt": None,
    "user_response": "",
    "ai_response": None,
    "score": {"Human": 0, "AI": 0},
    "round": 0,
    "difficulty": "Medium",
    "timer_end": None,
    "yes_and_story": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------------------
# Prompt Templates & Data
# --------------------------
prompt_templates = [
    "Invent a new holiday that combines {A} and {B}.",
    "Write a slogan for {A}.",
    "Describe what happens if {A} meets {B} in the future.",
    "Design a product for {A} that also solves a problem with {B}.",
    "Write a short story beginning with: '{A}'",
    "Imagine a world where {A} and {B} are everyday realities. What changes?"
]

concepts = [
    "robots", "bananas", "astronauts", "time travel", "umbrellas", "dragons",
    "dinosaurs", "TikTok", "AI", "pirates", "coffee", "self-driving cars"
]

constraints = [
    "must include a banana",
    "must rhyme",
    "must use only 10 words",
    "must be written as a haiku",
    "must mention cats",
    "must be set in space"
]

difficulty_guidance = {
    "Easy": "Write 1–2 sentences.",
    "Medium": "Write 3–4 sentences.",
    "Hard": "Write 5–6 sentences."
}

# --------------------------
# Sidebar: Mode + Difficulty
# --------------------------
st.sidebar.header("⚙️ Game Settings")
mode = st.sidebar.radio(
    "Select game mode:",
    ["Classic", "Yes, And…", "Constraint", "Mash-up"]
)
difficulty = st.sidebar.radio("Select difficulty:", ["Easy", "Medium", "Hard"],
                              index=["Easy", "Medium", "Hard"].index(st.session_state.difficulty))
st.session_state.difficulty = difficulty

# --------------------------
# Mode: Classic
# --------------------------
if mode == "Classic":
    if st.button("✨ Generate Creative Prompt"):
        template = random.choice(prompt_templates)
        filled = template.format(A=random.choice(concepts), B=random.choice(concepts))
        st.session_state.prompt = filled
        st.session_state.ai_response = None
        st.session_state.user_response = ""
        st.session_state.round += 1
        st.session_state.timer_end = time.time() + 120

    if st.session_state.prompt:
        st.subheader(f"📝 Round {st.session_state.round}: Classic Challenge")
        st.info(st.session_state.prompt)
        st.markdown(f"**Guidance:** {difficulty_guidance[st.session_state.difficulty]}")

        # Timer
        if st.session_state.timer_end:
            remaining = int(st.session_state.timer_end - time.time())
            if remaining > 0:
                st.warning(f"⏱️ Time left: {remaining} seconds")
            else:
                st.error("⏰ Time’s up!")

        # Human input
        user_response = st.text_area("✍️ Your Idea:", height=150, value=st.session_state.user_response)
        st.session_state.user_response = user_response

        # AI response
        if st.button("🤖 See AI’s Idea"):
            with st.spinner("AI is thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": st.session_state.prompt}]
                )
                st.session_state.ai_response = response.choices[0].message.content

        # Showdown + Voting
        if st.session_state.ai_response:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 👤 Your Idea")
                st.write(st.session_state.user_response or "*You didn’t write anything yet!*")
            with col2:
                st.markdown("### 🤖 AI’s Idea")
                st.write(st.session_state.ai_response)

            st.subheader("🗳️ Vote")
            if st.button("👍 Human Wins"):
                st.session_state.score["Human"] += 1
            if st.button("🤖 AI Wins"):
                st.session_state.score["AI"] += 1
            st.write(f"**Human:** {st.session_state.score['Human']} | **AI:** {st.session_state.score['AI']}")

# --------------------------
# Mode: Yes, And…
# --------------------------
elif mode == "Yes, And…":
    st.subheader("🎭 Yes, And… Mode (Collaborative Improv)")
    st.markdown("You start with a sentence. The AI will continue. Then you add another, and so on!")

    if st.button("Start New Story"):
        st.session_state.yes_and_story = ""
        st.session_state.round += 1

    human_input = st.text_input("✍️ Your line:")
    if st.button("Add My Line"):
        st.session_state.yes_and_story += f"👤 {human_input}\n"

        with st.spinner("AI continues..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Continue this story: {st.session_state.yes_and_story}"}]
            )
            ai_line = response.choices[0].message.content
            st.session_state.yes_and_story += f"🤖 {ai_line}\n"

    st.text_area("Story so far:", st.session_state.yes_and_story, height=300)

# --------------------------
# Mode: Constraint
# --------------------------
elif mode == "Constraint":
    if st.button("✨ Generate Constraint Challenge"):
        concept = random.choice(concepts)
        constraint = random.choice(constraints)
        st.session_state.prompt = f"Create something involving **{concept}** — but it {constraint}!"
        st.session_state.ai_response = None
        st.session_state.user_response = ""
        st.session_state.round += 1

    if st.session_state.prompt:
        st.subheader(f"📝 Round {st.session_state.round}: Constraint Mode")
        st.info(st.session_state.prompt)
        st.markdown(f"**Guidance:** {difficulty_guidance[st.session_state.difficulty]}")

        user_response = st.text_area("✍️ Your constrained idea:", height=150, value=st.session_state.user_response)
        st.session_state.user_response = user_response

        if st.button("🤖 See AI’s Constrained Idea"):
            with st.spinner("AI is thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": st.session_state.prompt}]
                )
                st.session_state.ai_response = response.choices[0].message.content

        if st.session_state.ai_response:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 👤 Your Idea")
                st.write(st.session_state.user_response or "*You didn’t write anything yet!*")
            with col2:
                st.markdown("### 🤖 AI’s Idea")
                st.write(st.session_state.ai_response)

            st.subheader("🗳️ Vote")
            if st.button("👍 Human Wins"):
                st.session_state.score["Human"] += 1
            if st.button("🤖 AI Wins"):
                st.session_state.score["AI"] += 1
            st.write(f"**Human:** {st.session_state.score['Human']} | **AI:** {st.session_state.score['AI']}")

# --------------------------
# Mode: Mash-up
# --------------------------
elif mode == "Mash-up":
    if st.button("✨ Generate Mash-up Challenge"):
        A, B = random.sample(concepts, 2)
        st.session_state.prompt = f"Blend **{A}** and **{B}** into a new invention, story, or ad."
        st.session_state.ai_response = None
        st.session_state.user_response = ""
        st.session_state.round += 1

    if st.session_state.prompt:
        st.subheader(f"📝 Round {st.session_state.round}: Mash-up Mode")
        st.info(st.session_state.prompt)
        st.markdown(f"**Guidance:** {difficulty_guidance[st.session_state.difficulty]}")

        user_response = st.text_area("✍️ Your mash-up idea:", height=150, value=st.session_state.user_response)
        st.session_state.user_response = user_response

        if st.button("🤖 See AI’s Mash-up Idea"):
            with st.spinner("AI is thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": st.session_state.prompt}]
                )
                st.session_state.ai_response = response.choices[0].message.content

        if st.session_state.ai_response:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 👤 Your Idea")
                st.write(st.session_state.user_response or "*You didn’t write anything yet!*")
            with col2:
                st.markdown("### 🤖 AI’s Idea")
                st.write(st.session_state.ai_response)

            st.subheader("🗳️ Vote")
            if st.button("👍 Human Wins"):
                st.session_state.score["Human"] += 1
            if st.button("🤖 AI Wins"):
                st.session_state.score["AI"] += 1
            st.write(f"**Human:** {st.session_state.score['Human']} | **AI:** {st.session_state.score['AI']}")

