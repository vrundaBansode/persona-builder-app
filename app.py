# import streamlit as st
# import google.generativeai as genai
# import os
# import json
# import io
# from PIL import Image # Pillow library for image handling
# from config import Config # Assuming config.py is in the same directory

# # --- Session State Initialization (Crucial for Streamlit Apps) ---
# # These variables persist across reruns of the Streamlit app
# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []
# if 'current_persona_chat_model' not in st.session_state:
#     st.session_state.current_persona_chat_model = None
# if 'current_persona_details' not in st.session_state:
#     st.session_state.current_persona_details = None
# if 'generated_personas' not in st.session_state:
#     st.session_state.generated_personas = []
# if 'selected_persona_index' not in st.session_state:
#     st.session_state.selected_persona_index = -1 # -1 means no persona selected
# if 'current_page' not in st.session_state:
#     st.session_state.current_page = "Persona Builder" # Default page

# # --- Configuration ---
# # Load API key from environment variable
# try:
#     GEMINI_API_KEY = Config.get_api_key("GEMINI_API_KEY")
#     if not GEMINI_API_KEY:
#         raise KeyError("GEMINI_API_KEY environment variable not set.")
#     genai.configure(api_key=GEMINI_API_KEY)
# except KeyError as e:
#     st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
#     st.stop() # Stop the app if API key is missing

# # Initialize Gemini Model
# # Using 'gemini-2.0-flash' for speed and multimodal capabilities.
# model = genai.GenerativeModel('gemini-2.0-flash')

# # --- Helper Functions for AI Interaction ---

# def parse_gemini_json_response(response_text):
#     """
#     Parses Gemini's text response, extracting JSON string if wrapped in markdown.
#     """
#     response_text = response_text.strip()
#     # Check if the response is wrapped in a markdown code block
#     if response_text.startswith("```json") and response_text.endswith("```"):
#         json_string = response_text[len("```json"): -len("```")].strip()
#     else:
#         json_string = response_text
#     return json.loads(json_string)

# def generate_persona_from_gemini(feedback_text, uploaded_image=None):
#     """
#     Calls Gemini API to generate a customer persona based on text and optional image.
#     """
#     st.info("Generating persona... this might take a moment.")
    
#     parts = []

#     # Add image part if provided
#     if uploaded_image:
#         image_bytes = uploaded_image.read()
#         parts.append({
#             "mime_type": uploaded_image.type,
#             "data": image_bytes
#         })

#     persona_prompt = f"""
#     As a highly skilled UX researcher and marketing strategist, your task is to synthesize a detailed customer persona based on the provided customer feedback (text) and any additional visual context (image, if provided). The image should inform the persona's context, environment, or aesthetic preferences.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona (e.g., "Sarah the Savvy Shopper").
#     - 'archetype': A concise, descriptive archetype (e.g., "The Budget-Conscious Student", "The Tech-Averse Senior").
#     - 'motivations': A list of 3-5 primary goals or what drives them.
#     - 'pain_points': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
#     - 'aspirations': A list of 2-3 things they hope to achieve or become.
#     - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service, integrating visual cues if an image was provided.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, highly informed by the overall persona attributes and the provided image.

#     Customer Feedback (Text):
#     \"\"\"
#     {feedback_text}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     parts.append({"text": persona_prompt})

#     try:
#         response = model.generate_content(parts)
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse Gemini's response as JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during Gemini API call: {e}")
#         st.warning("Please check your API key, network connection, or try simpler input.")
#         return None

# def analyze_scenario_with_persona(persona_data, scenario_description):
#     """
#     Asks Gemini to analyze a scenario from the perspective of the given persona.
#     """
#     persona_context = f"""
#     You are acting as the customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {', '.join(persona_data.get('motivations', []))}
#     Pain Points: {', '.join(persona_data.get('pain_points', []))}
#     Aspirations: {', '.join(persona_data.get('aspirations', []))}
#     Typical Scenario: {persona_data.get('typical_scenario', 'N/A')}
#     """

#     scenario_prompt = f"""
#     {persona_context}

#     Given this persona, please analyze the following scenario from their perspective and provide actionable insights. Respond in a strict JSON format with the following keys:
#     - 'initial_reaction': A short sentence describing their immediate feeling.
#     - 'key_considerations': A list of 3-5 factors they would weigh.
#     - 'potential_objections': A list of 2-4 specific problems or dislikes they might have.
#     - 'recommendations': A list of 2-4 concrete product, marketing, or UX recommendations to appeal to them.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
    
#     try:
#         response = model.generate_content([{"text": scenario_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse scenario analysis JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error analyzing scenario: {e}")
#         return None

# def generate_actionable_ideas(persona_data):
#     """
#     Asks Gemini to brainstorm product features and marketing angles for the persona.
#     """
#     persona_context = f"""
#     You are acting as a product and marketing expert, leveraging insights from the following customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {', '.join(persona_data.get('motivations', []))}
#     Pain Points: {', '.join(persona_data.get('pain_points', []))}
#     Aspirations: {', '.join(persona_data.get('aspirations', []))}
#     """

#     ideas_prompt = f"""
#     {persona_context}

#     Based on this persona's motivations, pain points, and aspirations, please suggest 3-5 specific product feature ideas and 3-5 compelling marketing message angles that would strongly appeal to them. Respond in a strict JSON format with the following keys:
#     - 'product_features': A list of product feature ideas.
#     - 'marketing_angles': A list of marketing message angles/slogans.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     try:
#         response = model.generate_content([{"text": ideas_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse ideas JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating ideas: {e}")
#         return None

# def generate_problem_solution_persona(problem_statement):
#     """
#     Generates a persona focused on a specific problem statement, including problem/solution fit.
#     """
#     st.info("Analyzing problem and synthesizing persona... This might take a moment.")
    
#     problem_persona_prompt = f"""
#     As a highly skilled product strategist and customer research expert, your task is to analyze the following problem statement and then synthesize a detailed customer persona that *primarily embodies this problem*, along with potential solution-fit insights.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona.
#     - 'archetype': A concise, descriptive archetype relevant to the problem.
#     - 'problem_description_from_persona_view': A 2-4 sentence description of the problem *from this persona's perspective*, including their current struggles and inefficiencies.
#     - 'current_solutions_and_their_flaws': A list of 2-3 ways they currently try to solve this problem, and why those solutions are inadequate.
#     - 'ideal_solution_expectations': A list of 2-3 key characteristics or outcomes they would expect from an ideal solution to this problem.
#     - 'motivations_related_to_problem': A list of 2-3 core motivations directly tied to solving this specific problem.
#     - 'pain_points_related_to_problem': A list of 2-3 acute pain points specifically caused by this problem.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, reflecting their struggle or their desire for a solution.

#     Problem Statement:
#     \"\"\"
#     {problem_statement}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = model.generate_content([{"text": problem_persona_prompt}])
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse problem-solution persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating problem-solution persona: {e}")
#         return None

# # --- Streamlit UI ---

# st.set_page_config(
#     layout="centered",
#     page_title="AI Persona & Insight Engine 🚀",
#     # Initial theme is determined by Streamlit settings/browser, users can toggle
#     # We ensure a wide layout for better content display
#     initial_sidebar_state="expanded" 
# )

# st.title("🚀 AI-Powered Product-Market Fit Engine")
# st.markdown("Instantly understand customer demands and accelerate your product development with AI-driven insights for early founders and small business owners.")

# # --- Sidebar Navigation ---
# st.sidebar.header("Explore Features")
# page_selection = st.sidebar.radio(
#     "Go to:",
#     ("Persona Builder", "Problem-Solution Fit"),
#     key="page_selection"
# )

# if page_selection == "Persona Builder":
#     st.session_state.current_page = "Persona Builder"
#     st.header("1. Build Customer Personas from Feedback")
#     st.markdown("Synthesize detailed customer personas from raw feedback and visual context.")

#     feedback_text = st.text_area(
#         "Paste raw customer feedback, survey responses, or interview snippets here:",
#         height=180,
#         placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'"
#     )

#     uploaded_image = st.file_uploader(
#         "Optionally upload an image representing the customer's environment or product usage:",
#         type=["jpg", "jpeg", "png"]
#     )

#     if uploaded_image:
#         st.image(uploaded_image, caption="Uploaded Customer Context Image", width=250)
#         st.success("Image uploaded successfully!")

#     st.header("2. Generate Persona")
#     if st.button("✨ Generate Persona", use_container_width=True):
#         if not feedback_text and not uploaded_image:
#             st.warning("Please provide either text feedback or an image (or both) to generate a persona.")
#         else:
#             with st.spinner("Generating persona with Gemini AI... This might take a moment."):
#                 persona = generate_persona_from_gemini(feedback_text, uploaded_image)

#             if persona:
#                 st.session_state.generated_personas.append(persona)
#                 st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
#                 st.session_state.current_persona_details = persona # Set the newly generated persona as current

#                 # Initialize a new chat session with the persona's context
#                 initial_chat_prompt = f"""
#                 You are now role-playing as the customer persona:
#                 Name: {persona.get('name', 'N/A')}
#                 Archetype: {persona.get('archetype', 'N/A')}
#                 Motivations: {', '.join(persona.get('motivations', []))}
#                 Pain Points: {', '.join(persona.get('pain_points', []))}
#                 Aspirations: {', '.join(persona.get('aspirations', []))}
#                 Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#                 When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#                 """
#                 st.session_state.current_persona_chat_model = model.start_chat(history=[
#                     {"role": "user", "parts": [initial_chat_prompt]},
#                     {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#                 ])
#                 st.session_state.chat_history = [] # Reset chat history for new persona

#                 st.rerun() # Rerun to display the persona and enable new sections

#     # --- Persona History Selector ---
#     if st.session_state.generated_personas:
#         st.sidebar.header("View Past Personas")
#         persona_names = [f"{p.get('name', 'Unnamed')} ({p.get('archetype', 'No Archetype')})" for p in st.session_state.generated_personas]
        
#         selected_name = st.sidebar.selectbox(
#             "Select a persona to view/interact with:",
#             options=persona_names,
#             index=st.session_state.selected_persona_index,
#             key="persona_selector"
#         )
        
#         # Update the selected persona if a different one is chosen from the selectbox
#         new_index = persona_names.index(selected_name)
#         if new_index != st.session_state.selected_persona_index:
#             st.session_state.selected_persona_index = new_index
#             st.session_state.current_persona_details = st.session_state.generated_personas[new_index]
#             st.session_state.chat_history = [] # Clear chat history when switching personas
            
#             # Re-initialize chat model for the selected persona
#             persona = st.session_state.current_persona_details
#             initial_chat_prompt = f"""
#             You are now role-playing as the customer persona:
#             Name: {persona.get('name', 'N/A')}
#             Archetype: {persona.get('archetype', 'N/A')}
#             Motivations: {', '.join(persona.get('motivations', []))}
#             Pain Points: {', '.join(persona.get('pain_points', []))}
#             Aspirations: {', '.join(persona.get('aspirations', []))}
#             Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#             When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#             """
#             st.session_state.current_persona_chat_model = model.start_chat(history=[
#                 {"role": "user", "parts": [initial_chat_prompt]},
#                 {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#             ])
#             st.experimental_rerun() # Rerun to update the main display and chat

#     # --- Display Current Persona Details and Features ---
#     if st.session_state.current_persona_details:
#         persona = st.session_state.current_persona_details # Use the currently selected/generated persona

#         st.header("3. Your Synthesized Customer Persona")
#         st.subheader(f"## {persona.get('name', 'N/A')} - *{persona.get('archetype', 'N/A')}*")
#         st.markdown("---")

#         col1, col2 = st.columns(2) # Create two columns for layout

#         with col1:
#             st.markdown("**Motivations:**")
#             for m in persona.get('motivations', []):
#                 st.markdown(f"- 💡 {m}") # Added emoji for visual flair
            
#             st.markdown("**Aspirations:**")
#             for a in persona.get('aspirations', []):
#                 st.markdown(f"- ✨ {a}") # Added emoji for visual flair

#         with col2:
#             st.markdown("**Pain Points:**")
#             for p in persona.get('pain_points', []):
#                 st.markdown(f"- 😤 {p}") # Added emoji for visual flair
            
#             if 'visual_avatar_description' in persona:
#                 st.markdown("**Visual Avatar Idea:**")
#                 st.code(persona['visual_avatar_description']) # Display as code for easy copy-paste to image generator
        
#         st.markdown("**Typical Scenario:**")
#         st.info(f"> {persona.get('typical_scenario', 'N/A')}")

#         st.markdown("---")
#         st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

#         # --- Scenario-Based Analysis ---
#         st.header(f"4. Analyze Scenarios from {persona.get('name', 'Persona')}'s Perspective")
        
#         scenario_description = st.text_area(
#             "Describe a scenario for the persona to analyze (e.g., 'Launching a new premium product that costs 20% more.'):",
#             height=100,
#             key="scenario_input"
#         )

#         if st.button("Analyze Scenario", key="analyze_scenario_btn", use_container_width=True):
#             if not scenario_description:
#                 st.warning("Please describe a scenario to analyze.")
#             else:
#                 with st.spinner("Analyzing scenario..."):
#                     scenario_analysis = analyze_scenario_with_persona(
#                         persona, # Use the current persona details
#                         scenario_description
#                     )
#                 if scenario_analysis:
#                     st.subheader("Scenario Analysis:")
#                     if 'initial_reaction' in scenario_analysis:
#                         st.markdown(f"**Initial Reaction:** {scenario_analysis['initial_reaction']}")
#                     if 'key_considerations' in scenario_analysis:
#                         st.markdown(f"**Key Considerations:**")
#                         for item in scenario_analysis['key_considerations']:
#                             st.markdown(f"- {item}")
#                     if 'potential_objections' in scenario_analysis:
#                         st.markdown(f"**Potential Objections:**")
#                         for item in scenario_analysis['potential_objections']:
#                             st.markdown(f"- {item}")
#                     if 'recommendations' in scenario_analysis:
#                         st.markdown(f"**Recommendations for Us:**")
#                         for item in scenario_analysis['recommendations']:
#                             st.markdown(f"- {item}")
#                     st.markdown("---")

#         # --- Actionable Insights & Feature Ideas ---
#         st.header(f"5. Generate Actionable Ideas for {persona.get('name', 'Persona')}")
        
#         if st.button("Brainstorm Ideas", key="brainstorm_ideas_btn", use_container_width=True):
#             with st.spinner("Brainstorming product and marketing ideas..."):
#                 actionable_ideas = generate_actionable_ideas(persona) # Use the current persona details
            
#             if actionable_ideas:
#                 st.subheader("Ideas for You:")
#                 if 'product_features' in actionable_ideas:
#                     st.markdown("**Product Feature Ideas:**")
#                     for item in actionable_ideas['product_features']:
#                         st.markdown(f"- 🛠️ {item}") # Added emoji
#                 if 'marketing_angles' in actionable_ideas:
#                     st.markdown(f"**Marketing Message Angles:**")
#                     for item in actionable_ideas['marketing_angles']:
#                         st.markdown(f"- 📢 {item}") # Added emoji
#                 st.markdown("---")

#         # --- Persona "Simulation" / Conversational Interaction ---
#         st.header(f"6. Chat with {persona.get('name', 'the Persona')}")
#         st.info("Ask questions like: 'How would you react to a new feature that costs more?' or 'What do you think about our new marketing campaign?'")

#         # Display chat messages from history
#         for message in st.session_state.chat_history:
#             avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         # Chat input
#         if prompt := st.chat_input("Ask the persona..."):
#             st.session_state.chat_history.append({"role": "user", "content": prompt})
#             with st.chat_message("user", avatar="🧑‍💻"):
#                 st.markdown(prompt)

#             try:
#                 # Send user's prompt to the persona chat model
#                 response = st.session_state.current_persona_chat_model.send_message(prompt)
                
#                 # Append model's response to chat history
#                 with st.chat_message("assistant", avatar="🤖"):
#                     st.markdown(response.text)
#                 st.session_state.chat_history.append({"role": "assistant", "content": response.text})
#             except Exception as e:
#                 st.error(f"Error during chat with persona: {e}")
#                 st.warning("The persona might be experiencing a momentary lapse in character. Please try again.")

# elif page_selection == "Problem-Solution Fit":
#     st.session_state.current_page = "Problem-Solution Fit"
#     st.header("⚡ Discover Problem-Solution Fit with AI")
#     st.markdown("Start with a problem, and let AI reveal the ideal customer persona and key insights for your solution.")

#     problem_input = st.text_area(
#         "Describe a core problem you're trying to solve:",
#         height=150,
#         placeholder="e.g., 'Small businesses struggle to manage their inventory efficiently across multiple sales channels.'"
#     )

#     if st.button("Uncover Problem-Solution Persona", use_container_width=True):
#         if not problem_input:
#             st.warning("Please describe a problem to analyze.")
#         else:
#             with st.spinner("Analyzing problem and synthesizing solution-oriented persona..."):
#                 problem_persona = generate_problem_solution_persona(problem_input)
            
#             if problem_persona:
#                 st.subheader("💡 Your Problem-Solution Persona:")
#                 st.subheader(f"## {problem_persona.get('name', 'N/A')} - *{problem_persona.get('archetype', 'N/A')}*")
#                 st.markdown("---")

#                 st.markdown("**The Problem from Their View:**")
#                 st.info(f"> {problem_persona.get('problem_description_from_persona_view', 'N/A')}")

#                 st.markdown("**Current Solutions & Their Flaws:**")
#                 for item in problem_persona.get('current_solutions_and_their_flaws', []):
#                     st.markdown(f"- ❌ {item}")
                
#                 st.markdown("**Ideal Solution Expectations:**")
#                 for item in problem_persona.get('ideal_solution_expectations', []):
#                     st.markdown(f"- ✅ {item}")

#                 st.markdown("**Motivations (Problem-Related):**")
#                 for item in problem_persona.get('motivations_related_to_problem', []):
#                     st.markdown(f"- 🎯 {item}")

#                 st.markdown("**Pain Points (Problem-Related):**")
#                 for item in problem_persona.get('pain_points_related_to_problem', []):
#                     st.markdown(f"- 😖 {item}")
                
#                 if 'visual_avatar_description' in problem_persona:
#                     st.markdown("**Visual Avatar Idea:**")
#                     st.code(problem_persona['visual_avatar_description'])

#                 st.markdown("---")
#                 st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

# # --- Sidebar for Instructions and Notes ---
# st.sidebar.markdown("---")
# st.sidebar.header("How to Use This App")
# st.sidebar.markdown("""
# 1.  **Select a Feature:** Use the radio buttons above to navigate between "Persona Builder" and "Problem-Solution Fit."
# 2.  **Persona Builder:**
#     * Provide customer feedback (text) and optionally an image.
#     * Generate a detailed persona.
#     * Interact with the persona: chat, analyze scenarios, brainstorm ideas.
#     * Switch between generated personas from the "View Past Personas" dropdown.
# 3.  **Problem-Solution Fit (NEW!):**
#     * Describe a core problem you're trying to solve.
#     * Generate a persona specifically focused on that problem, revealing key insights for solution development.
# """)

