"""
gemini_client.py
================
Gemini API client with:
- 3-level model cascade: gemini-3.7-flash → gemini-3.6-flash → gemini-3.5-flash
- model_callback triggered on each failure before cascading
- Exponential backoff retry within each model
- Google Search Grounding enabled
"""

import logging
import time
from typing import Optional

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

MODEL_CASCADE = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

# Transient errors that warrant retry + cascade (rate limits, server errors)
TRANSIENT_ERRORS = (
    genai_errors.ServerError,   # 5xx — service unavailable, overloaded
    genai_errors.ClientError,   # 429 — quota / rate limit
)


def model_callback(attempted_model: str, error: Exception, attempt: int) -> Optional[str]:
    """
    Callback triggered on each model failure.

    Args:
        attempted_model: The model that just failed.
        error: The exception raised.
        attempt: Retry attempt number within this model (0-indexed).

    Returns:
        The next model name in the cascade, or None if cascade is exhausted.
    """
    logger.warning(
        f"[MODEL CALLBACK] Model '{attempted_model}' failed on attempt {attempt + 1}. "
        f"Reason: {type(error).__name__}: {error}"
    )
    idx = MODEL_CASCADE.index(attempted_model)
    if idx + 1 < len(MODEL_CASCADE):
        next_model = MODEL_CASCADE[idx + 1]
        logger.info(f"[MODEL CALLBACK] Cascading to: '{next_model}'")
        return next_model
    logger.error("[MODEL CALLBACK] Cascade exhausted. All models failed.")
    return None


def call_with_cascade(
    prompt: str,
    api_key: str,
    max_retries: int = 3,
    retry_delay: float = 10.0,
) -> tuple[str, str]:
    """
    Call Gemini API with Google Search Grounding, cascading through models on failure.

    Args:
        prompt: The full prompt string to send.
        api_key: Gemini API key.
        max_retries: Number of retries per model before cascading.
        retry_delay: Base delay in seconds (exponential backoff applied).

    Returns:
        Tuple of (response_text, model_actually_used).

    Raises:
        RuntimeError: If all models in the cascade fail.
    """
    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )

    for model_name in MODEL_CASCADE:
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling model '{model_name}' (attempt {attempt + 1}/{max_retries})...")

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

                response_text = response.text
                logger.info(f"Success with model '{model_name}'.")
                return response_text, model_name

            except TRANSIENT_ERRORS as e:
                model_callback(model_name, e, attempt)
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # exponential backoff
                    logger.info(f"Retrying in {wait_time:.0f}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"All {max_retries} retries exhausted for '{model_name}'. Moving to next model.")
                    break

            except Exception as e:
                # Non-transient error — cascade immediately
                model_callback(model_name, e, attempt)
                break

    raise RuntimeError(
        f"All models in cascade failed: {MODEL_CASCADE}. "
        "Check API key, quota limits, and network connectivity."
    )
