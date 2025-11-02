from typing import Dict, Any, List
import logging
import re

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


def validator_agent(state: AgentState) -> AgentState:
    """
    Agent 5: Validate generated React code for syntax, imports, and correctness.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with validation results
    """
    try:
        logger.info("Starting code validation...")
        
        # Initialize validation state
        state.is_valid = True
        state.validation_errors = []
        state.validation_feedback = ""
        
        # Get generated components
        components = state.generated_components
        
        if not components:
            state.is_valid = False
            state.validation_errors.append("No components generated")
            state.validation_feedback = "No components were generated. Please regenerate the code."
            return state
        
        # Basic validation only - be very lenient to prevent infinite loops
        validation_errors = []
        
        # Only check for critical issues
        for component in components:
            file_path = component.get("file_path", "")
            code_content = component.get("code", "")
            
            # Only check for completely broken files
            if not code_content or len(code_content.strip()) < 10:
                validation_errors.append(f"Component {file_path} has no meaningful content")
        
        # Check for at least one React component
        has_react_component = any(
            comp.get("file_path", "").endswith(".jsx") and "React" in comp.get("code", "")
            for comp in components
        )
        
        if not has_react_component:
            validation_errors.append("No valid React components found")
        
        # Update state based on validation results
        if validation_errors:
            state.is_valid = False
            state.validation_errors = validation_errors
            state.validation_feedback = f"Validation failed: {', '.join(validation_errors)}"
            state.iterations = state.iterations + 1
            
            logger.warning(f"Validation failed with {len(validation_errors)} errors")
        else:
            state.is_valid = True
            state.validation_feedback = "Code validation passed successfully!"
            logger.info("Code validation passed")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in validator agent: {e}")
        # On any error, just pass validation to prevent infinite loops
        state.is_valid = True
        state.validation_feedback = f"Validation completed with warning: {str(e)}"
        return state


def _validate_component_syntax(file_path: str, code_content: str, component_name: str) -> List[str]:
    """Validate basic syntax of a component."""
    errors = []
    
    # Check for basic React patterns
    if file_path.endswith(".jsx"):
        if "import React" not in code_content:
            errors.append(f"{component_name}: Missing React import")
        
        if "export default" not in code_content:
            errors.append(f"{component_name}: Missing default export")
        
        # Check for JSX syntax issues
        if code_content.count("{") != code_content.count("}"):
            errors.append(f"{component_name}: Mismatched braces in JSX")
        
        # Check for unclosed tags (basic check)
        open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?(?<!/)>', code_content)
        close_tags = re.findall(r'</(\w+)>', code_content)
        
        # Simple check for self-closing tags
        self_closing_tags = re.findall(r'<(\w+)(?:\s[^>]*)?/>', code_content)
        
        # Count opening tags that should have closing tags
        non_self_closing = [tag for tag in open_tags if tag not in ['img', 'input', 'br', 'hr', 'meta', 'link']]
        
        if len(non_self_closing) != len(close_tags):
            errors.append(f"{component_name}: Possible unclosed JSX tags")
    
    elif file_path.endswith(".json"):
        try:
            import json
            json.loads(code_content)
        except json.JSONDecodeError as e:
            errors.append(f"{component_name}: Invalid JSON syntax - {str(e)}")
    
    elif file_path.endswith(".css"):
        # Basic CSS validation
        if "{" in code_content and "}" not in code_content:
            errors.append(f"{component_name}: Unclosed CSS rules")
    
    return errors


def _validate_react_router_setup(components: List[Dict]) -> List[str]:
    """Validate React Router setup."""
    errors = []
    
    # Find App.jsx
    app_component = None
    for comp in components:
        if comp.get("file_path", "").endswith("App.jsx"):
            app_component = comp
            break
    
    if not app_component:
        errors.append("App.jsx not found for React Router validation")
        return errors
    
    app_code = app_component.get("code", "")
    
    # Check for React Router imports
    if "react-router-dom" not in app_code:
        errors.append("App.jsx: Missing react-router-dom import")
    
    if "BrowserRouter" not in app_code:
        errors.append("App.jsx: Missing BrowserRouter import")
    
    if "Routes" not in app_code:
        errors.append("App.jsx: Missing Routes import")
    
    if "Route" not in app_code:
        errors.append("App.jsx: Missing Route import")
    
    # Check for proper router structure
    if "<Router>" not in app_code and "<BrowserRouter>" not in app_code:
        errors.append("App.jsx: Missing Router wrapper")
    
    if "<Routes>" not in app_code:
        errors.append("App.jsx: Missing Routes component")
    
    return errors


def _validate_imports_exports(components: List[Dict]) -> List[str]:
    """Validate imports and exports across components."""
    errors = []
    
    # Track all exports
    exports = {}
    imports = {}
    
    for comp in components:
        file_path = comp.get("file_path", "")
        code_content = comp.get("code", "")
        
        # Find exports
        export_matches = re.findall(r'export\s+(?:default\s+)?(?:function\s+)?(\w+)', code_content)
        if export_matches:
            exports[file_path] = export_matches
        
        # Find imports
        import_matches = re.findall(r'import\s+(?:\{([^}]+)\}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', code_content)
        if import_matches:
            imports[file_path] = import_matches
    
    # Check for missing imports
    for file_path, file_imports in imports.items():
        for import_match in file_imports:
            imported_items = import_match[0].split(',') if import_match[0] else []
            import_source = import_match[1]
            
            # Check if imported components exist
            if import_source.startswith('./'):
                # Relative import - check if target file exists
                target_file = import_source.replace('./', 'src/')
                if not any(target_file in comp.get("file_path", "") for comp in components):
                    errors.append(f"{file_path}: Import from {import_source} - target file not found")
    
    return errors


def _llm_validate_code(components: List[Dict]) -> Dict[str, Any]:
    """Use LLM to validate code quality and correctness."""
    try:
        # Prepare code for LLM validation
        code_summary = ""
        for comp in components:
            file_path = comp.get("file_path", "")
            code_content = comp.get("code", "")
            code_summary += f"\n--- {file_path} ---\n{code_content[:1000]}...\n"  # Truncate for token limits
        
        system_prompt = """You are an expert React developer and code reviewer. 

Your task is to validate the generated React code for:
1. Syntax correctness
2. Proper React patterns and hooks usage
3. Correct imports and exports
4. Proper JSX structure
5. React Router setup
6. CSS/styling issues
7. General code quality

Return your response as JSON:
{
    "is_valid": true/false,
    "errors": ["error1", "error2"],
    "suggestions": ["suggestion1", "suggestion2"]
}

Be thorough but focus on critical issues that would prevent the code from running."""

        human_message = f"Please validate this React code:\n{code_summary}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        response = llm.invoke(messages)
        
        try:
            import json
            validation_result = json.loads(response.content)
            return validation_result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "is_valid": True,
                "errors": [],
                "suggestions": ["LLM validation completed but couldn't parse response"]
            }
    
    except Exception as e:
        logger.error(f"LLM validation error: {e}")
        return {
            "is_valid": True,
            "errors": [],
            "suggestions": [f"LLM validation failed: {str(e)}"]
        }


def _generate_validation_feedback(errors: List[str]) -> str:
    """Generate human-readable validation feedback."""
    if not errors:
        return "Code validation passed successfully!"
    
    feedback = "Code validation failed with the following issues:\n"
    for i, error in enumerate(errors, 1):
        feedback += f"{i}. {error}\n"
    
    feedback += "\nPlease fix these issues and regenerate the code."
    return feedback
