import streamlit as st
from shared import generate_problem_solution_persona, generate_persona_image, text_model, parse_gemini_json_response
import plotly.graph_objects as go
import pandas as pd
import json
from streamlit.components.v1 import html as st_html

def generate_solution_ideas(persona_data):
    """
    Generates solution ideas based on the problem-solution persona data.
    Returns a structured dictionary of solution ideas with implementation details.
    """
    prompt = f"""
    Based on the following problem-solution persona data, generate innovative solution ideas that address the core problem.
    Focus on practical, implementable solutions that align with the persona's needs and expectations.

    Persona Data:
    {json.dumps(persona_data, indent=2)}

    Generate the output as a JSON object with the following structure:
    {{
        "solution_ideas": [
            {{
                "title": "Solution name/title",
                "description": "Brief description of the solution",
                "key_features": ["feature1", "feature2", "feature3"],
                "implementation_steps": ["step1", "step2", "step3"],
                "potential_challenges": ["challenge1", "challenge2"],
                "success_metrics": ["metric1", "metric2"]
            }}
        ],
        "prioritization": {{
            "high_priority": ["solution1", "solution2"],
            "medium_priority": ["solution3"],
            "low_priority": ["solution4"]
        }},
        "implementation_timeline": {{
            "phase1": {{
                "duration": "X weeks",
                "activities": ["activity1", "activity2"]
            }},
            "phase2": {{
                "duration": "Y weeks",
                "activities": ["activity3", "activity4"]
            }}
        }}
    }}

    Ensure the response is ONLY a valid JSON object with no extra text or markdown outside the JSON block.
    """

    try:
        response = text_model.generate_content(prompt)
        solution_data = parse_gemini_json_response(response.text)
        return solution_data
    except Exception as e:
        st.error(f"Error generating solution ideas: {e}")
        return None

def create_solution_card(solution):
    """Creates a styled card for displaying a solution idea."""
    key_features_html = ''.join([f'<li>{feature}</li>' for feature in solution['key_features']])
    implementation_steps_html = ''.join([f'<li>{step}</li>' for step in solution['implementation_steps']])
    potential_challenges_html = ''.join([f'<li>{challenge}</li>' for challenge in solution['potential_challenges']])
    success_metrics_html = ''.join([f'<li>{metric}</li>' for metric in solution['success_metrics']])

    html_template = r"""
    <div style="background-color: #ffffff; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1a73e8; margin-top: 0;">{title}</h3>
        <p style="color: #5f6368;">{description}</p>
        
        <div style="margin-top: 15px;">
            <h4 style="color: #202124; margin-bottom: 10px;">Key Features:</h4>
            <ul style="color: #5f6368; margin-top: 0;">
                {key_features}
            </ul>
        </div>
        
        <div style="margin-top: 15px;">
            <h4 style="color: #202124; margin-bottom: 10px;">Implementation Steps:</h4>
            <ol style="color: #5f6368; margin-top: 0;">
                {implementation_steps}
            </ol>
        </div>
        
        <div style="margin-top: 15px;">
            <h4 style="color: #202124; margin-bottom: 10px;">Potential Challenges:</h4>
            <ul style="color: #5f6368; margin-top: 0;">
                {potential_challenges}
            </ul>
        </div>
        
        <div style="margin-top: 15px;">
            <h4 style="color: #202124; margin-bottom: 10px;">Success Metrics:</h4>
            <ul style="color: #5f6368; margin-top: 0;">
                {success_metrics}
            </ul>
        </div>
    </div>
    """
    return html_template.format(
        title=solution['title'],
        description=solution['description'],
        key_features=key_features_html,
        implementation_steps=implementation_steps_html,
        potential_challenges=potential_challenges_html,
        success_metrics=success_metrics_html
    )