# st.sidebar.header("Project Notes")
# st.sidebar.markdown("""
# * **AI Model:** Powered by Google Gemini (`gemini-2.0-flash`).
# * **Framework:** Built with Streamlit for rapid prototyping and interactive UI.
# * **API Key Security:** Your `GEMINI_API_KEY` is loaded from environment variables.
# * **Persistence:** Personas are currently stored in memory for the current session. Firebase Firestore integration is a future step for long-term storage across sessions.
# * **UI/UX:** Designed for clarity and ease of use, leveraging Streamlit's native features. Streamlit supports light/dark themes, which can be toggled via your browser/Streamlit settings.
# """)

# import streamlit as st
# import google.generativeai as genai
# import os
# import json
# import io
# from PIL import Image # Pillow library for image handling
# from config import Config # Assuming config.py is in the same directory

# # --- Session State Initialization (Crucial for Streamlit Apps) ---
# # These variables persist across reruns of the Streamlit app
# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []
# if 'current_persona_chat_model' not in st.session_state:
#     st.session_state.current_persona_chat_model = None
# if 'current_persona_details' not in st.session_state:
#     st.session_state.current_persona_details = None
# if 'generated_personas' not in st.session_state:
#     st.session_state.generated_personas = []
# if 'selected_persona_index' not in st.session_state:
#     st.session_state.selected_persona_index = -1 # -1 means no persona selected
# if 'current_page' not in st.session_state:
#     st.session_state.current_page = "Persona Builder" # Default page

# # --- Configuration ---
# # Load API key from environment variable
# try:
#     GEMINI_API_KEY = Config.get_api_key("GEMINI_API_KEY")
#     if not GEMINI_API_KEY:
#         raise KeyError("GEMINI_API_KEY environment variable not set.")
#     genai.configure(api_key=GEMINI_API_KEY)
# except KeyError as e:
#     st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
#     st.stop() # Stop the app if API key is missing

# # Initialize Gemini Model
# # Using 'gemini-2.0-flash' for speed and multimodal capabilities.
# model = genai.GenerativeModel('gemini-2.0-flash')

# # --- Helper Functions for AI Interaction ---

# def parse_gemini_json_response(response_text):
#     """
#     Parses Gemini's text response, extracting JSON string if wrapped in markdown.
#     """
#     response_text = response_text.strip()
#     # Check if the response is wrapped in a markdown code block
#     if response_text.startswith("```json") and response_text.endswith("```"):
#         json_string = response_text[len("```json"): -len("```")].strip()
#     else:
#         json_string = response_text
#     return json.loads(json_string)

# def generate_persona_from_gemini(feedback_text, uploaded_image=None):
#     """
#     Calls Gemini API to generate a customer persona based on text and optional image.
#     """
#     st.info("Generating persona... this might take a moment.")
    
#     parts = []

#     # Add image part if provided
#     if uploaded_image:
#         image_bytes = uploaded_image.read()
#         parts.append({
#             "mime_type": uploaded_image.type,
#             "data": image_bytes
#         })

#     persona_prompt = f"""
#     As a highly skilled UX researcher and marketing strategist, your task is to synthesize a detailed customer persona based on the provided customer feedback (text) and any additional visual context (image, if provided). The image should inform the persona's context, environment, or aesthetic preferences.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona (e.g., "Sarah the Savvy Shopper").
#     - 'archetype': A concise, descriptive archetype (e.g., "The Budget-Conscious Student", "The Tech-Averse Senior").
#     - 'motivations': A list of 3-5 primary goals or what drives them.
#     - 'pain_points': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
#     - 'aspirations': A list of 2-3 things they hope to achieve or become.
#     - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service, integrating visual cues if an image was provided.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, highly informed by the overall persona attributes and the provided image.

#     Customer Feedback (Text):
#     \"\"\"
#     {feedback_text}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     parts.append({"text": persona_prompt})

#     try:
#         response = model.generate_content(parts)
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse Gemini's response as JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during Gemini API call: {e}")
#         st.warning("Please check your API key, network connection, or try simpler input.")
#         return None

# def analyze_scenario_with_persona(persona_data, scenario_description):
#     """
#     Asks Gemini to analyze a scenario from the perspective of the given persona.
#     """
#     persona_context = f"""
#     You are acting as the customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {', '.join(persona_data.get('motivations', []))}
#     Pain Points: {', '.join(persona_data.get('pain_points', []))}
#     Aspirations: {', '.join(persona_data.get('aspirations', []))}
#     Typical Scenario: {persona_data.get('typical_scenario', 'N/A')}
#     """

#     scenario_prompt = f"""
#     {persona_context}

#     Given this persona, please analyze the following scenario from their perspective and provide actionable insights. Respond in a strict JSON format with the following keys:
#     - 'initial_reaction': A short sentence describing their immediate feeling.
#     - 'key_considerations': A list of 3-5 factors they would weigh.
#     - 'potential_objections': A list of 2-4 specific problems or dislikes they might have.
#     - 'recommendations': A list of 2-4 concrete product, marketing, or UX recommendations to appeal to them.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
    
#     try:
#         response = model.generate_content([{"text": scenario_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse scenario analysis JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error analyzing scenario: {e}")
#         return None

# def generate_actionable_ideas(persona_data):
#     """
#     Asks Gemini to brainstorm product features and marketing angles for the persona.
#     """
#     persona_context = f"""
#     You are acting as a product and marketing expert, leveraging insights from the following customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {', '.join(persona_data.get('motivations', []))}
#     Pain Points: {', '.join(persona_data.get('pain_points', []))}
#     Aspirations: {', '.join(persona_data.get('aspirations', []))}
#     """

#     ideas_prompt = f"""
#     {persona_context}

#     Based on this persona's motivations, pain points, and aspirations, please suggest 3-5 specific product feature ideas and 3-5 compelling marketing message angles that would strongly appeal to them. Respond in a strict JSON format with the following keys:
#     - 'product_features': A list of product feature ideas.
#     - 'marketing_angles': A list of marketing message angles/slogans.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     try:
#         response = model.generate_content([{"text": ideas_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse ideas JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating ideas: {e}")
#         return None

# def generate_problem_solution_persona(problem_statement):
#     """
#     Generates a persona focused on a specific problem statement, including problem/solution fit.
#     """
#     st.info("Analyzing problem and synthesizing persona... This might take a moment.")
    
#     problem_persona_prompt = f"""
#     As a highly skilled product strategist and customer research expert, your task is to analyze the following problem statement and then synthesize a detailed customer persona that *primarily embodies this problem*, along with potential solution-fit insights.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona.
#     - 'archetype': A concise, descriptive archetype relevant to the problem.
#     - 'problem_description_from_persona_view': A 2-4 sentence description of the problem *from this persona's perspective*, including their current struggles and inefficiencies.
#     - 'current_solutions_and_their_flaws': A list of 2-3 ways they currently try to solve this problem, and why those solutions are inadequate.
#     - 'ideal_solution_expectations': A list of 2-3 key characteristics or outcomes they would expect from an ideal solution to this problem.
#     - 'motivations_related_to_problem': A list of 2-3 core motivations directly tied to solving this specific problem.
#     - 'pain_points_related_to_problem': A list of 2-3 acute pain points specifically caused by this problem.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, reflecting their struggle or their desire for a solution.

#     Problem Statement:
#     \"\"\"
#     {problem_statement}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = model.generate_content([{"text": problem_persona_prompt}])
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse problem-solution persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating problem-solution persona: {e}")
#         return None

# def generate_anti_persona_and_opportunity_cost(product_description):
#     """
#     Generates anti-personas and identifies opportunity costs based on a product description.
#     """
#     st.info("Analyzing product and identifying anti-personas/opportunity costs... This might take a moment.")

#     anti_persona_prompt = f"""
#     As a highly strategic market analyst and product de-risking expert, your task is to analyze the following product description. Based on this product, identify 1-2 "Anti-Personas" – profiles of users who would *actively dislike, reject, or churn from this product*, and explain *why*. Additionally, identify 1-2 "Opportunity Costs" – potential market segments or product features that might be neglected by focusing solely on this product's current direction.

#     Return the response in a strict JSON format with the following keys:
#     - 'anti_personas': A list of objects, each with:
#         - 'name': A creative name for the anti-persona (e.g., "The Feature Overwhelmed User").
#         - 'reason_for_dislike': A 2-3 sentence explanation of why this persona would reject or churn from the product.
#         - 'key_traits_that_clash': A list of 2-3 traits that make them incompatible with the product.
#     - 'opportunity_costs': A list of objects, each with:
#         - 'area_neglected': A brief description of the market segment or feature area being overlooked.
#         - 'potential_value_missed': A 1-2 sentence explanation of the value or revenue potential being missed.

#     Product Description:
#     \"\"\"
#     {product_description}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = model.generate_content([{"text": anti_persona_prompt}])
#         anti_persona_data = parse_gemini_json_response(response.text)
#         return anti_persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse anti-persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating anti-persona: {e}")
#         return None


# # --- Streamlit UI ---

# st.set_page_config(
#     layout="centered",
#     page_title="AI Persona & Insight Engine 🚀",
#     # Initial theme is determined by Streamlit settings/browser, users can toggle
#     initial_sidebar_state="expanded" 
# )

# st.title("🚀 AI-Powered Product-Market Fit Engine")
# st.markdown("Instantly understand customer demands and accelerate your product development with AI-driven insights for early founders and small business owners.")

# # --- Sidebar Navigation ---
# st.sidebar.header("Explore Features")
# page_selection = st.sidebar.radio(
#     "Go to:",
#     ("Persona Builder", "Problem-Solution Fit", "Anti-Persona Engine"),
#     key="page_selection"
# )

# if page_selection == "Persona Builder":
#     st.session_state.current_page = "Persona Builder"
#     st.header("1. Build Customer Personas from Feedback")
#     st.markdown("Synthesize detailed customer personas from raw feedback and visual context.")

#     feedback_text = st.text_area(
#         "Paste raw customer feedback, survey responses, or interview snippets here:",
#         height=180,
#         placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'"
#     )

#     uploaded_image = st.file_uploader(
#         "Optionally upload an image representing the customer's environment or product usage:",
#         type=["jpg", "jpeg", "png"]
#     )

#     if uploaded_image:
#         st.image(uploaded_image, caption="Uploaded Customer Context Image", width=250)
#         st.success("Image uploaded successfully!")

#     st.header("2. Generate Persona")
#     if st.button("✨ Generate Persona", use_container_width=True):
#         if not feedback_text and not uploaded_image:
#             st.warning("Please provide either text feedback or an image (or both) to generate a persona.")
#         else:
#             with st.spinner("Generating persona with Gemini AI... This might take a moment."):
#                 persona = generate_persona_from_gemini(feedback_text, uploaded_image)

#             if persona:
#                 st.session_state.generated_personas.append(persona)
#                 st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
#                 st.session_state.current_persona_details = persona # Set the newly generated persona as current

#                 # Initialize a new chat session with the persona's context
#                 initial_chat_prompt = f"""
#                 You are now role-playing as the customer persona:
#                 Name: {persona.get('name', 'N/A')}
#                 Archetype: {persona.get('archetype', 'N/A')}
#                 Motivations: {', '.join(persona.get('motivations', []))}
#                 Pain Points: {', '.join(persona.get('pain_points', []))}
#                 Aspirations: {', '.join(persona.get('aspirations', []))}
#                 Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#                 When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#                 """
#                 st.session_state.current_persona_chat_model = model.start_chat(history=[
#                     {"role": "user", "parts": [initial_chat_prompt]},
#                     {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#                 ])
#                 st.session_state.chat_history = [] # Reset chat history for new persona

#                 st.rerun() # Rerun to display the persona and enable new sections

#     # --- Persona History Selector ---
#     if st.session_state.generated_personas:
#         st.sidebar.header("View Past Personas")
#         persona_names = [f"{p.get('name', 'Unnamed')} ({p.get('archetype', 'No Archetype')})" for p in st.session_state.generated_personas]
        
#         selected_name = st.sidebar.selectbox(
#             "Select a persona to view/interact with:",
#             options=persona_names,
#             index=st.session_state.selected_persona_index,
#             key="persona_selector"
#         )
        
#         # Update the selected persona if a different one is chosen from the selectbox
#         new_index = persona_names.index(selected_name)
#         if new_index != st.session_state.selected_persona_index:
#             st.session_state.selected_persona_index = new_index
#             st.session_state.current_persona_details = st.session_state.generated_personas[new_index]
#             st.session_state.chat_history = [] # Clear chat history when switching personas
            
#             # Re-initialize chat model for the selected persona
#             persona = st.session_state.current_persona_details
#             initial_chat_prompt = f"""
#             You are now role-playing as the customer persona:
#             Name: {persona.get('name', 'N/A')}
#             Archetype: {persona.get('archetype', 'N/A')}
#             Motivations: {', '.join(persona.get('motivations', []))}
#             Pain Points: {', '.join(persona.get('pain_points', []))}
#             Aspirations: {', '.join(persona.get('aspirations', []))}
#             Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#             When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#             """
#             st.session_state.current_persona_chat_model = model.start_chat(history=[
#                 {"role": "user", "parts": [initial_chat_prompt]},
#                 {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#             ])
#             st.experimental_rerun() # Rerun to update the main display and chat

#     # --- Display Current Persona Details and Features ---
#     if st.session_state.current_persona_details:
#         persona = st.session_state.current_persona_details # Use the currently selected/generated persona

#         st.header("3. Your Synthesized Customer Persona")
#         st.subheader(f"## {persona.get('name', 'N/A')} - *{persona.get('archetype', 'N/A')}*")
#         st.markdown("---")

#         col1, col2 = st.columns(2) # Create two columns for layout

#         with col1:
#             st.markdown("**Motivations:**")
#             for m in persona.get('motivations', []):
#                 st.markdown(f"- 💡 {m}") # Added emoji for visual flair
            
#             st.markdown("**Aspirations:**")
#             for a in persona.get('aspirations', []):
#                 st.markdown(f"- ✨ {a}") # Added emoji for visual flair

#         with col2:
#             st.markdown("**Pain Points:**")
#             for p in persona.get('pain_points', []):
#                 st.markdown(f"- 😤 {p}") # Added emoji for visual flair
            
#             if 'visual_avatar_description' in persona:
#                 st.markdown("**Visual Avatar Idea:**")
#                 st.code(persona['visual_avatar_description']) # Display as code for easy copy-paste to image generator
        
#         st.markdown("**Typical Scenario:**")
#         st.info(f"> {persona.get('typical_scenario', 'N/A')}")

#         st.markdown("---")
#         st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

#         # --- Scenario-Based Analysis ---
#         st.header(f"4. Analyze Scenarios from {persona.get('name', 'Persona')}'s Perspective")
        
#         scenario_description = st.text_area(
#             "Describe a scenario for the persona to analyze (e.g., 'Launching a new premium product that costs 20% more.'):",
#             height=100,
#             key="scenario_input"
#         )

#         if st.button("Analyze Scenario", key="analyze_scenario_btn", use_container_width=True):
#             if not scenario_description:
#                 st.warning("Please describe a scenario to analyze.")
#             else:
#                 with st.spinner("Analyzing scenario..."):
#                     scenario_analysis = analyze_scenario_with_persona(
#                         persona, # Use the current persona details
#                         scenario_description
#                     )
#                 if scenario_analysis:
#                     st.subheader("Scenario Analysis:")
#                     if 'initial_reaction' in scenario_analysis:
#                         st.markdown(f"**Initial Reaction:** {scenario_analysis['initial_reaction']}")
#                     if 'key_considerations' in scenario_analysis:
#                         st.markdown(f"**Key Considerations:**")
#                         for item in scenario_analysis['key_considerations']:
#                             st.markdown(f"- {item}")
#                     if 'potential_objections' in scenario_analysis:
#                         st.markdown(f"**Potential Objections:**")
#                         for item in scenario_analysis['potential_objections']:
#                             st.markdown(f"- {item}")
#                     if 'recommendations' in scenario_analysis:
#                         st.markdown(f"**Recommendations for Us:**")
#                         for item in scenario_analysis['recommendations']:
#                             st.markdown(f"- {item}")
#                     st.markdown("---")

#         # --- Actionable Insights & Feature Ideas ---
#         st.header(f"5. Generate Actionable Ideas for {persona.get('name', 'Persona')}")
        
#         if st.button("Brainstorm Ideas", key="brainstorm_ideas_btn", use_container_width=True):
#             with st.spinner("Brainstorming product and marketing ideas..."):
#                 actionable_ideas = generate_actionable_ideas(persona) # Use the current persona details
            
#             if actionable_ideas:
#                 st.subheader("Ideas for You:")
#                 if 'product_features' in actionable_ideas:
#                     st.markdown("**Product Feature Ideas:**")
#                     for item in actionable_ideas['product_features']:
#                         st.markdown(f"- 🛠️ {item}") # Added emoji
#                 if 'marketing_angles' in actionable_ideas:
#                     st.markdown(f"**Marketing Message Angles:**")
#                     for item in actionable_ideas['marketing_angles']:
#                         st.markdown(f"- 📢 {item}") # Added emoji
#                 st.markdown("---")

#         # --- Persona "Simulation" / Conversational Interaction ---
#         st.header(f"6. Chat with {persona.get('name', 'the Persona')}")
#         st.info("Ask questions like: 'How would you react to a new feature that costs more?' or 'What do you think about our new marketing campaign?'")

#         # Display chat messages from history
#         for message in st.session_state.chat_history:
#             avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         # Chat input
#         if prompt := st.chat_input("Ask the persona..."):
#             st.session_state.chat_history.append({"role": "user", "content": prompt})
#             with st.chat_message("user", avatar="🧑‍💻"):
#                 st.markdown(prompt)

#             try:
#                 # Send user's prompt to the persona chat model
#                 response = st.session_state.current_persona_chat_model.send_message(prompt)
                
#                 # Append model's response to chat history
#                 with st.chat_message("assistant", avatar="🤖"):
#                     st.markdown(response.text)
#                 st.session_state.chat_history.append({"role": "assistant", "content": response.text})
#             except Exception as e:
#                 st.error(f"Error during chat with persona: {e}")
#                 st.warning("The persona might be experiencing a momentary lapse in character. Please try again.")

# elif page_selection == "Problem-Solution Fit":
#     st.session_state.current_page = "Problem-Solution Fit"
#     st.header("⚡ Discover Problem-Solution Fit with AI")
#     st.markdown("Start with a problem, and let AI reveal the ideal customer persona and key insights for your solution.")

#     problem_input = st.text_area(
#         "Describe a core problem you're trying to solve:",
#         height=150,
#         placeholder="e.g., 'Small businesses struggle to manage their inventory efficiently across multiple sales channels.'"
#     )

#     if st.button("Uncover Problem-Solution Persona", use_container_width=True):
#         if not problem_input:
#             st.warning("Please describe a problem to analyze.")
#         else:
#             with st.spinner("Analyzing problem and synthesizing solution-oriented persona..."):
#                 problem_persona = generate_problem_solution_persona(problem_input)
            
#             if problem_persona:
#                 st.subheader("💡 Your Problem-Solution Persona:")
#                 st.subheader(f"## {problem_persona.get('name', 'N/A')} - *{problem_persona.get('archetype', 'N/A')}*")
#                 st.markdown("---")

#                 st.markdown("**The Problem from Their View:**")
#                 st.info(f"> {problem_persona.get('problem_description_from_persona_view', 'N/A')}")

