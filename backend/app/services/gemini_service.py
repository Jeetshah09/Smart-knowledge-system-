"""Google Gemini integration.

All AI calls go through this service so the API key stays in the backend .env
and the rest of the codebase never talks to Gemini directly.
"""
import json
import logging
import random
import re
import time
from typing import Any

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

from app.core.config import settings
from app.utils.text_utils import truncate_for_prompt

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 90  # per-attempt ceiling; the server never hangs forever
RATE_LIMIT_MESSAGE = (
    "The free-tier AI limit was reached (about 10 requests per minute). "
    "Please wait a few seconds and try again."
)

# gemini-flash-latest currently resolves to a thinking model that burns the
# whole token budget reasoning and often returns empty answers; flash-lite
# answers in ~1-2s. We try the configured model first and fall back through
# this chain so a single dead/retired/slow alias can never take the app down.
MODEL_FALLBACK_CHAIN = [
    None,  # the configured default model
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
]

# Provider-neutral model aliases exposed to the API layer. Clients only ever
# send/receive these keys - real provider model IDs stay server-side.
MODEL_ALIASES: dict[str, str] = {
    "fast": "gemini-flash-lite-latest",
    "balanced": "gemini-flash-latest",
    "advanced": "gemini-2.5-pro",
    "turbo": "gemini-3.6-flash",
}
DEFAULT_MODEL_ALIAS = "fast"


def resolve_model(alias: str | None) -> str:
    """Map a provider-neutral alias to the real model ID (backend-only).

    Unknown values pass through unchanged so existing stored rows keep working.
    """
    if not alias:
        return MODEL_ALIASES[DEFAULT_MODEL_ALIAS]
    key = alias.strip().lower()
    return MODEL_ALIASES.get(key, alias)


def alias_for_model(value: str | None) -> str:
    """Normalize any stored/sent model value to its provider-neutral alias.

    Accepts aliases (unchanged), legacy raw model IDs (mapped back), and
    anything unknown (falls back to the default alias).
    """
    if not value:
        return DEFAULT_MODEL_ALIAS
    key = value.strip().lower()
    if key in MODEL_ALIASES:
        return key
    for alias, model_id in MODEL_ALIASES.items():
        if key == model_id.lower():
            return alias
    return DEFAULT_MODEL_ALIAS

CHAT_SYSTEM_INSTRUCTION = """You are an educational knowledge assistant.
Answer questions using the learning material provided by the user.
Explain concepts clearly and accurately.
If the requested information is not available in the provided learning material,
clearly tell the user that the information is not available in the selected resources.
Do not invent information."""


class GeminiError(Exception):
    """Raised when the Gemini API fails or returns unusable output."""


def _configure():
    if not settings.GEMINI_API_KEY:
        raise GeminiError(
            "GEMINI_API_KEY is not set. Add your key to backend/.env and restart the server."
        )
    genai.configure(api_key=settings.GEMINI_API_KEY)


def _model(model_name: str | None = None, system_instruction: str | None = None):
    _configure()
    return genai.GenerativeModel(
        model_name=model_name or settings.GEMINI_MODEL,
        system_instruction=system_instruction,
    )


def _is_rate_limit(exc: Exception) -> bool:
    text = str(exc)
    return "429" in text or "quota" in text.lower() or "ResourceExhausted" in text


def _is_model_unavailable(exc: Exception) -> bool:
    text = str(exc)
    return (
        "no longer available" in text
        or "not found" in text.lower()
        or "is not supported" in text
        or "does not exist" in text
        or "404" in text
    )


def _empty_response(exc: ValueError) -> GeminiError:
    """Distinguish real empty answers from blocked prompts (safety filter)."""
    if re.search(r"finish_reason.{0,40}is 4\b", str(exc)):
        raise GeminiError(
            "The AI declined to answer this prompt. Try rephrasing or use different sources."
        ) from exc
    return GeminiError("Gemini returned an empty response. Try again.")


def _generation_config(**kwargs) -> Any:
    """Build a GenerationConfig, dropping options this SDK version does not know."""
    try:
        return genai.types.GenerationConfig(**kwargs)
    except (TypeError, ValueError):
        cleaned = {}
        known = set()
        try:
            known = set(genai.types.GenerationConfig.__fields__ or [])
        except Exception:  # pragma: no cover - very old SDKs
            pass
        if not known:
            try:
                import dataclasses

                known = {f.name for f in dataclasses.fields(genai.types.GenerationConfig)}
            except Exception:
                known = set()
        cleaned = {k: v for k, v in kwargs.items() if not known or k in known}
        return genai.types.GenerationConfig(**cleaned)