def create_timeline_card(timeline):
    """Creates a styled card for displaying the implementation timeline."""
    timeline_html_content = ""
    for phase, details in timeline.items():
        activities_html = ''.join([f'<li>{activity}</li>' for activity in details['activities']])
        timeline_html_content += r"""
        <div style="margin-top: 15px;">
            <h4 style="color: #202124; margin-bottom: 10px;">{phase_title} ({duration})</h4>
            <ul style="color: #5f6368; margin-top: 0;">
                {activities}
            </ul>
        </div>
        """.format(
            phase_title=phase.replace('_', ' ').title(),
            duration=details['duration'],
            activities=activities_html
        )
    
    html_template = r"""
    <div style="background-color: #ffffff; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1a73e8; margin-top: 0;">Implementation Timeline</h3>
        {content}
    </div>
    """
    return html_template.format(content=timeline_html_content)

def create_fit_score_chart(current_solutions, ideal_solution):
    """Creates a radar chart comparing current solutions vs ideal solution."""
    categories = ['Ease of Use', 'Cost Efficiency', 'Time Savings', 'Reliability', 'Scalability']
    
    # Generate scores based on the descriptions
    current_scores = [3, 2, 2, 3, 2]  # Example scores for current solutions
    ideal_scores = [5, 4, 5, 5, 4]    # Example scores for ideal solution
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=current_scores,
        theta=categories,
        fill='toself',
        name='Current Solutions'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=ideal_scores,
        theta=categories,
        fill='toself',
        name='Ideal Solution'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        showlegend=True,
        height=400,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig

