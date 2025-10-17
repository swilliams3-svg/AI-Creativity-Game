import streamlit as st
import random
import time
from openai import OpenAI

# --------------------------
# App Config
# --------------------------
st.set_page_config(page_title="🎲 AI Creativity Challenge", layout="centered")

# --------------------------
# Lightweight styling
# --------------------------
st.markdown("""
<style>
:root {
  --bg-card: #ffffff;
  --text-muted: #5f6c7b;
  --ring: rgba(0,0,0,0.06);
  --grad-1: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
  --grad-2: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%);
  --grad-3: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
  --grad-4: linear-gradient(135deg, #E56B6F 0%, #6D9DC5 100%);
}
.hero { padding: 1.25rem; border-radius: 1rem; background: var(--grad-4); color: #fff;
  box-shadow: 0 6px 24px rgba(0,0,0,0.16); margin-bottom: 1rem; }
.card { border-radius: 1rem; background: var(--bg-card); border: 1px solid var(--ring);
  padding: 1rem; margin: .5rem 0 1rem; box-shadow: 0 6px 16px rgba(0,0,0,0.06); }
.card h3 { margin: 0 0 .25rem 0; }
.card p { color: var(--text-muted); margin: .25rem 0 .75rem; }
.stButton>button { border:0; color:#fff; border-radius: 999px; padding:.6rem 1rem; font-weight:600;
  box-shadow:0 6px 16px rgba(0,0,0,0.12); transition: transform 80ms, box-shadow 80ms, filter 80ms;
  background-image: var(--grad-1); }
.stButton>button:hover { transform: translateY(-1px); filter: brightness(1.05); }
.btn-alt .stButton>button { background-image: var(--grad-2); }
.btn-alt-2 .stButton>button { background-image: var(--grad-3); }
.tip { color: var(--text-muted); font-size: .95rem; }
.small { color: var(--text-muted); font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

# --------------------------
# OpenAI client (expects OPENAI_API_KEY in Streamlit Secrets)
# --------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------
# Session State
# --------------------------
defaults = {
    "page": "intro",       # "intro" -> "home" -> "play"
    "mode": None,          # "Classic", "Yes, And…", "Constraint", "Mash-up"
    "prompt": None,
    "user_response": "",
    "ai_response": None,
    "score": {"Human": 0, "AI": 0},
    "round": 0,
    "difficulty": "Medium",
    "timer_total": 120,
    "timer_end": None,
    "yes_and_story": "",
    "skip_intro_next_time": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------------------
# Title & Hero  (show ONLY on intro/home)
# --------------------------
if st.session_state.get("page", "intro") in ["intro", "home"]:
    st.title("🎲 AI Creativity Challenge")
    st.markdown("""
    <div class="hero">
      <h2 style="margin:.25rem 0;">Unleash your imagination ✨</h2>
      <p style="margin:.25rem 0;">
        Pick a mode, write your idea, and compare or collaborate with AI.
        Start on the Introduction page to see how everything works.
      </p>
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# Live timer auto-refresh (updates every second while timer is active)
# --------------------------
try:
    from streamlit_autorefresh import st_autorefresh
    if (
        st.session_state.get("page") == "play"
        and st.session_state.get("timer_end")
        and time.time() < st.session_state["timer_end"]
    ):
        st_autorefresh(interval=1000, limit=None, key="live-timer")
except Exception:
    # If the package isn't installed, timer will still work but update on interaction.
    pass

# --------------------------
# Prompt building blocks
# --------------------------
prompt_templates = [
    # Inventions & Products
    "Invent a new holiday that combines {A} and {B}.",
    "Design a product for {A} that also solves a problem with {B}.",
    "Create a gadget that makes life easier for people who love {A} but struggle with {B}.",
    "Imagine a toy that fuses {A} with {B}.",
    "Design a futuristic vehicle powered by {A} and inspired by {B}.",
    "Create a food or drink that combines {A} and {B}.",

    # Ads & Marketing
    "Write a slogan for {A}.",
    "Create a social media campaign for {A} using {B}.",
    "Come up with a catchy jingle that includes both {A} and {B}.",
    "Write a movie trailer voiceover that sells a story about {A} and {B}.",

    # Stories & Characters
    "Describe what happens if {A} meets {B} in the future.",
    "Write a short story beginning with: '{A}'.",
    "Tell a fairy tale that includes both {A} and {B}.",
    "Imagine {A} as a superhero and {B} as their sidekick.",
    "What happens in a world where {A} secretly controls {B}?",

    # Worlds & What-ifs
    "Imagine a world where {A} and {B} are everyday realities. What changes?",
    "Describe a school subject that combines {A} and {B}.",
    "What would a city look like if it were built around {A} and {B}?",
    "Imagine a festival where {A} and {B} are celebrated together.",
    "Describe how the world would change if everyone suddenly valued {A} more than {B}.",

    # Weird Twists
    "Pitch a reality TV show starring {A} and {B}.",
    "Imagine a magical spell powered by {A} but cursed by {B}.",
    "If {A} could talk, what would it say to {B}?",
    "Write a newspaper headline about {A} colliding with {B}.",
    "Create a conspiracy theory linking {A} and {B}.",

    # Role-play
    "Pretend you are {A}, trying to convince people to love {B}.",
    "Write a diary entry from {A} about their adventure with {B}.",
    "Imagine a debate between {A} and {B} on live TV.",
]

concepts = [
    # Everyday
    "bananas", "umbrellas", "coffee", "backpacks", "mirrors", "shoes", "toothbrushes",
    "keys", "lamps", "sunglasses", "stairs", "beds", "refrigerators", "bicycles",
    # Food & Drink
    "pizza", "ice cream", "sushi", "tacos", "chocolate", "spaghetti", "smoothies",
    "tea", "burgers", "cheese", "doughnuts", "sandwiches", "oranges",
    # Animals & Myth
    "cats", "dogs", "parrots", "octopuses", "penguins", "whales", "bees", "cows",
    "dragons", "unicorns", "dinosaurs", "werewolves", "phoenixes", "mermaids",
    # People / Characters
    "pirates", "astronauts", "wizards", "robots", "ninjas", "vampires", "superheroes",
    "clowns", "detectives", "chefs", "pop stars", "zombies",
    # Places
    "space stations", "volcanoes", "haunted houses", "castles", "deserts", "jungles",
    "theme parks", "beaches", "libraries", "underwater cities", "floating islands",
    # Tech & Science
    "time travel", "AI", "holograms", "quantum computers", "self-driving cars",
    "virtual reality", "jetpacks", "lasers", "drones", "3D printers", "black holes",
    # Arts & Media
    "TikTok", "YouTube", "comic books", "video games", "paintings", "poetry",
    "musicals", "movies", "podcasts", "memes", "dance", "fashion shows",
]

constraints = [
    # Word / length limits
    "must use only 10 words",
    "must be exactly 3 sentences long",
    "must include at least one question",
    "must rhyme",
    "must be written backwards",
    "must only use words of 5 letters or less",
    # Style / genre
    "must be written as a haiku",
    "must be written as a rap verse",
    "must be in Shakespearean style",
    "must sound like a news headline",
    "must be written like a fairy tale",
    "must be an instruction manual",
    "must be in the style of a recipe",
    "must be a tweet (under 280 characters)",
    "must be written like a motivational poster",
    "must be a breaking news alert",
    "must sound like a love letter",
    # Characters / tone
    "must mention cats",
    "must include a banana",
    "must feature pirates",
    "must have a plot twist at the end",
    "must include dialogue between two characters",
    "must be funny",
    "must be scary",
    "must be inspirational",
    # Surreal twists
    "must be set in space",
    "must include a time machine",
    "must describe a dream",
    "must use only emojis",
    "must swap the roles of {A} and {B}",
]

difficulty_guidance = {
    "Easy": "Write 1–2 sentences.",
    "Medium": "Write 3–4 sentences.",
    "Hard": "Write 5–6 sentences."
}

# --------------------------
# Sidebar (global settings)
# --------------------------
st.sidebar.header("⚙️ Settings")
st.sidebar.write("You can change these anytime.")
st.session_state.difficulty = st.sidebar.radio(
    "Difficulty:", ["Easy", "Medium", "Hard"],
    index=["Easy", "Medium", "Hard"].index(st.session_state.difficulty)
)
st.session_state.timer_total = st.sidebar.slider(
    "⏱️ Timer (seconds, Classic mode)", 30, 300, st.session_state.timer_total, 10
)

# --------------------------
# Helpers
# --------------------------
def back_to_nav():
    st.divider()
    cols = st.columns(3)
    with cols[0]:
        if st.button("🏠 Home"):
            st.session_state.page = "home"
            st.session_state.mode = None
            st.session_state.prompt = None
            st.session_state.user_response = ""
            st.session_state.ai_response = None
            st.session_state.timer_end = None
    with cols[1]:
        if st.button("📖 Introduction"):
            st.session_state.page = "intro"
            st.session_state.mode = None
            st.session_state.prompt = None
            st.session_state.user_response = ""
            st.session_state.ai_response = None
            st.session_state.timer_end = None
    with cols[2]:
        if st.button("🔄 Reset Scoreboard"):
            st.session_state.score = {"Human": 0, "AI": 0}

def fmt_dynamic(text: str, A: str, B: str) -> str:
    return text.replace("{A}", A).replace("{B}", B)

def show_showdown_and_vote():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        st.markdown("### 👤 Your Idea")
        st.write(st.session_state.user_response or "*You didn’t write anything yet!*")
    with cols[1]:
        st.markdown("### 🤖 AI’s Idea")
        st.write(st.session_state.ai_response)
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🗳️ Vote")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("👍 Human Wins"):
            st.session_state.score["Human"] += 1
            st.balloons()
            st.success("Point for Human!")
    with c2:
        if st.button("🤖 AI Wins"):
            st.session_state.score["AI"] += 1
            st.snow()
            st.info("Point for AI!")
    st.write(f"**Human:** {st.session_state.score['Human']} | **AI:** {st.session_state.score['AI']}")

# --------------------------
# INTRODUCTION PAGE
# --------------------------
def render_intro():
    st.markdown("""
### 👋 Welcome
This is a playful space to practice **originality**, **imagination**, and **storycraft** with a little help from AI.

#### How it works
1) Pick a **mode**  
2) Get a **prompt** (and sometimes a constraint)  
3) **Write your idea** (follow the guidance for length/detail)  
4) In competitive modes, compare with the **AI’s idea** and **vote** 🗳️

#### Modes at a glance
- **🎮 Classic** — Head-to-head: Human vs AI with voting, timer & difficulty.  
- **🎭 Yes, And…** — Improv storytelling: you add a line, AI continues (no scoring).  
- **🔒 Constraint** — Same as Classic but with a twist (e.g., rhyme, haiku, emojis…).  
- **🌀 Mash-up** — Blend two random concepts into a single idea (with voting).

#### Difficulty & Timer
- **Easy**: 1–2 sentences • **Medium**: 3–4 • **Hard**: 5–6  
- Classic mode includes a countdown (change seconds in the sidebar).

#### Scoring
- **Classic, Constraint, Mash-up**: vote Human or AI each round → scoreboard updates.  
- **Yes, And…**: collaborative; **no scoring**.

> Tip: Have fun! Surprise yourself. It’s not about perfection — it’s about **play**.
""")
    st.checkbox("Skip this introduction next time", value=st.session_state.skip_intro_next_time,
                key="skip_intro_next_time", help="We'll take you straight to the Home screen on reload.")
    st.divider()
    if st.button("🚀 Go to Game Home"):
        st.session_state.page = "home"

# --------------------------
# HOME (mode chooser with descriptions)
# --------------------------
def render_home():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🎮 Classic Mode")
    st.write("""
Get a random creative prompt (holiday, slogan, product, story).  
Write your idea, then see the AI’s. **Vote** on who did it better.  
Includes **timer**, **difficulty**, **round counter**, and **scoreboard**.
""")
    if st.button("Start Classic ▶️"):
        st.session_state.mode = "Classic"
        st.session_state.page = "play"
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🎭 Yes, And… Mode (Improv)")
    st.write("""
You start a story with a line. The AI continues. You add another line… and so on!  
This mode is **collaborative** — no scoring, just playful storytelling.
""")
    if st.button("Start Yes, And… ▶️"):
        st.session_state.mode = "Yes, And…"
        st.session_state.page = "play"
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🔒 Constraint Mode")
    st.write("""
You’ll get a challenge **with a silly restriction** (rhyme, haiku, emojis, bananas…).  
Both you and the AI respond, then you can **vote**.
""")
    st.markdown('<div class="btn-alt">', unsafe_allow_html=True)
    if st.button("Start Constraint ▶️"):
        st.session_state.mode = "Constraint"
        st.session_state.page = "play"
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🌀 Mash-up Mode")
    st.write("""
Blend **two random concepts** into a new invention, ad, or story.  
Both you and the AI respond, then you can **vote**.
""")
    st.markdown('<div class="btn-alt-2">', unsafe_allow_html=True)
    if st.button("Start Mash-up ▶️"):
        st.session_state.mode = "Mash-up"
        st.session_state.page = "play"
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🏆 Scoreboard (this session)")
    st.write(f"**Human:** {st.session_state.score['Human']} | **AI:** {st.session_state.score['AI']}")
    if st.button("🔄 Reset Scoreboard"):
        st.session_state.score = {"Human": 0, "AI": 0}

# --------------------------
# Mode: Classic (with live timer + voting)
# --------------------------
def render_classic():
    back_to_nav()
    st.markdown("## 📝 Classic Challenge")

    if st.button("✨ Generate Creative Prompt"):
        template = random.choice(prompt_templates)
        A, B = random.sample(concepts, 2)
        st.session_state.prompt = template.format(A=A, B=B)
        st.session_state.ai_response = None
        st.session_state.user_response = ""
        st.session_state.round += 1
        st.session_state.timer_end = time.time() + st.session_state.timer_total

    if st.session_state.prompt:
        st.markdown(f"**Round:** {st.session_state.round}")
        st.info(st.session_state.prompt)
        st.markdown(f"**Guidance:** {difficulty_guidance[st.session_state.difficulty]}")

        # Live timer (progress + text). Auto-refreshed above.
        if st.session_state.timer_end:
            remaining = max(0, int(st.session_state.timer_end - time.time()))
            total = st.session_state.timer_total
            elapsed = min(total, total - remaining)
            st.progress(elapsed / total)
            st.warning(f"⏱️ Time left: {remaining} seconds" if remaining > 0 else "⏰ Time’s up!")

        # Human input
        st.session_state.user_response = st.text_area(
            "✍️ Your Idea:", height=150, value=st.session_state.user_response,
            placeholder="Aim for creativity and clarity. Surprise us!"
        )

        # AI response
        if st.button("🤖 See AI’s Idea"):
            with st.spinner("AI is thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": st.session_state.prompt}]
                )
                st.session_state.ai_response = resp.choices[0].message.content

        if st.session_state.ai_response:
            show_showdown_and_vote()

