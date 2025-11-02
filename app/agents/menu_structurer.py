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
    temperature=0.1
)


def menu_structurer_agent(state: AgentState) -> AgentState:
    """
    Agent 2: Structure extracted text into organized menu data.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with structured menu data
    """
    try:
        logger.info("Starting menu structuring...")
        
        # Create system prompt for menu structuring
        system_prompt = """You are an expert at analyzing restaurant menu text and extracting structured information.

Your task is to parse the provided menu text and extract:
1. Restaurant name
2. Menu categories (appetizers, mains, desserts, etc.)
3. Menu items with names, descriptions, and prices
4. Restaurant information (contact, hours, address, about section)

Return your response as a JSON object with this exact structure:
{
    "restaurant_name": "Restaurant Name",
    "menu_categories": [
        {
            "name": "Category Name",
            "items": [
                {
                    "name": "Item Name",
                    "description": "Item description",
                    "price": "$XX.XX"
                }
            ]
        }
    ],
    "restaurant_info": {
        "address": "Restaurant address",
        "phone": "Phone number",
        "hours": "Operating hours",
        "about": "Restaurant description/story",
        "website": "Website URL if mentioned"
    }
}

Be precise and accurate. If information is not available, use null or empty strings."""

        # Create human message with extracted text
        human_message = f"Please analyze this restaurant menu text and extract the structured information:\n\n{state.extracted_text}"
        
        # Get LLM response
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        response = llm.invoke(messages)
        structured_data_str = response.content
        
        # Parse JSON response
        try:
            structured_data = json.loads(structured_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Try to extract JSON from response if it's wrapped in markdown
            if "```json" in structured_data_str:
                json_start = structured_data_str.find("```json") + 7
                json_end = structured_data_str.find("```", json_start)
                if json_end > json_start:
                    structured_data = json.loads(structured_data_str[json_start:json_end])
                else:
                    raise e
            else:
                raise e
        
        # Update state with structured data
        state.structured_data = structured_data
        state.restaurant_name = structured_data.get("restaurant_name") if structured_data else "Restaurant"
        state.menu_categories = structured_data.get("menu_categories", []) if structured_data else []
        state.restaurant_info = structured_data.get("restaurant_info", {}) if structured_data else {}
        
        logger.info(f"Menu structuring completed. Found {len(state.menu_categories)} categories for {state.restaurant_name}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in menu structurer agent: {e}")
        # Ensure state remains valid even if parsing fails
        state.structured_data = {}
        state.restaurant_name = "Restaurant"
        state.menu_categories = []
        state.restaurant_info = {}
        state.final_status = "failed"
        state.error_message = f"Menu structuring failed: {str(e)}"
        return state