def render(api_key):
    st.header("Problem-Solution Fit 🧩")
    st.markdown("""
    <div style='color: #5F6368; font-size: 0.95em; margin-bottom: 1em;'>
        Define a core problem, and AI will generate a persona that embodies that problem, along with insights into ideal solutions.
    </div>
    """, unsafe_allow_html=True)

    # Problem Statement Input
    problem_statement_input = st.text_area(
        "Describe a specific problem your target customers face:",
        height=150,
        key="problem_statement_input",
        placeholder="e.g., 'Small business owners struggle to manage their inventory efficiently across multiple sales channels, leading to stockouts and overstocking.'"
    )

    if st.button("🔍 Generate Problem-Solution Persona", use_container_width=True, key="generate_problem_persona_btn"):
        if problem_statement_input:
            with st.spinner("Analyzing problem and generating persona..."):
                problem_persona = generate_problem_solution_persona(problem_statement_input)
                if problem_persona:
                    st.session_state['problem_solution_persona'] = problem_persona
                    st.success("Problem-Solution Persona generated successfully!")
                    
                    # Generate and store avatar
                    if 'visual_avatar_description' in problem_persona and problem_persona['visual_avatar_description']:
                        with st.spinner("Generating persona avatar..."):
                            avatar_image = generate_persona_image(problem_persona['visual_avatar_description'], api_key)
                            if avatar_image:
                                st.session_state['problem_solution_avatar'] = avatar_image
                            # else:
                                # st.warning("Failed to generate avatar image.") # Removed debug warning
                    st.rerun()
                else:
                    st.error("Failed to generate problem-solution persona.")
        else:
            st.warning("Please provide a problem statement to generate a persona.")

    # Display Results
    if 'problem_solution_persona' in st.session_state:
        persona = st.session_state['problem_solution_persona']
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display Avatar
            if 'problem_solution_avatar' in st.session_state:
                st.image(st.session_state['problem_solution_avatar'], use_container_width=True)
            
            # Persona Overview
            st.subheader("👤 Persona Overview")
            st.markdown(f"""
            <div style='background-color: #f0f3f6; padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                <h4 style='margin-top: 0; color: #1a73e8;'>{persona.get('name', 'Unnamed Persona')}</h4>
                <p style='margin-bottom: 5px;'><strong>Archetype:</strong> {persona.get('archetype', 'N/A')}</p>
                <p style='margin-bottom: 5px;'><strong>Problem Summary:</strong> {persona.get('problem_description_from_persona_view_summary', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Problem-Solution Analysis
            st.subheader("📊 Problem-Solution Analysis")
            
            # Create tabs for different aspects
            if 'active_problem_solution_tab_index' not in st.session_state:
                st.session_state.active_problem_solution_tab_index = 0

            tab_titles = ["Current vs Ideal", "Motivations & Pain Points", "Solution Expectations"]
            selected_tab_title = st.radio("Problem Solution Tabs", tab_titles, index=st.session_state.active_problem_solution_tab_index, horizontal=True, label_visibility="hidden")
            st.session_state.active_problem_solution_tab_index = tab_titles.index(selected_tab_title)

            if selected_tab_title == "Current vs Ideal":
                st.markdown("### Current Solutions vs Ideal Solution")
                current_solutions = persona.get('current_solutions_and_their_flaws_details', [])
                ideal_solution = persona.get('ideal_solution_expectations_details', [])
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("#### Current Solutions")
                    for solution in current_solutions:
                        st.markdown(f"- {solution}")
                
                with col_b:
                    st.markdown("#### Ideal Solution")
                    for expectation in ideal_solution:
                        st.markdown(f"- {expectation}")
                
                st.plotly_chart(create_fit_score_chart(current_solutions, ideal_solution), use_container_width=True)
            
            elif selected_tab_title == "Motivations & Pain Points":
                st.markdown("### Motivations & Pain Points")
                col_m, col_p = st.columns(2)
                
                with col_m:
                    st.markdown("#### Core Motivations")
                    st.markdown(f"**Summary:** {persona.get('motivations_related_to_problem_summary', 'N/A')}")
                    for motivation in persona.get('motivations_related_to_problem_details', []):
                        st.markdown(f"- {motivation}")
                
                with col_p:
                    st.markdown("#### Pain Points")
                    st.markdown(f"**Summary:** {persona.get('pain_points_related_to_problem_summary', 'N/A')}")
                    for pain_point in persona.get('pain_points_related_to_problem_details', []):
                        st.markdown(f"- {pain_point}")
            
            elif selected_tab_title == "Solution Expectations":
                st.markdown("### Solution Expectations")
                st.markdown(f"**Summary:** {persona.get('ideal_solution_expectations_summary', 'N/A')}")
                for expectation in persona.get('ideal_solution_expectations_details', []):
                    st.markdown(f"- {expectation}")
                
                if st.button("💡 Generate Solution Ideas", use_container_width=True):
                    with st.spinner("Generating innovative solution ideas..."):
                        solution_data = generate_solution_ideas(persona)
                        if solution_data:
                            st.session_state['solution_ideas'] = solution_data
                            st.success("Solution ideas generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate solution ideas.")

    # Display Solution Ideas if available
    if 'solution_ideas' in st.session_state:
        st.markdown("---")
        st.header("🎯 Generated Solution Ideas")
        
        # Display prioritization
        prioritization = st.session_state['solution_ideas'].get('prioritization', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### High Priority")
            for solution in prioritization.get('high_priority', []):
                st.markdown(f"- {solution}")
        
        with col2:
            st.markdown("### Medium Priority")
            for solution in prioritization.get('medium_priority', []):
                st.markdown(f"- {solution}")
        
        with col3:
            st.markdown("### Low Priority")
            for solution in prioritization.get('low_priority', []):
                st.markdown(f"- {solution}")
        
        # Display detailed solution cards
        st.markdown("### Detailed Solution Proposals")
        for solution in st.session_state['solution_ideas'].get('solution_ideas', []):
            solution_card_html = create_solution_card(solution)
            st_html(solution_card_html, height=400, scrolling=True) # Use st_html for robust rendering
        
        # Display implementation timeline
        timeline_card_html = create_timeline_card(st.session_state['solution_ideas'].get('implementation_timeline', {}))
        st_html(timeline_card_html, height=300, scrolling=True) 