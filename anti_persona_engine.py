import streamlit as st
from shared import text_model, parse_gemini_json_response
import json # Import json for potential debugging/display
import io # For image handling
import base64 # For image encoding
import pandas as pd # For charts
import matplotlib.pyplot as plt # For charts
from streamlit.components.v1 import html as st_html # Import html from streamlit.components.v1

def generate_anti_persona_data(product_description, api_key):
    """
    Generates detailed anti-persona and opportunity cost reports using Gemini.
    Returns a dictionary containing structured data for each report.
    """
    prompt = f"""
    Analyze the following product or service description and generate structured content for three distinct reports:
    1.  Negative Marketing & Sales Guidelines
    2.  Product Feature Exclusion/Refinement Brief
    3.  New Market/Product Exploration Briefs

    Product/Service Description: {product_description}

    Generate the output in a single JSON object with the following top-level keys and nested structures:

    {{
        "negative_marketing_card": {{
            "title": "Negative Marketing & Sales Guidelines",
            "summary": "(Concise summary of who NOT to target and why, max 250 characters, ensuring it's a complete sentence or two)",
            "keywords_to_exclude": ["keyword1", "keyword2"], # Keywords/phrases to exclude from advertising campaigns
            "channels_to_deprioritize": ["channel1", "channel2"], # Marketing channels to de-prioritize
            "sales_red_flags": ["behavior1", "behavior2"] # Behaviors/questions from leads indicating anti-persona
        }},
        "product_brief_card": {{
            "title": "Product Feature Exclusion/Refinement Brief",
            "summary": "(Concise summary of product features to avoid/refine for anti-personas, max 250 characters, ensuring it's a complete sentence or two)",
            "undesirable_features": ["feature1", "feature2"], # Product characteristics/features undesirable for core users but appealing to anti-personas
            "refinement_suggestions": ["suggestion1", "suggestion2"], # Suggestions for refining existing features
            "misuse_warnings": ["warning1", "warning2"] # Potential misuses or unintended behaviors
        }},
        "opportunity_report_card": {{
            "title": "New Market/Product Exploration Briefs",
            "summary": "(Concise summary of identified missed opportunities and new market potential, max 250 characters, ensuring it's a complete sentence or two)",
            "neglected_areas": [ # List of identified opportunity areas
                {{
                    "area_summary": "(Concise summary of the neglected market area)",
                    "value_score": 0, # Integer score 1-5 for potential value
                    "details": ["detail1", "detail2"] # Bullet points detailing potential value missed and exploration ideas
                }}
            ],
            "overall_exploration_ideas": ["idea1", "idea2"] # General exploration ideas if needed
        }},
        "suggested_anti_personas": [ # New section for suggested anti-personas
            {{
                "persona_name": "The Over-Engineer",
                "reason": "Prefers overly complex solutions; would be frustrated by simplicity."
            }}
        ]
    }}

    Ensure the response is ONLY a valid JSON object with no extra text or markdown outside the JSON block.
    Provide meaningful content for each field based on the product description.
    Each summary must be concise and complete, not exceeding 250 characters.
    """

    try:
        # Use the shared text_model (assuming API key is handled)
        response = text_model.generate_content(prompt)
        raw_text = response.text.strip()

        # Parse the JSON response using the shared helper
        parsed_data = parse_gemini_json_response(raw_text)

        # Basic validation of the top-level structure
        if (parsed_data
            and isinstance(parsed_data, dict)
            and 'negative_marketing_card' in parsed_data and isinstance(parsed_data['negative_marketing_card'], dict)
            and 'product_brief_card' in parsed_data and isinstance(parsed_data['product_brief_card'], dict)
            and 'opportunity_report_card' in parsed_data and isinstance(parsed_data['opportunity_report_card'], dict)
            and 'suggested_anti_personas' in parsed_data and isinstance(parsed_data['suggested_anti_personas'], list)): # Added validation for new field

            # Basic validation for nested lists and scores
            nm_card = parsed_data.get('negative_marketing_card', {})
            pb_card = parsed_data.get('product_brief_card', {})
            or_card = parsed_data.get('opportunity_report_card', {})
            anti_personas_list = parsed_data.get('suggested_anti_personas', []) # Get new list

            if (
                isinstance(nm_card.get('keywords_to_exclude', []), list) and
                isinstance(nm_card.get('channels_to_deprioritize', []), list) and
                isinstance(nm_card.get('sales_red_flags', []), list) and
                isinstance(pb_card.get('undesirable_features', []), list) and
                isinstance(pb_card.get('refinement_suggestions', []), list) and
                isinstance(pb_card.get('misuse_warnings', []), list) and
                isinstance(or_card.get('neglected_areas', []), list) and
                isinstance(or_card.get('overall_exploration_ideas', []), list) and
                isinstance(anti_personas_list, list) # Validate the new list
            ):
                 # Validate scores in opportunity_report_card's neglected_areas
                 valid_opportunity_areas = []
                 for area in or_card.get('neglected_areas', []):
                      if isinstance(area, dict) and 'value_score' in area and isinstance(area['value_score'], (int, float)):
                           valid_opportunity_areas.append(area)
                      else:
                           st.warning(f"Skipping opportunity area due to missing/invalid value_score: {area.get('area_summary', 'Unnamed Opportunity Area')}")
                 or_card['neglected_areas'] = valid_opportunity_areas

                 # Validate suggested_anti_personas list items
                 valid_anti_personas = []
                 for persona in anti_personas_list:
                     if isinstance(persona, dict) and 'persona_name' in persona and 'reason' in persona:
                         valid_anti_personas.append(persona)
                     else:
                         st.warning(f"Skipping invalid anti-persona entry: {persona}")
                 parsed_data['suggested_anti_personas'] = valid_anti_personas # Update with validated list

                 # Validate nested lists and scores and truncate summaries if necessary
                 for card_key, card_data in parsed_data.items():
                      if 'summary' in card_data and isinstance(card_data['summary'], str):
                           if len(card_data['summary']) > 250:
                                card_data['summary'] = card_data['summary'][:247] + "..."

                 return parsed_data
            else:
                st.error("Generated content has incorrect nested list structures or missing fields.")
                st.text_area("Raw Model Output:", raw_text, height=200)
                return None

        else:
            st.error("Generated content is not in the expected top-level JSON format.")
            st.text_area("Raw Model Output:", raw_text, height=200)
            return None

    except Exception as e:
        st.error(f"Error generating anti-persona data: {e}")
        return None