# --------------------------
# Mode: Yes, And… (collaborative; no scoring)
# --------------------------
def render_yes_and():
    back_to_nav()
    st.markdown("## 🎭 Yes, And… (Collaborative Improv)")
    st.markdown('<p class="tip">Start with a line; the AI continues; then you add another. Build a story together!</p>', unsafe_allow_html=True)

    if st.button("Start New Story"):
        st.session_state.yes_and_story = ""
        st.session_state.round += 1

    human_input = st.text_input("✍️ Your line:", placeholder="Once upon a time in a floating library...")
    if st.button("Add My Line"):
        if human_input.strip():
            st.session_state.yes_and_story += f"👤 {human_input}\n"
            with st.spinner("AI continues..."):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Continue this story in 1–2 sentences max: {st.session_state.yes_and_story}"}]
                )
                ai_line = resp.choices[0].message.content.strip()
                st.session_state.yes_and_story += f"🤖 {ai_line}\n"

    st.text_area("Story so far:", st.session_state.yes_and_story, height=320)

# --------------------------
# Mode: Constraint (dynamic {A}/{B} + optional double constraint + voting)
# --------------------------
def render_constraint():
    back_to_nav()
    st.markdown("## 🔒 Constraint Mode")
    st.markdown('<p class="tip">A playful restriction makes creativity pop: rhyme, haiku, emojis, bananas, and more.</p>', unsafe_allow_html=True)

    double_constraint = st.checkbox("🎯 Double challenge (use two constraints)")

    if st.button("✨ Generate Constraint Challenge"):
        A, B = random.sample(concepts, 2)
        chosen = random.sample(constraints, 2) if double_constraint else [random.choice(constraints)]
        filled_constraints = [fmt_dynamic(c, A, B) for c in chosen]
        constraint_text = " AND ".join(filled_constraints)
        st.session_state.prompt = f"Create something involving **{A}** and **{B}** — but it {constraint_text}."
        st.session_state.ai_response = None
        st.session_state.user_response = ""
        st.session_state.round += 1

    if st.session_state.prompt:
        st.markdown(f"**Round:** {st.session_state.round}")
        st.info(st.session_state.prompt)
        st.markdown(f"**Guidance:** {difficulty_guidance[st.session_state.difficulty]}")

        st.session_state.user_response = st.text_area(
            "✍️ Your constrained idea:", height=150, value=st.session_state.user_response,
            placeholder="Try meeting the constraint in a playful way…"
        )

        if st.button("🤖 See AI’s Constrained Idea"):
            with st.spinner("AI is thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Please satisfy the constraint: {st.session_state.prompt}"}]
                )
                st.session_state.ai_response = resp.choices[0].message.content

        if st.session_state.ai_response:
            show_showdown_and_vote()

