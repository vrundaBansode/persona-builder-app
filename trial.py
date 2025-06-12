import streamlit as st
import google.generativeai as genai
import os
import json
import io
from PIL import Image # Pillow library for image handling
import base64 # For encoding/decoding images
import requests # For direct API calls (e.g., Imagen)
import pandas as pd # For CSV handling
import time # For showing temporary messages
import re # For regex to parse JSON from markdown
from google.cloud import storage
from google.cloud import aiplatform
from shared import text_model, generate_content_for_persona, parse_gemini_json_response, generate_problem_solution_persona, generate_persona_image, display_image, vision_model
import messaging_generator
import problem_solution_fit
import anti_persona_engine
import copy # copy is used in this file for persona export
import shared

# --- Streamlit UI Configuration ---
st.set_page_config(
    layout="wide",
    page_title="AI Persona & Product-Market Fit Engine 🚀",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.google.com',
        'Report a bug': "https://www.google.com",
        'About': "# This is a Product-Market Fit Engine powered by Google Gemini and Imagen models."
    }
)

# --- API Key Configuration ---
# class Config:
#     @staticmethod
#     def get_api_key(key_name):
#         return os.getenv(key_name)

# try:
#     GEMINI_API_KEY = Config.get_api_key("GEMINI_API_key")
#     if not GEMINI_API_KEY:
#         raise KeyError("GEMINI_API_key environment variable not set.")
#     genai.configure(api_key=GEMINI_API_KEY)
# except KeyError as e:
#     st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
#     st.stop()
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    if not GEMINI_API_KEY:
        raise KeyError("GEMINI_API_key environment variable not set.")
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError as e:
    st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
    st.stop()

# --- Session State Initialization ---
def init_session():
    defaults = {
        'chat_history': [],
        'current_persona_chat_model': None,
        'current_persona_details': None,
        'generated_personas': [],
        'selected_persona_index': -1,
        'uploaded_image_bytes': None,
        'uploaded_image_type': None,
        'processed_feedback_data': [],
        'generated_avatar_base64': None,
        'persona_generation_prompt_history': {},
        'active_main_tab_index': 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# --- App Header ---
st.title("AI Product-Market Fit Engine 🚀")
st.markdown("""
<div style='text-align: center; color: #5F6368; font-size: 1.1em; margin-bottom: 1.5em;'>
    Instantly understand customer demands and accelerate your product development with AI-driven insights for early founders and small business owners.
</div>
""", unsafe_allow_html=True)

# --- Tab Selection Workaround ---
tab_names = ["Persona Builder", "Messaging Generator", "Problem-Solution Fit", "Anti-Persona Engine"]
selected_tab = st.radio("Main Tabs", tab_names, index=st.session_state.active_main_tab_index, horizontal=True, label_visibility="hidden")
st.session_state.active_main_tab_index = tab_names.index(selected_tab)

# --- Helper Functions ---
def analyze_sentiment(text):
    """
    Analyzes the sentiment of the given text using Gemini.
    Returns: "Positive", "Negative", or "Neutral".
    """
    prompt = f"Analyze the sentiment of the following text and respond with only 'Positive', 'Negative', or 'Neutral'.\nText: {text}"
    try:
        response = text_model.generate_content(prompt)
        sentiment = response.text.strip().capitalize()
        if sentiment not in ["Positive", "Negative", "Neutral"]:
            return "Neutral"
        return sentiment
    except Exception as e:
        st.error(f"Error analyzing sentiment with Gemini: {e}")
        return "Neutral"

def analyze_image_context(image_bytes, mime_type):
    """
    Analyzes the context of an image using Gemini's multimodal capabilities.
    Returns a string summary of the image context relevant for persona creation.
    """
    if not image_bytes or not mime_type:
        return ""

    try:
        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }
        prompt_parts = [
            image_part,
            "Describe the key elements, environment, mood, and potential lifestyle suggested by this image, specifically focusing on details that could inform a customer persona. For example, is it a busy professional, a calm home user, an outdoor adventurer? Keep it concise and relevant to user context."
        ]
        response = vision_model.generate_content(prompt_parts)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error analyzing image context with Gemini Vision: {e}")
        return ""