# --- Formatting Functions for Outputs (No longer needed, model generates structured content directly) ---
# The old format_ functions are now fully removed or commented out.

def render(api_key, active_main_tab_index):
    """
    Render the Anti-Persona & Opportunity Cost Analysis section.
    Args:
        api_key (str): The API key for accessing the AI services.
        active_main_tab_index (int): The index of the currently active main tab.
    """
    st.header("Anti-Persona & Opportunity Cost Analysis 🚫")
    st.markdown("""
    <div style='color: #5F6368; font-size: 0.95em; margin-bottom: 1em;'>
        Identify user segments who would *not* be a good fit for your product, and discover potential missed opportunities.
    </div>
    """, unsafe_allow_html=True)

    product_description = st.text_area(
        "Describe your product or service:",
        height=150,
        key="anti_persona_product_description",
        placeholder="e.g., 'Our mobile app helps busy professionals track their daily water intake and sends smart reminders to stay hydrated.'"
    )

    if st.button("📉 Analyze Anti-Personas & Opportunity Costs", use_container_width=True, key="analyze_anti_persona_btn"):
        if not product_description:
            st.warning("Please provide a product or service description.")
        else:
            with st.spinner("Analyzing anti-personas and opportunity costs with Gemini AI..."):
                # anti_persona_results now holds the structured reports directly
                anti_persona_reports = generate_anti_persona_data(product_description, api_key) 
                if anti_persona_reports:
                    st.session_state['anti_persona_reports'] = anti_persona_reports 
                    st.success("Analysis complete! Interactive reports below.")
                    # Preserve the main tab state before rerunning
                    st.session_state.active_main_tab_index = active_main_tab_index
                    st.rerun()
                else:
                    st.error("Failed to generate analysis.")

    # Display Results with Flip Cards
    if 'anti_persona_reports' in st.session_state and st.session_state['anti_persona_reports']:
        reports = st.session_state['anti_persona_reports']

        # Prepare all card HTML, CSS, and JS within a single block for st_html.html
        all_component_html = """
        <style>
            html, body { margin: 0; padding: 0; } /* Reset html and body margins/padding within iframe */

            /* CSS for cards and layout */
            .cards-row {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-evenly; /* Center cards horizontally with even spacing */
                gap: 20px;
                margin-top: 20px;
                margin-bottom: 20px;
                height: 500px; /* Increased height significantly */
            }
            .flip-card-container {
                background-color: transparent;
                width: 350px;
                height: 400px; /* Increased height significantly */
                perspective: 1000px;
                margin: 10px;
                cursor: pointer;
                flex-shrink: 0;
            }
            .flip-card-inner {
                position: relative;
                width: 100%;
                height: 100%;
                text-align: center;
                transition: transform 0.8s;
                transform-style: preserve-3d;
                border-radius: 12px;
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            .flip-card-container.flipped .flip-card-inner {
                transform: rotateY(180deg);
            }
            .flip-card-front, .flip-card-back {
                position: absolute;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                border-radius: 12px;
                display: flex;
                flex-direction: column;
                justify-content: flex-start; /* Ensure content starts from the top */
                align-items: flex-start; /* Ensure content aligns to the left */
                box-sizing: border-box;
                color: #3C4043;
                font-family: 'Inter', sans-serif;
            }
            .flip-card-front {
                background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 0px 10px;
            }
            .flip-card-back {
                background-color: #ffffff;
                transform: rotateY(180deg);
                text-align: left;
                overflow-y: auto;
                font-family: 'Inter', sans-serif;
                padding: 30px 20px 20px 20px; /* Ample top padding */
                display: flex;
                flex-direction: column;
                gap: 20px;
                min-height: 100%;
                box-sizing: border-box;
            }
            .card-title {
                font-size: 1.3em;
                font-weight: 700;
                margin: 0; /* Reset all margins */
                text-align: center;
                width: 100%;
                padding: 0; /* Reset all padding */
                flex-shrink: 0; /* Prevent shrinking */
            }
            .card-summary {
                font-size: 0.95em;
                line-height: 1.5;
                display: block;
                text-align: center; /* Centered text */
            }
            .card-details {
                font-size: 0.95em;
                line-height: 1.7;
                margin: 0; /* Reset all margins */
                width: 100%;
                padding: 0; /* Reset all padding */
                flex-grow: 1;
                flex-shrink: 0; /* Prevent shrinking */
            }
            .card-details h5 {
                font-size: 1.1em;
                margin-top: 0; /* Reset margin-top for subheadings */
                margin-bottom: 8px;
                color: #5F6368;
            }
            .card-details ul {
                padding-left: 20px;
                margin-top: 0; /* Reset margin-top for ul */
                margin-bottom: 10px;
            }
            .card-details li {
                margin-bottom: 5px;
                line-height: 1.5;
            }
            .card-chart-container {
                width: 100%;
                height: 150px;
                margin-top: 15px;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }
        </style>
        <script>
            // Function to toggle the 'flipped' class
            function flipCard(cardId) {
                console.log(`flipCard called for: ${cardId}`); // DEBUG log
                const card = document.getElementById(cardId);
                if (card) {
                    card.classList.toggle('flipped');
                    console.log(`Card ${cardId} flipped!`); // DEBUG log
                } else {
                    console.log(`Card ${cardId} not found!`); // DEBUG log
                }
            }

            // Attach event listeners after the DOM is fully loaded within the iframe
            document.addEventListener('DOMContentLoaded', function() {
                console.log("st_html.html DOMContentLoaded fired."); // DEBUG log
                const cards = document.querySelectorAll('.flip-card-container');
                console.log(`Found ${cards.length} flip card containers within iframe.`); // DEBUG log
                cards.forEach(card => {
                    console.log(`Attaching listener to card with ID: ${card.id}`); // DEBUG log
                    card.addEventListener('click', function() {
                        flipCard(this.id);
                    });
                });
                console.log("Event listeners attachment complete within iframe."); // DEBUG log
            });
        </script>
        <div class='cards-row animated-section'>
        """

        # --- Negative Marketing Card ---
        nm_card = reports.get('negative_marketing_card', {})
        if nm_card:
            nm_details_html = ""
            if nm_card.get("keywords_to_exclude"):
                keywords_html = "".join([f'<li>{item}</li>' for item in nm_card['keywords_to_exclude']])
                nm_details_html += f"<h5>Keywords to Exclude:</h5><ul>{keywords_html}</ul>"
            if nm_card.get("channels_to_deprioritize"):
                channels_html = "".join([f'<li>{item}</li>' for item in nm_card['channels_to_deprioritize']])
                nm_details_html += f"<h5>Channels to Deprioritize:</h5><ul>{channels_html}</ul>"
            if nm_card.get("sales_red_flags"):
                sales_red_flags_html = "".join([f'<li>{item}</li>' for item in nm_card['sales_red_flags']])
                nm_details_html += f"<h5>Sales Red Flags:</h5><ul>{sales_red_flags_html}</ul>"

            all_component_html += f"""
            <div class="flip-card-container" id="nmCard">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div class="card-title">📉 {nm_card.get('title', 'Negative Marketing')}</div>
                        <p class="card-summary">{nm_card.get('summary', 'N/A')}</p>
                    </div>
                    <div class="flip-card-back">
                        <div class="card-title">{nm_card.get('title', 'Negative Marketing')} Details</div>
                        <div class="card-details">
                            {nm_details_html}
                        </div>
                    </div>
                </div>
            </div>
            """

        # --- Product Brief Card ---
        pb_card = reports.get('product_brief_card', {})
        if pb_card:
            pb_details_html = ""
            if pb_card.get("undesirable_features"):
                undesirable_features_html = "".join([f'<li>{item}</li>' for item in pb_card['undesirable_features']])
                pb_details_html += f"<h5>Undesirable Features:</h5><ul>{undesirable_features_html}</ul>"
            if pb_card.get("refinement_suggestions"):
                refinement_suggestions_html = "".join([f'<li>{item}</li>' for item in pb_card['refinement_suggestions']])
                pb_details_html += f"<h5>Refinement Suggestions:</h5><ul>{refinement_suggestions_html}</ul>"
            if pb_card.get("misuse_warnings"):
                misuse_warnings_html = "".join([f'<li>{item}</li>' for item in pb_card['misuse_warnings']])
                pb_details_html += f"<h5>Misuse Warnings:</h5><ul>{misuse_warnings_html}</ul>"

            all_component_html += f"""
            <div class="flip-card-container" id="pbCard">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div class="card-title">🛠️ {pb_card.get('title', 'Product Brief')}</div>
                        <p class="card-summary">{pb_card.get('summary', 'N/A')}</p>
                    </div>
                    <div class="flip-card-back">
                        <div class="card-title">{pb_card.get('title', 'Product Brief')} Details</div>
                        <div class="card-details">
                            {pb_details_html}
                        </div>
                    </div>
                </div>
            </div>
            """

        # --- Opportunity Report Card ---
        or_card = reports.get('opportunity_report_card', {})
        if or_card:
            or_details_html = ""
            opportunity_areas_for_chart = [] # Data for the bar chart

            if 'neglected_areas' in or_card and or_card['neglected_areas']:
                or_details_html += "<h5>Neglected Areas & Value:</h5>"
                for area in or_card['neglected_areas']:
                    summary = area.get('area_summary', 'Unnamed Area')
                    score = area.get('value_score', 'N/A')
                    details = area.get('details', [])
                    or_details_html += f"<h6>{summary} (Value: {score}/5)</h6>"
                    if details:
                        or_details_html += "<ul>"
                        for detail in details:
                            or_details_html += f"<li>{detail}</li>"
                        or_details_html += "</ul>"
                    # Add data for chart
                    if isinstance(score, (int, float)):
                         opportunity_areas_for_chart.append({'Area': summary, 'Value': score})
                or_details_html += "</ul>"
            
            if 'overall_exploration_ideas' in or_card and or_card['overall_exploration_ideas']:
                 or_details_html += "<h5>General Exploration Ideas:</h5><ul>"
                 for idea in or_card['overall_exploration_ideas']:
                      or_details_html += f"<li>{idea}</li>"
                 or_details_html += "</ul>"

            # Generate chart as Base64 image and embed it
            chart_img_base64 = ""
            if opportunity_areas_for_chart:
                df_chart = pd.DataFrame(opportunity_areas_for_chart)
                df_chart = df_chart.set_index('Area')
                
                # Create matplotlib figure and axes
                fig, ax = plt.subplots(figsize=(6, 3.5)) # Adjust size as needed
                df_chart.plot(kind='bar', ax=ax, legend=False, color='#F9AB00')
                ax.set_title('Potential Value Score', fontsize=10)
                ax.set_xlabel('', fontsize=8)
                ax.set_ylabel('Score (1-5)', fontsize=8)
                ax.tick_params(axis='x', rotation=45, labelsize=7)
                ax.tick_params(axis='y', labelsize=8)
                plt.tight_layout()

                # Save plot to BytesIO and encode to Base64
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', transparent=True) # transparent background
                buf.seek(0)
                chart_img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig) # Close the plot to free memory

            chart_html_embed = f"<div class='card-chart-container'><img src='data:image/png;base64,{chart_img_base64}' style='width:100%; height:100%; object-fit: contain;'/></div>" if chart_img_base64 else ""

            all_component_html += f"""
            <div class="flip-card-container" id="orCard">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div class="card-title">💡 {or_card.get('title', 'Opportunity Report')}</div>
                        <p class="card-summary">{or_card.get('summary', 'N/A')}</p>
                    </div>
                    <div class="flip-card-back">
                        <div class="card-title">{or_card.get('title', 'Opportunity Report')} Details</div>
                        <div class="card-details">
                            {or_details_html}
                        </div>
                        {chart_html_embed} <!-- Embedded chart -->
                    </div>
                </div>
            </div>
            """

        all_component_html += "</div>" # Close cards-row container
        
        st_html(all_component_html, height=500, scrolling=False) # Increased height, removed scroll

        # --- Suggested Anti-Personas Section ---
        if 'suggested_anti_personas' in reports and reports['suggested_anti_personas']:
            st.subheader("Suggested Anti-Personas 👻")
            st.markdown("""
            <div style='color: #5F6368; font-size: 0.95em; margin-bottom: 1em;'>
                These are user archetypes that are likely to be a poor fit for your product or service.
            </div>
            """, unsafe_allow_html=True)
            for persona in reports['suggested_anti_personas']:
                st.markdown(f"""
                <div style='background-color: #f0f3f6; padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                    <h6 style='margin-top: 0; margin-bottom: 5px; color: #4285F4;'>{persona.get('persona_name', 'Unnamed Anti-Persona')}</h6>
                    <p style='margin-top: 0; font-size: 0.9em; line-height: 1.4;'>{persona.get('reason', 'No reason provided.')}</p>
                </div>
                """, unsafe_allow_html=True)