def _attempt_generate(
    model_name: str,
    prompt: str,
    system_instruction: str | None,
    temperature: float,
    max_output_tokens: int,
) -> str:
    """One model attempt with its own timeout; raises on unusable output."""
    model = _model(model_name, system_instruction)

    request = genai.types.RequestOptions(timeout=REQUEST_TIMEOUT_SECONDS)
    result = model.generate_content(
        prompt,
        generation_config=_generation_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
        request_options=request,
    )

    if not result.candidates:
        raise GeminiError("Gemini returned no candidates. Try again.")
    try:
        text = (result.text or "").strip()
    except ValueError as exc:
        # No valid Part - usually the thinking budget consumed all tokens.
        logger.warning("Model %s returned an empty part: %s", model_name, exc)
        raise _empty_response(exc) from exc
    if not text:
        raise GeminiError("Gemini returned an empty response. Try again.")
    return text


def _build_chain(model_name: str | None) -> list[str]:
    """Models to try in order: requested -> configured -> known-good fallbacks."""
    chain: list[str] = []
    for candidate in [
        model_name,
        settings.GEMINI_MODEL,
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-lite",
    ]:
        if candidate and candidate not in chain:
            chain.append(candidate)
    return chain


def _call(
    prompt: str,
    model_name: str | None = None,
    system_instruction: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int = 2048,
) -> str:
    """Call Gemini with retries, per-attempt timeout and a model fallback chain.

    The chain always ends with known-good fallbacks, even when a specific model
    was requested - so one dead or slow model can never make the app unusable.
    """
    chain = _build_chain(model_name)
    last_error: Exception | None = None
    for model_candidate in chain:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return _attempt_generate(
                    model_candidate,
                    prompt,
                    system_instruction,
                    temperature,
                    max_output_tokens,
                )
            except GeminiError as exc:
                # Usable-output problems: retry once on this model, then move on.
                last_error = exc
                if attempt < MAX_ATTEMPTS:
                    logger.warning(
                        "Model %s unusable output (%s); retrying (attempt %d/%d)",
                        model_candidate, exc, attempt, MAX_ATTEMPTS,
                    )
                    time.sleep(BASE_DELAY_SECONDS)
                    continue
                break
            except GoogleAPIError as exc:
                last_error = exc
                if _is_rate_limit(exc):
                    if attempt < MAX_ATTEMPTS:
                        delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, 1)
                        logger.info(
                            "Gemini rate limited on %s, retrying in %.0fs (attempt %d/%d)",
                            model_candidate, delay, attempt, MAX_ATTEMPTS,
                        )
                        time.sleep(delay)
                        continue
                    break
                if _is_model_unavailable(exc):
                    logger.warning("Model %s unavailable (%s)", model_candidate, exc)
                    break  # move to the next model in the chain immediately
                logger.warning("Gemini API error on %s: %s", model_candidate, exc)
                if attempt < MAX_ATTEMPTS:
                    time.sleep(BASE_DELAY_SECONDS)
                    continue
                break
            except Exception as exc:  # network errors, timeouts, unexpected
                last_error = exc
                logger.warning("Gemini call failed on %s: %s", model_candidate, exc)
                if attempt < MAX_ATTEMPTS:
                    time.sleep(BASE_DELAY_SECONDS)
                    continue
                break

    logger.warning("All Gemini attempts failed; last error: %s", last_error)
    if last_error is not None and _is_rate_limit(last_error):
        raise GeminiError(RATE_LIMIT_MESSAGE) from last_error
    raise GeminiError(f"AI service is temporarily unavailable. Please try again. ({last_error})") from last_error


# ---------------------------------------------------------------- chat