#                 st.markdown("**Current Solutions & Their Flaws:**")
#                 for item in problem_persona.get('current_solutions_and_their_flaws', []):
#                     st.markdown(f"- ❌ {item}")
                
#                 st.markdown("**Ideal Solution Expectations:**")
#                 for item in problem_persona.get('ideal_solution_expectations', []):
#                     st.markdown(f"- ✅ {item}")

#                 st.markdown("**Motivations (Problem-Related):**")
#                 for item in problem_persona.get('motivations_related_to_problem', []):
#                     st.markdown(f"- 🎯 {item}")

#                 st.markdown("**Pain Points (Problem-Related):**")
#                 for item in problem_persona.get('pain_points_related_to_problem', []):
#                     st.markdown(f"- 😖 {item}")
                
#                 if 'visual_avatar_description' in problem_persona:
#                     st.markdown("**Visual Avatar Idea:**")
#                     st.code(problem_persona['visual_avatar_description'])

#                 st.markdown("---")
#                 st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

# elif page_selection == "Anti-Persona Engine":
#     st.session_state.current_page = "Anti-Persona Engine"
#     st.header("🚫 Identify Anti-Personas & Opportunity Costs")
#     st.markdown("Understand who your product is *not* for, and discover potential missed market opportunities.")

#     product_description_input = st.text_area(
#         "Describe your product or service:",
#         height=150,
#         placeholder="e.g., 'A mobile app for busy professionals to manage personal finances with AI-driven budgeting and investment advice.'"
#     )

#     if st.button("Uncover Anti-Personas & Opportunities", use_container_width=True):
#         if not product_description_input:
#             st.warning("Please describe your product to analyze.")
#         else:
#             with st.spinner("Analyzing product and identifying anti-personas/opportunity costs..."):
#                 anti_persona_insights = generate_anti_persona_and_opportunity_cost(product_description_input)
            
#             if anti_persona_insights:
#                 st.subheader("👻 Anti-Personas (Who Your Product is NOT For):")
#                 if 'anti_personas' in anti_persona_insights and anti_persona_insights['anti_personas']:
#                     for i, anti_p in enumerate(anti_persona_insights['anti_personas']):
#                         st.markdown(f"**Anti-Persona {i+1}: {anti_p.get('name', 'Unnamed Anti-Persona')}**")
#                         st.markdown(f"**Reason for Dislike:** {anti_p.get('reason_for_dislike', 'N/A')}")
#                         st.markdown(f"**Key Traits that Clash:**")
#                         for trait in anti_p.get('key_traits_that_clash', []):
#                             st.markdown(f"- ⛔ {trait}")
#                         st.markdown("---")
#                 else:
#                     st.info("No specific anti-personas identified at this time.")

#                 st.subheader("🔭 Opportunity Costs (What You Might Be Missing):")
#                 if 'opportunity_costs' in anti_persona_insights and anti_persona_insights['opportunity_costs']:
#                     for i, opp_cost in enumerate(anti_persona_insights['opportunity_costs']):
#                         st.markdown(f"**Opportunity {i+1}: {opp_cost.get('area_neglected', 'N/A')}**")
#                         st.markdown(f"**Potential Value Missed:** {opp_cost.get('potential_value_missed', 'N/A')}")
#                         st.markdown("---")
#                 else:
#                     st.info("No specific opportunity costs identified at this time.")

#                 st.caption("Insights generated by Google Gemini AI. Always review for accuracy and potential biases.")


# # --- Sidebar for Instructions and Notes ---
# st.sidebar.markdown("---")
# st.sidebar.header("How to Use This App")
# st.sidebar.markdown("""
# 1.  **Select a Feature:** Use the radio buttons above to navigate between "Persona Builder", "Problem-Solution Fit", and "Anti-Persona Engine".
# 2.  **Persona Builder:**
#     * Provide customer feedback (text) and optionally an image.
#     * Generate a detailed persona.
#     * Interact with the persona: chat, analyze scenarios, brainstorm ideas.
#     * Switch between generated personas from the "View Past Personas" dropdown.
# 3.  **Problem-Solution Fit:**
#     * Describe a core problem you're trying to solve.
#     * Generate a persona specifically focused on that problem, revealing key insights for solution development.
# 4.  **Anti-Persona Engine (NEW!):**
#     * Describe your product or service.
#     * Identify "anti-personas" (users who won't like your product) and "opportunity costs" (missed market segments/features).
# """)

# st.sidebar.header("Project Notes")
# st.sidebar.markdown("""
# * **AI Model:** Powered by Google Gemini (`gemini-2.0-flash`).
# * **Framework:** Built with Streamlit for rapid prototyping and interactive UI.
# * **API Key Security:** Your `GEMINI_API_KEY` is loaded from environment variables.
# * **Persistence:** Personas are currently stored in memory for the current session. Firebase Firestore integration is a future step for long-term storage across sessions.
# * **UI/UX:** Designed for clarity and ease of use, leveraging Streamlit's native features. Streamlit supports light/dark themes, which can be toggled via your browser/Streamlit settings.
# """)


# import streamlit as st
# import google.generativeai as genai
# import os
# import json
# import io
# from PIL import Image # Pillow library for image handling
# import base64 # For encoding/decoding images
# import requests # New import for direct API calls

# # --- Placeholder Config Class (as referenced in original code) ---
# # IMPORTANT: In a real deployment, ensure your API key is securely managed
# # via environment variables or a secure secrets management system.
# class Config:
#     @staticmethod
#     def get_api_key(key_name):
#         """Retrieves API key from environment variables."""
#         return os.getenv(key_name)

# # --- Session State Initialization (Crucial for Streamlit Apps) ---
# # These variables persist across reruns of the Streamlit app
# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []
# if 'current_persona_chat_model' not in st.session_state:
#     st.session_state.current_persona_chat_model = None
# if 'current_persona_details' not in st.session_state:
#     st.session_state.current_persona_details = None
# if 'generated_personas' not in st.session_state:
#     st.session_state.generated_personas = []
# if 'selected_persona_index' not in st.session_state:
#     st.session_state.selected_persona_index = -1 # -1 means no persona selected
# if 'current_page' not in st.session_state:
#     st.session_state.current_page = "Persona Builder" # Default page

# # --- Configuration ---
# # Load API key from environment variable
# try:
#     GEMINI_API_KEY = Config.get_api_key("GEMINI_API_KEY")
#     if not GEMINI_API_KEY:
#         raise KeyError("GEMINI_API_KEY environment variable not set.")
#     genai.configure(api_key=GEMINI_API_KEY) # Configure genai for text models
# except KeyError as e:
#     st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
#     st.stop() # Stop the app if API key is missing

# # Initialize Gemini Model for text generation and multimodal input
# # Using 'gemini-2.0-flash' for speed and multimodal capabilities.
# text_model = genai.GenerativeModel('gemini-2.0-flash')

# # Note: For image generation with 'imagen-3.0-generate-002', we will use direct requests
# # as specified in the prompt's instructions, rather than a genai.GenerativeModel instance
# # for this specific model, due to its 'predict' endpoint nature.

# # --- Helper Functions for AI Interaction ---

# def parse_gemini_json_response(response_text):
#     """
#     Parses Gemini's text response, extracting JSON string if wrapped in markdown.
#     """
#     response_text = response_text.strip()
#     # Check if the response is wrapped in a markdown code block
#     if response_text.startswith("```json") and response_text.endswith("```"):
#         json_string = response_text[len("```json"): -len("```")].strip()
#     else:
#         json_string = response_text
#     return json.loads(json_string)

# def analyze_sentiment(text):
#     """
#     Analyzes the sentiment of the given text using Gemini.
#     Returns a simple sentiment (e.g., "Positive", "Negative", "Neutral").
#     """
#     if not text.strip():
#         return "N/A"

#     sentiment_prompt = f"""
#     Analyze the sentiment of the following customer feedback. Respond with a single word: 'Positive', 'Negative', or 'Neutral'.

#     Customer Feedback:
#     \"\"\"
#     {text}
#     \"\"\"
#     """
#     try:
#         response = text_model.generate_content([{"text": sentiment_prompt}])
#         sentiment = response.text.strip().capitalize()
#         if sentiment not in ["Positive", "Negative", "Neutral"]:
#             return "Neutral" # Fallback for unexpected responses
#         return sentiment
#     except Exception as e:
#         st.warning(f"Could not analyze sentiment: {e}")
#         return "N/A"

# def generate_persona_from_gemini(feedback_text, uploaded_image=None):
#     """
#     Calls Gemini API to generate a customer persona based on text and optional image.
#     """
#     st.info("Generating persona... this might take a moment.")
    
#     parts = []

#     # Add image part if provided
#     if uploaded_image:
#         image_bytes = uploaded_image.read()
#         parts.append({
#             "mime_type": uploaded_image.type,
#             "data": image_bytes
#         })

#     persona_prompt = f"""
#     As a highly skilled UX researcher and marketing strategist, your task is to synthesize a detailed customer persona based on the provided customer feedback (text) and any additional visual context (image, if provided). The image should inform the persona's context, environment, or aesthetic preferences.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona (e.g., "Sarah the Savvy Shopper").
#     - 'archetype': A concise, descriptive archetype (e.g., "The Budget-Conscious Student", "The Tech-Averse Senior").
#     - 'motivations': A list of 3-5 primary goals or what drives them.
#     - 'pain_points': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
#     - 'aspirations': A list of 2-3 things they hope to achieve or become.
#     - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service, integrating visual cues if an image was provided.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, highly informed by the overall persona attributes and the provided image.

#     Customer Feedback (Text):
#     \"\"\"
#     {feedback_text}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     parts.append({"text": persona_prompt})

#     try:
#         response = text_model.generate_content(parts)
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse Gemini's response as JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during Gemini API call: {e}")
#         st.warning("Please check your API key, network connection, or try simpler input.")
#         return None

# def refine_persona_with_gemini(existing_persona_data, refinement_feedback):
#     """
#     Refines an existing persona based on new feedback using Gemini.
#     """
#     st.info("Refining persona... this might take a moment.")

#     persona_json_string = json.dumps(existing_persona_data, indent=2)

#     refinement_prompt = f"""
#     You are a highly skilled UX researcher and marketing strategist. Your task is to refine an existing customer persona based on new feedback or additional instructions.

#     Here is the current persona data in JSON format:
#     ```json
#     {persona_json_string}
#     ```

#     Here is the new feedback or refinement instruction:
#     \"\"\"
#     {refinement_feedback}
#     \"\"\"

#     Please update the persona based on this new information. The updated persona should still adhere to the strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona.
#     - 'archetype': A concise, descriptive archetype.
#     - 'motivations': A list of 3-5 primary goals or what drives them.
#     - 'pain_points': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
#     - 'aspirations': A list of 2-3 things they hope to achieve or become.
#     - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, updated to reflect any changes.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     try:
#         response = text_model.generate_content([{"text": refinement_prompt}])
#         refined_persona_data = parse_gemini_json_response(response.text)
#         return refined_persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse refined persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error refining persona: {e}")
#         return None

# def generate_persona_image(description):
#     """
#     Generates an animated, cartoon, 3D avatar based on the persona's visual_avatar_description using Imagen.
#     Returns the base64 encoded image data.
#     """
#     st.info("Generating persona avatar... this might take a moment.")
    
#     # Construct a more specific prompt for the desired avatar style
#     # Adding "cartoon, 3D, animated style" to the prompt for consistency
#     image_prompt = f"A 3D animated cartoon avatar of a person. {description}. Ensure the avatar is visually appealing and represents the persona's core traits."
#     print(f"DEBUG: Image prompt sent to Imagen: {image_prompt}")

#     # API endpoint for Imagen 3.0 Generation
#     # This URL is derived from the prompt's instructions for using imagen-3.0-generate-002:predict
#     api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"

#     # Payload for the Imagen API call
#     payload = {
#         "instances": {
#             "prompt": image_prompt
#         },
#         "parameters": {
#             "sampleCount": 1 # Requesting one image
#         }
#     }
#     print(f"DEBUG: Imagen API URL: {api_url}")
#     print(f"DEBUG: Imagen API Payload: {json.dumps(payload, indent=2)}")

#     try:
#         # Make the POST request to the Imagen API
#         response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
#         response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
#         result = response.json()
#         print(f"DEBUG: Imagen raw API response: {json.dumps(result, indent=2)}")
        
#         # Extract the base64 encoded image data as per the prompt's instructions
#         if result.get("predictions") and len(result["predictions"]) > 0 and result["predictions"][0].get("bytesBase64Encoded"):
#             base64_encoded_image = result["predictions"][0]["bytesBase64Encoded"]
#             print(f"DEBUG: Successfully received base64 encoded image data.")
#             print(f"DEBUG: Base64 encoded image length: {len(base64_encoded_image)} characters.")
#             return base64_encoded_image
#         else:
#             st.warning("Imagen model did not return image data in expected format. Check API response structure.")
#             print("DEBUG: Imagen response did not contain 'predictions' or 'bytesBase64Encoded'.")
#             return None

#     except requests.exceptions.RequestException as e:
#         st.error(f"Network or API request error during image generation: {e}")
#         st.warning("Please check your network connection and API key permissions for `imagen-3.0-generate-002`.")
#         return None
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse Imagen API response as JSON: {e}")
#         st.code(response.text) # Show the raw response if it's not valid JSON
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during image generation: {e}")
#         return None


# def analyze_scenario_with_persona(persona_data, scenario_description):
#     """
#     Asks Gemini to analyze a scenario from the perspective of the given persona.
#     """
#     persona_context = f"""
#     You are acting as the customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {', '.join(persona_data.get('motivations', []))}
#     Pain Points: {', '.join(persona_data.get('pain_points', []))}
#     Aspirations: {', '.join(persona_data.get('aspirations', []))}
#     Typical Scenario: {persona_data.get('typical_scenario', 'N/A')}
#     """

#     scenario_prompt = f"""
#     {persona_context}

#     Given this persona, please analyze the following scenario from their perspective and provide actionable insights. Respond in a strict JSON format with the following keys:
#     - 'initial_reaction': A short sentence describing their immediate feeling.
#     - 'key_considerations': A list of 3-5 factors they would weigh.
#     - 'potential_objections': A list of 2-4 specific problems or dislikes they might have.
#     - 'recommendations': A list of 2-4 concrete product, marketing, or UX recommendations to appeal to them.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
    
#     try:
#         response = text_model.generate_content([{"text": scenario_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse scenario analysis JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error analyzing scenario: {e}")
#         return None

# def generate_actionable_ideas(persona_data):
#     """
#     Asks Gemini to brainstorm product features and marketing angles for the persona.
#     """
#     persona_context = f"""
#     You are acting as a product and marketing expert, leveraging insights from the following customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {', '.join(persona_data.get('motivations', []))}
#     Pain Points: {', '.join(persona_data.get('pain_points', []))}
#     Aspirations: {', '.join(persona_data.get('aspirations', []))}
#     """

#     ideas_prompt = f"""
#     {persona_context}

#     Based on this persona's motivations, pain points, and aspirations, please suggest 3-5 specific product feature ideas and 3-5 compelling marketing message angles that would strongly appeal to them. Respond in a strict JSON format with the following keys:
#     - 'product_features': A list of product feature ideas.
#     - 'marketing_angles': A list of marketing message angles/slogans.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     try:
#         response = text_model.generate_content([{"text": ideas_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse ideas JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating ideas: {e}")
#         return None

# def generate_problem_solution_persona(problem_statement):
#     """
#     Generates a persona focused on a specific problem statement, including problem/solution fit.
#     """
#     st.info("Analyzing problem and synthesizing persona... This might take a moment.")
    
#     problem_persona_prompt = f"""
#     As a highly skilled product strategist and customer research expert, your task is to analyze the following problem statement and then synthesize a detailed customer persona that *primarily embodies this problem*, along with potential solution-fit insights.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona.
#     - 'archetype': A concise, descriptive archetype relevant to the problem.
#     - 'problem_description_from_persona_view': A 2-4 sentence description of the problem *from this persona's perspective*, including their current struggles and inefficiencies.
#     - 'current_solutions_and_their_flaws': A list of 2-3 ways they currently try to solve this problem, and why those solutions are inadequate.
#     - 'ideal_solution_expectations': A list of 2-3 key characteristics or outcomes they would expect from an ideal solution to this problem.
#     - 'motivations_related_to_problem': A list of 2-3 core motivations directly tied to solving this specific problem.
#     - 'pain_points_related_to_problem': A list of 2-3 acute pain points specifically caused by this problem.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, reflecting their struggle or their desire for a solution.

#     Problem Statement:
#     \"\"\"
#     {problem_statement}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = text_model.generate_content([{"text": problem_persona_prompt}])
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse problem-solution persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating problem-solution persona: {e}")
#         return None

# def generate_anti_persona_and_opportunity_cost(product_description):
#     """
#     Generates anti-personas and identifies opportunity costs based on a product description.
#     """
#     st.info("Analyzing product and identifying anti-personas/opportunity costs... This might take a moment.")

#     anti_persona_prompt = f"""
#     As a highly strategic market analyst and product de-risking expert, your task is to analyze the following product description. Based on this product, identify 1-2 "Anti-Personas" – profiles of users who would *actively dislike, reject, or churn from this product*, and explain *why*. Additionally, identify 1-2 "Opportunity Costs" – potential market segments or product features that might be neglected by focusing solely on this product's current direction.

#     Return the response in a strict JSON format with the following keys:
#     - 'anti_personas': A list of objects, each with:
#         - 'name': A creative name for the anti-persona (e.g., "The Feature Overwhelmed User").
#         - 'reason_for_dislike': A 2-3 sentence explanation of why this persona would reject or churn from the product.
#         - 'key_traits_that_clash': A list of 2-3 traits that make them incompatible with the product.
#     - 'opportunity_costs': A list of objects, each with:
#         - 'area_neglected': A brief description of the market segment or feature area being overlooked.
#         - 'potential_value_missed': A 1-2 sentence explanation of the value or revenue potential being missed.

#     Product Description:
#     \"\"\"
#     {product_description}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = text_model.generate_content([{"text": anti_persona_prompt}])
#         anti_persona_data = parse_gemini_json_response(response.text)
#         return anti_persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse anti-persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating anti-persona: {e}")
#         return None


# # --- Streamlit UI ---

# st.set_page_config(
#     layout="centered",
#     page_title="AI Persona & Insight Engine 🚀",
#     initial_sidebar_state="expanded" 
# )

# st.title("🚀 AI-Powered Product-Market Fit Engine")
# st.markdown("Instantly understand customer demands and accelerate your product development with AI-driven insights for early founders and small business owners.")

# # --- Sidebar Navigation ---
# st.sidebar.header("Explore Features")
# page_selection = st.sidebar.radio(
#     "Go to:",
#     ("Persona Builder", "Problem-Solution Fit", "Anti-Persona Engine"),
#     key="page_selection"
# )

# if page_selection == "Persona Builder":
#     st.session_state.current_page = "Persona Builder"
#     st.header("1. Build Customer Personas from Feedback")
#     st.markdown("Synthesize detailed customer personas from raw feedback and visual context.")

#     feedback_text = st.text_area(
#         "Paste raw customer feedback, survey responses, or interview snippets here:",
#         height=180,
#         placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'"
#     )

