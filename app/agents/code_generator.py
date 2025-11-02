from typing import Dict, Any, List
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
    temperature=0.2
)


def code_generator_agent(state: AgentState) -> AgentState:
    """
    Agent 4: Generate complete React SPA with routing using LLM.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with generated React components
    """
    try:
        logger.info("Starting code generation...")
        
        # Prepare context data
        restaurant_name = state.restaurant_name or "Restaurant"
        menu_categories = state.menu_categories or []
        restaurant_info = state.restaurant_info or {}
        design_system = state.design_system or {}
        typography = state.typography or {}
        layout_style = state.layout_style or "modern"
        
        # Create system prompt for React code generation
        system_prompt = """You are an expert React developer specializing in creating modern, responsive restaurant websites.

Your task is to generate a complete React Single Page Application with the following requirements:

1. **File Structure**: Generate these files:
   - package.json (with React dependencies)
   - public/index.html (HTML template)
   - src/index.js (entry point)
   - src/App.jsx (main app with React Router)
   - src/index.css (global styles with CSS variables)
   - src/components/Home.jsx (hero section + features)
   - src/components/Menu.jsx (menu display)
   - src/components/About.jsx (restaurant story)
   - src/components/Contact.jsx (contact info)
   - src/components/Navigation.jsx (navigation bar)

2. **React Router Setup**: Use React Router v6 with routes for /, /menu, /about, /contact

3. **Design System**: Use the provided design system (colors, typography, spacing) as CSS variables

4. **Responsive Design**: Make it mobile-first and responsive

5. **Modern React**: Use functional components, hooks, and modern patterns

6. **Code Quality**: Clean, readable, well-structured code

Return your response as a JSON object with this exact structure:
{
  "components": [
    {
      "file_path": "package.json",
      "code": "file content here",
      "component_name": "package.json"
    },
    {
      "file_path": "src/App.jsx", 
      "code": "file content here",
      "component_name": "App.jsx"
    }
    // ... more files
  ]
}

Make sure all imports and exports are correct, and the code is production-ready."""

        # Prepare context for code generation
        context = f"""
Restaurant: {restaurant_name}
Menu Categories: {json.dumps(menu_categories, indent=2)}
Restaurant Info: {json.dumps(restaurant_info, indent=2)}
Design System: {json.dumps(design_system, indent=2)}
Typography: {json.dumps(typography, indent=2)}
Layout Style: {layout_style}
"""
        
        human_message = f"Generate a complete React SPA for this restaurant:\n\n{context}"
        
        # Get LLM response
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        response = llm.invoke(messages)
        code_data_str = response.content
        
        # Parse JSON response
        try:
            code_data = json.loads(code_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse code generation JSON response: {e}")
            # Try to extract JSON from response if it's wrapped in markdown
            if "```json" in code_data_str:
                json_start = code_data_str.find("```json") + 7
                json_end = code_data_str.find("```", json_start)
                if json_end > json_start:
                    code_data = json.loads(code_data_str[json_start:json_end])
                else:
                    raise e
            else:
                raise e
        
        # Extract components from response
        components = code_data.get("components", [])
        
        # Update state
        state.generated_components = components
        state.component_files = components
        
        logger.info(f"Code generation completed. Generated {len(components)} components")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in code generator agent: {e}")
        state.final_status = "failed"
        state.error_message = f"Code generation failed: {str(e)}"
        return state
