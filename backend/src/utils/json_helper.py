import json
import logging
from pydantic import ValidationError

logger = logging.getLogger(__name__)

def parse_and_validate_json(raw_text: str, schema_class, mapper_func=None):
    """
    Cleans raw LLM response text, parses it as JSON, runs custom key mapping
    to normalize slight key deviations, and validates it against the specified Pydantic schema.
    """
    cleaned_text = raw_text.strip()
    
    # Strip markdown backticks if outputted by the LLM
    if cleaned_text.startswith("```"):
        lines = cleaned_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned_text = "\n".join(lines).strip()
        
    logger.info(f"Raw LLM response received:\n{raw_text}")
    logger.info(f"Cleaned LLM response for JSON loads:\n{cleaned_text}")
    
    try:
        parsed_json = json.loads(cleaned_text)
        logger.info(f"Successfully deserialized raw JSON payload.")
    except Exception as e:
        logger.error(f"JSON deserialization failed: {e}. Raw payload: {raw_text}")
        raise ValueError(f"LLM output is not syntactically valid JSON: {e}")
        
    # Apply mapping transformer if defined
    if mapper_func:
        try:
            parsed_json = mapper_func(parsed_json)
            logger.info("Custom key mapping successfully applied.")
        except Exception as e:
            logger.warning(f"Key mapping transformer failed: {e}. Using raw parsed JSON.")
            
    # Run Pydantic validation
    try:
        validated_obj = schema_class.model_validate(parsed_json)
        logger.info(f"Pydantic validation passed for schema: {schema_class.__name__}")
        return validated_obj
    except ValidationError as ve:
        logger.error(f"Pydantic validation failed for schema {schema_class.__name__}.\nValidation errors: {ve}\nPayload: {parsed_json}")
        raise ve

def invoke_llm_with_fallback(model_name: str, messages: list, temperature: float = 0.0) -> str:
    """
    Invokes ChatGroq. If it hits a rate limit (429), falls back to a different model 
    (e.g., 'llama-3.1-8b-instant' or 'gemma2-9b-it') to keep the analysis online.
    """
    from langchain_groq import ChatGroq
    from src.core.config import settings
    
    try:
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=model_name,
            temperature=temperature
        )
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg or "rate_limit" in err_msg or "rate limit" in err_msg:
            fallback_models = ["llama-3.1-8b-instant", "gemma2-9b-it", "mixtral-8x7b-32768"]
            for fallback in fallback_models:
                if fallback != model_name:
                    logger.warning(f"Rate limit hit for {model_name}. Falling back to {fallback}...")
                    try:
                        llm = ChatGroq(
                            api_key=settings.GROQ_API_KEY,
                            model_name=fallback,
                            temperature=temperature
                        )
                        response = llm.invoke(messages)
                        return response.content
                    except Exception as fe:
                        logger.error(f"Fallback model {fallback} also failed: {fe}")
        raise e