def generate_chat_response(
    resource_content: str,
    user_message: str,
    history: list[dict] | None = None,
    response_style: str = "balanced",
) -> str:
    style_hint = {
        "concise": "Keep answers short and to the point.",
        "detailed": "Give thorough, well-structured explanations with examples.",
        "balanced": "",
    }.get(response_style, "")

    material = truncate_for_prompt(resource_content)
    history_text = ""
    if history:
        turns = [
            f"{m['role'].capitalize()}: {m['content']}" for m in history[-8:]
        ]
        history_text = "Recent conversation:\n" + "\n".join(turns) + "\n\n"

    prompt = f"""Learning Material:
{material}

{history_text}User Question:
{user_message}"""

    return _call(
        prompt,
        system_instruction=CHAT_SYSTEM_INSTRUCTION + ("\n" + style_hint if style_hint else ""),
        temperature=0.7,
        max_output_tokens=2048,
    )


# ------------------------------------------------- structured JSON output

def _extract_json(text: str) -> Any:
    """Parse JSON out of a model reply, tolerating markdown fences."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise GeminiError("Gemini returned invalid structured data. Please try again.")


def generate_summary(resource_content: str) -> dict:
    material = truncate_for_prompt(resource_content)
    prompt = f"""Summarize the following learning material.

Return ONLY valid JSON (no markdown) with this exact shape:
{{"short_summary": "2-3 sentence overview", "detailed_summary": "multi-paragraph detailed summary", "key_points": ["point 1", "point 2", "..."]}}

Material:
{material}"""
    data = _extract_json(_call(prompt, temperature=0.4, max_output_tokens=2048))
    if not isinstance(data, dict) or "short_summary" not in data:
        raise GeminiError("Gemini returned an unexpected summary format. Please try again.")
    data.setdefault("detailed_summary", "")
    data.setdefault("key_points", [])
    return data


def generate_quiz(resource_content: str, number_of_questions: int = 10) -> dict:
    material = truncate_for_prompt(resource_content)
    prompt = f"""Create a multiple-choice quiz with exactly {number_of_questions} questions based on the material.

Return ONLY valid JSON (no markdown):
{{"questions": [{{"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": "the correct option text exactly as in options", "explanation": "why this is correct"}}]}}

Material:
{material}"""
    data = _extract_json(_call(prompt, temperature=0.5, max_output_tokens=4096))
    if not isinstance(data, dict) or not data.get("questions"):
        raise GeminiError("Gemini returned an unexpected quiz format. Please try again.")
    return data


def generate_flashcards(resource_content: str, number_of_cards: int = 10) -> dict:
    material = truncate_for_prompt(resource_content)
    prompt = f"""Create {number_of_cards} flashcards based on the material.

Return ONLY valid JSON (no markdown):
{{"cards": [{{"question": "...", "answer": "...", "explanation": "..."}}]}}

Material:
{material}"""
    data = _extract_json(_call(prompt, temperature=0.5, max_output_tokens=4096))
    if not isinstance(data, dict) or not data.get("cards"):
        raise GeminiError("Gemini returned an unexpected flashcards format. Please try again.")
    return data


def generate_faq(resource_content: str) -> dict:
    material = truncate_for_prompt(resource_content)
    prompt = f"""Create a list of the 8 most useful FAQ entries a student might ask about this material.

Return ONLY valid JSON (no markdown):
{{"faqs": [{{"question": "...", "answer": "..."}}]}}

Material:
{material}"""
    data = _extract_json(_call(prompt, temperature=0.5, max_output_tokens=3072))
    if not isinstance(data, dict) or not data.get("faqs"):
        raise GeminiError("Gemini returned an unexpected FAQ format. Please try again.")
    return data


def generate_study_notes(resource_content: str) -> dict:
    material = truncate_for_prompt(resource_content)
    prompt = f"""Create structured study notes from this material.

Return ONLY valid JSON (no markdown):
{{"title": "...", "overview": "...", "important_concepts": [{{"name": "...", "explanation": "..."}}], "key_points": ["..."], "conclusion": "..."}}

Material:
{material}"""
    data = _extract_json(_call(prompt, temperature=0.4, max_output_tokens=3072))
    if not isinstance(data, dict) or "overview" not in data:
        raise GeminiError("Gemini returned an unexpected study notes format. Please try again.")
    data.setdefault("title", "Study Notes")
    data.setdefault("important_concepts", [])
    data.setdefault("key_points", [])
    data.setdefault("conclusion", "")
    return data


def generate_prompt_response(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int = 1000,
) -> str:
    """Free-form generation for the AI Studio / Prompt Playground."""
    return _call(
        prompt,
        model_name=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
