from typing import Dict, Any
import logging
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    model="gpt-4",
    api_key=settings.openai_api_key,
    temperature=0.3
)


def ui_designer_agent(state: AgentState) -> AgentState:
    """
    Agent 3: Generate design system and UI specifications.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with design system
    """
    try:
        logger.info("Starting UI design...")
        
        # Create system prompt for UI design
        system_prompt = """You are a professional UI/UX designer specializing in modern restaurant websites.

Your task is to create a beautiful, responsive design system for a restaurant website based on the provided menu data and optional design description.

If a design description is provided, follow it closely. If not, create a modern, elegant design that's not typical - think contemporary, sophisticated, and visually appealing.

Return your response as a JSON object with this exact structure:
{
    "design_system": {
        "primary_color": "#hexcode",
        "secondary_color": "#hexcode", 
        "accent_color": "#hexcode",
        "background_color": "#hexcode",
        "text_color": "#hexcode",
        "text_secondary": "#hexcode"
    },
    "typography": {
        "heading_font": "Font Name",
        "body_font": "Font Name",
        "heading_size": "2.5rem",
        "body_size": "1rem",
        "small_size": "0.875rem"
    },
    "layout_style": "modern|minimalist|elegant|rustic|contemporary",
    "component_styles": {
        "button_style": "rounded|square|pill",
        "card_style": "elevated|flat|outlined",
        "navigation_style": "horizontal|vertical|hamburger"
    },
    "spacing": {
        "small": "0.5rem",
        "medium": "1rem", 
        "large": "2rem",
        "xl": "3rem"
    }
}

Choose colors that work well together and create an appealing, professional look. Use modern web fonts available via Google Fonts.
Make the design sophisticated and contemporary - avoid generic restaurant website aesthetics."""

        # Prepare context for design
        restaurant_name = state.restaurant_name or "Restaurant"
        menu_categories = state.menu_categories or []
        design_description = state.design_description or ""
        
        # Create human message
        context = f"""
Restaurant: {restaurant_name}
Menu Categories: {', '.join([cat.get('name', '') for cat in menu_categories])}
Design Description: {design_description if design_description else "No specific design requirements - create a modern, sophisticated design"}
"""
        
        human_message = f"Create a design system for this restaurant website:\n\n{context}"
        
        # Get LLM response
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        response = llm.invoke(messages)
        design_data_str = response.content
        
        # Parse JSON response
        try:
            design_data = json.loads(design_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse design JSON response: {e}")
            # Try to extract JSON from response if it's wrapped in markdown
            if "```json" in design_data_str:
                json_start = design_data_str.find("```json") + 7
                json_end = design_data_str.find("```", json_start)
                if json_end > json_start:
                    design_data = json.loads(design_data_str[json_start:json_end])
                else:
                    raise e
            else:
                raise e
        
        # Update state with design data
        state.design_system = design_data.get("design_system", {})
        state.color_palette = design_data.get("design_system", {})
        state.typography = design_data.get("typography", {})
        state.layout_style = design_data.get("layout_style", "modern")
        
        logger.info(f"UI design completed. Style: {state.layout_style}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in UI designer agent: {e}")
        state.final_status = "failed"
        state.error_message = f"UI design failed: {str(e)}"
        return state