#     # Display sentiment analysis
#     if feedback_text:
#         sentiment = analyze_sentiment(feedback_text)
#         st.markdown(f"**Sentiment of Feedback:** {sentiment}")

#     uploaded_image = st.file_uploader(
#         "Optionally upload an image representing the customer's environment or product usage:",
#         type=["jpg", "jpeg", "png"]
#     )

#     if uploaded_image:
#         st.image(uploaded_image, caption="Uploaded Customer Context Image", width=250)
#         st.success("Image uploaded successfully!")

#     st.header("2. Generate Persona")
#     if st.button("✨ Generate Persona", use_container_width=True):
#         if not feedback_text and not uploaded_image:
#             st.warning("Please provide either text feedback or an image (or both) to generate a persona.")
#         else:
#             with st.spinner("Generating persona with Gemini AI... This might take a moment."):
#                 persona = generate_persona_from_gemini(feedback_text, uploaded_image)

#             if persona:
#                 # Generate and store persona avatar
#                 if 'visual_avatar_description' in persona and persona['visual_avatar_description']:
#                     with st.spinner("Generating persona avatar..."):
#                         avatar_base64 = generate_persona_image(persona['visual_avatar_description'])
#                         persona['avatar_base64'] = avatar_base64 # Store avatar directly in persona
#                         print(f"DEBUG: Persona avatar_base64 set: {len(persona['avatar_base64']) if persona['avatar_base64'] else 'None'}")
#                 else:
#                     persona['avatar_base64'] = None
#                     print("DEBUG: No visual_avatar_description, avatar_base64 set to None.")

#                 # IMPORTANT FIX: Always update the session state lists with the full persona object
#                 # that now contains the avatar_base64.
#                 st.session_state.generated_personas.append(persona)
#                 st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
#                 st.session_state.current_persona_details = persona # Set the newly generated persona as current
#                 print(f"DEBUG: Current persona details updated in session state: {st.session_state.current_persona_details.get('name')}")
                
#                 # Initialize a new chat session with the persona's context
#                 initial_chat_prompt = f"""
#                 You are now role-playing as the customer persona:
#                 Name: {persona.get('name', 'N/A')}
#                 Archetype: {persona.get('archetype', 'N/A')}
#                 Motivations: {', '.join(persona.get('motivations', []))}
#                 Pain Points: {', '.join(persona.get('pain_points', []))}
#                 Aspirations: {', '.join(persona.get('aspirations', []))}
#                 Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#                 When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#                 """
#                 st.session_state.current_persona_chat_model = text_model.start_chat(history=[
#                     {"role": "user", "parts": [initial_chat_prompt]},
#                     {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#                 ])
#                 st.session_state.chat_history = [] # Reset chat history for new persona

#                 st.rerun() # Rerun to display the persona and enable new sections

#     # --- Persona History Selector ---
#     if st.session_state.generated_personas:
#         st.sidebar.header("View Past Personas")
#         persona_names = [f"{p.get('name', 'Unnamed')} ({p.get('archetype', 'No Archetype')})" for p in st.session_state.generated_personas]
        
#         selected_name = st.sidebar.selectbox(
#             "Select a persona to view/interact with:",
#             options=persona_names,
#             index=st.session_state.selected_persona_index,
#             key="persona_selector"
#         )
        
#         # Update the selected persona if a different one is chosen from the selectbox
#         new_index = persona_names.index(selected_name)
#         if new_index != st.session_state.selected_persona_index:
#             st.session_state.selected_persona_index = new_index
#             st.session_state.current_persona_details = st.session_state.generated_personas[new_index]
#             print(f"DEBUG: Switched to persona: {st.session_state.current_persona_details.get('name')}")
            
#             st.session_state.chat_history = [] # Clear chat history when switching personas
            
#             # Re-initialize chat model for the selected persona
#             persona = st.session_state.current_persona_details
#             initial_chat_prompt = f"""
#             You are now role-playing as the customer persona:
#             Name: {persona.get('name', 'N/A')}
#             Archetype: {persona.get('archetype', 'N/A')}
#             Motivations: {', '.join(persona.get('motivations', []))}
#             Pain Points: {', '.join(persona.get('pain_points', []))}
#             Aspirations: {', '.join(persona.get('aspirations', []))}
#             Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#             When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#             """
#             st.session_state.current_persona_chat_model = text_model.start_chat(history=[
#                 {"role": "user", "parts": [initial_chat_prompt]},
#                 {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#             ])
#             st.experimental_rerun() # Rerun to update the main display and chat

#     # --- Display Current Persona Details and Features ---
#     if st.session_state.current_persona_details:
#         persona = st.session_state.current_persona_details # Use the currently selected/generated persona

#         st.header("3. Your Synthesized Customer Persona")
#         st.subheader(f"## {persona.get('name', 'N/A')} - *{persona.get('archetype', 'N/A')}*")
#         st.markdown("---")

#         col1, col2 = st.columns(2) # Create two columns for layout

#         with col1:
#             st.markdown("**Motivations:**")
#             for m in persona.get('motivations', []):
#                 st.markdown(f"- 💡 {m}") # Added emoji for visual flair
            
#             st.markdown("**Aspirations:**")
#             for a in persona.get('aspirations', []):
#                 st.markdown(f"- ✨ {a}") # Added emoji for visual flair

#         with col2:
#             st.markdown("**Pain Points:**")
#             for p in persona.get('pain_points', []):
#                 st.markdown(f"- 😤 {p}") # Added emoji for visual flair
            
#             if 'visual_avatar_description' in persona:
#                 st.markdown("**Visual Avatar Idea:**")
#                 st.code(persona['visual_avatar_description']) # Display as code for easy copy-paste to image generator
        
#         # Display generated avatar if available (now retrieved from persona dict)
#         if 'avatar_base64' in persona and persona['avatar_base64']:
#             st.subheader("Persona Avatar:")
#             st.image(f"data:image/png;base64,{persona['avatar_base64']}", caption="AI-Generated Persona Avatar", width=300)
#             print(f"DEBUG: Displaying avatar for {persona.get('name')}. Base64 length: {len(persona['avatar_base64'])}")
#         else:
#             st.info("No avatar generated for this persona yet. Generate a new persona or refine an existing one to get an avatar.")
#             print(f"DEBUG: No avatar_base64 found for {persona.get('name')}.")

#         st.markdown("**Typical Scenario:**")
#         st.info(f"> {persona.get('typical_scenario', 'N/A')}")

#         st.markdown("---")
#         st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

#         # --- Persona Refinement ---
#         st.header(f"4. Refine {persona.get('name', 'Persona')}")
#         refinement_input = st.text_area(
#             "Provide additional feedback or specific instructions to refine this persona:",
#             height=100,
#             key="refinement_input",
#             placeholder="e.g., 'Make her more tech-savvy and less price-sensitive.', 'Add a new pain point about time management.'"
#         )
#         if st.button("Refine Persona", key="refine_persona_btn", use_container_width=True):
#             if not refinement_input:
#                 st.warning("Please provide refinement instructions.")
#             else:
#                 with st.spinner("Refining persona..."):
#                     refined_persona = refine_persona_with_gemini(persona, refinement_input)
                
#                 if refined_persona:
#                     # Re-generate avatar for the refined persona
#                     if 'visual_avatar_description' in refined_persona and refined_persona['visual_avatar_description']:
#                         with st.spinner("Generating new avatar for refined persona..."):
#                             avatar_base64 = generate_persona_image(refined_persona['visual_avatar_description'])
#                             refined_persona['avatar_base64'] = avatar_base64 # Store updated avatar
#                             print(f"DEBUG: Refined persona avatar_base64 set: {len(refined_persona['avatar_base64']) if refined_persona['avatar_base64'] else 'None'}")
#                     else:
#                         refined_persona['avatar_base64'] = None
#                         print("DEBUG: No visual_avatar_description for refined persona, avatar_base64 set to None.")

#                     # IMPORTANT FIX: Update both the current_persona_details AND the generated_personas list
#                     st.session_state.current_persona_details = refined_persona
#                     st.session_state.generated_personas[st.session_state.selected_persona_index] = refined_persona

#                     st.success("Persona refined successfully!")
#                     st.experimental_rerun() # Rerun to display updated persona and avatar

#         # --- Scenario-Based Analysis (Now Section 5) ---
#         st.header(f"5. Analyze Scenarios from {persona.get('name', 'Persona')}'s Perspective")
        
#         scenario_description = st.text_area(
#             "Describe a scenario for the persona to analyze (e.g., 'Launching a new premium product that costs 20% more.'):",
#             height=100,
#             key="scenario_input"
#         )

#         if st.button("Analyze Scenario", key="analyze_scenario_btn", use_container_width=True):
#             if not scenario_description:
#                 st.warning("Please describe a scenario to analyze.")
#             else:
#                 with st.spinner("Analyzing scenario..."):
#                     scenario_analysis = analyze_scenario_with_persona(
#                         persona, # Use the current persona details
#                         scenario_description
#                     )
#                 if scenario_analysis:
#                     st.subheader("Scenario Analysis:")
#                     if 'initial_reaction' in scenario_analysis:
#                         st.markdown(f"**Initial Reaction:** {scenario_analysis['initial_reaction']}")
#                     if 'key_considerations' in scenario_analysis:
#                         st.markdown(f"**Key Considerations:**")
#                         for item in scenario_analysis['key_considerations']:
#                             st.markdown(f"- {item}")
#                     if 'potential_objections' in scenario_analysis:
#                         st.markdown(f"**Potential Objections:**")
#                         for item in scenario_analysis['potential_objections']:
#                             st.markdown(f"- {item}")
#                     if 'recommendations' in scenario_analysis:
#                         st.markdown(f"**Recommendations for Us:**")
#                         for item in scenario_analysis['recommendations']:
#                             st.markdown(f"- {item}")
#                     st.markdown("---")

#         # --- Actionable Insights & Feature Ideas (Now Section 6) ---
#         st.header(f"6. Generate Actionable Ideas for {persona.get('name', 'Persona')}")
        
#         if st.button("Brainstorm Ideas", key="brainstorm_ideas_btn", use_container_width=True):
#             with st.spinner("Brainstorming product and marketing ideas..."):
#                 actionable_ideas = generate_actionable_ideas(persona) # Use the current persona details
            
#             if actionable_ideas:
#                 st.subheader("Ideas for You:")
#                 if 'product_features' in actionable_ideas:
#                     st.markdown("**Product Feature Ideas:**")
#                     for item in actionable_ideas['product_features']:
#                         st.markdown(f"- 🛠️ {item}") # Added emoji
#                 if 'marketing_angles' in actionable_ideas:
#                     st.markdown(f"**Marketing Message Angles:**")
#                     for item in actionable_ideas['marketing_angles']:
#                         st.markdown(f"- 📢 {item}") # Added emoji
#                 st.markdown("---")

#         # --- Persona "Simulation" / Conversational Interaction (Now Section 7) ---
#         st.header(f"7. Chat with {persona.get('name', 'the Persona')}")
#         st.info("Ask questions like: 'How would you react to a new feature that costs more?' or 'What do you think about our new marketing campaign?'")

#         # Display chat messages from history
#         for message in st.session_state.chat_history:
#             avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         # Chat input
#         if prompt := st.chat_input("Ask the persona..."):
#             st.session_state.chat_history.append({"role": "user", "content": prompt})
#             with st.chat_message("user", avatar="🧑‍💻"):
#                 st.markdown(prompt)

#             try:
#                 # Send user's prompt to the persona chat model
#                 response = st.session_state.current_persona_chat_model.send_message(prompt)
                
#                 # Append model's response to chat history
#                 with st.chat_message("assistant", avatar="🤖"):
#                     st.markdown(response.text)
#                 st.session_state.chat_history.append({"role": "assistant", "content": response.text})
#             except Exception as e:
#                 st.error(f"Error during chat with persona: {e}")
#                 st.warning("The persona might be experiencing a momentary lapse in character. Please try again.")

# elif page_selection == "Problem-Solution Fit":
#     st.session_state.current_page = "Problem-Solution Fit"
#     st.header("⚡ Discover Problem-Solution Fit with AI")
#     st.markdown("Start with a problem, and let AI reveal the ideal customer persona and key insights for your solution.")

#     problem_input = st.text_area(
#         "Describe a core problem you're trying to solve:",
#         height=150,
#         placeholder="e.g., 'Small businesses struggle to manage their inventory efficiently across multiple sales channels.'"
#     )

#     if st.button("Uncover Problem-Solution Persona", use_container_width=True):
#         if not problem_input:
#             st.warning("Please describe a problem to analyze.")
#         else:
#             with st.spinner("Analyzing problem and synthesizing solution-oriented persona..."):
#                 problem_persona = generate_problem_solution_persona(problem_input)
            
#             if problem_persona:
#                 st.subheader("💡 Your Problem-Solution Persona:")
#                 st.subheader(f"## {problem_persona.get('name', 'N/A')} - *{problem_persona.get('archetype', 'N/A')}*")
#                 st.markdown("---")

#                 st.markdown("**The Problem from Their View:**")
#                 st.info(f"> {problem_persona.get('problem_description_from_persona_view', 'N/A')}")

#                 st.markdown("**Current Solutions & Their Flaws:**")
#                 for item in problem_persona.get('current_solutions_and_their_flaws', []):
#                     st.markdown(f"- ❌ {item}")
                
#                 st.markdown("**Ideal Solution Expectations:**")
#                 for item in problem_persona.get('ideal_solution_expectations', []):
#                     st.markdown(f"- ✅ {item}")

#                 st.markdown("**Motivations (Problem-Related):**")
#                 for item in problem_persona.get('motivations_related_to_problem', []):
#                     st.markdown(f"- 🎯 {item}")

#                 st.markdown("**Pain Points (Problem-Related):**")
#                 for item in problem_persona.get('pain_points_related_to_problem', []):
#                     st.markdown(f"- 😖 {item}")
                
#                 if 'visual_avatar_description' in problem_persona:
#                     st.markdown("**Visual Avatar Idea:**")
#                     st.code(problem_persona['visual_avatar_description'])

#                 st.markdown("---")
#                 st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

# elif page_selection == "Anti-Persona Engine":
#     st.session_state.current_page = "Anti-Persona Engine"
#     st.header("🚫 Identify Anti-Personas & Opportunity Costs")
#     st.markdown("Understand who your product is *not* for, and discover potential missed market opportunities.")

#     product_description_input = st.text_area(
#         "Describe your product or service:",
#         height=150,
#         placeholder="e.g., 'A mobile app for busy professionals to manage personal finances with AI-driven budgeting and investment advice.'"
#     )

#     if st.button("Uncover Anti-Personas & Opportunities", use_container_width=True):
#         if not product_description_input:
#             st.warning("Please describe your product to analyze.")
#         else:
#             with st.spinner("Analyzing product and identifying anti-personas/opportunity costs..."):
#                 anti_persona_insights = generate_anti_persona_and_opportunity_cost(product_description_input)
            
#             if anti_persona_insights:
#                 st.subheader("👻 Anti-Personas (Who Your Product is NOT For):")
#                 if 'anti_personas' in anti_persona_insights and anti_persona_insights['anti_personas']:
#                     for i, anti_p in enumerate(anti_persona_insights['anti_personas']):
#                         st.markdown(f"**Anti-Persona {i+1}: {anti_p.get('name', 'Unnamed Anti-Persona')}**")
#                         st.markdown(f"**Reason for Dislike:** {anti_p.get('reason_for_dislike', 'N/A')}")
#                         st.markdown(f"**Key Traits that Clash:**")
#                         for trait in anti_p.get('key_traits_that_clash', []):
#                             st.markdown(f"- ⛔ {trait}")
#                         st.markdown("---")
#                 else:
#                     st.info("No specific anti-personas identified at this time.")

#                 st.subheader("🔭 Opportunity Costs (What You Might Be Missing):")
#                 if 'opportunity_costs' in anti_persona_insights and anti_persona_insights['opportunity_costs']:
#                     for i, opp_cost in enumerate(anti_persona_insights['opportunity_costs']):
#                         st.markdown(f"**Opportunity {i+1}: {opp_cost.get('area_neglected', 'N/A')}**")
#                         st.markdown(f"**Potential Value Missed:** {opp_cost.get('potential_value_missed', 'N/A')}")
#                         st.markdown("---")
#                 else:
#                     st.info("No specific opportunity costs identified at this time.")

#                 st.caption("Insights generated by Google Gemini AI. Always review for accuracy and potential biases.")


# # --- Sidebar for Instructions and Notes ---
# st.sidebar.markdown("---")
# st.sidebar.header("How to Use This App")
# st.sidebar.markdown("""
# 1.  **Select a Feature:** Use the radio buttons above to navigate between "Persona Builder", "Problem-Solution Fit", and "Anti-Persona Engine".
# 2.  **Persona Builder:**
#     * Provide customer feedback (text) and optionally an image.
#     * **NEW!** See instant sentiment analysis of your feedback.
#     * Generate a detailed persona.
#     * **NEW!** An AI-generated avatar will appear for your persona.
#     * **NEW!** Refine an existing persona with more details or corrections.
#     * Interact with the persona: chat, analyze scenarios, brainstorm ideas.
#     * Switch between generated personas from the "View Past Personas" dropdown.
# 3.  **Problem-Solution Fit:**
#     * Describe a core problem you're trying to solve.
#     * Generate a persona specifically focused on that problem, revealing key insights for solution development.
# 4.  **Anti-Persona Engine:**
#     * Describe your product or service.
#     * Identify "anti-personas" (users who won't like your product) and "opportunity costs" (missed market segments/features).
# """)

# st.sidebar.header("Project Notes")
# st.sidebar.markdown("""
# * **AI Models:** Powered by Google Gemini (`gemini-2.0-flash` for text, `imagen-3.0-generate-002` for images).
# * **Framework:** Built with Streamlit for rapid prototyping and interactive UI.
# * **API Key Security:** Your `GEMINI_API_KEY` is loaded from environment variables.
# * **Persistence:** Personas are currently stored in memory for the current session. Firebase Firestore integration is a future step for long-term storage across sessions.
# * **UI/UX:** Designed for clarity and ease of use, leveraging Streamlit's native features. Streamlit supports light/dark themes, which can be toggled via your browser/Streamlit settings.
# """)


# import streamlit as st
# import google.generativeai as genai
# import os
# import json
# import io
# from PIL import Image # Pillow library for image handling
# import base64 # For encoding/decoding images
# import requests # New import for direct API calls

# # --- Placeholder Config Class (as referenced in original code) ---
# # IMPORTANT: In a real deployment, ensure your API key is securely managed
# # via environment variables or a secure secrets management system.
# class Config:
#     @staticmethod
#     def get_api_key(key_name):
#         """Retrieves API key from environment variables."""
#         return os.getenv(key_name)

# # --- Session State Initialization (Crucial for Streamlit Apps) ---
# # These variables persist across reruns of the Streamlit app
# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []
# if 'current_persona_chat_model' not in st.session_state:
#     st.session_state.current_persona_chat_model = None
# if 'current_persona_details' not in st.session_state:
#     st.session_state.current_persona_details = None
# if 'generated_personas' not in st.session_state:
#     st.session_state.generated_personas = []
# if 'selected_persona_index' not in st.session_state:
#     st.session_state.selected_persona_index = -1 # -1 means no persona selected
# if 'uploaded_image_bytes' not in st.session_state: # Store image bytes
#     st.session_state.uploaded_image_bytes = None
# if 'uploaded_image_type' not in st.session_state: # Store image MIME type
#     st.session_state.uploaded_image_type = None


