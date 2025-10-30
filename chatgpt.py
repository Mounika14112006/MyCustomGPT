import streamlit as st
from groq import Groq
from langdetect import detect
from gtts import gTTS
import base64
import random
import io
import json
from datetime import datetime
import os

# ------------------ CONFIG ------------------
client = Groq(api_key="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")  # ✅ Replace with your valid Groq API key
st.set_page_config(page_title="Mounika's Custom GPT", page_icon="🤖", layout="centered")

# ------------------ CUSTOM HEADER ------------------
st.markdown(
    """
    <div style="text-align:center; padding: 20px 0;">
        <h1 style="margin-bottom: 0; font-size: 56px; font-weight: bold;">
            <span style="color:#FF6F00;">Mounika's</span> Custom GPT 🤖
        </h1>
        <p style="margin-top: 5px; font-size: 22px; color: #6A5ACD; font-style: italic;">
            Learn and chat with fun! 🚀
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------ HISTORY SETUP ------------------
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

all_history = load_history()
today_str = datetime.now().strftime("%Y-%m-%d")
if "current_date" not in st.session_state:
    st.session_state.current_date = today_str

all_dates = sorted(list(set([today_str] + list(all_history.keys()))), reverse=True)
selected_date = st.sidebar.selectbox("📅 Select Chat Date", all_dates)

if selected_date != st.session_state.current_date:
    st.session_state.current_date = selected_date
    st.session_state.chat_history = all_history.get(selected_date, [])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = all_history.get(selected_date, [])

# ------------------ SIDEBAR SETTINGS ------------------
st.sidebar.title("⚙️ Settings")

personality = st.sidebar.selectbox("Personality", [
    "🎓 Teacher", "🧠 Coder", "🧙 Philosopher", "😄 Friendly Chat"
])
personality_prompts = {
    "🎓 Teacher": "You are a patient teacher who explains things clearly.",
    "🧠 Coder": "You are a skilled coding assistant who gives precise code and explanations.",
    "🧙 Philosopher": "You are a wise philosopher who answers with depth.",
    "😄 Friendly Chat": "You are a cheerful, friendly companion."
}

language_option = st.sidebar.selectbox("Preferred Language", [
    "Auto Detect", "English", "Hindi", "Telugu"
])
language_codes = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te"
}

tts_enabled = st.sidebar.checkbox("🔊 Enable Text-to-Speech", value=False)

# ------------------ FUN FACT + WELCOME ------------------
fun_facts = [
    "🧠 Did you know? The average human brain has about 86 billion neurons.",
    "💡 Tip: Taking regular breaks boosts productivity!",
    "🌍 Fun fact: There are over 7,000 languages spoken in the world.",
    "🔋 Tip: Drink water — even mild dehydration reduces cognitive performance.",
    "📖 Word of the day: 'Serendipity' – the occurrence of events by chance in a happy or beneficial way."
]
st.success("👋 Welcome! Ask me anything below.")
st.info(random.choice(fun_facts))

# ------------------ USER INPUT FORM ------------------
with st.form(key="chat_form", clear_on_submit=True):
    st.text_area("💬 Ask me something...", height=100, key="user_input")
    submit_button = st.form_submit_button("🔼 Send")

# ------------------ GPT CHAT ------------------
if submit_button and st.session_state.user_input.strip():
    user_input = st.session_state.user_input.strip()

    if language_option == "Auto Detect":
        detected_lang = detect(user_input)
    else:
        detected_lang = language_codes[language_option]

    system_prompt = f"{personality_prompts[personality]} Reply in {language_option if language_option != 'Auto Detect' else detected_lang} language."

    messages = [{"role": "system", "content": system_prompt}]
    for i in range(0, len(st.session_state.chat_history), 2):
        messages.append({"role": "user", "content": st.session_state.chat_history[i][1]})
        messages.append({"role": "assistant", "content": st.session_state.chat_history[i+1][1]})
    messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
            )
            response = completion.choices[0].message.content
        except Exception as e:
            response = f"❌ Error: {e}"

    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("ai", response))

    all_history[st.session_state.current_date] = st.session_state.chat_history
    save_history(all_history)

# ------------------ DISPLAY CHAT ------------------
st.markdown("---")
st.subheader(f"🗂️ Chat on {st.session_state.current_date}")

for role, msg in st.session_state.chat_history:
    display_name = "🧑‍💻 You" if role == "user" else "🤖 AI"
    st.markdown(f"**{display_name}:** {msg}")

    if role == "ai" and tts_enabled:
        try:
            tts = gTTS(text=msg, lang=detected_lang if detected_lang in ["en", "hi", "te"] else "en")
            with io.BytesIO() as audio_buffer:
                tts.write_to_fp(audio_buffer)
                audio_bytes = audio_buffer.getvalue()
                b64 = base64.b64encode(audio_bytes).decode()
                audio_html = f"""
                    <audio controls>
                        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
        except Exception:
            st.warning("⚠️ Could not generate voice output.")

# ------------------ SUMMARIZE CHAT ------------------
if st.button("🧾 Summarize Chat"):
    if st.session_state.chat_history:
        combined = "\n".join([f"{r.upper()}: {m}" for r, m in st.session_state.chat_history])
        messages = [
            {"role": "system", "content": "Summarize the following chat briefly:"},
            {"role": "user", "content": combined}
        ]
        with st.spinner("Summarizing..."):
            try:
                summary = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=500
                ).choices[0].message.content
                st.success("📌 Summary:")
                st.info(summary)
            except Exception as e:
                st.error(f"❌ Failed to summarize: {e}")
    else:
        st.warning("No chat to summarize.")

# ------------------ DOWNLOAD CHAT ------------------
export_text = "\n".join([f"{r.upper()}: {m}" for r, m in st.session_state.chat_history])
st.download_button("📥 Download Chat as .txt", export_text, file_name=f"chat_{st.session_state.current_date}.txt")