def generate_persona_from_gemini(feedback_text_combined, image_context=None):
    """
    Generates a detailed customer persona using Gemini AI, with optional image context.
    Returns a dictionary of persona details.
    """
    base_prompt = """
    Based on the following customer feedback and context, generate a detailed customer persona in JSON format.
    The persona should include:
    - `name`: A creative name for the persona.
    - `archetype`: A concise archetype (e.g., 'The Budget-Conscious Shopper', 'The Tech Enthusiast').
    - `motivations_summary`: A concise summary of their main motivations (1-2 sentences).
    - `motivations_details`: A list of 3-5 bullet points detailing their motivations.
    - `pain_points_summary`: A concise summary of their main pain points (1-2 sentences).
    - `pain_points_details`: A list of 3-5 bullet points detailing their pain points.
    - `aspirations_summary`: A concise summary of their main aspirations (1-2 sentences).
    - `aspirations_details`: A list of 3-5 bullet points detailing their aspirations.
    - `typical_scenario`: A short paragraph describing a typical scenario where this persona interacts with a product/service relevant to their needs.
    - `visual_avatar_description`: A short, descriptive phrase (max 10 words) for generating a visual avatar (e.g., 'A professional woman coding on a laptop', 'Elderly man gardening').

    Customer Feedback:
    {feedback_text}

    {image_context_str}

    Ensure the response is ONLY a JSON object.
    """

    image_context_str = f"Image Context: {image_context}\n" if image_context else ""
    full_prompt = base_prompt.format(feedback_text=feedback_text_combined, image_context_str=image_context_str)

    try:
        response = text_model.generate_content(full_prompt)
        persona_data = parse_gemini_json_response(response.text)
        return persona_data
    except Exception as e:
        st.error(f"Error generating persona with Gemini: {e}")
        return None

def refine_persona_with_gemini(existing_persona_data, refinement_feedback):
    """
    Refines an existing persona based on user feedback using Gemini.
    Returns an updated dictionary of persona details.
    """
    persona_for_prompt = {k: v for k, v in existing_persona_data.items() if k != 'avatar_image'}

    prompt = f"""
    You are an AI assistant tasked with refining customer personas.
    Given the existing persona details below (in JSON format) and new refinement feedback,
    update the persona. Ensure the output is ONLY the updated JSON object, adhering to the original structure.
    Do not add any additional text or markdown outside the JSON.

    Existing Persona:
    {json.dumps(persona_for_prompt, indent=2)}

    Refinement Feedback:
    {refinement_feedback}

    Updated Persona:
    """
    try:
        response = text_model.generate_content(prompt)
        refined_persona = parse_gemini_json_response(response.text)
        return refined_persona
    except Exception as e:
        st.error(f"Error refining persona with Gemini: {e}")
        return None

# The following functions are moved to shared.py:
# def generate_persona_image(...)
# def display_image(...)
# def generate_content_for_persona(...)
# def copy_to_clipboard_button(...)

# generate_problem_solution_persona is also moved to shared.py

