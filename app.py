import streamlit as st
import google.generativeai as genai
import os
import json
import io
from PIL import Image # For handling image data with Streamlit
from config import Config

# Get an API key

# --- Configuration ---
# Load API key from environment variable
try:
    GEMINI_API_KEY = Config.get_api_key("GEMINI_API_KEY")
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("GEMINI_API_KEY environment variable not set. "
             "Please set it before running the app. "
             "Example: export GEMINI_API_KEY='YOUR_API_KEY'")
    st.stop() # Stop the app if API key is missing

# Initialize Gemini Model
# We use 'gemini-2.0-flash' for speed and multimodal capabilities.
# 'gemini-1.5-flash' is also a good option.
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Helper Function for Persona Generation ---

def generate_persona_from_gemini(feedback_text, uploaded_image=None):
    """
    Calls Gemini API to generate a customer persona based on text and optional image.
    """
    
    parts = []

    # Add image part if provided
    if uploaded_image:
        # Streamlit's file_uploader gives a BytesIO-like object.
        # We need to read its content.
        image_bytes = uploaded_image.read()
        parts.append({
            "mime_type": uploaded_image.type, # e.g., "image/jpeg"
            "data": image_bytes
        })

    # Add text prompt part
    # We instruct Gemini to consider both text and image if both are present.
    persona_prompt = f"""
    As a highly skilled UX researcher and marketing strategist, your task is to synthesize a detailed customer persona based on the provided customer feedback (text) and any additional visual context (image, if provided). The image should inform the persona's context, environment, or aesthetic preferences.

    The persona should be returned in a strict JSON format with the following keys:
    - 'name': A creative, memorable name for this persona (e.g., "Sarah the Savvy Shopper").
    - 'archetype': A concise, descriptive archetype (e.g., "The Budget-Conscious Student", "The Tech-Averse Senior").
    - 'motivations': A list of 3-5 primary goals or what drives their decisions.
    - 'pain_points': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
    - 'aspirations': A list of 2-3 things they hope to achieve or become.
    - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service, integrating visual cues if an image was provided.
    - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, highly informed by the overall persona attributes and the provided image.

    Customer Feedback (Text):
    \"\"\"
    {feedback_text}
    \"\"\"

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """
    parts.append({"text": persona_prompt})

    try:
        # Make the API call
        response = model.generate_content(parts)
        
        # Attempt to parse the text as JSON
        # Gemini might wrap JSON in markdown code blocks, so we need to extract it
        response_text = response.text.strip()
        if response_text.startswith("```json") and response_text.endswith("```"):
            json_string = response_text[len("```json"): -len("```")].strip()
        else:
            json_string = response_text

        persona_data = json.loads(json_string)
        return persona_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse Gemini's response as JSON. Please try again or refine your input. Error: {e}")
        st.code(response_text) # Show raw response for debugging
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during Gemini API call: {e}")
        st.warning("Please check your API key, network connection, or try simpler input.")
        return None

# --- Streamlit UI ---

st.set_page_config(layout="centered", page_title="AI Persona Builder 👥")

st.title("👥 AI-Powered Customer Persona Builder")
st.markdown("Synthesize detailed customer personas from feedback and visual context using Google Gemini's multimodal AI.")

st.header("1. Provide Customer Insights")

feedback_text = st.text_area(
    "Paste raw customer feedback, survey responses, or interview snippets here:",
    height=180,
    placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'"
)

uploaded_image = st.file_uploader(
    "Optionally upload an image representing the customer's environment or product usage (e.g., a typical workspace, a product in use, or a relevant lifestyle image):",
    type=["jpg", "jpeg", "png"]
)

if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Customer Context Image", width=250)
    st.success("Image uploaded successfully!")

st.header("2. Generate Persona")
if st.button("✨ Generate Persona", use_container_width=True):
    if not feedback_text and not uploaded_image:
        st.warning("Please provide either text feedback or an image (or both) to generate a persona.")
    else:
        with st.spinner("Generating persona with Gemini AI... This might take a moment."):
            persona = generate_persona_from_gemini(feedback_text, uploaded_image)

        if persona:
            st.success("Persona Generated Successfully!")
            st.header("3. Your Synthesized Customer Persona")

            # Display Persona Details
            st.subheader(f"{persona.get('name', 'N/A')} - *{persona.get('archetype', 'N/A')}*")

            st.markdown("---")

            st.markdown("**Motivations:**")
            for m in persona.get('motivations', []):
                st.markdown(f"- {m}")

            st.markdown("**Pain Points:**")
            for p in persona.get('pain_points', []):
                st.markdown(f"- {p}")

            st.markdown("**Aspirations:**")
            for a in persona.get('aspirations', []):
                st.markdown(f"- {a}")

            st.markdown("**Typical Scenario:**")
            st.info(f"> {persona.get('typical_scenario', 'N/A')}")

            if 'visual_avatar_description' in persona:
                st.markdown("**Visual Avatar Idea:**")
                st.code(persona['visual_avatar_description']) # Display as code for easy copy-paste to image generator

            st.markdown("---")
            st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

# --- Instructions for Running ---
st.sidebar.header("How to Run This App")
st.sidebar.markdown("""
1.  **Save the code:** Save the above code as `app.py` in your project folder.
2.  **Set API Key:** Ensure your Gemini API key is set as an environment variable named `GEMINI_API_KEY` in the terminal you're using.
3.  **Run the app:**
    * Open your terminal/command prompt.
    * Navigate to your project folder (`cd persona_builder_app`).
    * Ensure your `venv` is active (`source venv/bin/activate` or `.\venv\Scripts\activate`).
    * Run the Streamlit command:
        ```bash
        streamlit run app.py
        ```
4.  **Interact:** A new tab will open in your web browser with the app. Provide text feedback, optionally upload an image, and click "Generate Persona."
""")

st.sidebar.header("Prioritization & Optimization Notes")
st.sidebar.markdown("""
* **Functionality First:** This initial version focuses on getting the core AI generation working.
* **API Key Security:** Using environment variables is crucial for security.
* **Error Handling:** Basic error handling is included for API calls and JSON parsing.
* **UI Simplicity:** Streamlit makes the UI simple; no complex CSS/HTML is required for core functionality.
* **Future Optimizations (Next Steps):**
    * **Persistent Storage:** Integrate Firebase Firestore to save/retrieve generated personas.
    * **Rate Limiting/Cost Management:** For real-world use, implement mechanisms to control API calls.
    * **Advanced UI:** More sophisticated layouts, search/filter for stored personas.
    * **Direct Image Generation:** Integrate a separate text-to-image model (like Imagen on Vertex AI or Stability AI) to actually generate the avatar image from the `visual_avatar_description`.
    * **User Authentication:** For a multi-user environment.
""")