"""
Translation utility using deep_translator for multilingual support.
Supports: English, Telugu, Hindi
"""

from deep_translator import GoogleTranslator
from typing import Tuple

# Supported languages
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Telugu": "te",
    "Hindi": "hi"
}

# Reverse mapping
CODE_TO_LANGUAGE = {v: k for k, v in SUPPORTED_LANGUAGES.items()}


def detect_language(text: str) -> str:
    """
    Detect the language of input text.
    Returns language code (en, te, hi).

    Note: This is a simple heuristic. For production, use a proper
    language detection library like langdetect.
    """
    # Check for Telugu Unicode range (0C00-0C7F)
    if any('\u0C00' <= char <= '\u0C7F' for char in text):
        return "te"

    # Check for Hindi/Devanagari Unicode range (0900-097F)
    if any('\u0900' <= char <= '\u097F' for char in text):
        return "hi"

    # Default to English
    return "en"


def translate_to_english(text: str, source_lang: str = "auto") -> Tuple[str, str]:
    """
    Translate text to English.

    Args:
        text: Text to translate
        source_lang: Source language code or "auto" for detection

    Returns:
        Tuple of (translated_text, detected_source_language)
    """
    if source_lang == "auto":
        source_lang = detect_language(text)

    if source_lang == "en":
        return text, "en"

    try:
        translator = GoogleTranslator(source=source_lang, target="en")
        translated = translator.translate(text)
        return translated, source_lang
    except Exception as e:
        print(f"Translation error: {e}")
        return text, source_lang


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text to target language.

    Args:
        text: English text to translate
        target_lang: Target language code (te, hi)

    Returns:
        Translated text
    """
    if target_lang == "en":
        return text

    try:
        translator = GoogleTranslator(source="en", target=target_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def get_language_name(code: str) -> str:
    """Get language name from code."""
    return CODE_TO_LANGUAGE.get(code, "English")


def get_language_code(name: str) -> str:
    """Get language code from name."""
    return SUPPORTED_LANGUAGES.get(name, "en")


# Test
if __name__ == "__main__":
    # Test Telugu
    telugu_text = "నాకు జ్వరం వచ్చింది"
    print(f"Telugu input: {telugu_text}")
    english, lang = translate_to_english(telugu_text)
    print(f"Detected language: {lang}")
    print(f"English translation: {english}")

    # Test Hindi
    hindi_text = "मुझे बुखार है"
    print(f"\nHindi input: {hindi_text}")
    english, lang = translate_to_english(hindi_text)
    print(f"Detected language: {lang}")
    print(f"English translation: {english}")

    # Test reverse translation
    english_response = "You should take rest and drink plenty of fluids."
    print(f"\nEnglish response: {english_response}")
    print(f"Telugu: {translate_from_english(english_response, 'te')}")
    print(f"Hindi: {translate_from_english(english_response, 'hi')}")
