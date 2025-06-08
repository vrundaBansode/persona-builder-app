import streamlit as st
import google.generativeai as genai
import json
import io
from PIL import Image as PIL_Image
from PIL import ImageOps as PIL_ImageOps
import re
import typing
import base64
import requests

# --- Shared Gemini Model Initialization ---
# (Assume GEMINI_API_KEY is set in trial.py before importing shared.py)
text_model = genai.GenerativeModel('gemini-2.0-flash')
vision_model = genai.GenerativeModel('gemini-2.0-flash') # Multimodal for image analysis
generation_model = None # Will be initialized in trial.py after vertexai.init

# --- Shared Helper Functions ---
def parse_gemini_json_response(response_text):
    match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if match:
        json_content = match.group(1)
    else:
        json_content = response_text.strip()
    try:
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON response: {e}. Raw response: {json_content}")
        raise

def generate_content_for_persona(persona_data, content_type):
    persona_name = persona_data.get('name', 'the user')
    persona_archetype = persona_data.get('archetype', 'a typical customer')
    motivations = persona_data.get('motivations_details', [])
    pain_points = persona_data.get('pain_points_details', [])
    aspirations = persona_data.get('aspirations_details', [])
    motivations_summary = persona_data.get('motivations_summary', '')
    pain_points_summary = persona_data.get('pain_points_summary', '')
    aspirations_summary = persona_data.get('aspirations_summary', '')
    scenario = persona_data.get('typical_scenario', '')

    base_prompt = f"""
You are an expert marketing copywriter and product strategist. Generate {content_type} for the following customer persona. Use their motivations, pain points, aspirations, and archetype to make the content highly relevant and persuasive.

Persona Name: {persona_name}
Archetype: {persona_archetype}
Motivations: {motivations_summary} {', '.join(motivations)}
Pain Points: {pain_points_summary} {', '.join(pain_points)}
Aspirations: {aspirations_summary} {', '.join(aspirations)}
Typical Scenario: {scenario}
"""

    try:
        if content_type == "Landing Page Copy":
            prompt = base_prompt + """
Generate a landing page copy with:
- A headline (hero section)
- A problem section
- A solution section
- A call to action
Each section should be concise, impactful, and tailored to the persona's needs.
Provide the output as a JSON object with keys: 'Hero', 'Problem', 'Solution', 'Call to Action'.
"""
            response = text_model.generate_content(prompt)
            content_json = parse_gemini_json_response(response.text)
            raw_text = json.dumps(content_json, indent=2)
            html_output = _create_landing_page_html(content_json)
            return raw_text, html_output

        elif content_type == "Pitch Slide Headlines":
            prompt = base_prompt + """
Generate 5-7 concise, compelling pitch slide headlines for an investor deck. Each headline should capture a key aspect of the product/solution in a way that resonates with the persona's problems and aspirations, and hints at market opportunity.
Provide the output as a JSON object with a single key 'headlines' whose value is a list of strings.
"""
            response = text_model.generate_content(prompt)
            content_json = parse_gemini_json_response(response.text)
            headlines = content_json.get('headlines', [])
            raw_text = "\n".join(headlines)
            html_output = _create_pitch_slides_html(headlines)
            return raw_text, html_output

        elif content_type == "Cold Email / Re-engagement Campaigns":
            prompt = base_prompt + """
Generate a short, personalized cold email (or re-engagement email) for this persona. Include a catchy subject line, a brief body that addresses a key pain point and offers a clear value proposition, and a call to action. Keep it under 100 words.
Provide the output as a JSON object with keys: 'subject' (string) and 'body' (string).
"""
            response = text_model.generate_content(prompt)
            content_json = parse_gemini_json_response(response.text)
            subject = content_json.get('subject', 'No Subject')
            body = content_json.get('body', 'No body.')
            raw_text = f"Subject: {subject}\n\n{body}"
            html_output = _create_email_html(subject, body)
            return raw_text, html_output

        elif content_type == "Taglines / Hero Section Ideas":
            prompt = base_prompt + """
Generate 5-7 short, memorable taglines or hero section ideas for a website. These should instantly communicate the core value proposition and resonate with the persona's primary motivation or aspiration.
Provide the output as a JSON object with a single key 'taglines' whose value is a list of strings.
"""
            response = text_model.generate_content(prompt)
            content_json = parse_gemini_json_response(response.text)
            taglines = content_json.get('taglines', [])
            raw_text = "\n".join(taglines)
            html_output = "<ul style='list-style-type: none; padding: 0;'>" + "".join([f"<li style='background-color: #e8f0fe; padding: 8px 12px; margin-bottom: 5px; border-radius: 5px; color: #1A73E8; font-weight: 500;'>{t}</li>" for t in taglines]) + "</ul>"
            return raw_text, html_output

        elif content_type == "Social Post Hooks":
            prompt = base_prompt + """
Generate 3-5 engaging social media post hooks (for Twitter, LinkedIn, or Instagram). Each hook should be short, attention-grabbing, and designed to pique the persona's interest by addressing a pain point or aspiration. Include relevant emojis.
Provide the output as a JSON object with a single key 'posts' whose value is a list of strings.
"""
            response = text_model.generate_content(prompt)
            content_json = parse_gemini_json_response(response.text)
            posts = content_json.get('posts', [])
            raw_text = "\n\n".join(posts)
            # Create platform-specific mockups for each post
            html_output = ""
            for i, post in enumerate(posts):
                platform = "twitter" if i % 3 == 0 else "linkedin" if i % 3 == 1 else "instagram"
                html_output += _create_social_post_html(post, platform)
            return raw_text, html_output

        else:
            return "Invalid content type.", "<p style='color: red;'>Invalid content type selected.</p>"

    except Exception as e:
        error_msg = f"[Error generating content: {e}]"
        return error_msg, f"<p style='color: red;'>{error_msg}</p>"