# # --- Configuration ---
# # Load API key from environment variable
# try:
#     GEMINI_API_KEY = Config.get_api_key("GEMINI_API_key")
#     if not GEMINI_API_KEY:
#         raise KeyError("GEMINI_API_key environment variable not set.")
#     genai.configure(api_key=GEMINI_API_KEY) # Configure genai for text models
# except KeyError as e:
#     st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
#     st.stop() # Stop the app if API key is missing

# # Initialize Gemini Model for text generation and multimodal input
# # Using 'gemini-2.0-flash' for speed and multimodal capabilities.
# text_model = genai.GenerativeModel('gemini-2.0-flash')

# # --- Helper Functions for AI Interaction ---

# def parse_gemini_json_response(response_text):
#     """
#     Parses Gemini's text response, extracting JSON string if wrapped in markdown.
#     """
#     response_text = response_text.strip()
#     # Check if the response is wrapped in a markdown code block
#     if response_text.startswith("```json") and response_text.endswith("```"):
#         json_string = response_text[len("```json"): -len("```")].strip()
#     else:
#         json_string = response_text
#     return json.loads(json_string)

# def analyze_sentiment(text):
#     """
#     Analyzes the sentiment of the given text using Gemini.
#     Returns a simple sentiment (e.g., "Positive", "Negative", "Neutral").
#     """
#     if not text.strip():
#         return "N/A"

#     sentiment_prompt = f"""
#     Analyze the sentiment of the following customer feedback. Respond with a single word: 'Positive', 'Negative', or 'Neutral'.

#     Customer Feedback:
#     \"\"\"
#     {text}
#     \"\"\"
#     """
#     try:
#         response = text_model.generate_content([{"text": sentiment_prompt}])
#         sentiment = response.text.strip().capitalize()
#         if sentiment not in ["Positive", "Negative", "Neutral"]:
#             return "Neutral" # Fallback for unexpected responses
#         return sentiment
#     except Exception as e:
#         st.warning(f"Could not analyze sentiment: {e}")
#         return "N/A"

# def analyze_image_context(image_bytes, mime_type):
#     """
#     Analyzes an image using Gemini's multimodal capabilities to extract
#     sentiment, objects, and lifestyle context.
#     Returns a dictionary with extracted details.
#     """
#     if not image_bytes:
#         return {}

#     image_part = {
#         "mime_type": mime_type,
#         "data": image_bytes
#     }

#     image_analysis_prompt = """
#     Analyze the provided image and describe its key elements, overall mood/sentiment, and any implied lifestyle or context.
#     Focus on:
#     1.  **Objects/Scenes:** What prominent objects or scenes are depicted?
#     2.  **Mood/Sentiment:** What is the general mood or sentiment conveyed by the image (e.g., calm, energetic, busy, relaxed)?
#     3.  **Lifestyle/Context:** What kind of lifestyle or environment does this image suggest (e.g., urban, rural, professional, casual, family-oriented, tech-focused, outdoor)?
    
#     Respond in a concise JSON format with keys: 'objects', 'mood', 'lifestyle'.
#     Example: {"objects": ["laptop", "coffee cup"], "mood": "focused", "lifestyle": "work-from-home professional"}
#     """
    
#     try:
#         response = text_model.generate_content([image_part, {"text": image_analysis_prompt}])
#         image_context = parse_gemini_json_response(response.text)
#         return image_context
#     except json.JSONDecodeError as e:
#         st.warning(f"Failed to parse image analysis JSON. Error: {e}. Raw response: {response.text}")
#         return {}
#     except Exception as e:
#         st.warning(f"Could not analyze image context: {e}")
#         return {}

# def generate_persona_from_gemini(feedback_text, image_bytes=None, image_type=None):
#     """
#     Calls Gemini API to generate a customer persona based on text and optional image.
#     Now includes image context analysis.
#     """
#     st.info("Generating persona... this might take a moment.")
    
#     parts = []
#     image_context_str = ""

#     # Analyze image context if image bytes are provided
#     if image_bytes and image_type:
#         with st.spinner("Analyzing image context..."):
#             image_context = analyze_image_context(image_bytes, image_type)
#             if image_context:
#                 image_context_str = (
#                     f"Additional visual context from image: "
#                     f"Objects/Scenes: {image_context.get('objects', 'N/A')}. "
#                     f"Mood: {image_context.get('mood', 'N/A')}. "
#                     f"Lifestyle: {image_context.get('lifestyle', 'N/A')}. "
#                 )
#                 # Store image context in session state for display later if needed
#                 st.session_state.last_image_context = image_context
#             else:
#                 st.session_state.last_image_context = {}
        
#         # Add image part for persona generation
#         parts.append({
#             "mime_type": image_type,
#             "data": image_bytes
#         })

#     persona_prompt = f"""
#     As a highly skilled UX researcher and marketing strategist, your task is to synthesize a detailed customer persona based on the provided customer feedback (text) and any additional visual context (image, if provided). The image should inform the persona's context, environment, or aesthetic preferences.

#     {image_context_str}

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona (e.g., "Sarah the Savvy Shopper").
#     - 'archetype': A concise, descriptive archetype (e.g., "The Budget-Conscious Student", "The Tech-Averse Senior").
#     - 'motivations_summary': A single, concise, impactful phrase (max 10 words) summarizing their primary goals.
#     - 'motivations_details': A list of 3-5 primary goals or what drives them.
#     - 'pain_points_summary': A single, concise, impactful phrase (max 10 words) summarizing their key frustrations.
#     - 'pain_points_details': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
#     - 'aspirations_summary': A single, concise, impactful phrase (max 10 words) summarizing their main aspirations.
#     - 'aspirations_details': A list of 2-3 things they hope to achieve or become.
#     - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service, integrating visual cues if an image was provided and its context was analyzed.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, highly informed by the overall persona attributes and the provided image.

#     Customer Feedback (Text):
#     \"\"\"
#     {feedback_text}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     parts.append({"text": persona_prompt})

#     try:
#         response = text_model.generate_content(parts)
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse Gemini's response as JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during Gemini API call: {e}")
#         st.warning("Please check your API key, network connection, or try simpler input.")
#         return None

# def refine_persona_with_gemini(existing_persona_data, refinement_feedback):
#     """
#     Refines an existing persona based on new feedback using Gemini.
#     """
#     st.info("Refining persona... this might take a moment.")

#     persona_json_string = json.dumps(existing_persona_data, indent=2)

#     refinement_prompt = f"""
#     You are a highly skilled UX researcher and marketing strategist. Your task is to refine an existing customer persona based on new feedback or additional instructions.

#     Here is the current persona data in JSON format:
#     ```json
#     {persona_json_string}
#     ```

#     Here is the new feedback or refinement instruction:
#     \"\"\"
#     {refinement_feedback}
#     \"\"\"

#     Please update the persona based on this new information. The updated persona should still adhere to the strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona.
#     - 'archetype': A concise, descriptive archetype.
#     - 'motivations_summary': A single, concise, impactful phrase (max 10 words) summarizing their primary goals.
#     - 'motivations_details': A list of 3-5 primary goals or what drives them.
#     - 'pain_points_summary': A single, concise, impactful phrase (max 10 words) summarizing their key frustrations.
#     - 'pain_points_details': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
#     - 'aspirations_summary': A single, concise, impactful phrase (max 10 words) summarizing their main aspirations.
#     - 'aspirations_details': A list of 2-3 things they hope to achieve or become.
#     - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, updated to reflect any changes.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     try:
#         response = text_model.generate_content([{"text": refinement_prompt}])
#         refined_persona_data = parse_gemini_json_response(response.text)
#         return refined_persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse refined persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error refining persona: {e}")
#         return None

# def generate_persona_image(description):
#     """
#     Generates an animated, cartoon, 3D avatar based on the persona's visual_avatar_description using Imagen.
#     Returns the base64 encoded image data.
#     """
#     image_prompt = f"A static 3D vector cartoon avatar of a person. {description}. Rendered with a transparent or very minimalist white background. Ensure the avatar is visually appealing and represents the persona's core traits."
#     api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"

#     payload = {
#         "instances": {
#             "prompt": image_prompt
#         },
#         "parameters": {
#             "sampleCount": 1 
#         }
#     }
#     try:
#         response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
#         response.raise_for_status() 
        
#         result = response.json()
#         if result.get("predictions") and len(result["predictions"]) > 0 and result["predictions"][0].get("bytesBase64Encoded"):
#             base64_encoded_image = result["predictions"][0]["bytesBase64Encoded"]
#             return base64_encoded_image
#         else:
#             st.warning("Imagen model did not return image data in expected format. Check API response structure.")
#             return None

#     except requests.exceptions.RequestException as e:
#         st.error(f"Network or API request error during image generation: {e}")
#         st.warning("Please check your network connection and API key permissions for `imagen-3.0-generate-002`.")
#         return None
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse Imagen API response as JSON: {e}")
#         st.code(response.text) 
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during image generation: {e}")
#         return None


# def analyze_scenario_with_persona(persona_data, scenario_description):
#     """
#     Asks Gemini to analyze a scenario from the perspective of the given persona.
#     """
#     persona_context = f"""
#     You are acting as the customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {persona_data.get('motivations_summary', 'N/A')}
#     Pain Points: {persona_data.get('pain_points_summary', 'N/A')}
#     Aspirations: {persona_data.get('aspirations_summary', 'N/A')}
#     Typical Scenario: {persona_data.get('typical_scenario', 'N/A')}
#     """

#     scenario_prompt = f"""
#     {persona_context}

#     Given this persona, please analyze the following scenario from their perspective and provide actionable insights. Respond in a strict JSON format with the following keys:
#     - 'initial_reaction': A short, impactful phrase (max 10 words) describing their immediate feeling/reaction.
#     - 'key_considerations_summary': A single, concise, impactful phrase (max 15 words) summarizing the most important factors they would weigh.
#     - 'key_considerations_details': A list of 2-3 detailed factors they would weigh.
#     - 'potential_objections_summary': A single, concise, impactful phrase (max 15 words) summarizing their main objections.
#     - 'potential_objections_details': A list of 2-3 specific problems or dislikes they might have.
#     - 'recommendations_summary': A single, concise, impactful phrase (max 15 words) summarizing the key recommendations to appeal to them.
#     - 'recommendations_details': A list of 2-3 concrete product, marketing, or UX recommendations to appeal to them.

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
    
#     try:
#         response = text_model.generate_content([{"text": scenario_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse scenario analysis JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error analyzing scenario: {e}")
#         return None

# def generate_actionable_ideas(persona_data):
#     """
#     Asks Gemini to brainstorm product features and marketing angles for the persona.
#     """
#     persona_context = f"""
#     You are acting as a product and marketing expert, leveraging insights from the following customer persona:
#     Name: {persona_data.get('name', 'N/A')}
#     Archetype: {persona_data.get('archetype', 'N/A')}
#     Motivations: {persona_data.get('motivations_summary', 'N/A')}
#     Pain Points: {persona_data.get('pain_points_summary', 'N/A')}
#     Aspirations: {persona_data.get('aspirations_summary', 'N/A')}
#     """

#     ideas_prompt = f"""
#     {persona_context}

#     Based on this persona's motivations, pain points, and aspirations, please suggest 2-3 specific product feature ideas and 2-3 compelling marketing message angles that would strongly appeal to them. Respond in a strict JSON format with the following keys:
#     - 'product_features': A list of concise product feature ideas (max 15 words each).
#     - 'marketing_angles': A list of concise marketing message angles/slogans (max 15 words each).

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """
#     try:
#         response = text_model.generate_content([{"text": ideas_prompt}])
#         return parse_gemini_json_response(response.text)
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse ideas JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating ideas: {e}")
#         return None

# def generate_problem_solution_persona(problem_statement):
#     """
#     Generates a persona focused on a specific problem statement, including problem/solution fit.
#     """
#     st.info("Analyzing problem and synthesizing persona... this might take a moment.")
    
#     problem_persona_prompt = f"""
#     As a highly skilled product strategist and customer research expert, your task is to analyze the following problem statement and then synthesize a detailed customer persona that *primarily embodies this problem*, along with potential solution-fit insights.

#     The persona should be returned in a strict JSON format with the following keys:
#     - 'name': A creative, memorable name for this persona.
#     - 'archetype': A concise, descriptive archetype relevant to the problem.
#     - 'problem_description_from_persona_view_summary': A 1-2 sentence concise, impactful description of the problem *from this persona's perspective*.
#     - 'problem_description_from_persona_view_details': A 2-4 sentence detailed description.
#     - 'current_solutions_and_their_flaws_summary': A 1-2 sentence concise, impactful summary of their current inadequate solutions.
#     - 'current_solutions_and_their_flaws_details': A list of 2-3 ways they currently try to solve this problem, and why those solutions are inadequate.
#     - 'ideal_solution_expectations_summary': A 1-2 sentence concise, impactful summary of their ideal solution expectations.
#     - 'ideal_solution_expectations_details': A list of 2-3 key characteristics or outcomes they would expect from an ideal solution to this problem.
#     - 'motivations_related_to_problem_summary': A single, concise, impactful phrase (max 10 words) summarizing core motivations directly tied to solving this specific problem.
#     - 'motivations_related_to_problem_details': A list of 2-3 core motivations directly tied to solving this specific problem.
#     - 'pain_points_related_to_problem_summary': A single, concise, impactful phrase (max 10 words) summarizing acute pain points specifically caused by this problem.
#     - 'pain_points_related_to_problem_details': A list of 2-3 acute pain points specifically caused by this problem.
#     - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, reflecting their struggle or their desire for a solution.

#     Problem Statement:
#     \"\"\"
#     {problem_statement}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = text_model.generate_content([{"text": problem_persona_prompt}])
#         persona_data = parse_gemini_json_response(response.text)
#         return persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse problem-solution persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"Error generating problem-solution persona: {e}")
#         return None

# def generate_anti_persona_and_opportunity_cost(product_description):
#     """
#     Generates anti-personas and identifies opportunity costs based on a product description.
#     """
#     st.info("Analyzing product and identifying anti-personas/opportunity costs... This might take a moment.")

#     anti_persona_prompt = f"""
#     As a highly strategic market analyst and product de-risking expert, your task is to analyze the following product description. Based on this product, identify 1-2 "Anti-Personas" – profiles of users who would *actively dislike, reject, or churn from this product*, and explain *why*. Additionally, identify 1-2 "Opportunity Costs" – potential market segments or product features that might be neglected by focusing solely on this product's current direction.

#     Return the response in a strict JSON format with the following keys:
#     - 'anti_personas': A list of objects, each with:
#         - 'name': A creative name for the anti-persona.
#         - 'reason_for_dislike_summary': A 1-2 sentence concise, impactful explanation of why this persona would reject or churn from the product.
#         - 'reason_for_dislike_details': A 2-3 sentence explanation.
#         - 'key_traits_that_clash': A list of 2-3 concise traits that make them incompatible with the product.
#     - 'opportunity_costs': A list of objects, each with:
#         - 'area_neglected_summary': A brief, concise, impactful description (max 15 words) of the market segment or feature area being overlooked.
#         - 'potential_value_missed_details': A 1-2 sentence concise explanation of the value or revenue potential being missed.

#     Product Description:
#     \"\"\"
#     {product_description}
#     \"\"\"

#     Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
#     """

#     try:
#         response = text_model.generate_content([{"text": anti_persona_prompt}])
#         anti_persona_data = parse_gemini_json_response(response.text)
#         return anti_persona_data
#     except json.JSONDecodeError as e:
#         st.error(f"Failed to parse anti-persona JSON. Error: {e}")
#         st.code(response.text)
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred during anti-persona generation: {e}")
#         return None


# # --- Streamlit UI ---

# st.set_page_config(
#     layout="centered", # Set to "wide" for more space, "centered" if prefer narrower
#     page_title="AI Persona & Insight Engine 🚀",
#     initial_sidebar_state="expanded" 
# )

# # Custom CSS for persona card elements - NO OVERLAPPING CSS
# # Keeping only the specific styles for the summary boxes and avatar.
# st.markdown("""
# <style>
# .summary-box {
#     padding: 8px 12px;
#     border-radius: 5px;
#     margin-bottom: 8px;
#     font-size: 0.9em;
#     font-weight: bold;
#     color: white;
#     text-align: center;
# }
# .summary-motivations { background-color: #52c41a; } /* Green for motivations */
# .summary-pain-points { background-color: #faad14; } /* Orange for pain points */
# .summary-aspirations { background-color: #1890ff; } /* Blue for aspirations */

# .avatar-img {
#     border-radius: 50%; /* Make avatar perfectly round */
#     border: 3px solid #FF4B4B; /* Streamlit red for avatar border */
#     box-shadow: 0 0 10px rgba(0,0,0,0.2);
#     object-fit: cover;
#     margin-bottom: 15px;
# }
# </style>
# """, unsafe_allow_html=True)


# st.title("🚀 AI-Powered Product-Market Fit Engine")
# st.markdown("Instantly understand customer demands and accelerate your product development with AI-driven insights for early founders and small business owners.")

# # --- Main Feature Selection using Radio Buttons ---
# selected_feature = st.radio(
#     "Select a feature:",
#     ["👤 Persona Builder", "🧩 Problem-Solution Fit", "🚫 Anti-Persona Engine"],
#     key="main_feature_selector"
# )

# if selected_feature == "👤 Persona Builder": # Persona Builder Section
#     st.header("Build Customer Personas from Feedback")
#     st.markdown("Synthesize detailed customer personas from raw feedback and visual context.")

#     feedback_text = st.text_area(
#         "Paste raw customer feedback, survey responses, or interview snippets here:",
#         height=180,
#         placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'"
#     )

#     # Display sentiment analysis
#     if feedback_text:
#         sentiment = analyze_sentiment(feedback_text)
#         st.markdown(f"**Feedback Sentiment:** <span style='font-weight:bold; color:{'green' if sentiment=='Positive' else ('red' if sentiment=='Negative' else 'orange')};'>{sentiment}</span>", unsafe_allow_html=True)
#         st.markdown("---")


#     uploaded_image = st.file_uploader(
#         "Optional: Upload an image representing the customer's environment or product usage:",
#         type=["jpg", "jpeg", "png"]
#     )

#     # Store uploaded image bytes and type in session state
#     if uploaded_image is not None:
#         st.session_state.uploaded_image_bytes = uploaded_image.read()
#         st.session_state.uploaded_image_type = uploaded_image.type
#         st.image(uploaded_image, caption="Uploaded Context Image", width=200) # Display original uploaded image
#         st.success("Image uploaded successfully!")
#         # Display extracted image context
#         if 'last_image_context' in st.session_state and st.session_state.last_image_context:
#             st.subheader("Image Context Detected:")
#             st.write(f"**Objects/Scenes:** {st.session_state.last_image_context.get('objects', 'N/A')}")
#             st.write(f"**Mood:** {st.session_state.last_image_context.get('mood', 'N/A')}")
#             st.write(f"**Lifestyle:** {st.session_state.last_image_context.get('lifestyle', 'N/A')}")
#             st.markdown("---")
#     else:
#         # Clear image data from session state if no image is currently uploaded
#         st.session_state.uploaded_image_bytes = None
#         st.session_state.uploaded_image_type = None
#         st.session_state.last_image_context = {}


