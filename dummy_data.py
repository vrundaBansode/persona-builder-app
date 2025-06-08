import streamlit as st
from PIL import Image
import io
import base64
from shared import generate_persona_image

# Dummy persona data
DUMMY_PERSONA = {
    'name': 'Sarah Chen',
    'archetype': 'Tech-Savvy Professional',
    'motivations_summary': 'Career growth and work-life balance',
    'motivations_details': [
        'Advancing in her tech career',
        'Maintaining work-life balance',
        'Staying updated with latest technologies'
    ],
    'pain_points_summary': 'Time management and skill development',
    'pain_points_details': [
        'Struggling to find time for learning new skills',
        'Difficulty balancing work and personal development',
        'Overwhelmed by rapid technological changes'
    ],
    'aspirations_summary': 'Becoming a tech leader',
    'aspirations_details': [
        'Leading innovative tech projects',
        'Mentoring junior developers',
        'Contributing to open-source projects'
    ],
    'typical_scenario': 'Sarah is a senior software engineer who works remotely for a tech company. She spends her days coding, attending virtual meetings, and trying to find time for learning new technologies. She often feels overwhelmed by the rapid pace of technological change and struggles to maintain a healthy work-life balance while advancing her career.',
    'visual_avatar_description': 'A professional Asian woman in her early 30s with a friendly smile, wearing business casual attire, in a modern office setting with a laptop and coffee cup. The style is clean, minimalist, and professional.',
    'avatar_image': None  # This will be set when the app initializes
}

def generate_dummy_avatar(api_key):
    """Generate an avatar for the dummy persona."""
    try:
        avatar = generate_persona_image(DUMMY_PERSONA['visual_avatar_description'], api_key)
        if avatar:
            DUMMY_PERSONA['avatar_image'] = avatar
            return True
    except Exception as e:
        st.error(f"Error generating dummy avatar: {e}")
    return False

def initialize_dummy_persona(api_key):
    """Initialize the dummy persona in the session state if it doesn't exist."""
    if 'generated_personas' not in st.session_state:
        st.session_state.generated_personas = [DUMMY_PERSONA]
    elif not st.session_state.generated_personas:
        st.session_state.generated_personas = [DUMMY_PERSONA]
    
    # Set the selected persona index
    if 'selected_persona_index' not in st.session_state:
        st.session_state.selected_persona_index = 0
    
    # Generate avatar if not already present
    if DUMMY_PERSONA['avatar_image'] is None:
        generate_dummy_avatar(api_key)

def get_dummy_persona():
    """Return the dummy persona data."""
    return DUMMY_PERSONA 