def generate_problem_solution_persona(problem_statement):
    import google.generativeai as genai # Import locally if needed only here
    # Assume text_model is available from the shared scope
    problem_persona_prompt = f"""
    As a highly skilled product strategist and customer research expert, your task is to analyze the following problem statement and then synthesize a detailed customer persona that *primarily embodies this problem*, along with potential solution-fit insights.

    The persona should be returned in a strict JSON format with the following keys:
    - 'name': A creative, memorable name for this persona.
    - 'archetype': A concise, descriptive archetype relevant to the problem.
    - 'problem_description_from_persona_view_summary': A 1-2 sentence concise, impactful description of the problem *from this persona's perspective*.
    - 'problem_description_from_persona_view_details': A 2-4 sentence detailed description.
    - 'current_solutions_and_their_flaws_summary': A 1-2 sentence concise, impactful summary of their current inadequate solutions.
    - 'current_solutions_and_their_flaws_details': A list of 2-3 ways they currently try to solve this problem, and why those solutions are inadequate.
    - 'ideal_solution_expectations_summary': A 1-2 sentence concise, impactful summary of their ideal solution expectations.
    - 'ideal_solution_expectations_details': A list of 2-3 key characteristics or outcomes they would expect from an ideal solution to this problem.
    - 'motivations_related_to_problem_summary': A single, concise, impactful phrase (max 10 words) summarizing core motivations directly tied to solving this specific problem.
    - 'motivations_related_to_problem_details': A list of 2-3 core motivations directly tied to solving this specific problem.
    - 'pain_points_related_to_problem_summary': A single, concise, impactful phrase (max 10 words) summarizing acute pain points specifically caused by this problem.
    - 'pain_points_related_to_problem_details': A list of 2-3 acute pain points specifically caused by this problem.
    - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, reflecting their struggle or their desire for a solution.

    Problem Statement:
    {problem_statement}

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """
    try:
        response = text_model.generate_content([{"text": problem_persona_prompt}])
        persona_data = parse_gemini_json_response(response.text)
        return persona_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse problem-solution persona JSON. Error: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"Error generating problem-solution persona: {e}")
        return None

def generate_persona_image(description, api_key):
    """
    Generates an animated, cartoon, 3D avatar based on the persona's visual_avatar_description using Google's Imagen model via the Generative Language API.
    Requires the GEMINI_API_KEY to be passed.
    Returns a PIL Image object.
    """
    try:
        # st.info(f"--- Attempting to generate image for description: '{description}' ---") # Removed debug info

        # Use the Imagen model endpoint via Generative Language API
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"

        # Refine the image prompt for the desired avatar style
        image_prompt = (
            "A static 3D vector cartoon avatar portrait of a person, in the style of modern Pixar or DreamWorks animation. "
            "The avatar should have an individual that's friendly, approachable expression, big expressive eyes, smooth skin, clean lines, minimalist features, "
            "and a soft pastel or neutral background. The style should be sophisticated, professional, and visually appealing, "
            "similar to high-quality 3D illustrations used in tech branding. "
            f"{description}"
        )

        payload = {
            "instances": {
                "prompt": image_prompt
            },
            "parameters": {
                "sampleCount": 1
            }
        }

        # st.info(f"[DEBUG] Sending request to Imagen API...") # Removed debug info
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        
        # Check for HTTP errors
        if response.status_code != 200:
            st.error(f"Imagen API request failed with status code {response.status_code}")
            st.error(f"Response: {response.text}")
            return None

        try:
            result = response.json()
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse Imagen API response as JSON: {e}")
            st.error(f"Raw response: {response.text[:500]}...")  # Show first 500 chars of response
            return None

        # Validate response structure
        if not isinstance(result, dict):
            st.error("Imagen API response is not a dictionary")
            return None

        predictions = result.get("predictions", [])
        if not predictions or not isinstance(predictions, list):
            st.error("No predictions found in Imagen API response")
            return None

        first_prediction = predictions[0]
        if not isinstance(first_prediction, dict):
            st.error("First prediction is not a dictionary")
            return None

        base64_image = first_prediction.get("bytesBase64Encoded")
        if not base64_image or not isinstance(base64_image, str):
            st.error("No base64 image data found in prediction")
            return None

        try:
            # Decode base64 image data
            image_bytes = base64.b64decode(base64_image)
            generated_image = PIL_Image.open(io.BytesIO(image_bytes))
            # st.success("Successfully generated and decoded image") # Removed debug success message
            return generated_image
        except Exception as e:
            st.error(f"Failed to decode or open image data: {e}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Network error while calling Imagen API: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error in generate_persona_image: {e}")
        return None

def display_image(
    image,
    max_width: int = 600,
    max_height: int = 350,
) -> None:
    # The input `image` is now expected to be a PIL Image object directly
    pil_image = typing.cast(PIL_Image.Image, image)
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    image_width, image_height = pil_image.size
    if max_width < image_width or max_height < image_height:
        pil_image = PIL_ImageOps.contain(pil_image, (max_width, max_height))
    st.image(pil_image)

# Add other shared functions as needed (e.g., generate_problem_solution_persona, generate_persona_image) 