#     st.subheader("Generate New Persona")
#     if st.button("✨ Synthesize New Persona", use_container_width=True):
#         if not feedback_text and not st.session_state.uploaded_image_bytes:
#             st.warning("Please provide either text feedback or an image (or both) to generate a persona.")
#         else:
#             with st.spinner("Generating persona with Gemini AI... This might take a moment."):
#                 persona = generate_persona_from_gemini(
#                     feedback_text, 
#                     st.session_state.uploaded_image_bytes, 
#                     st.session_state.uploaded_image_type
#                 )

#             if persona:
#                 if 'visual_avatar_description' in persona and persona['visual_avatar_description']:
#                     with st.spinner("Crafting persona avatar..."):
#                         avatar_base64 = generate_persona_image(persona['visual_avatar_description'])
#                         persona['avatar_base64'] = avatar_base64 
#                 else:
#                     persona['avatar_base64'] = None

#                 st.session_state.generated_personas.append(persona)
#                 st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
#                 st.session_state.current_persona_details = persona
                
#                 initial_chat_prompt = f"""
#                 You are now role-playing as the customer persona:
#                 Name: {persona.get('name', 'N/A')}
#                 Archetype: {persona.get('archetype', 'N/A')}
#                 Motivations: {persona.get('motivations_summary', 'N/A')}
#                 Pain Points: {persona.get('pain_points_summary', 'N/A')}
#                 Aspirations: {persona.get('aspirations_summary', 'N/A')}
#                 Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#                 When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#                 """
#                 st.session_state.current_persona_chat_model = text_model.start_chat(history=[
#                     {"role": "user", "parts": [initial_chat_prompt]},
#                     {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#                 ])
#                 st.session_state.chat_history = [] 

#                 st.rerun() 

#     # --- Persona History Selector ---
#     if st.session_state.generated_personas:
#         st.sidebar.header("Explore Saved Personas")
#         persona_names = [f"{p.get('name', 'Unnamed')} ({p.get('archetype', 'No Archetype')})" for p in st.session_state.generated_personas]
        
#         selected_name = st.sidebar.selectbox(
#             "Select a persona:",
#             options=persona_names,
#             index=st.session_state.selected_persona_index,
#             key="persona_selector"
#         )
        
#         new_index = persona_names.index(selected_name)
#         if new_index != st.session_state.selected_persona_index:
#             st.session_state.selected_persona_index = new_index
#             st.session_state.current_persona_details = st.session_state.generated_personas[new_index]
            
#             st.session_state.chat_history = [] 
            
#             persona = st.session_state.current_persona_details
#             initial_chat_prompt = f"""
#             You are now role-playing as the customer persona:
#             Name: {persona.get('name', 'N/A')}
#             Archetype: {persona.get('archetype', 'N/A')}
#             Motivations: {persona.get('motivations_summary', 'N/A')}
#             Pain Points: {persona.get('pain_points_summary', 'N/A')}
#             Aspirations: {persona.get('aspirations_summary', 'N/A')}
#             Typical Scenario: {persona.get('typical_scenario', 'N/A')}

#             When responding, strictly adhere to this persona's voice, motivations, pain points, and aspirations. Be concise and focus on their perspective. Do NOT break character.
#             """
#             st.session_state.current_persona_chat_model = text_model.start_chat(history=[
#                 {"role": "user", "parts": [initial_chat_prompt]},
#                 {"role": "model", "parts": ["Understood. I am ready to embody this persona. How can I help you understand my perspective?"]}
#             ])
#             st.rerun() 

#     # --- Display Current Persona Details and Features ---
#     if st.session_state.current_persona_details:
#         persona = st.session_state.current_persona_details 

#         st.markdown("---")
#         st.subheader("Your Synthesized Customer Persona")

#         # Start of improved persona card using Streamlit containers and columns
#         with st.container(border=True):
#             col1, col2 = st.columns([1, 2]) # Adjust column ratios as needed

#             with col1:
#                 if persona.get('avatar_base64'):
#                     st.markdown(
#                         f'<img src="data:image/png;base64,{persona["avatar_base64"]}" class="avatar-img" width="120" height="120" style="object-fit: cover; display: block; margin-left: auto; margin-right: auto;"/>',
#                         unsafe_allow_html=True
#                     )
#                 else:
#                     st.image("https://via.placeholder.com/120?text=No+Avatar", width=120, caption="No Avatar")
                
#                 # Regenerate Avatar Button (inside column for better alignment)
#                 if st.button("🔄 Regenerate Look", key="regenerate_avatar_btn_card", use_container_width=True):
#                     if 'visual_avatar_description' in persona and persona['visual_avatar_description']:
#                         with st.spinner("Crafting a new avatar..."):
#                             new_avatar_base64 = generate_persona_image(persona['visual_avatar_description'])
#                             if new_avatar_base64:
#                                 st.session_state.current_persona_details['avatar_base64'] = new_avatar_base64
#                                 st.session_state.generated_personas[st.session_state.selected_persona_index] = st.session_state.current_persona_details
#                                 st.success("New avatar generated!")
#                                 st.rerun()
#                             else:
#                                 st.error("Failed to generate a new avatar. Please try again.")
#                     else:
#                         st.warning("Cannot regenerate avatar: No visual description found for this persona.")

#             with col2:
#                 st.markdown(f"### {persona.get('name', 'N/A')}")
#                 st.markdown(f"*{persona.get('archetype', 'N/A')}*")
#                 st.markdown(f'<div class="summary-box summary-motivations">🎯 Motivations: {persona.get("motivations_summary", "N/A")}</div>', unsafe_allow_html=True)
#                 st.markdown(f'<div class="summary-box summary-pain-points">😖 Pain Points: {persona.get("pain_points_summary", "N/A")}</div>', unsafe_allow_html=True)
#                 st.markdown(f'<div class="summary-box summary-aspirations">✨ Aspirations: {persona.get("aspirations_summary", "N/A")}</div>', unsafe_allow_html=True)

#         # End of improved persona card

#         with st.expander("View Full Persona Details"):
#             st.markdown("#### Motivations:")
#             for m in persona.get('motivations_details', []):
#                 st.markdown(f"- 💡 {m}")
#             st.markdown("#### Pain Points:")
#             for p in persona.get('pain_points_details', []):
#                 st.markdown(f"- 😤 {p}")
#             st.markdown("#### Aspirations:")
#             for a in persona.get('aspirations_details', []):
#                 st.markdown(f"- ✨ {a}")
#             st.markdown("#### Typical Scenario:")
#             st.info(f"> {persona.get('typical_scenario', 'N/A')}")
#             if 'visual_avatar_description' in persona and persona['visual_avatar_description']:
#                 st.markdown("#### Visual Avatar Description (for AI generation):")
#                 st.code(persona['visual_avatar_description'])

#         st.markdown("---")
        
#         # --- Persona Refinement ---
#         st.subheader(f"Refine {persona.get('name', 'Persona')}")
#         refinement_input = st.text_area(
#             "Provide additional feedback or specific instructions to refine this persona:",
#             height=80,
#             key="refinement_input",
#             placeholder="e.g., 'Make her more tech-savvy and less price-sensitive.', 'Add a new pain point about time management.'"
#         )
#         if st.button("🔄 Refine Persona", key="refine_persona_btn", use_container_width=True):
#             if not refinement_input:
#                 st.warning("Please provide refinement instructions.")
#             else:
#                 with st.spinner("Refining persona..."):
#                     refined_persona = refine_persona_with_gemini(persona, refinement_input)
                
#                 if refined_persona:
#                     if 'visual_avatar_description' in refined_persona and refined_persona['visual_avatar_description']:
#                         with st.spinner("Crafting new avatar for refined persona..."):
#                             avatar_base64 = generate_persona_image(refined_persona['visual_avatar_description'])
#                             refined_persona['avatar_base64'] = avatar_base64
#                     else:
#                         refined_persona['avatar_base64'] = None

#                     st.session_state.current_persona_details = refined_persona
#                     st.session_state.generated_personas[st.session_state.selected_persona_index] = refined_persona

#                     st.success("Persona refined successfully! Reloading...")
#                     st.experimental_rerun() 

#         st.markdown("---")

#         # --- Scenario-Based Analysis ---
#         st.subheader(f"Analyze Scenarios from {persona.get('name', 'Persona')}'s View")
#         scenario_description = st.text_area(
#             "Describe a scenario for the persona to analyze:",
#             height=80,
#             key="scenario_input",
#             placeholder="e.g., 'Launching a new premium product that costs 20% more.'"
#         )

#         if st.button("🔬 Analyze Scenario", key="analyze_scenario_btn", use_container_width=True):
#             if not scenario_description:
#                 st.warning("Please describe a scenario to analyze.")
#             else:
#                 with st.spinner("Analyzing scenario..."):
#                     scenario_analysis = analyze_scenario_with_persona(
#                         persona, 
#                         scenario_description
#                     )
#                 if scenario_analysis:
#                     with st.container(border=True): # Insight Card
#                         st.markdown(f"**Immediate Reaction:** {scenario_analysis.get('initial_reaction', 'N/A')}")
                        
#                         col_cons, col_obj, col_rec = st.columns(3)
#                         with col_cons:
#                             st.markdown("##### Key Considerations:")
#                             st.info(scenario_analysis.get('key_considerations_summary', 'N/A'))
#                             with st.expander("Details"):
#                                 for item in scenario_analysis.get('key_considerations_details', []):
#                                     st.markdown(f"- 🤔 {item}")
#                         with col_obj:
#                             st.markdown("##### Potential Objections:")
#                             st.warning(scenario_analysis.get('potential_objections_summary', 'N/A'))
#                             with st.expander("Details"):
#                                 for item in scenario_analysis.get('potential_objections_details', []):
#                                     st.markdown(f"- 🛑 {item}")
#                         with col_rec:
#                             st.markdown("##### Recommendations:")
#                             st.success(scenario_analysis.get('recommendations_summary', 'N/A'))
#                             with st.expander("Details"):
#                                 for item in scenario_analysis.get('recommendations_details', []):
#                                     st.markdown(f"- ✅ {item}")
#                     st.markdown("---")

#         # --- Actionable Insights & Feature Ideas ---
#         st.subheader(f"Brainstorm Ideas for {persona.get('name', 'Persona')}")
        
#         if st.button("💡 Brainstorm Ideas", key="brainstorm_ideas_btn", use_container_width=True):
#             with st.spinner("Brainstorming product and marketing ideas..."):
#                 actionable_ideas = generate_actionable_ideas(persona) 
            
#             if actionable_ideas:
#                 with st.container(border=True): # Insight Card
#                     col_features, col_angles = st.columns(2)
#                     with col_features:
#                         st.markdown("##### Product Feature Ideas:")
#                         if actionable_ideas.get('product_features'):
#                             for item in actionable_ideas.get('product_features', []):
#                                 st.markdown(f"- 🛠️ {item}") 
#                         else:
#                             st.info("No product features generated.")
#                     with col_angles:
#                         st.markdown("##### Marketing Message Angles:")
#                         if actionable_ideas.get('marketing_angles'):
#                             for item in actionable_ideas.get('marketing_angles', []):
#                                 st.markdown(f"- 📢 {item}") 
#                         else:
#                             st.info("No marketing angles generated.")
#                 st.markdown("---")

#         # --- Persona "Simulation" / Conversational Interaction ---
#         st.subheader(f"Chat with {persona.get('name', 'the Persona')}")
#         st.info("Ask questions like: 'How would you react to a new feature that costs more?' or 'What do you think about our new marketing campaign?'")

#         for message in st.session_state.chat_history:
#             avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
#             with st.chat_message(message["role"], avatar=avatar):
#                 st.markdown(message["content"])

#         if prompt := st.chat_input("Ask the persona..."):
#             st.session_state.chat_history.append({"role": "user", "content": prompt})
#             with st.chat_message("user", avatar="🧑‍💻"):
#                 st.markdown(prompt)

#             try:
#                 response = st.session_state.current_persona_chat_model.send_message(prompt)
                
#                 with st.chat_message("assistant", avatar="🤖"):
#                     st.markdown(response.text)
#                 st.session_state.chat_history.append({"role": "assistant", "content": response.text})
#             except Exception as e:
#                 st.error(f"Error during chat with persona: {e}")
#                 st.warning("The persona might be experiencing a momentary lapse in character. Please try again.")

# elif selected_feature == "🧩 Problem-Solution Fit": # Problem-Solution Fit Section
#     st.header("Discover Problem-Solution Fit with AI")
#     st.markdown("Start with a problem, and let AI reveal the ideal customer persona and key insights for your solution.")

#     problem_input = st.text_area(
#         "Describe a core problem you're trying to solve:",
#         height=120,
#         placeholder="e.g., 'Small businesses struggle to manage their inventory efficiently across multiple sales channels.'"
#     )

#     if st.button("🧩 Uncover Problem-Solution Persona", use_container_width=True):
#         if not problem_input:
#             st.warning("Please describe a problem to analyze.")
#         else:
#             with st.spinner("Analyzing problem and synthesizing solution-oriented persona..."):
#                 problem_persona = generate_problem_solution_persona(problem_input)
            
#             if problem_persona:
#                 st.markdown("---")
#                 st.subheader("Your Problem-Solution Persona Snapshot:")
                
#                 with st.container(border=True):
#                     col_name, col_desc = st.columns([1, 2])
#                     with col_name:
#                         st.markdown(f"### {problem_persona.get('name', 'N/A')}")
#                         st.markdown(f"*{problem_persona.get('archetype', 'N/A')}*")
#                     with col_desc:
#                         st.markdown(f"**Problem from Their View:**")
#                         st.info(problem_persona.get('problem_description_from_persona_view_summary', 'N/A'))
                    
#                     st.markdown("---")
#                     col_current_sol, col_ideal_sol = st.columns(2)

#                     with col_current_sol:
#                         st.markdown("##### Current Solutions & Their Flaws:")
#                         st.warning(problem_persona.get('current_solutions_and_their_flaws_summary', 'N/A'))
#                         with st.expander("Details"):
#                             for item in problem_persona.get('current_solutions_and_their_flaws_details', []):
#                                 st.markdown(f"- ❌ {item}")
                    
#                     with col_ideal_sol:
#                         st.markdown("##### Ideal Solution Expectations:")
#                         st.success(problem_persona.get('ideal_solution_expectations_summary', 'N/A'))
#                         with st.expander("Details"):
#                             for item in problem_persona.get('ideal_solution_expectations_details', []):
#                                 st.markdown(f"- ✅ {item}")
                    
#                     # Moved these outside the columns to avoid deep nesting issues
#                     st.markdown("---") # Separator for visual clarity
#                     col_motiv_rel, col_pain_rel = st.columns(2)
#                     with col_motiv_rel:
#                         st.markdown("##### Motivations (Problem-Related):")
#                         st.info(problem_persona.get('motivations_related_to_problem_summary', 'N/A'))
#                         with st.expander("Details"):
#                             for item in problem_persona.get('motivations_related_to_problem_details', []):
#                                 st.markdown(f"- 🎯 {item}")
#                     with col_pain_rel:
#                         st.markdown("##### Pain Points (Problem-Related):")
#                         st.warning(problem_persona.get('pain_points_related_to_problem_summary', 'N/A'))
#                         with st.expander("Details"):
#                             for item in problem_persona.get('pain_points_related_to_problem_details', []):
#                                 st.markdown(f"- 😖 {item}")

#                     if 'visual_avatar_description' in problem_persona:
#                         with st.expander("Visual Avatar Idea (for AI generation)"):
#                             st.code(problem_persona['visual_avatar_description'])

#                 st.markdown("---")
#                 st.caption("Persona generated by Google Gemini AI. Always review for accuracy and potential biases.")

# elif selected_feature == "🚫 Anti-Persona Engine": # Anti-Persona Engine Section
#     st.header("Identify Anti-Personas & Opportunity Costs")
#     st.markdown("Understand who your product is *not* for, and discover potential missed market opportunities.")

#     product_description_input = st.text_area(
#         "Describe your product or service:",
#         height=120,
#         placeholder="e.g., 'A mobile app for busy professionals to manage personal finances with AI-driven budgeting and investment advice.'"
#     )

#     if st.button("🚫 Uncover Anti-Personas & Opportunities", use_container_width=True):
#         if not product_description_input:
#             st.warning("Please describe your product to analyze.")
#         else:
#             with st.spinner("Analyzing product and identifying anti-personas/opportunity costs..."):
#                 anti_persona_insights = generate_anti_persona_and_opportunity_cost(product_description_input)
            
#             if anti_persona_insights:
#                 st.markdown("---")
#                 st.subheader("👻 Anti-Personas (Who Your Product is NOT For):")
#                 if 'anti_personas' in anti_persona_insights and anti_persona_insights['anti_personas']:
#                     for i, anti_p in enumerate(anti_persona_insights['anti_personas']):
#                         with st.container(border=True):
#                             st.markdown(f"**Anti-Persona {i+1}: {anti_p.get('name', 'Unnamed Anti-Persona')}**")
#                             st.warning(anti_p.get('reason_for_dislike_summary', 'N/A'))
#                             with st.expander(f"More on {anti_p.get('name', 'this persona')}'s Dislike"):
#                                 st.markdown(f"**Reason for Dislike:** {anti_p.get('reason_for_dislike_details', 'N/A')}")
#                                 st.markdown(f"**Key Traits that Clash:**")
#                                 for trait in anti_p.get('key_traits_that_clash', []):
#                                     st.markdown(f"- ⛔ {trait}")
#                         st.markdown("---")
#                 else:
#                     st.info("No specific anti-personas identified at this time.")

#                 st.subheader("🔭 Opportunity Costs (What You Might Be Missing):")
#                 if 'opportunity_costs' in anti_persona_insights and anti_persona_insights['opportunity_costs']:
#                     for i, opp_cost in enumerate(anti_persona_insights['opportunity_costs']):
#                         with st.container(border=True):
#                             st.markdown(f"**Opportunity {i+1}: {opp_cost.get('area_neglected_summary', 'N/A')}**")
#                             st.info(opp_cost.get('area_neglected_summary', 'N/A'))
#                             with st.expander(f"Value Missed for {opp_cost.get('area_neglected_summary', 'this opportunity')}"):
#                                 st.markdown(f"**Potential Value Missed:** {opp_cost.get('potential_value_missed_details', 'N/A')}")
#                         st.markdown("---")
#                 else:
#                     st.info("No specific opportunity costs identified at this time.")

#                 st.caption("Insights generated by Google Gemini AI. Always review for accuracy and potential biases.")


