import streamlit as st
import random
from openai import OpenAI

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="AI Creativity Challenge", layout="centered")

st.title("AI Creativity Challenge")
st.markdown("""
Welcome to the **AI Creativity Challenge** 
- You'll be given a **creative prompt**.  
- Follow the guidance on how much to write.  
- Focus on **imagination, originality, and fun** — not perfection.  
- Then click *See AI’s Idea* to compare with the AI.  
""")

# --------------------------
# OpenAI client
# --------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------
# Session State Setup
# --------------------------
if "prompt" not in st.session_state:
    st.session_state.prompt = None
if "user_response" not in st.session_state:
    st.session_state.user_response = ""
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None
if "score" not in st.session_state:
    st.session_state.score = {"Human": 0, "AI": 0}

# --------------------------
# Prompt Templates
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

# --------------------------
# Instructions per prompt type
# --------------------------
instructions = {
    "holiday": "**Guidance**: Write at least 3 sentences. Explain what happens, who celebrates, and why it’s unique.",
    "slogan": "**Guidance**: Keep it short and punchy — 1 catchy line is enough!",
    "story": "**Guidance**: Write 5–6 sentences. Be creative and surprising!",
    "product": "**Guidance**: Write at least 3 sentences. Explain what it is, how it works, and why people need it.",
    "imagine": "**Guidance**: Write 3–4 sentences describing how life would change.",
    "default": "**Guidance**: Aim for 3–5 sentences with creative details."
}

# --------------------------
# Generate Prompt
# --------------------------
if st.button("Generate Creative Prompt"):
    template = random.choice(prompt_templates)
    filled = template.format(
        A=random.choice(concepts),
        B=random.choice(concepts)
    )
    st.session_state.prompt = filled
    st.session_state.ai_response = None
    st.session_state.user_response = ""

if st.session_state.prompt:
    st.subheader("Your Challenge")
    st.info(st.session_state.prompt)

    # Show matching guidance
    prompt_lower = st.session_state.prompt.lower()
    if "holiday" in prompt_lower:
        st.markdown(instructions["holiday"])
    elif "slogan" in prompt_lower:
        st.markdown(instructions["slogan"])
    elif "story" in prompt_lower:
        st.markdown(instructions["story"])
    elif "product" in prompt_lower:
        st.markdown(instructions["product"])
    elif "imagine" in prompt_lower:
        st.markdown(instructions["imagine"])
    else:
        st.markdown(instructions["default"])

    # --------------------------
    # Player Input
    # --------------------------
    user_response = st.text_area("Your Idea:", height=150, value=st.session_state.user_response)
    st.session_state.user_response = user_response

    # --------------------------
    # AI Response
    # --------------------------
    if st.button("See AI’s Idea"):
        with st.spinner("AI is thinking..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": st.session_state.prompt}]
            )
            ai_text = response.choices[0].message.content
            st.session_state.ai_response = ai_text

    # --------------------------
    # Results Display + Voting
    # --------------------------
    if st.session_state.ai_response:
        st.subheader("⚡ The Showdown")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Your Idea")
            st.write(st.session_state.user_response if st.session_state.user_response else "*You didn’t write anything yet!*")

        with col2:
            st.markdown("### AI’s Idea")
            st.write(st.session_state.ai_response)

        st.markdown("---")
        st.subheader("Vote: Who did it better?")

        col3, col4 = st.columns(2)
        with col3:
            if st.button("Human Wins"):
                st.session_state.score["Human"] += 1
        with col4:
            if st.button("AI Wins"):
                st.session_state.score["AI"] += 1

        # Show running score
        st.markdown("### 🏆 Scoreboard")
        st.write(f"**Human:** {st.session_state.score['Human']} | **AI:** {st.session_state.score['AI']}")

        if st.button("🔄 Reset Scoreboard"):
            st.session_state.score = {"Human": 0, "AI": 0}