# --- Conditional Rendering by Tab ---
if selected_tab == "Persona Builder":
    st.header("Build Customer Personas from Feedback ✨")
    st.markdown("""
    <div style='color: #5F6368; font-size: 0.95em; margin-bottom: 1em;'>
        Synthesize detailed customer personas by providing raw feedback, survey responses, or even a contextual image.
    </div>
    """, unsafe_allow_html=True)

    feedback_option = st.radio(
        "Choose feedback input method:",
        ("Paste Text", "Upload CSV"),
        key="feedback_input_option_tab1",
        horizontal=True
    )

    feedback_text_combined = ""
    st.session_state.processed_feedback_data = []

    if feedback_option == "Paste Text":
        feedback_text_area = st.text_area(
            "Paste raw customer feedback, survey responses, or interview snippets here:",
            height=180,
            placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'",
            key="feedback_paste_area"
        )
        if feedback_text_area:
            feedback_text_combined = feedback_text_area
            sentiment = analyze_sentiment(feedback_text_area)
            st.session_state.processed_feedback_data.append({'text': feedback_text_area, 'sentiment': sentiment})
            st.markdown(f"**Overall Feedback Sentiment:** <span style='font-weight:bold; color:{'green' if sentiment=='Positive' else ('red' if sentiment=='Negative' else 'orange')};'>{sentiment}</span>", unsafe_allow_html=True)
            st.markdown("---")

    elif feedback_option == "Upload CSV":
        uploaded_csv = st.file_uploader(
            "Upload a CSV file with customer feedback (ensure one column is named 'feedback'):",
            type=["csv"],
            key="feedback_csv_uploader"
        )
        if uploaded_csv is not None:
            try:
                df = pd.read_csv(uploaded_csv)
                if 'feedback' in df.columns:
                    feedback_entries = df['feedback'].dropna().astype(str).tolist()
                    if feedback_entries:
                        st.info(f"Processing {len(feedback_entries)} feedback entries from CSV... (Sentiment analysis may take time)")

                        all_feedback_for_sentiment = []
                        for i, entry in enumerate(feedback_entries):
                            current_sentiment = analyze_sentiment(entry)
                            st.session_state.processed_feedback_data.append({'text': entry, 'sentiment': current_sentiment})
                            all_feedback_for_sentiment.append(f"Feedback {i+1} (Sentiment: {current_sentiment}): {entry}")

                        feedback_text_combined = "\n\n".join([item['text'] for item in st.session_state.processed_feedback_data])

                        if feedback_text_combined:
                            overall_sentiment = analyze_sentiment(feedback_text_combined)
                            st.markdown(f"**Overall Feedback Sentiment:** <span style='font-weight:bold; color:{'green' if overall_sentiment=='Positive' else ('red' if overall_sentiment=='Negative' else 'orange')};'>{overall_sentiment}</span>", unsafe_allow_html=True)

                        with st.expander("View Individual Feedback Entries & Sentiments ⬇️"):
                            for i, entry_data in enumerate(st.session_state.processed_feedback_data):
                                color = 'green' if entry_data['sentiment'] == 'Positive' else ('red' if entry_data['sentiment'] == 'Negative' else 'orange')
                                st.markdown(f"**Entry {i+1}** (Sentiment: <span style='color:{color}'>{entry_data['sentiment']}</span>): {entry_data['text']}", unsafe_allow_html=True)
                                st.markdown("---")
                    else:
                        st.warning("No valid feedback entries found in the 'feedback' column of the CSV.")
                else:
                    st.error("CSV must contain a column named 'feedback'.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        st.markdown("---")

    uploaded_image = st.file_uploader(
        "Optional: Upload an image representing the customer's environment or product usage (e.g., a photo of their workspace, or them using a similar product):",
        type=["jpg", "jpeg", "png"],
        key="context_image_uploader"
    )

    image_context_description = ""
    if uploaded_image is not None:
        st.session_state.uploaded_image_bytes = uploaded_image.read()
        st.session_state.uploaded_image_type = uploaded_image.type
        st.image(uploaded_image, caption="Uploaded Context Image", width=150)
        with st.spinner("Analyzing image for context..."):
            image_context_description = analyze_image_context(st.session_state.uploaded_image_bytes, st.session_state.uploaded_image_type)
            if image_context_description:
                st.success("Image context analyzed.")
                with st.expander("View Image Context Analysis ⬇️"):
                    st.write(image_context_description)
            else:
                st.warning("Could not extract meaningful context from the image.")
        st.markdown("---")
    else:
        st.session_state.uploaded_image_bytes = None
        st.session_state.uploaded_image_type = None

    st.subheader("Generate New Persona 🤖")
    if st.button("✨ Synthesize New Persona", use_container_width=True, key="generate_persona_btn"):
        if not feedback_text_combined and not st.session_state.uploaded_image_bytes:
            st.warning("Please provide either text feedback (paste or CSV) or an image (or both) to generate a persona.")
        else:
            with st.spinner("Generating persona with Gemini AI... This might take a moment."):
                persona = generate_persona_from_gemini(
                    feedback_text_combined,
                    image_context_description
                )

            if persona:
                st.session_state.generated_personas.append(persona)
                st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
                st.success("Persona generated successfully!")
                if 'visual_avatar_description' in persona and persona['visual_avatar_description']:
                    with st.spinner("Generating persona avatar..."):
                        avatar_image = generate_persona_image(persona['visual_avatar_description'], GEMINI_API_KEY)
                        if avatar_image:
                            st.session_state.generated_avatar_image = avatar_image
                            st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_image'] = avatar_image
                st.rerun()
            else:
                st.error("Failed to generate persona. Please check input and API keys.")

    if st.session_state.generated_personas:
        st.subheader("Your Generated Personas 🧑‍💻")
        persona_names = [p.get('name', f"Persona {i+1}") for i, p in enumerate(st.session_state.generated_personas)]
        
        if st.session_state.selected_persona_index >= len(st.session_state.generated_personas):
            st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
        if st.session_state.selected_persona_index < 0 and len(st.session_state.generated_personas) > 0:
            st.session_state.selected_persona_index = 0

        selected_persona_name = st.selectbox(
            "Select a persona to view/refine:",
            persona_names,
            index=st.session_state.selected_persona_index,
            key="persona_selector_tab1"
        )
        st.session_state.selected_persona_index = persona_names.index(selected_persona_name)
        st.session_state.current_persona_details = st.session_state.generated_personas[st.session_state.selected_persona_index]

        if 'avatar_image' in st.session_state.current_persona_details:
            avatar = st.session_state.current_persona_details['avatar_image']
            if avatar is not None and type(avatar).__name__ == 'GeneratedImage':
                st.session_state.current_persona_details['avatar_image'] = None
                st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_image'] = None

        current_persona = st.session_state.current_persona_details
        st.markdown("---")
        st.subheader(f"Details for: {current_persona.get('name', 'N/A')} ({current_persona.get('archetype', 'N/A')})")

        col1, col2 = st.columns([1, 2])
        with col1:
            if current_persona.get('avatar_image'):
                display_image(current_persona['avatar_image'])
                if st.button("🔄 Regenerate Avatar", key="regenerate_avatar_btn_tab1", use_container_width=True):
                    with st.spinner("Regenerating persona avatar..."):
                        if 'visual_avatar_description' in current_persona and current_persona['visual_avatar_description']:
                            avatar_image = generate_persona_image(current_persona['visual_avatar_description'], GEMINI_API_KEY)
                            if avatar_image:
                                st.session_state.generated_avatar_image = avatar_image
                                st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_image'] = avatar_image
                                st.success("Avatar regenerated!")
                                st.rerun()
                            else:
                                st.error("Failed to regenerate avatar.")
                        else:
                            st.warning("No visual avatar description available for this persona.")
            else:
                st.info("No avatar generated yet.")
                if st.button("✨ Generate Avatar Now", key="generate_avatar_now_btn_tab1", use_container_width=True):
                    with st.spinner("Generating persona avatar..."):
                        if 'visual_avatar_description' in current_persona and current_persona['visual_avatar_description']:
                            avatar_image = generate_persona_image(current_persona['visual_avatar_description'], GEMINI_API_KEY)
                            if avatar_image:
                                st.session_state.generated_avatar_image = avatar_image
                                st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_image'] = avatar_image
                                st.success("Avatar generated!")
                                st.rerun()
                            else:
                                st.error("Failed to generate avatar.")
                        else:
                            st.warning("No visual avatar description available for this persona.")

        with col2:
            st.markdown(f"<div class='summary-box summary-motivations'>🎯 Motivations: {current_persona.get('motivations_summary', 'N/A')}</div>", unsafe_allow_html=True)
            for detail in current_persona.get('motivations_details', []):
                st.markdown(f"• {detail}")

            st.markdown(f"<div class='summary-box summary-pain-points'>😩 Pain Points: {current_persona.get('pain_points_summary', 'N/A')}</div>", unsafe_allow_html=True)
            for detail in current_persona.get('pain_points_details', []):
                st.markdown(f"• {detail}")

            st.markdown(f"<div class='summary-box summary-aspirations'>✨ Aspirations: {current_persona.get('aspirations_summary', 'N/A')}</div>", unsafe_allow_html=True)
            for detail in current_persona.get('aspirations_details', []):
                st.markdown(f"• {detail}")

        st.markdown("---")
        st.subheader("Typical Scenario 🗓️")
        st.write(current_persona.get('typical_scenario', 'N/A'))
        st.markdown("---")

        st.subheader("Refine Persona ✏️")
        refinement_text = st.text_area(
            "Provide feedback to refine this persona (e.g., 'Make her more tech-savvy', 'Add a pain point about time management').",
            key="refinement_text_area_tab1",
            height=80
        )
        if st.button("🔄 Refine Persona", use_container_width=True, key="refine_persona_btn"):
            if refinement_text:
                with st.spinner("Refining persona..."):
                    refined_persona = refine_persona_with_gemini(current_persona, refinement_text)
                    if refined_persona:
                        refined_persona['avatar_image'] = current_persona.get('avatar_image')
                        st.session_state.generated_personas[st.session_state.selected_persona_index] = refined_persona
                        st.success("Persona refined successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to refine persona.")
            else:
                st.warning("Please enter refinement feedback.")

        st.markdown("---")
        st.subheader("Save & Export Persona 📥")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            persona_export = copy.deepcopy(current_persona)
            if 'avatar_image' in persona_export and not isinstance(persona_export['avatar_image'], (str, type(None))):
                try:
                    if isinstance(persona_export['avatar_image'], Image.Image):
                        buffered = io.BytesIO()
                        persona_export['avatar_image'].save(buffered, format="PNG")
                        persona_export['avatar_image'] = base64.b64encode(buffered.getvalue()).decode()
                    else:
                        persona_export['avatar_image'] = "Avatar image not included in export."
                except Exception as e:
                    st.error(f"Error handling avatar image for export: {e}")
                    persona_export['avatar_image'] = "Error processing avatar for export."

            persona_json = json.dumps(persona_export, indent=2)
            st.download_button(
                label="Download Persona (JSON) ⬇️",
                data=persona_json,
                file_name=f"{current_persona.get('name', 'persona').replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True,
                key="download_json_btn"
            )
        with col_dl2:
            motivations_details_formatted = '\n'.join([f'• {detail}' for detail in current_persona.get('motivations_details', [])])
            pain_points_details_formatted = '\n'.join([f'• {detail}' for detail in current_persona.get('pain_points_details', [])])
            aspirations_details_formatted = '\n'.join([f'• {detail}' for detail in current_persona.get('aspirations_details', [])])

            persona_txt = (
                f"Persona Name: {current_persona.get('name', 'N/A')}\n"
                f"Archetype: {current_persona.get('archetype', 'N/A')}\n\n"
                f"Motivations Summary: {current_persona.get('motivations_summary', 'N/A')}\n"
                f"Motivations Details:\n"
                f"{motivations_details_formatted}\n\n"
                f"Pain Points Summary: {current_persona.get('pain_points_summary', 'N/A')}\n"
                f"Pain Points Details:\n"
                f"{pain_points_details_formatted}\n\n"
                f"Aspirations Summary: {current_persona.get('aspirations_summary', 'N/A')}\n"
                f"Aspirations Details:\n"
                f"{aspirations_details_formatted}\n\n"
                f"Typical Scenario:\n"
                f"{current_persona.get('typical_scenario', 'N/A')}\n\n"
                f"Visual Avatar Description: {current_persona.get('visual_avatar_description', 'N/A')}"
            )
            st.download_button(
                label="Download Persona (TXT) ⬇️",
                data=persona_txt,
                file_name=f"{current_persona.get('name', 'persona').replace(' ', '_').lower()}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_txt_btn"
            )
        st.markdown("---")

        st.subheader("Manage Personas 🗑️")
        if st.button("❌ Delete Current Persona", use_container_width=True, key="delete_persona_btn"):
            if st.session_state.generated_personas:
                st.session_state.generated_personas.pop(st.session_state.selected_persona_index)
                if len(st.session_state.generated_personas) > 0:
                    st.session_state.selected_persona_index = max(0, st.session_state.selected_persona_index - 1)
                else:
                    st.session_state.selected_persona_index = -1
                st.success("Persona deleted.")
                st.rerun()
            else:
                st.warning("No personas to delete.")

elif selected_tab == "Messaging Generator":
    messaging_generator.render(GEMINI_API_KEY)

elif selected_tab == "Problem-Solution Fit":
    problem_solution_fit.render(GEMINI_API_KEY)

elif selected_tab == "Anti-Persona Engine":
    anti_persona_engine.render(GEMINI_API_KEY, st.session_state.active_main_tab_index)

# Custom CSS for a minimalistic, seamless, and visually pleasing UI
st.markdown("""
<style>
    /* Google-like Font */
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Google Sans', sans-serif;
        color: #3C4043; /* Google Grey 800 */
    }

    /* Main Container & Background */
    .main .block-container {
        /* Removed max-width here because layout="wide" handles it */
        padding-top: 2rem; /* Reduce top padding */
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 2rem;
        /* max-width: 900px;  This line is now less relevant due to layout="wide" */
    }
    .stApp {
        background-color: #F8F9FA; /* Light Grey background */
        background-image: linear-gradient(to bottom, #FFFFFF, #F8F9FA); /* Subtle gradient */
    }

    /* Header Styling */
    h1 {
        color: #1A73E8; /* Google Blue */
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.5em;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
    }
    h2 {
        color: #4285F4; /* Google Blue */
        font-weight: 500;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
    }
    h3 {
        color: #34A853; /* Google Green */
        font-weight: 500;
        margin-top: 1em;
        margin-bottom: 0.6em;
    }
    h4 {
        color: #EA4335; /* Google Red */
        font-weight: 500;
        margin-top: 0.8em;
        margin-bottom: 0.5em;
    }

    /* Buttons - Minimalist & Animated */
    .stButton > button {
        background-color: #4285F4; /* Google Blue */
        color: white;
        border: none;
        border-radius: 8px; /* Slightly more rounded */
        padding: 0.7em 1.5em;
        font-size: 1em;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out; /* Smooth transition */
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #357AE8; /* Darker blue on hover */
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px); /* Lift effect */
    }
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }

    /* Radio Buttons / Tabs - Seamless & Visually Clear */
    div[role="radiogroup"] label {
        padding: 8px 15px;
        margin: 5px;
        border-radius: 20px; /* Pill-shaped */
        border: 1px solid #DADCE0; /* Light border */
        color: #5F6368; /* Grey text */
        transition: all 0.2s ease-in-out;
        cursor: pointer;
    }
    div[role="radiogroup"] label:hover {
        background-color: #F0F0F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[role="radiogroup"] label[data-baseweb="radio"] input:checked + div {
        background-color: #E8F0FE !important; /* Light blue background for selected */
        border-color: #B2D0F0 !important; /* Blue border for selected */
        color: #1A73E8 !important; /* Blue text for selected */
        font-weight: 500;
    }

    /* Text Areas & Inputs - Clean */
    .stTextArea textarea, .stTextInput input[type="text"] {
        border-radius: 8px;
        border: 1px solid #DADCE0;
        padding: 10px 15px;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
        transition: border-color 0.2s ease-in-out;
    }
    .stTextArea textarea:focus, .stTextInput input[type="text"]:focus {
        border-color: #4285F4;
        box-shadow: 0 0 0 1px #4285F4; /* Focus ring */
    }

    /* Info, Success, Warning Messages */
    .stAlert {
        border-radius: 8px;
        font-size: 0.9em;
    }

    /* Avatar and Summary Boxes (from previous iteration, refined) */
    .summary-box {
        padding: 8px 12px;
        border-radius: 8px; /* Slightly more rounded */
        margin-bottom: 8px;
        font-size: 0.9em;
        font-weight: 500; /* Lighter font weight */
        color: white;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .summary-motivations { background-color: #34A853; } /* Google Green */
    .summary-pain-points { background-color: #FBBC04; } /* Google Yellow */
    .summary-aspirations { background-color: #4285F4; } /* Google Blue */

    .avatar-img {
        border-radius: 50%; /* Make avatar perfectly round */
        border: 4px solid #EA4335; /* Google Red for avatar border */
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
        object-fit: cover;
        margin-bottom: 15px;
        transition: transform 0.3s ease-in-out; /* Smooth hover effect */
    }
    .avatar-img:hover {
        transform: scale(1.05); /* Slight zoom on hover */
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: #E6EEF9; /* Light background for expander header */
        border-radius: 8px;
        padding: 10px 15px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
        color: #1A73E8;
    }
    .streamlit-expanderHeader:hover {
        background-color: #DDEBF9;
    }
    .streamlit-expanderContent {
        padding: 10px 15px;
        border-left: 3px solid #DDEBF9;
        margin-left: 5px;
    }

    /* Tabs Styling - Enhanced for visual appeal */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; /* Space between tabs */
        justify-content: center; /* Center the tabs */
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        white-space: nowrap;
        border-radius: 20px; /* Pill shape */
        padding: 0px 20px;
        gap: 5px;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
        color: #5F6368; /* Default tab text */
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #F0F0F0; /* Light hover background */
        color: #1A73E8; /* Blue text on hover */
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #E8F0FE; /* Light blue for selected tab */
        border-bottom-color: #E8F0FE !important; /* Hide default bottom border */
        color: #1A73E8; /* Blue text for selected tab */
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); /* Subtle shadow for selected */
    }
            
    .stSelectbox>[data-baseweb="select"]>div>div>div{
        color: #f6f6f6;
    }
            
    .stTooltipHoverTarget>div>div{
        color: #f3dbe6        
    }

    /* Streamlit Spinner Customization */
    /* Target the container that holds the spinner and text */
    .stSpinner > div > div {
        border-top-color: #1A73E8; /* Spinner color to match Google Blue */
        border-left-color: #1A73E8;
    }
    /* Target the text next to the spinner */
    .stSpinner > div > div > div:nth-child(2) {
        color: #5F6368; /* Text color */
        font-weight: 500;
    }
    /* Ensure the spinner container itself doesn't break layout */
    .stSpinner {
        margin-top: 20px; /* Add some space above the spinner */
        margin-bottom: 20px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 50px; /* Ensure a minimum height to prevent sudden jumps */
    }
    /* Reduce default padding/margin of components within spinner to avoid extra space */
    .stProgress, .stSuccess, .stError, .stWarning, .stInfo {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

</style>
""", unsafe_allow_html=True)