# # --- Sidebar for Instructions and Notes ---
# st.sidebar.markdown("---")
# st.sidebar.header("How to Use This App")
# st.sidebar.markdown("""
# 1.  **Navigate with Radio Buttons:** Use the radio buttons at the top to switch between "Persona Builder", "Problem-Solution Fit", and "Anti-Persona Engine".
# 2.  **Persona Builder:**
#     * Provide customer feedback (text) and optionally an image.
#     * See instant sentiment analysis.
#     * Generate a detailed persona.
#     * An AI-generated avatar is displayed, and you can click "Regenerate Look" to get a new image for the same persona description.
#     * If an image is uploaded, its detected objects, mood, and lifestyle context will be displayed.
#     * **UPDATED!** Persona display now uses a cleaner, non-overlapping card design for better readability.
#     * Refine an existing persona for updated insights and avatar.
#     * Analyze scenarios and brainstorm ideas.
#     * Chat with the persona.
#     * Switch between generated personas from the "Explore Saved Personas" dropdown in the sidebar.
# 3.  **Problem-Solution Fit:**
#     * Describe a core problem.
#     * Uncover a problem-centric persona with key insights on solutions and flaws.
# 4.  **Anti-Persona Engine:**
#     * Describe your product.
#     * Identify "anti-personas" (who your product isn't for) and "opportunity costs" (missed segments/features).
# """)

# st.sidebar.header("Project Notes")
# st.sidebar.markdown("""
# * **AI Models:** Powered by Google Gemini (`gemini-2.0-flash` for text, `imagen-3.0-generate-002` for images).
# * **Framework:** Built with Streamlit for rapid prototyping and interactive UI.
# * **API Key Security:** Your `GEMINI_API_KEY` is loaded from environment variables.
# * **Persistence:** Personas are currently stored in memory for the current session. Firebase Firestore integration is a future step for long-term storage across sessions.
# * **UI/UX:** Uses Streamlit's default styling, with custom CSS for summary boxes and avatar.
# """)

































import streamlit as st
import google.generativeai as genai
import os
import json
import io
from PIL import Image # Pillow library for image handling
import base64 # For encoding/decoding images
import requests # New import for direct API calls
import pandas as pd # New import for CSV handling
import time # For showing temporary messages

# --- Placeholder Config Class (as referenced in original code) ---
# IMPORTANT: In a real deployment, ensure your API key is securely managed
# via environment variables or a secure secrets management system.
class Config:
    @staticmethod
    def get_api_key(key_name):
        """Retrieves API key from environment variables."""
        return os.getenv(key_name)

# --- Session State Initialization (Crucial for Streamlit Apps) ---
# These variables persist across reruns of the Streamlit app
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_persona_chat_model' not in st.session_state:
    st.session_state.current_persona_chat_model = None
if 'current_persona_details' not in st.session_state:
    st.session_state.current_persona_details = None
if 'generated_personas' not in st.session_state:
    st.session_state.generated_personas = []
if 'selected_persona_index' not in st.session_state:
    st.session_state.selected_persona_index = -1 # -1 means no persona selected
if 'uploaded_image_bytes' not in st.session_state: # Store image bytes
    st.session_state.uploaded_image_bytes = None
if 'uploaded_image_type' not in st.session_state: # Store image MIME type
    st.session_state.uploaded_image_type = None
if 'processed_feedback_data' not in st.session_state: # Store processed feedback and sentiment
    st.session_state.processed_feedback_data = [] # List of {'text': '...', 'sentiment': '...'}
if 'generated_avatar_base64' not in st.session_state:
    st.session_state.generated_avatar_base64 = None


# --- Configuration ---
# Load API key from environment variable
try:
    GEMINI_API_KEY = Config.get_api_key("GEMINI_API_key")
    if not GEMINI_API_KEY:
        raise KeyError("GEMINI_API_key environment variable not set.")
    genai.configure(api_key=GEMINI_API_KEY) # Configure genai for text models
except KeyError as e:
    st.error(f"{e} Please set it before running the app. Example: export GEMINI_API_KEY='YOUR_API_KEY'")
    st.stop() # Stop the app if API key is missing

# Initialize Gemini Model for text generation and multimodal input
# Using 'gemini-2.0-flash' for speed and multimodal capabilities.
text_model = genai.GenerativeModel('gemini-2.0-flash')

# --- Helper Functions for AI Interaction ---

def parse_gemini_json_response(response_text):
    """
    Parses Gemini's text response, extracting JSON string if wrapped in markdown.
    """
    response_text = response_text.strip()
    # Check if the response is wrapped in a markdown code block
    if response_text.startswith("```json") and response_text.endswith("```"):
        json_string = response_text[len("```json"): -len("```")].strip()
    else:
        json_string = response_text
    return json.loads(json_string)

def analyze_sentiment(text):
    """
    Analyzes the sentiment of the given text using Gemini.
    Returns a simple sentiment (e.g., "Positive", "Negative", "Neutral").
    """
    if not text.strip():
        return "N/A"

    sentiment_prompt = f"""
    Analyze the sentiment of the following customer feedback. Respond with a single word: 'Positive', 'Negative', or 'Neutral'.

    Customer Feedback:
    \"\"\"
    {text}
    \"\"\"
    """
    try:
        response = text_model.generate_content([{"text": sentiment_prompt}])
        sentiment = response.text.strip().capitalize()
        if sentiment not in ["Positive", "Negative", "Neutral"]:
            return "Neutral" # Fallback for unexpected responses
        return sentiment
    except Exception as e:
        st.warning(f"Could not analyze sentiment: {e}")
        return "N/A"

def analyze_image_context(image_bytes, mime_type):
    """
    Analyzes an image using Gemini's multimodal capabilities to extract
    sentiment, objects, and lifestyle context.
    Returns a dictionary with extracted details.
    """
    if not image_bytes:
        return {}

    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }

    image_analysis_prompt = """
    Analyze the provided image and describe its key elements, overall mood/sentiment, and any implied lifestyle or context.
    Focus on:
    1.  **Objects/Scenes:** What prominent objects or scenes are depicted?
    2.  **Mood/Sentiment:** What is the general mood or sentiment conveyed by the image (e.g., calm, energetic, busy, relaxed)?
    3.  **Lifestyle/Context:** What kind of lifestyle or environment does this image suggest (e.g., urban, rural, professional, casual, family-oriented, tech-focused, outdoor)?

    Respond in a concise JSON format with keys: 'objects', 'mood', 'lifestyle'.
    Example: {"objects": ["laptop", "coffee cup"], "mood": "focused", "lifestyle": "work-from-home professional"}
    """

    try:
        response = text_model.generate_content([image_part, {"text": image_analysis_prompt}])
        image_context = parse_gemini_json_response(response.text)
        return image_context
    except json.JSONDecodeError as e:
        st.warning(f"Failed to parse image analysis JSON. Error: {e}. Raw response: {response.text}")
        return {}
    except Exception as e:
        st.warning(f"Could not analyze image context: {e}")
        return {}

def generate_persona_from_gemini(feedback_text_combined, image_bytes=None, image_type=None):
    """
    Calls Gemini API to generate a customer persona based on combined text and optional image.
    """
    st.info("Generating persona... this might take a moment.")

    parts = []
    image_context_str = ""

    # Analyze image context if image bytes are provided
    if image_bytes and image_type:
        with st.spinner("Analyzing image context..."):
            image_context = analyze_image_context(image_bytes, image_type)
            if image_context:
                image_context_str = (
                    f"Additional visual context from image: "
                    f"Objects/Scenes: {image_context.get('objects', 'N/A')}. "
                    f"Mood: {image_context.get('mood', 'N/A')}. "
                    f"Lifestyle: {image_context.get('lifestyle', 'N/A')}. "
                )
                # Store image context in session state for display later if needed
                st.session_state.last_image_context = image_context
            else:
                st.session_state.last_image_context = {}

        # Add image part for persona generation
        parts.append({
            "mime_type": image_type,
            "data": image_bytes
        })

    persona_prompt = f"""
    As a highly skilled UX researcher and marketing strategist, your task is to synthesize a detailed customer persona based on the provided customer feedback (text) and any additional visual context (image, if provided). The image should inform the persona's context, environment, or aesthetic preferences.

    {image_context_str}

    The persona should be returned in a strict JSON format with the following keys:
    - 'name': A creative, memorable name for this persona (e.g., "Sarah the Savvy Shopper").
    - 'archetype': A concise, descriptive archetype (e.g., "The Budget-Conscious Student", "The Tech-Averse Senior").
    - 'motivations_summary': A single, concise, impactful phrase (max 10 words) summarizing their primary goals.
    - 'motivations_details': A list of 3-5 primary goals or what drives them.
    - 'pain_points_summary': A single, concise, impactful phrase (max 10 words) summarizing their key frustrations.
    - 'pain_points_details': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
    - 'aspirations_summary': A single, concise, impactful phrase (max 10 words) summarizing their main aspirations.
    - 'aspirations_details': A list of 2-3 things they hope to achieve or become.
    - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service, integrating visual cues if an image was provided and its context was analyzed.
    - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, highly informed by the overall persona attributes and the provided image.

    Customer Feedback (Combined Text):
    \"\"\"
    {feedback_text_combined}
    \"\"\"

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """
    parts.append({"text": persona_prompt})

    try:
        response = text_model.generate_content(parts)
        persona_data = parse_gemini_json_response(response.text)
        return persona_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse Gemini's response as JSON. Error: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during Gemini API call: {e}")
        st.warning("Please check your API key, network connection, or try simpler input.")
        return None

def refine_persona_with_gemini(existing_persona_data, refinement_feedback):
    """
    Refines an existing persona based on new feedback using Gemini.
    """
    st.info("Refining persona... this might take a moment.")

    persona_json_string = json.dumps(existing_persona_data, indent=2)

    refinement_prompt = f"""
    You are a highly skilled UX researcher and marketing strategist. Your task is to refine an existing customer persona based on new feedback or additional instructions.

    Here is the current persona data in JSON format:
    ```json
    {persona_json_string}
    ```

    Here is the new feedback or refinement instruction:
    \"\"\"
    {refinement_feedback}
    \"\"\"

    Please update the persona based on this new information. The updated persona should still adhere to the strict JSON format with the following keys:
    - 'name': A creative, memorable name for this persona.
    - 'archetype': A concise, descriptive archetype.
    - 'motivations_summary': A single, concise, impactful phrase (max 10 words) summarizing their primary goals.
    - 'motivations_details': A list of 3-5 primary goals or what drives them.
    - 'pain_points_summary': A single, concise, impactful phrase (max 10 words) summarizing their key frustrations.
    - 'pain_points_details': A list of 3-5 key frustrations or challenges they face, especially related to products/services.
    - 'aspirations_summary': A single, concise, impactful phrase (max 10 words) summarizing their main aspirations.
    - 'aspirations_details': A list of 2-3 things they hope to achieve or become.
    - 'typical_scenario': A short narrative (2-4 sentences) describing a typical day or a common interaction they have related to the product/service.
    - 'visual_avatar_description': A textual description (1-2 sentences) suitable for generating an image that represents this persona, updated to reflect any changes.

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """
    try:
        response = text_model.generate_content([{"text": refinement_prompt}])
        refined_persona_data = parse_gemini_json_response(response.text)
        return refined_persona_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse refined persona JSON. Error: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"Error refining persona: {e}")
        return None

def generate_persona_image(description):
    """
    Generates an animated, cartoon, 3D avatar based on the persona's visual_avatar_description using Imagen.
    Returns the base64 encoded image data.
    """
    image_prompt = f"A static 3D vector cartoon avatar of a person. {description}. Rendered with a transparent or very minimalist white background. Ensure the avatar is visually appealing and represents the persona's core traits."
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"

    payload = {
        "instances": {
            "prompt": image_prompt
        },
        "parameters": {
            "sampleCount": 1
        }
    }
    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()

        result = response.json()
        if result.get("predictions") and len(result["predictions"]) > 0 and result["predictions"][0].get("bytesBase64Encoded"):
            base64_encoded_image = result["predictions"][0]["bytesBase64Encoded"]
            return base64_encoded_image
        else:
            st.warning("Imagen model did not return image data in expected format. Check API response structure.")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Network or API request error during image generation: {e}")
        st.warning("Please check your network connection and API key permissions for `imagen-3.0-generate-002`.")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse Imagen API response as JSON: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during image generation: {e}")
        return None


def analyze_scenario_with_persona(persona_data, scenario_description):
    """
    Asks Gemini to analyze a scenario from the perspective of the given persona.
    """
    persona_context = f"""
    You are acting as the customer persona:
    Name: {persona_data.get('name', 'N/A')}
    Archetype: {persona_data.get('archetype', 'N/A')}
    Motivations: {persona_data.get('motivations_summary', 'N/A')}
    Pain Points: {persona_data.get('pain_points_summary', 'N/A')}
    Aspirations: {persona_data.get('aspirations_summary', 'N/A')}
    Typical Scenario: {persona_data.get('typical_scenario', 'N/A')}
    """

    scenario_prompt = f"""
    {persona_context}

    Given this persona, please analyze the following scenario from their perspective and provide actionable insights. Respond in a strict JSON format with the following keys:
    - 'initial_reaction': A short, impactful phrase (max 10 words) describing their immediate feeling/reaction.
    - 'key_considerations_summary': A single, concise, impactful phrase (max 15 words) summarizing the most important factors they would weigh.
    - 'key_considerations_details': A list of 2-3 detailed factors they would weigh.
    - 'potential_objections_summary': A single, concise, impactful phrase (max 15 words) summarizing their main objections.
    - 'potential_objections_details': A list of 2-3 specific problems or dislikes they might have.
    - 'recommendations_summary': A single, concise, impactful phrase (max 15 words) summarizing the key recommendations to appeal to them.
    - 'recommendations_details': A list of 2-3 concrete product, marketing, or UX recommendations to appeal to them.

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """

    try:
        response = text_model.generate_content([{"text": scenario_prompt}])
        return parse_gemini_json_response(response.text)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse scenario analysis JSON. Error: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"Error analyzing scenario: {e}")
        return None

def generate_actionable_ideas(persona_data):
    """
    Asks Gemini to brainstorm product features and marketing angles for the persona.
    """
    persona_context = f"""
    You are acting as a product and marketing expert, leveraging insights from the following customer persona:
    Name: {persona_data.get('name', 'N/A')}
    Archetype: {persona_data.get('archetype', 'N/A')}
    Motivations: {persona_data.get('motivations_summary', 'N/A')}
    Pain Points: {persona_data.get('pain_points_summary', 'N/A')}
    Aspirations: {persona_data.get('aspirations_summary', 'N/A')}
    """

    ideas_prompt = f"""
    {persona_context}

    Based on this persona's motivations, pain points, and aspirations, please suggest 2-3 specific product feature ideas and 2-3 compelling marketing message angles that would strongly appeal to them. Respond in a strict JSON format with the following keys:
    - 'product_features': A list of concise product feature ideas (max 15 words each).
    - 'marketing_angles': A list of concise marketing message angles/slogans (max 15 words each).

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """
    try:
        response = text_model.generate_content([{"text": ideas_prompt}])
        return parse_gemini_json_response(response.text)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse ideas JSON. Error: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"Error generating ideas: {e}")
        return None

def generate_problem_solution_persona(problem_statement):
    """
    Generates a persona focused on a specific problem statement, including problem/solution fit.
    """
    st.info("Analyzing problem and synthesizing persona... this might take a moment.")

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
    \"\"\"
    {problem_statement}
    \"\"\"

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

def generate_anti_persona_and_opportunity_cost(product_description):
    """
    Generates anti-personas and identifies opportunity costs based on a product description.
    """
    st.info("Analyzing product and identifying anti-personas/opportunity costs... This might take a moment.")

    anti_persona_prompt = f"""
    As a highly strategic market analyst and product de-risking expert, your task is to analyze the following product description. Based on this product, identify 1-2 "Anti-Personas" – profiles of users who would *actively dislike, reject, or churn from this product*, and explain *why*. Additionally, identify 1-2 "Opportunity Costs" – potential market segments or product features that might be neglected by focusing solely on this product's current direction.

    Return the response in a strict JSON format with the following keys:
    - 'anti_personas': A list of objects, each with:
        - 'name': A creative name for the anti-persona.
        - 'reason_for_dislike_summary': A 1-2 sentence concise, impactful explanation of why this persona would reject or churn from the product.
        - 'reason_for_dislike_details': A 2-3 sentence explanation.
        - 'key_traits_that_clash': A list of 2-3 concise traits that make them incompatible with the product.
    - 'opportunity_costs': A list of objects, each with:
        - 'area_neglected_summary': A brief, concise, impactful description (max 15 words) of the market segment or feature area being overlooked.
        - 'potential_value_missed_details': A 1-2 sentence concise explanation of the value or revenue potential being missed.

    Product Description:
    \"\"\"
    {product_description}
    \"\"\"

    Ensure the entire response is a single, valid JSON object. Do not include any introductory or concluding remarks outside the JSON.
    """

    try:
        response = text_model.generate_content([{"text": anti_persona_prompt}])
        anti_persona_data = parse_gemini_json_response(response.text)
        return anti_persona_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse anti-persona JSON. Error: {e}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during anti-persona generation: {e}")
        return None

# --- NEW: Messaging Generation Functions ---

def generate_content_for_persona(persona_data, content_type):
    """
    Generates various content types (Landing Page, Pitch, Email, Taglines, Social)
    based on the selected persona.
    """
    persona_name = persona_data.get('name', 'the user')
    persona_archetype = persona_data.get('archetype', 'a typical customer')
    persona_motivations = ", ".join(persona_data.get('motivations_details', ['their goals']))
    persona_pain_points = ", ".join(persona_data.get('pain_points_details', ['their frustrations']))
    persona_aspirations = ", ".join(persona_data.get('aspirations_details', ['their desires']))

    base_prompt = f"""
    You are a highly creative marketing and copywriting expert. Your goal is to generate compelling content tailored for the following customer persona:

    Persona Name: {persona_name}
    Archetype: {persona_archetype}
    Motivations: {persona_motivations}
    Pain Points: {persona_pain_points}
    Aspirations: {persona_aspirations}

    Generate the following content type, keeping the persona's needs, desires, and pain points in mind. Be concise, impactful, and persuasive.
    """

    if content_type == "Landing Page Copy":
        prompt = f"""
        {base_prompt}
        Generate 3-4 short, impactful sections of landing page copy (e.g., Hero, Problem, Solution, Call to Action). Focus on addressing the persona's pain points and highlighting solutions that align with their motivations and aspirations.
        """
    elif content_type == "Pitch Slide Headlines":
        prompt = f"""
        {base_prompt}
        Generate 5-7 concise, compelling pitch slide headlines for an investor deck. Each headline should capture a key aspect of the product/solution in a way that resonates with the persona's problems and aspirations, and hints at market opportunity.
        """
    elif content_type == "Cold Email / Re-engagement Campaigns":
        prompt = f"""
        {base_prompt}
        Generate a short, personalized cold email or re-engagement email (approx. 50-70 words). The subject line should be catchy. The body should quickly address a key pain point of the persona and offer a clear, concise value proposition. Include a clear call to action.
        """
    elif content_type == "Taglines / Hero Section Ideas":
        prompt = f"""
        {base_prompt}
        Generate 5-7 short, memorable taglines or hero section ideas for a website. These should instantly communicate the core value proposition and resonate with the persona's primary motivation or aspiration.
        """
    elif content_type == "Social Post Hooks":
        prompt = f"""
        {base_prompt}
        Generate 3-5 engaging social media post hooks (e.g., for Twitter, LinkedIn, Instagram captions). Each hook should be short, attention-grabbing, and designed to pique the persona's interest by addressing a pain point or aspiration. Include relevant emojis.
        """
    else:
        return "Invalid content type."

    try:
        with st.spinner(f"Generating {content_type} for {persona_name}..."):
            response = text_model.generate_content([{"text": prompt}])
            return response.text.strip()
    except Exception as e:
        st.error(f"Error generating {content_type}: {e}")
        return "Could not generate content."

