import streamlit as st
from shared import text_model, generate_persona_image, generation_model # Import necessary functions and models
import json
import base64
from datetime import datetime
import re # Import re for parsing JSON from markdown
import io # Import io for image processing
from PIL import Image as PIL_Image # Import PIL Image

def _generate_content_for_persona(persona_data, content_type, api_key):
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

    if content_type == "Landing Page Copy":
        prompt = base_prompt + """
Generate a landing page copy in JSON format. The JSON should have the following structure:
{
    "Hero": {
        "Headline": "A compelling headline (string, MUST be a descriptive, non-empty headline)",
        "Sub-headline": "A concise sub-headline (string, MUST be a descriptive, non-empty sub-headline)"
    },
    "Problem": {
        "Title": "Problem title (string, MUST be a descriptive, non-empty title)",
        "Paragraph_1": "Description of the problem (string, MUST be a descriptive, non-empty paragraph)",
        "Bullet_Points": ["Bullet point 1 (string, MUST be a descriptive, non-empty bullet point)", "Bullet point 2 (string, MUST be a descriptive, non-empty bullet point)", "Bullet point 3 (string, MUST be a descriptive, non-empty bullet point)"]
    },
    "Solution": {
        "Title": "Solution title (string, MUST be a descriptive, non-empty title)",
        "Paragraph_1": "Description of the solution (string, MUST be a descriptive, non-empty paragraph)",
        "Features": ["Feature 1 (string, MUST be a descriptive, non-empty feature)", "Feature 2 (string, MUST be a descriptive, non-empty feature)", "Feature 3 (string, MUST be a descriptive, non-empty feature)"],
        "Paragraph_2": "Further explanation of the solution (string, MUST be a descriptive, non-empty paragraph)"
    },
    "Call to Action": {
        "Button_Text": "Text for the call to action button (string, MUST be a descriptive, non-empty button text)",
        "Subtext": "Optional subtext for the call to action (string, if provided, MUST be descriptive and non-empty)"
    }
}
All strings in the JSON must contain meaningful, non-empty content. Respond with ONLY the JSON object, ensuring it is valid and contains no extra text or markdown outside the JSON block.
"""
    elif content_type == "Pitch Slide Headlines":
        prompt = base_prompt + """
Generate 5-7 concise, compelling pitch slide headlines for an investor deck. Each headline should capture a key aspect of the product/solution in a way that resonates with the persona's problems and aspirations, and hints at market opportunity.

Respond with a JSON object in this exact format:
{
    "headlines": [
        "Headline 1 (string, MUST be non-empty and compelling)",
        "Headline 2 (string, MUST be non-empty and compelling)",
        "Headline 3 (string, MUST be non-empty and compelling)",
        "Headline 4 (string, MUST be non-empty and compelling)",
        "Headline 5 (string, MUST be non-empty and compelling)"
    ]
}
All strings in the list must be non-empty and descriptive. Ensure the response is valid JSON with no extra text or markdown outside the JSON block.
"""
    elif content_type == "Cold Email / Re-engagement Campaigns":
        prompt = base_prompt + """
Generate a short, personalized cold email (or re-engagement email) for this persona. Include a catchy subject line, a brief body that addresses a key pain point and offers a clear value proposition, and a call to action. Keep it under 100 words.

Respond with a JSON object in this exact format:
{
    "subject": "Your compelling subject line here (string, MUST be non-empty)",
    "body": "Your email body here. Can include multiple paragraphs separated by newlines. (string, MUST be non-empty)"
}
All strings in the JSON must contain meaningful, non-empty content. Ensure the response is valid JSON with no extra text or markdown outside the JSON block.
"""
    elif content_type == "Taglines / Hero Section Ideas":
        prompt = base_prompt + """
Generate 5-7 short, memorable taglines or hero section ideas for a website. These should instantly communicate the core value proposition and resonate with the persona's primary motivation or aspiration.

Respond with a JSON object in this exact format:
{
    "taglines": [
        "Tagline 1 (string, MUST be non-empty and memorable)",
        "Tagline 2 (string, MUST be non-empty and memorable)",
        "Tagline 3 (string, MUST be non-empty and memorable)",
        "Tagline 4 (string, MUST be non-empty and memorable)",
        "Tagline 5 (string, MUST be non-empty and memorable)"
    ]
}
All strings in the list must be non-empty and descriptive. Ensure the response is valid JSON with no extra text or markdown outside the JSON block.
"""
    elif content_type == "Social Post Hooks":
        prompt = base_prompt + """
Generate 3-5 engaging social media post hooks (for Twitter, LinkedIn, or Instagram). Each hook should be short, attention-grabbing, and designed to pique the persona's interest by addressing a pain point or aspiration. Include relevant emojis.

Respond with a JSON object in this exact format:
{
    "posts": [
        "Hook 1 including relevant emojis ✨ (string, MUST be non-empty)",
        "Hook 2 addressing a pain point 😬 (string, MUST be non-empty)",
        "Hook 3 with a call to action 👉 (string, MUST be non-empty)"
    ]
}
All strings in the list must be non-empty and descriptive. Ensure the response is valid JSON with no extra text or markdown outside the JSON block.
"""
    else:
        return "Invalid content type.", "<h2>Invalid content type.</h2>"

    raw_text = ""
    html_output = ""
    parsed_content = None
    error_message = None

    try:
        response = text_model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # --- Attempt JSON Parsing First (more robust) ---
        json_string = None
        parsed_content = None

        # Try finding JSON object or array using regex
        json_match = re.search(r'```json\n(.*)\n```', raw_text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
        else:
            # If no markdown code block, try finding the first { and last }
            start_index = raw_text.find('{')
            end_index = raw_text.rfind('}')
            # Also try finding the first [ and last ] for array responses
            start_array_index = raw_text.find('[')
            end_array_index = raw_text.rfind(']')

            if start_index != -1 and end_index != -1 and end_index > start_index:
                # Found a potential object
                json_string = raw_text[start_index : end_index + 1]
            elif start_array_index != -1 and end_array_index != -1 and end_array_index > start_array_index:
                # Found a potential array (might be the case for Social Hooks)
                json_string = raw_text[start_array_index : end_array_index + 1]
            else:
                # If no JSON structure found, raise error to go to fallback
                raise json.JSONDecodeError("No JSON structure found", raw_text, 0)

        # Attempt to load the identified JSON string
        if json_string:
            try:
                parsed_content = json.loads(json_string)
            except json.JSONDecodeError:
                # If direct load fails, try cleaning up common issues
                cleaned_json_string = re.sub(r',\s*}', '}', json_string)
                cleaned_json_string = re.sub(r',\s*\]', ']', cleaned_json_string)
                cleaned_json_string = re.sub(r'//.*', '', cleaned_json_string)
                
                try:
                    parsed_content = json.loads(cleaned_json_string)
                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse cleaned JSON: {e}")
                    raise e

        # --- Generate HTML based on content type and parsed JSON ---
        if content_type == "Landing Page Copy" and parsed_content:
            flat_content = {}

            # Hero Section
            hero = parsed_content.get('Hero', {})
            if isinstance(hero, dict):
                headline = hero.get('Headline', '').strip()
                sub_headline = hero.get('Sub-headline', '').strip()
                flat_content['Hero'] = f"{headline}\n{sub_headline}".strip()
            elif isinstance(hero, str):
                flat_content['Hero'] = hero.strip()

            # Problem Section
            problem = parsed_content.get('Problem', {})
            if isinstance(problem, dict):
                title = problem.get('Title', '').strip()
                paragraph = problem.get('Paragraph_1', '').strip()
                points = problem.get('Bullet_Points', [])
                
                problem_parts = []
                if title: problem_parts.append(title)
                if paragraph: problem_parts.append(paragraph)
                if points and isinstance(points, list):
                    cleaned_points = [f'- {p.strip()}' for p in points if isinstance(p, str) and p.strip()]
                    problem_parts.extend(cleaned_points)
                
                flat_content['Problem'] = "\n\n".join(problem_parts)
            elif isinstance(problem, str):
                flat_content['Problem'] = problem.strip()

            # Solution Section
            solution = parsed_content.get('Solution', {})
            if isinstance(solution, dict):
                title = solution.get('Title', '').strip()
                paragraph1 = solution.get('Paragraph_1', '').strip()
                features = solution.get('Features', [])
                paragraph2 = solution.get('Paragraph_2', '').strip()

                solution_parts = []
                if title: solution_parts.append(title)
                if paragraph1: solution_parts.append(paragraph1)
                if features and isinstance(features, list):
                    cleaned_features = [f'- {f.strip()}' for f in features if isinstance(f, str) and f.strip()]
                    solution_parts.extend(cleaned_features)
                if paragraph2: solution_parts.append(paragraph2)

                flat_content['Solution'] = "\n\n".join(solution_parts)
            elif isinstance(solution, str):
                flat_content['Solution'] = solution.strip()

            # Call to Action Section
            cta = parsed_content.get('Call to Action', {})
            if isinstance(cta, dict):
                button_text = cta.get('Button_Text', '').strip()
                subtext = cta.get('Subtext', '').strip()
                cta_parts = []
                if button_text: cta_parts.append(button_text)
                if subtext: cta_parts.append(subtext)
                flat_content['Call to Action'] = "\n".join(cta_parts)
            elif isinstance(cta, str):
                flat_content['Call to Action'] = cta.strip()

            # Check if we have any content
            if any(value.strip() for value in flat_content.values()):
                html_output = _create_landing_page_html(flat_content)
            else:
                st.warning(f"Parsed JSON for {content_type} but could not extract sufficient content. Displaying raw text.")
                html_output = f"<pre>{raw_text}</pre>"

        elif content_type == "Pitch Slide Headlines" and parsed_content:
            headlines = parsed_content.get('headlines', [])
            
            # Add check for valid list of strings
            if isinstance(headlines, list) and headlines and all(isinstance(h, str) and h.strip() for h in headlines):
                html_output = _create_pitch_slides_html(headlines)
            elif isinstance(headlines, list) and not all(isinstance(h, str) and h.strip() for h in headlines):
                 st.warning("Parsed JSON for Pitch Slide Headlines, but content list contains non-string or empty elements. Displaying raw text.")
                 html_output = f"<pre>{raw_text}</pre>"
            else:
                st.warning("No valid 'headlines' list found in the response. Displaying raw text.")
                html_output = f"<pre>{raw_text}</pre>"

        elif content_type == "Cold Email / Re-engagement Campaigns" and parsed_content:
            subject = parsed_content.get('subject', '')
            body = parsed_content.get('body', '')
            
            # Add checks for valid subject and body strings
            if isinstance(subject, str) and subject.strip() and isinstance(body, str) and body.strip():
                html_output = _create_email_html(subject, body)
            elif parsed_content is not None:
                 st.warning("Parsed JSON for Cold Email, but 'subject' or 'body' are missing or not strings. Displaying raw text.")
                 html_output = f"<pre>{raw_text}</pre>"
            else:
                st.warning("Could not find 'subject' or 'body' in the response. Displaying raw text.")
                html_output = f"<pre>{raw_text}</pre>"

        elif content_type == "Taglines / Hero Section Ideas" and parsed_content:
            taglines = parsed_content.get('taglines', [])
            
            # Add check for valid list of strings
            if isinstance(taglines, list) and taglines and all(isinstance(t, str) and t.strip() for t in taglines):
                html_output = """
                <style>
                .tagline-item {
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    transition: all 0.3s ease;
                }
                .tagline-item:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    background: linear-gradient(135deg, #e8f0fe 0%, #ffffff 100%);
                }
                /* Instagram Gradient on Hover */
                .tagline-item:hover {
                    background: linear-gradient(to right, #833ab4, #fd1d1d, #fcb045); /* Instagram colors */
                    color: white; /* Optional: change text color for better contrast */
                }
                </style>
                <div class="taglines-container">
                """
                for tagline in taglines:
                    html_output += f'<div class="tagline-item">{tagline}</div>'
                html_output += "</div>"
            elif isinstance(taglines, list) and not all(isinstance(t, str) and t.strip() for t in taglines):
                st.warning("Parsed JSON for Taglines, but content list contains non-string or empty elements. Displaying raw text.")
                html_output = f"<pre>{raw_text}</pre>"
            else:
                st.warning("No valid 'taglines' list found in the response. Displaying raw text.")
                html_output = f"<pre>{raw_text}</pre>"

        elif content_type == "Social Post Hooks" and parsed_content:
            posts = parsed_content.get('posts', [])
            
            # Add check for valid list of strings
            if isinstance(posts, list) and posts and all(isinstance(p, str) and p.strip() for p in posts):
                html_output = ""
                # Prepare list to hold posts with images
                posts_with_images = []
                for i, post_text in enumerate(posts):
                    platform = "twitter" if i % 3 == 0 else "linkedin" if i % 3 == 1 else "instagram"
                    image_base64 = None # Initialize image_base64
                    
                    # Only generate images for Instagram and LinkedIn
                    if platform in ["instagram", "linkedin"]:
                         # Create a prompt for the image based on the post text and persona
                         image_prompt = f"Create a compelling visual concept for a social media post designed for {platform.capitalize()} with the following message: '{post_text}'. The image should be highly relevant to the message content, visually striking, and aligned with the overall persona: {persona_data.get('summary', persona_data.get('archetype', 'customer'))}. Focus on capturing the feeling or key idea of the post."
                         try:
                              # Generate image
                              generated_image = generate_persona_image(image_prompt, api_key=api_key)
                              if generated_image:
                                  # Convert PIL Image to base64
                                  buffered = io.BytesIO()
                                  generated_image.save(buffered, format="PNG")
                                  image_base64 = base64.b64encode(buffered.getvalue()).decode()
                         except Exception as img_e:
                              st.warning(f"Could not generate image for post {i+1}: {img_e}")
                              image_base64 = None # Ensure it's None if generation fails

                    # Store post text and generated image (or None)
                    posts_with_images.append({'text': post_text, 'platform': platform, 'image_base64': image_base64})
                
                # Generate HTML using the posts with images
                for post_data in posts_with_images:
                     html_output += _create_social_post_html(post_data['text'], post_data['platform'], post_data['image_base64'])

            elif isinstance(posts, list) and not all(isinstance(p, str) and p.strip() for p in posts):
                 st.warning("Parsed JSON for Social Posts, but content list contains non-string or empty elements. Displaying raw text.")
                 html_output = f"<pre>{raw_text}</pre>"
            else:
                st.warning("No valid 'posts' list found in the response. Displaying raw text.")
                html_output = f"<pre>{raw_text}</pre>"

        else:
            st.warning(f"Could not parse content for {content_type}. Displaying raw text.")
            html_output = f"<pre>{raw_text}</pre>"

        return raw_text, html_output

    except Exception as e:
        error_msg = f"[Error generating content: {e}]"
        return error_msg, f"<p style='color: red;'>{error_msg}</p>"

# --- HTML Mockup Functions ---
def _create_landing_page_html(content_sections):
    """Generates HTML for a simplified landing page mockup with improved styling."""
    # Extract specific content for the hero section
    hero_content = content_sections.get('Hero', '')
    hero_parts = hero_content.split('\n', 1)
    headline = hero_parts[0] if hero_parts else ''
    sub_headline = hero_parts[1] if len(hero_parts) > 1 else ''

    # Extract and format Call to Action button text
    cta_content = content_sections.get('Call to Action', '')
    cta_parts = cta_content.split('\n')
    cta_text = cta_parts[0] if cta_parts else ''
    
    # Generate button text based on CTA content
    button_text = 'Get Started'  # Default text
    if cta_text:
        # Common action words to look for
        action_words = ['start', 'try', 'get', 'join', 'sign up', 'schedule', 'book', 'learn', 'discover', 'explore']
        cta_lower = cta_text.lower()
        
        # Find the first action word in the CTA
        for action in action_words:
            if action in cta_lower:
                # Extract the action and the next word or two
                start_idx = cta_lower.find(action)
                words = cta_text[start_idx:].split()
                if len(words) >= 2:
                    # Take the action word and the next word
                    button_text = ' '.join(words[:2]).capitalize()
                else:
                    button_text = words[0].capitalize()
                break

    html_content = f"""
    <div style="font-family: 'Google Sans', sans-serif; max-width: 700px; margin: 20px auto; padding: 30px; border: 1px solid #e0e0e0; border-radius: 12px; background-color: #fdfbf6; box-shadow: 0 6px 12px rgba(0,0,0,0.1); overflow-y: auto; max-height: 500px; color: #3C4043;">
        <div style="text-align: center; padding: 30px 0 40px; border-bottom: 1px solid #eee; margin-bottom: 30px;">
            <h1 style="color: #202124; font-size: 2.5em; font-weight: 700; margin-bottom: 10px; line-height: 1.2;">{headline}</h1>
            <p style="color: #5F6368; font-size: 1.1em; margin-top: 0;">{sub_headline}</p>
            <div style="margin-top: 30px;">
                 <button style="background-color: #202124; color: white; padding: 12px 25px; border: none; border-radius: 25px; cursor: pointer; font-size: 1.1em; font-weight: 500; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: background-color 0.3s ease;">&rarr; {button_text}</button>
            </div>
        </div>
        <div style="padding: 0 10px;">
    """
    # Exclude 'Hero' as it's handled separately
    for section_name, text in content_sections.items():
        if section_name != 'Hero' and text and text.strip(): # Only display if section is not Hero and has content after stripping
            # Convert bullet points to HTML list items
            if '-' in text:
                parts = text.split('\n')
                formatted_parts = []
                for part in parts:
                    if part.strip().startswith('-'):
                        formatted_parts.append(f"<li>{part.strip()[1:].strip()}</li>")
                    else:
                        formatted_parts.append(f"<p>{part}</p>")
                formatted_text = '\n'.join(formatted_parts)
                if any('<li>' in part for part in formatted_parts):
                    formatted_text = f"<ul style='list-style-type: none; padding-left: 0;'>{formatted_text}</ul>"
            else:
                formatted_text = f"<p>{text}</p>"

            html_content += f"""
            <div style="margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #f0f0f0;">
                <h3 style="color: #34A853; font-size: 1.5em; font-weight: 500; margin-bottom: 12px;">{section_name}</h3>
                <div style="color: #3C4043; line-height: 1.7; font-size: 1em; white-space: pre-wrap;">{formatted_text}</div>
            </div>
        """
    html_content += """
        </div>
    </div>
    """
    return html_content

def _create_pitch_slides_html(headlines):
    """Generates HTML for an interactive pitch slides carousel with enhanced styling."""
    # Define pastel color palettes for slides
    pastel_colors = [
        {
            'bg': 'linear-gradient(135deg, #FFE5E5 0%, #FFF0F0 100%)',  # Soft pink
            'accent': '#FF9999',
            'text': '#4A4A4A'
        },
        {
            'bg': 'linear-gradient(135deg, #E5F4FF 0%, #F0F9FF 100%)',  # Soft blue
            'accent': '#99CCFF',
            'text': '#4A4A4A'
        },
        {
            'bg': 'linear-gradient(135deg, #E5FFE5 0%, #F0FFF0 100%)',  # Soft green
            'accent': '#99FF99',
            'text': '#4A4A4A'
        },
        {
            'bg': 'linear-gradient(135deg, #FFE5F4 0%, #FFF0F9 100%)',  # Soft purple
            'accent': '#FF99CC',
            'text': '#4A4A4A'
        },
        {
            'bg': 'linear-gradient(135deg, #FFF4E5 0%, #FFF9F0 100%)',  # Soft orange
            'accent': '#FFCC99',
            'text': '#4A4A4A'
        },
        {
            'bg': 'linear-gradient(135deg, #F4E5FF 0%, #F9F0FF 100%)',  # Soft lavender
            'accent': '#CC99FF',
            'text': '#4A4A4A'
        },
        {
            'bg': 'linear-gradient(135deg, #E5FFF4 0%, #F0FFF9 100%)',  # Soft mint
            'accent': '#99FFCC',
            'text': '#4A4A4A'
        }
    ]

    slides_html = ""
    for i, headline in enumerate(headlines):
        # Get color scheme for this slide (cycle through colors if more slides than colors)
        color_scheme = pastel_colors[i % len(pastel_colors)]
        
        slides_html += f"""
        <div class="slide" style="display: {'block' if i == 0 else 'none'}; 
            width: 100%; 
            height: 400px; 
            background: {color_scheme['bg']};
            border: 1px solid #e0e0e0; 
            border-radius: 12px; 
            margin-bottom: 15px; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            text-align: center; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
            padding: 30px;
            position: relative;
            transition: opacity 0.3s ease;">
            
            <!-- Slide number indicator -->
            <div style="position: absolute; top: 15px; right: 15px; 
                background-color: {color_scheme['accent']}; 
                color: {color_scheme['text']}; 
                padding: 5px 12px; 
                border-radius: 15px; 
                font-size: 0.9em;
                font-weight: 500;">
                {i+1}/{len(headlines)}
            </div>
            
            <!-- Main content -->
            <div style="max-width: 80%; display: flex; flex-direction: column; align-items: center;">
                <h2 style="color: {color_scheme['text']}; 
                    font-size: 2em; 
                    line-height: 1.3; 
                    margin-bottom: 20px; 
                    font-weight: 600;
                    text-align: center;">
                    {headline}
                </h2>
                
                <!-- Decorative element -->
                <div style="width: 60px; 
                    height: 4px; 
                    background: {color_scheme['accent']}; 
                    margin: 20px auto; 
                    border-radius: 2px;">
                </div>
                
                <!-- Placeholder for supporting text -->
                <p style="color: {color_scheme['text']}; 
                    font-size: 1.1em; 
                    line-height: 1.5; 
                    margin-top: 20px;
                    text-align: center;
                    opacity: 0.8;">
                    Supporting text for this slide would go here
                </p>
            </div>
        </div>
        """
    
    navigation_html = """
    <div style="display: flex; justify-content: center; gap: 15px; margin: 20px 0;">
        <button onclick="prevSlide()" 
            style="background-color: #4285F4; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            ← Previous
        </button>
        <button onclick="nextSlide()" 
            style="background-color: #4285F4; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            Next →
        </button>
    </div>
    """
    
    javascript = """
    <script>
    let currentSlide = 0;
    const slides = document.getElementsByClassName('slide');
    
    function showSlide(n) {
        // Hide all slides
        for (let i = 0; i < slides.length; i++) {
            slides[i].style.display = 'none';
            slides[i].style.opacity = '0';
        }
        // Show the current slide with a fade effect
        slides[n].style.display = 'block';
        setTimeout(() => {
            slides[n].style.opacity = '1';
        }, 50);
    }
    
    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }
    
    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }

    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowRight') {
            nextSlide();
        } else if (e.key === 'ArrowLeft') {
            prevSlide();
        }
    });
    </script>
    """
    
    return f"""
    <div style="position: relative; max-width: 900px; margin: 0 auto;">
        <div style="overflow: hidden; border-radius: 12px; margin-bottom: 20px;">
            {slides_html}
        </div>
        {navigation_html}
        {javascript}
    </div>
    """

def _escape_js_literal(s):
    return s.replace('\\', '\\\\').replace("'", "\'").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r").replace("<", "\\u003C").replace(">", "\\u003E").replace("&", "\\u0026")

def _create_email_html(subject, body):
    """Generates HTML for a realistic email client mockup."""
    # Ensure subject and body are strings and handle None values
    subject = str(subject) if subject is not None else ''
    body = str(body) if body is not None else ''
    
    # Replace newlines with <br> tags for HTML display
    body_html = body.replace('\n', '<br>')

    html_content = """
    <div style="font-family: 'Google Sans', sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background-color: #f0f0f0; padding: 10px 20px; border-bottom: 1px solid #e0e0e0; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.2em; color: #5F6368; margin-right: 10px;">✉️</span>
                <span style="font-weight: 500; color: #3C4043;">New Message</span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="window.print()" style="background-color: #4285F4; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em;">Print</button>
            </div>
        </div>
        <div style="padding: 15px 20px; border-bottom: 1px solid #f0f0f0;">
            <p style="margin: 0; font-size: 0.9em; color: #70757A;">From: Your Company &lt;info@yourcompany.com&gt;</p>
            <p style="margin: 5px 0 0; font-size: 0.9em; color: #70757A;">To: Persona Name &lt;persona@example.com&gt;</p>
            <p style="margin: 5px 0 0; font-weight: bold; color: #3C4043;">Subject: {subject}</p>
        </div>
        <div style="padding: 20px; line-height: 1.6; color: #3C4043; font-size: 0.95em;">
            {body_html}
        </div>
    </div>
    """.format(subject=subject, body_html=body_html)
    return html_content

def _create_social_post_html(post_text, platform="twitter", image_base64=None):
    """Generates HTML for platform-specific social media post mockups, including an image for Instagram."""
    platform_icons = {
        "twitter": "🐦",
        "linkedin": "💼",
        "instagram": "📸"
    }
    platform_colors = {
        "twitter": "#1DA1F2",
        "linkedin": "#0077B5",
        "instagram": "#E1306C"
    }
    
    # Escape post_text for use in JavaScript before inserting into HTML
    post_content_escaped = _escape_js_literal(post_text)

    # Generate the dynamic filename in Python
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_filename = f'{platform}_post_{timestamp}.txt'

    # Determine image content: use provided base64 image or the original placeholder
    image_content = ""
    if image_base64:
        image_content = f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; height: 100%; object-fit: cover;" alt="Social post image">'
    else:
        image_content = "Image Placeholder (Instagram)"

    # --- Start building platform-specific HTML --- #
    html_content = ""

    if platform == "twitter":
        html_content = f"""
        <div style="font-family: 'Google Sans', sans-serif; max-width: 500px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="padding: 15px; display: flex; align-items: center; border-bottom: 1px solid #f0f0f0;">
                <img src="https://placehold.co/40x40/{platform_colors[platform].replace('#', '')}/ffffff?text=C" style="border-radius: 50%; margin-right: 10px;">
                <div>
                    <p style="margin: 0; font-weight: bold; color: #3C4043;">Your Company Name</p>
                    <p style="margin: 0; font-size: 0.8em; color: #70757A;">@YourCompany • Just now</p>
                </div>
                <div style="margin-left: auto;">
                    <span style="font-size: 1.5em;">{platform_icons[platform]}</span>
                </div>
            </div>
            <div style="padding: 15px; line-height: 1.5; color: #3C4043; font-size: 0.95em;">
                {post_content_escaped}
            </div>
            <div style="padding: 10px 15px; border-top: 1px solid #f0f0f0; display: flex; justify-content: space-around; font-size: 0.9em; color: #70757A;">
                <span>❤️ Like</span>
                <span>💬 Comment</span>
                <span>🔁 Share</span>
                <span>📊 Analytics</span>
            </div>
            <div style="padding: 10px 15px; background-color: #f8f9fa; border-top: 1px solid #e0e0e0; text-align: right;">
                <button onclick="exportPost('{_escape_js_literal(download_filename)}')" style="background-color: {platform_colors[platform]}; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em;">Export Post</button>
            </div>
        </div>
        <script>
        function exportPost(filename) {{
            const postContent = `{post_content_escaped}`;
            const blob = new Blob([postContent], {{ type: 'text/plain' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename; // Use the filename passed as an argument
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }}
        </script>
        """

    elif platform == "instagram":
        html_content = f"""
        <div style="font-family: 'Google Sans', sans-serif; max-width: 350px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="padding: 10px 15px; display: flex; align-items: center;">
                 <img src="https://placehold.co/32x32/{platform_colors[platform].replace('#', '')}/ffffff?text=C" style="border-radius: 50%; margin-right: 10px;">
                 <div>
                     <p style="margin: 0; font-weight: bold; color: #262626; font-size: 0.9em;">yourcompany</p>
                     <p style="margin: 0; font-size: 0.7em; color: #8e8e8e;">Location (Optional)</p>
                 </div>
                 <div style="margin-left: auto;">
                     <span style="font-size: 1.2em; color: #8e8e8e;">...</span>
                 </div>
            </div>
            <div style="width: 100%; height: 350px; background-color: #efefef; display: flex; justify-content: center; align-items: center; color: #8e8e8e;">
                {image_content}
            </div>
            <div style="padding: 10px 15px;">
                 <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                     <div style="font-size: 1.4em; color: #262626;">
                         ❤️ 💬 ✈️
                     </div>
                     <div style="font-size: 1.4em; color: #262626;">
                         🔖
                     </div>
                 </div>
                 <p style="margin: 0 0 5px 0; font-weight: bold; color: #262626; font-size: 0.9em;">X likes</p>
                 <p style="margin: 0 0 5px 0; color: #262626; font-size: 0.9em;">
                     <span style="font-weight: bold;">yourcompany</span> {post_content_escaped}
                 </p>
                 <p style="margin: 0; font-size: 0.8em; color: #8e8e8e;">View all X comments</p>
                 <p style="margin: 5px 0 0 0; font-size: 0.7em; color: #8e8e8e;">X MINUTES AGO</p>
            </div>
             <div style="padding: 10px 15px; background-color: #f8f8f8; border-top: 1px solid #efefef; display: flex; align-items: center;">
                 <span style="font-size: 1.2em; margin-right: 10px;">😊</span>
                 <input type="text" placeholder="Add a comment..." style="border: none; outline: none; flex-grow: 1; background: none; font-size: 0.9em;">
                 <button style="border: none; background: none; color: #3897f0; font-weight: bold; cursor: pointer; font-size: 0.9em;">Post</button>
             </div>
             <div style="padding: 10px 15px; background-color: #f8f9fa; border-top: 1px solid #e0e0e0; text-align: right;">
                 <button onclick="exportPost('{_escape_js_literal(download_filename)}')" style="background-color: {platform_colors[platform]}; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em;">Export Post</button>
             </div>
        </div>
        <script>
        function exportPost(filename) {{
            const postContent = `{post_content_escaped}`;
            const blob = new Blob([postContent], {{ type: 'text/plain' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename; // Use the filename passed as an argument
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }}
        </script>
        """

    elif platform == "linkedin":
         html_content = f"""
         <div style="font-family: 'Google Sans', sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden;">
             <div style="padding: 12px 15px; display: flex; align-items: center;">
                  <img src="https://placehold.co/48x48/{platform_colors[platform].replace('#', '')}/ffffff?text=C" style="border-radius: 50%; margin-right: 10px;">
                  <div>
                      <p style="margin: 0; font-weight: bold; color: #212121; font-size: 0.9em;">Your Company Name</p>
                      <p style="margin: 0; font-size: 0.8em; color: #666; font-weight: normal;">Your Company • Follow</p>
                      <p style="margin: 0; font-size: 0.7em; color: #666;">Xh • 🌐</p>
                  </div>
                  <div style="margin-left: auto;">
                      <span style="font-size: 1.2em; color: #666;">...</span>
                  </div>
             </div>
             <div style="padding: 0 15px 12px 15px; color: #333; font-size: 0.9em; line-height: 1.4;">
                 {post_content_escaped}
             </div>
             <!-- Optional: Add a placeholder for a link preview or image -->
             <div style="background-color: #f0f0f0; height: 150px; display: flex; justify-content: center; align-items: center; color: #666; font-size: 0.9em;">
                 Link Preview or Image Placeholder ({platform.capitalize()})
             </div>
             <div style="padding: 8px 15px; display: flex; justify-content: space-between; align-items: center; font-size: 0.8em; color: #666; border-bottom: 1px solid #eee;">
                 <span>X Likes</span>
                 <span>X Comments • X Reposts</span>
             </div>
             <div style="padding: 8px 0; display: flex; justify-content-around; text-align: center; color: #666;">
                 <div style="flex-grow: 1; cursor: pointer; padding: 8px 0; border-radius: 4px; transition: background-color 0.2s ease;">👍 Like</div>
                 <div style="flex-grow: 1; cursor: pointer; padding: 8px 0; border-radius: 4px; transition: background-color 0.2s ease;">💬 Comment</div>
                 <div style="flex-grow: 1; cursor: pointer; padding: 8px 0; border-radius: 4px; transition: background-color 0.2s ease;">🔁 Repost</div>
                 <div style="flex-grow: 1; cursor: pointer; padding: 8px 0; border-radius: 4px; transition: background-color 0.2s ease;">✈️ Send</div>
             </div>
             <div style="padding: 10px 15px; background-color: #f8f9fa; border-top: 1px solid #e0e0e0; text-align: right;">
                 <button onclick="exportPost('{_escape_js_literal(download_filename)}')" style="background-color: {platform_colors[platform]}; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em;">Export Post</button>
             </div>
         </div>
         <script>
         function exportPost(filename) {{
             const postContent = `{post_content_escaped}`;
             const blob = new Blob([postContent], {{ type: 'text/plain' }});
             const url = window.URL.createObjectURL(blob);
             const a = document.createElement('a');
             a.href = url;
             a.download = filename; // Use the filename passed as an argument
             document.body.appendChild(a);
             a.click();
             window.URL.revokeObjectURL(url);
             document.body.removeChild(a);
         }}
         </script>
         """

    else:
        # Fallback for unknown platforms (shouldn't happen with current logic)
        html_content = f"<div>Unknown platform: {platform}</div>"

    return html_content

def render(api_key):
    st.header("Generate Messaging from Persona 💬")
    st.markdown("""
    <div style='color: #5F6368; font-size: 0.95em; margin-bottom: 1em;'>
        Leverage your generated personas to instantly create compelling marketing and pitch content.
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.generated_personas:
        st.warning("Please generate at least one persona in the 'Persona Builder' tab first.")
    else:
        persona_names = [p.get('name', f"Persona {i+1}") for i, p in enumerate(st.session_state.generated_personas)]
        selected_persona_for_messaging_name = st.selectbox(
            "Select a persona to generate messaging for:",
            persona_names,
            index=st.session_state.selected_persona_index if st.session_state.selected_persona_index != -1 else 0,
            key="persona_messaging_selector_tab2"
        )
        selected_persona_for_messaging = st.session_state.generated_personas[persona_names.index(selected_persona_for_messaging_name)]

        st.markdown(f"---")
        st.subheader(f"Content for: {selected_persona_for_messaging.get('name', 'N/A')} ({selected_persona_for_messaging.get('archetype', 'N/A')})")

        content_types = [
            "Landing Page Copy",
            "Pitch Slide Headlines",
            "Cold Email / Re-engagement Campaigns",
            "Taglines / Hero Section Ideas",
            "Social Post Hooks"
        ]

        for i, content_type in enumerate(content_types):
            st.markdown(f"### {content_type} ➡️")
            if st.button(f"Generate {content_type}", key=f"generate_btn_tab2_{content_type.replace(' ', '_').lower()}", use_container_width=True):
                raw_text, html_output = _generate_content_for_persona(selected_persona_for_messaging, content_type, api_key)
                
                # Display the HTML preview
                st.markdown("#### Preview")
                st.components.v1.html(html_output, height=400, scrolling=True)
                
                # Display the raw text for copying
                st.markdown("#### Raw Text (for copying)")
                if content_type == "Landing Page Copy":
                    st.code(raw_text, language="json")
                else:
                    st.code(raw_text, language="text")
                
                # Add export options based on content type
                if content_type == "Pitch Slide Headlines":
                    st.download_button(
                        "Download as HTML",
                        html_output,
                        file_name="pitch_slides.html",
                        mime="text/html"
                    )
                elif content_type == "Cold Email / Re-engagement Campaigns":
                    st.download_button(
                        "Download as Text",
                        raw_text,
                        file_name="email.txt",
                        mime="text/plain"
                    )
                elif content_type == "Social Post Hooks":
                    st.download_button(
                        "Download as Text",
                        raw_text,
                        file_name="social_posts.txt",
                        mime="text/plain"
                    )
                
            st.markdown("---")

# Define the JavaScript download filename literal outside the main f-string
js_download_assignment = 'a.download = \'email_${datetime.now().strftime("%%Y%%m%%d_%%H%%M%%S")}.txt\''; 