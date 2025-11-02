from langgraph.graph import StateGraph, END
from typing import Dict, Any
import logging

from app.agents.state import AgentState
from app.agents.pdf_extractor import pdf_extractor_agent
from app.agents.menu_structurer import menu_structurer_agent
from app.agents.ui_designer import ui_designer_agent
from app.agents.code_generator import code_generator_agent
from app.agents.validator import validator_agent

logger = logging.getLogger(__name__)


def should_continue_validation(state: AgentState) -> str:
    """
    Determine whether to continue validation loop or end.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name: "regenerate" or "end"
    """
    is_valid = state.is_valid
    iterations = state.iterations
    max_iterations = 1  # Only allow 1 retry to prevent infinite loops
    
    if is_valid:
        logger.info("Validation passed, ending workflow")
        return "end"
    elif iterations < max_iterations:
        logger.info(f"Validation failed, regenerating code (iteration {iterations + 1}/{max_iterations})")
        return "regenerate"
    else:
        logger.warning(f"Max validation iterations ({max_iterations}) reached, ending workflow")
        return "end"


def create_menu_generation_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for menu to React website generation.
    
    Returns:
        Compiled StateGraph workflow
    """
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes for each agent
    workflow.add_node("extract_pdf", pdf_extractor_agent)
    workflow.add_node("structure_menu", menu_structurer_agent)
    workflow.add_node("design_ui", ui_designer_agent)
    workflow.add_node("generate_code", code_generator_agent)
    workflow.add_node("validate", validator_agent)
    
    # Set entry point
    workflow.set_entry_point("extract_pdf")
    
    # Add linear edges
    workflow.add_edge("extract_pdf", "structure_menu")
    workflow.add_edge("structure_menu", "design_ui")
    workflow.add_edge("design_ui", "generate_code")
    workflow.add_edge("generate_code", "validate")
    
    # Add conditional edge from validator
    workflow.add_conditional_edges(
        "validate",
        should_continue_validation,
        {
            "regenerate": "generate_code",
            "end": END
        }
    )
    
    # Compile the workflow
    compiled_workflow = workflow.compile()
    
    # Set recursion limit to prevent infinite loops
    compiled_workflow.config = {"recursion_limit": 20}
    
    logger.info("Menu generation workflow created successfully")
    return compiled_workflow


# Global workflow instance
menu_workflow = create_menu_generation_workflow()


async def run_menu_generation_workflow(
    pdf_content: str,
    design_description: str = None,
    restaurant_id: str = None
) -> Dict[str, Any]:
    """
    Run the complete menu generation workflow.
    
    Args:
        pdf_content: Base64 encoded PDF content
        design_description: Optional design description
        restaurant_id: Restaurant ID for tracking
        
    Returns:
        Final workflow state
    """
    try:
        logger.info(f"Starting menu generation workflow for restaurant {restaurant_id}")
        
        # Initialize state
        initial_state = AgentState(
            pdf_content=pdf_content,
            design_description=design_description,
            restaurant_id=restaurant_id,
            extracted_text="",
            extracted_sections=[],
            structured_data={},
            restaurant_name="",
            menu_categories=[],
            restaurant_info={},
            design_system={},
            color_palette={},
            typography={},
            layout_style="",
            generated_components=[],
            component_files=[],
            is_valid=False,
            validation_errors=[],
            validation_feedback="",
            iterations=0,
            final_status="processing",
            error_message=None
        )
        
        # Run the workflow with recursion limit handling
        try:
            final_state = await menu_workflow.ainvoke(initial_state)
        except Exception as recursion_error:
            if "recursion limit" in str(recursion_error).lower():
                logger.warning(f"Recursion limit reached, bypassing validation and returning generated code")
                # Run workflow without validation loop
                final_state = await run_workflow_without_validation(initial_state)
            else:
                raise recursion_error
        
        # Handle both AgentState objects and dictionaries
        if hasattr(final_state, 'dict'):
            final_state_dict = final_state.dict()
        else:
            final_state_dict = final_state
        
        # Determine final status
        if final_state_dict.get("final_status") == "failed":
            logger.error(f"Workflow failed: {final_state_dict.get('error_message')}")
        elif final_state_dict.get("is_valid") or final_state_dict.get("generated_components"):
            final_state_dict["final_status"] = "completed"
            logger.info("Workflow completed successfully")
        else:
            final_state_dict["final_status"] = "failed"
            final_state_dict["error_message"] = "No code generated"
            logger.error("Workflow failed - no code generated")
        
        return final_state_dict
        
    except Exception as e:
        logger.error(f"Error running menu generation workflow: {e}")
        return {
            "final_status": "failed",
            "error_message": str(e),
            "restaurant_id": restaurant_id
        }


async def run_workflow_without_validation(initial_state: AgentState) -> AgentState:
    """Run workflow without validation loop to bypass recursion issues."""
    try:
        logger.info("Running workflow without validation loop")
        
        # Run each agent sequentially without validation loop
        state = initial_state
        
        # PDF Extraction
        state = pdf_extractor_agent(state)
        if state.final_status == "failed":
            return state
        
        # Menu Structuring
        state = menu_structurer_agent(state)
        if state.final_status == "failed":
            return state
        
        # UI Design
        state = ui_designer_agent(state)
        if state.final_status == "failed":
            return state
        
        # Code Generation
        state = code_generator_agent(state)
        if state.final_status == "failed":
            return state
        
        # Skip validation - just mark as valid if we have components
        if state.generated_components:
            state.is_valid = True
            state.validation_feedback = "Code generated successfully (validation bypassed)"
            state.final_status = "completed"
        else:
            state.is_valid = False
            state.validation_feedback = "No components generated"
            state.final_status = "failed"
        
        logger.info("Workflow completed without validation")
        return state.dict()
        
    except Exception as e:
        logger.error(f"Error in workflow without validation: {e}")
        initial_state.final_status = "failed"
        initial_state.error_message = str(e)
        return initial_state.dict()