# --------------------------
# Mode: Mash-up (voting)
# --------------------------
def render_mashup():
    back_to_nav()
    st.markdown("## 🌀 Mash-up Mode")
    st.markdown('<p class="tip">Two random concepts walk into a bar… now blend them into something brilliant.</p>', unsafe_allow_html=True)

    if st.button("✨ Generate Mash-up Challenge"):
        A, B = random.sample(concepts, 2)
        st.session_state.prompt = f"Blend **{A}** and **{B}** into a new invention, story, or ad."
        st.session_state.ai_response = None
        st.session_state.user_response = ""
        st.session_state.round += 1

    if st.session_state.prompt:
        st.markdown(f"**Round:** {st.session_state.round}")
        st.info(st.session_state.prompt)
        st.markdown(f"**Guidance:** {difficulty_guidance[st.session_state.difficulty]}")

        st.session_state.user_response = st.text_area(
            "✍️ Your mash-up idea:", height=150, value=st.session_state.user_response,
            placeholder="What’s the hook? What makes this mash-up work?"
        )

        if st.button("🤖 See AI’s Mash-up Idea"):
            with st.spinner("AI is thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": st.session_state.prompt}]
                )
                st.session_state.ai_response = resp.choices[0].message.content

        if st.session_state.ai_response:
            show_showdown_and_vote()

# --------------------------
# Router
# --------------------------
if st.session_state.page == "intro" and not st.session_state.skip_intro_next_time:
    render_intro()
elif st.session_state.page == "home" or (st.session_state.page == "intro" and st.session_state.skip_intro_next_time):
    st.session_state.page = "home"
    render_home()
else:
    if not st.session_state.mode:
        st.session_state.page = "home"
        render_home()
    else:
        if st.session_state.mode == "Classic":
            render_classic()
        elif st.session_state.mode == "Yes, And…":
            render_yes_and()
        elif st.session_state.mode == "Constraint":
            render_constraint()
        elif st.session_state.mode == "Mash-up":
            render_mashup()
        else:
            st.session_state.page = "home"
            render_home()