def copy_to_clipboard_button(text_to_copy, button_label="Copy", key="copy_button"):
    """
    Creates a button that, when clicked, displays a 'Copied!' message.
    Note: Direct clipboard access from Streamlit is complex without custom components.
    This provides visual feedback that the user should manually copy from the text area.
    """
    if st.button(button_label, key=key):
        st.success("Text copied to clipboard! (Please manually select and copy from the text box above if needed.)")
        # In a real web app, you'd use JavaScript for actual clipboard copy:
        # st.markdown(f"<script>navigator.clipboard.writeText(`{text_to_copy}`)</script>", unsafe_allow_html=True)
        # However, this doesn't work reliably in all Streamlit deployment environments due to iframe restrictions.

# --- Streamlit UI ---

st.set_page_config(
    layout="centered", # Set to "wide" for more space, "centered" if prefer narrower
    page_title="AI Persona & Insight Engine 🚀",
    initial_sidebar_state="expanded"
)

# Custom CSS for persona card elements - NO OVERLAPPING CSS
# Keeping only the specific styles for the summary boxes and avatar.
st.markdown("""
<style>
.summary-box {
    padding: 8px 12px;
    border-radius: 5px;
    margin-bottom: 8px;
    font-size: 0.9em;
    font-weight: bold;
    color: white;
    text-align: center;
}
.summary-motivations { background-color: #52c41a; } /* Green for motivations */
.summary-pain-points { background-color: #faad14; } /* Orange for pain points */
.summary-aspirations { background-color: #1890ff; } /* Blue for aspirations */

.avatar-img {
    border-radius: 50%; /* Make avatar perfectly round */
    border: 3px solid #FF4B4B; /* Streamlit red for avatar border */
    box-shadow: 0 0 10px rgba(0,0,0,0.2);
    object-fit: cover;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)


st.title("🚀 AI-Powered Product-Market Fit Engine")
st.markdown("Instantly understand customer demands and accelerate your product development with AI-driven insights for early founders and small business owners.")

# --- Main Feature Selection using Radio Buttons ---
selected_feature = st.radio(
    "Select a feature:",
    ["👤 Persona Builder", "📝 Generate Messaging from Persona", "🧩 Problem-Solution Fit", "🚫 Anti-Persona Engine"],
    key="main_feature_selector"
)

if selected_feature == "👤 Persona Builder": # Persona Builder Section
    st.header("Build Customer Personas from Feedback")
    st.markdown("Synthesize detailed customer personas from raw feedback and visual context.")

    feedback_option = st.radio(
        "Choose feedback input method:",
        ("Paste Text", "Upload CSV"),
        key="feedback_input_option"
    )

    feedback_text_combined = ""
    st.session_state.processed_feedback_data = [] # Reset processed feedback

    if feedback_option == "Paste Text":
        feedback_text_area = st.text_area(
            "Paste raw customer feedback, survey responses, or interview snippets here:",
            height=180,
            placeholder="e.g., 'The app is too complicated, I just want a simple way to track expenses. The onboarding was overwhelming.' or 'Love the new design, very intuitive and fast!'"
        )
        if feedback_text_area:
            feedback_text_combined = feedback_text_area
            # Process single text entry for sentiment
            sentiment = analyze_sentiment(feedback_text_area)
            st.session_state.processed_feedback_data.append({'text': feedback_text_area, 'sentiment': sentiment})
            st.markdown(f"**Overall Feedback Sentiment:** <span style='font-weight:bold; color:{'green' if sentiment=='Positive' else ('red' if sentiment=='Negative' else 'orange')};'>{sentiment}</span>", unsafe_allow_html=True)
            st.markdown("---")

    elif feedback_option == "Upload CSV":
        uploaded_csv = st.file_uploader(
            "Upload a CSV file with customer feedback (ensure one column is named 'feedback'):",
            type=["csv"]
        )
        if uploaded_csv is not None:
            try:
                df = pd.read_csv(uploaded_csv)
                if 'feedback' in df.columns:
                    feedback_entries = df['feedback'].dropna().astype(str).tolist()
                    if feedback_entries:
                        st.info(f"Processing {len(feedback_entries)} feedback entries from CSV...")

                        # Analyze sentiment for each entry and combine
                        combined_feedback_list = []
                        for i, entry in enumerate(feedback_entries):
                            current_sentiment = analyze_sentiment(entry)
                            st.session_state.processed_feedback_data.append({'text': entry, 'sentiment': current_sentiment})
                            combined_feedback_list.append(f"Feedback {i+1} (Sentiment: {current_sentiment}): {entry}")

                        feedback_text_combined = "\n\n".join(combined_feedback_list)

                        # Display overall sentiment for the combined text
                        if feedback_text_combined:
                            overall_sentiment = analyze_sentiment(feedback_text_combined)
                            st.markdown(f"**Overall Feedback Sentiment:** <span style='font-weight:bold; color:{'green' if overall_sentiment=='Positive' else ('red' if overall_sentiment=='Negative' else 'orange')};'>{overall_sentiment}</span>", unsafe_allow_html=True)

                        # Display individual entries with sentiment in an expander
                        with st.expander("View Individual Feedback Entries & Sentiments"):
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
        st.markdown("---") # Visual separator

    uploaded_image = st.file_uploader(
        "Optional: Upload an image representing the customer's environment or product usage:",
        type=["jpg", "jpeg", "png"]
    )

    # Store uploaded image bytes and type in session state
    if uploaded_image is not None:
        st.session_state.uploaded_image_bytes = uploaded_image.read()
        st.session_state.uploaded_image_type = uploaded_image.type
        st.image(uploaded_image, caption="Uploaded Context Image", width=200) # Display original uploaded image
        st.success("Image uploaded successfully!")
        # Display extracted image context
        if 'last_image_context' in st.session_state and st.session_state.last_image_context:
            st.subheader("Image Context Detected:")
            st.write(f"**Objects/Scenes:** {st.session_state.last_image_context.get('objects', 'N/A')}")
            st.write(f"**Mood:** {st.session_state.last_image_context.get('mood', 'N/A')}")
            st.write(f"**Lifestyle:** {st.session_state.last_image_context.get('lifestyle', 'N/A')}")
            st.markdown("---")
    else:
        # Clear image data from session state if no image is currently uploaded
        st.session_state.uploaded_image_bytes = None
        st.session_state.uploaded_image_type = None
        st.session_state.last_image_context = {}


    st.subheader("Generate New Persona")
    if st.button("✨ Synthesize New Persona", use_container_width=True):
        if not feedback_text_combined and not st.session_state.uploaded_image_bytes:
            st.warning("Please provide either text feedback (paste or CSV) or an image (or both) to generate a persona.")
        else:
            with st.spinner("Generating persona with Gemini AI... This might take a moment."):
                persona = generate_persona_from_gemini(
                    feedback_text_combined, # Pass combined text
                    st.session_state.uploaded_image_bytes,
                    st.session_state.uploaded_image_type
                )

            if persona:
                st.session_state.generated_personas.append(persona)
                st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
                st.success("Persona generated successfully!")

                # Generate and store avatar if description exists
                if 'visual_avatar_description' in persona and persona['visual_avatar_description']:
                    with st.spinner("Generating persona avatar..."):
                        avatar_base64 = generate_persona_image(persona['visual_avatar_description'])
                        if avatar_base64:
                            st.session_state.generated_avatar_base64 = avatar_base64
                            st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_base64'] = avatar_base64 # Store with persona
                        else:
                            st.session_state.generated_avatar_base64 = None
                else:
                    st.session_state.generated_avatar_base64 = None
                    st.warning("No visual avatar description found in persona to generate an image.")

    # --- Display and Select Personas ---
    if st.session_state.generated_personas:
        st.subheader("Your Generated Personas")
        persona_names = [p.get('name', f"Persona {i+1}") for i, p in enumerate(st.session_state.generated_personas)]
        selected_persona_name = st.selectbox(
            "Select a persona to view/refine:",
            persona_names,
            index=st.session_state.selected_persona_index if st.session_state.selected_persona_index != -1 else 0,
            key="persona_selector"
        )
        st.session_state.selected_persona_index = persona_names.index(selected_persona_name)
        st.session_state.current_persona_details = st.session_state.generated_personas[st.session_state.selected_persona_index]

        current_persona = st.session_state.current_persona_details
        st.markdown("---")
        st.subheader(f"Details for: {current_persona.get('name', 'N/A')}")
        st.markdown(f"**Archetype:** {current_persona.get('archetype', 'N/A')}")

        col1, col2 = st.columns([1, 2])
        with col1:
            if current_persona.get('avatar_base64'):
                st.image(
                    f"data:image/png;base64,{current_persona['avatar_base64']}",
                    caption=f"{current_persona.get('name', 'Persona')}'s Avatar",
                    use_column_width=True,
                    output_format="PNG",
                    clamp=True,
                    channels="RGB",
                    width=150
                )
                if st.button("🔄 Regenerate Avatar", key="regenerate_avatar_btn"):
                    if 'visual_avatar_description' in current_persona and current_persona['visual_avatar_description']:
                        with st.spinner("Regenerating persona avatar..."):
                            avatar_base64 = generate_persona_image(current_persona['visual_avatar_description'])
                            if avatar_base64:
                                st.session_state.generated_avatar_base64 = avatar_base64
                                st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_base64'] = avatar_base64
                                st.experimental_rerun() # Rerun to display new image
                            else:
                                st.warning("Could not regenerate avatar.")
                    else:
                        st.warning("No visual avatar description available for regeneration.")
            else:
                st.info("No avatar generated for this persona yet.")
                if 'visual_avatar_description' in current_persona and current_persona['visual_avatar_description']:
                    if st.button("✨ Generate Avatar", key="generate_avatar_now_btn"):
                        with st.spinner("Generating persona avatar..."):
                            avatar_base64 = generate_persona_image(current_persona['visual_avatar_description'])
                            if avatar_base64:
                                st.session_state.generated_avatar_base64 = avatar_base64
                                st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_base64'] = avatar_base64
                                st.experimental_rerun()
                            else:
                                st.warning("Could not generate avatar.")
                else:
                    st.warning("No visual avatar description to generate from.")


        with col2:
            st.markdown(f"<div class='summary-box summary-motivations'>🎯 Motivations: {current_persona.get('motivations_summary', 'N/A')}</div>", unsafe_allow_html=True)
            for detail in current_persona.get('motivations_details', []):
                st.markdown(f"- {detail}")

            st.markdown(f"<div class='summary-box summary-pain-points'>😩 Pain Points: {current_persona.get('pain_points_summary', 'N/A')}</div>", unsafe_allow_html=True)
            for detail in current_persona.get('pain_points_details', []):
                st.markdown(f"- {detail}")

            st.markdown(f"<div class='summary-box summary-aspirations'>✨ Aspirations: {current_persona.get('aspirations_summary', 'N/A')}</div>", unsafe_allow_html=True)
            for detail in current_persona.get('aspirations_details', []):
                st.markdown(f"- {detail}")

        st.markdown("---")
        st.subheader("Typical Scenario")
        st.write(current_persona.get('typical_scenario', 'N/A'))
        st.markdown("---")

        # Refinement Section
        st.subheader("Refine Persona")
        refinement_text = st.text_area(
            "Provide feedback to refine this persona (e.g., 'Make her more tech-savvy', 'Add a pain point about time management').",
            key="refinement_text_area",
            height=100
        )
        if st.button("🔄 Refine Persona", use_container_width=True):
            if refinement_text:
                with st.spinner("Refining persona..."):
                    refined_persona = refine_persona_with_gemini(current_persona, refinement_text)
                    if refined_persona:
                        st.session_state.generated_personas[st.session_state.selected_persona_index] = refined_persona
                        st.success("Persona refined successfully!")
                        # Regenerate avatar if description changed
                        if 'visual_avatar_description' in refined_persona and refined_persona['visual_avatar_description'] != current_persona.get('visual_avatar_description'):
                            with st.spinner("Generating new avatar for refined persona..."):
                                avatar_base64 = generate_persona_image(refined_persona['visual_avatar_description'])
                                if avatar_base64:
                                    st.session_state.generated_avatar_base64 = avatar_base64
                                    st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_base64'] = avatar_base64
                        st.experimental_rerun() # Rerun to display updated persona
                    else:
                        st.error("Failed to refine persona.")
            else:
                st.warning("Please enter refinement feedback.")

        st.markdown("---")
        # Save + Export Section
        st.subheader("Save & Export Persona")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            persona_json = json.dumps(current_persona, indent=2)
            st.download_button(
                label="Download Persona (JSON)",
                data=persona_json,
                file_name=f"{current_persona.get('name', 'persona').replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True
            )
        with col_dl2:
            persona_txt = f"""
Persona Name: {current_persona.get('name', 'N/A')}
Archetype: {current_persona.get('archetype', 'N/A')}

Motivations Summary: {current_persona.get('motivations_summary', 'N/A')}
Motivations Details:
{'- ' + '\n- '.join(current_persona.get('motivations_details', []))}

Pain Points Summary: {current_persona.get('pain_points_summary', 'N/A')}
Pain Points Details:
{'- ' + '\n- '.join(current_persona.get('pain_points_details', []))}

Aspirations Summary: {current_persona.get('aspirations_summary', 'N/A')}
Aspirations Details:
{'- ' + '\n- '.join(current_persona.get('aspirations_details', []))}

Typical Scenario:
{current_persona.get('typical_scenario', 'N/A')}

Visual Avatar Description: {current_persona.get('visual_avatar_description', 'N/A')}
            """
            st.download_button(
                label="Download Persona (TXT)",
                data=persona_txt,
                file_name=f"{current_persona.get('name', 'persona').replace(' ', '_').lower()}.txt",
                mime="text/plain",
                use_container_width=True
            )

elif selected_feature == "📝 Generate Messaging from Persona": # Messaging Generator Section
    st.header("Generate Messaging from Persona")
    st.markdown("Instantly create compelling marketing and pitch content tailored to your selected persona.")

    if not st.session_state.generated_personas:
        st.warning("Please generate a persona first in the 'Persona Builder' section.")
    else:
        persona_names = [p.get('name', f"Persona {i+1}") for i, p in enumerate(st.session_state.generated_personas)]
        selected_persona_for_messaging_name = st.selectbox(
            "Select a persona to generate messaging for:",
            persona_names,
            index=st.session_state.selected_persona_index if st.session_state.selected_persona_index != -1 else 0,
            key="persona_messaging_selector"
        )
        selected_persona_for_messaging = st.session_state.generated_personas[persona_names.index(selected_persona_for_messaging_name)]

        st.markdown(f"---")
        st.subheader(f"Generating content for: {selected_persona_for_messaging.get('name', 'N/A')}")
        st.markdown(f"**Archetype:** {selected_persona_for_messaging.get('archetype', 'N/A')}")

        content_types = [
            "Landing Page Copy",
            "Pitch Slide Headlines",
            "Cold Email / Re-engagement Campaigns",
            "Taglines / Hero Section Ideas",
            "Social Post Hooks"
        ]

        for content_type in content_types:
            st.markdown(f"### {content_type}")
            if st.button(f"Generate {content_type}", key=f"generate_btn_{content_type.replace(' ', '_').lower()}"):
                generated_text = generate_content_for_persona(selected_persona_for_messaging, content_type)
                st.text_area(f"{content_type} (Generated)", value=generated_text, height=200, key=f"output_{content_type.replace(' ', '_').lower()}", disabled=True)
                copy_to_clipboard_button(generated_text, key=f"copy_btn_{content_type.replace(' ', '_').lower()}")
            st.markdown("---")


elif selected_feature == "🧩 Problem-Solution Fit": # Problem-Solution Fit Section
    st.header("Problem-Solution Fit Persona")
    st.markdown("Define a core problem, and AI will generate a persona that embodies that problem, along with insights into ideal solutions.")

    problem_statement_input = st.text_area(
        "Describe a specific problem your target customers face:",
        height=150,
        placeholder="e.g., 'Small business owners struggle to manage their inventory efficiently across multiple sales channels, leading to stockouts and overstocking.'"
    )

    if st.button("🔍 Generate Problem-Solution Persona", use_container_width=True):
        if problem_statement_input:
            problem_persona = generate_problem_solution_persona(problem_statement_input)
            if problem_persona:
                st.session_state.generated_personas.append(problem_persona)
                st.session_state.selected_persona_index = len(st.session_state.generated_personas) - 1
                st.success("Problem-Solution Persona generated successfully!")

                # Generate and store avatar if description exists
                if 'visual_avatar_description' in problem_persona and problem_persona['visual_avatar_description']:
                    with st.spinner("Generating persona avatar..."):
                        avatar_base64 = generate_persona_image(problem_persona['visual_avatar_description'])
                        if avatar_base64:
                            st.session_state.generated_avatar_base64 = avatar_base64
                            st.session_state.generated_personas[st.session_state.selected_persona_index]['avatar_base64'] = avatar_base64
                        else:
                            st.session_state.generated_avatar_base64 = None
                else:
                    st.session_state.generated_avatar_base64 = None
                    st.warning("No visual avatar description found in persona to generate an image.")

                st.experimental_rerun() # Rerun to display the newly generated persona
            else:
                st.error("Failed to generate problem-solution persona.")
        else:
            st.warning("Please provide a problem statement to generate a persona.")

elif selected_feature == "🚫 Anti-Persona Engine": # Anti-Persona Engine Section
    st.header("Anti-Persona & Opportunity Cost Analysis")
    st.markdown("Identify user segments who would *not* be a good fit for your product, and discover potential missed opportunities.")

    product_description_input = st.text_area(
        "Describe your product or service:",
        height=150,
        placeholder="e.g., 'Our mobile app helps busy professionals track their daily water intake and sends smart reminders to stay hydrated.'"
    )

    if st.button("📉 Analyze Anti-Personas & Opportunity Costs", use_container_width=True):
        if product_description_input:
            anti_persona_analysis = generate_anti_persona_and_opportunity_cost(product_description_input)
            if anti_persona_analysis:
                st.subheader("Anti-Personas (Who would NOT use your product)")
                for i, ap in enumerate(anti_persona_analysis.get('anti_personas', [])):
                    st.markdown(f"#### Anti-Persona {i+1}: {ap.get('name', 'N/A')}")
                    st.markdown(f"**Reason for Dislike:** {ap.get('reason_for_dislike_summary', 'N/A')}")
                    st.write(ap.get('reason_for_dislike_details', 'N/A'))
                    st.markdown(f"**Key Traits that Clash:** {', '.join(ap.get('key_traits_that_clash', []))}")
                    st.markdown("---")

                st.subheader("Opportunity Costs (What you might be missing)")
                for i, oc in enumerate(anti_persona_analysis.get('opportunity_costs', [])):
                    st.markdown(f"#### Opportunity Cost {i+1}: {oc.get('area_neglected_summary', 'N/A')}")
                    st.write(oc.get('potential_value_missed_details', 'N/A'))
                    st.markdown("---")
            else:
                st.error("Failed to analyze anti-personas and opportunity costs.")
        else:
            st.warning("Please provide a product description for analysis.")
