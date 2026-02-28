# Tools/WebServer/language_mapper.py
"""
Language Code Mapper Utility

Converts between frontend display names and backend language codes.
Handles the translation between UI-friendly names and internal language identifiers.
"""

from typing import Optional, Dict

# Mapping from frontend display names to backend language codes
LANGUAGE_NAME_TO_CODE: Dict[str, str] = {
    # English variants
    "English": "english",
    "English (US)": "english",
    "English (UK)": "english_uk",

    # Chinese variants
    "Chinese (Simplified)": "chinese_simplified",
    "Chinese (Traditional)": "chinese_traditional",
    "Simplified Chinese": "chinese_simplified",
    "Traditional Chinese": "chinese_traditional",
    "Chinese": "chinese_simplified",  # Default to Simplified

    # Japanese
    "Japanese": "japanese",
    "Japanese (Japan)": "japanese",

    # Korean
    "Korean": "korean",
    "Korean (South Korea)": "korean",

    # Other languages
    "French": "french",
    "German": "german",
    "Spanish": "spanish",
    "Italian": "italian",
    "Portuguese": "portuguese",
    "Portuguese (Brazil)": "portuguese_brazil",
    "Portuguese (Portugal)": "portuguese_portugal",
    "Russian": "russian",
    "Arabic": "arabic",
    "Hindi": "hindi",
    "Thai": "thai",
    "Vietnamese": "vietnamese",
    "Indonesian": "indonesian",
    "Malay": "malay",
    "Filipino": "filipino",
    "Dutch": "dutch",
    "Polish": "polish",
    "Turkish": "turkish",
    "Ukrainian": "ukrainian",
    "Greek": "greek",
    "Hebrew": "hebrew",
    "Swedish": "swedish",
    "Norwegian": "norwegian",
    "Danish": "danish",
    "Finnish": "finnish",
    "Czech": "czech",
    "Hungarian": "hungarian",
    "Romanian": "romanian",
    "Bulgarian": "bulgarian",
    "Croatian": "croatian",
    "Serbian": "serbian",
    "Slovak": "slovak",
    "Slovenian": "slovenian",
    "Lithuanian": "lithuanian",
    "Latvian": "latvian",
    "Estonian": "estonian",
    "Icelandic": "icelandic",

    # Special values
    "Auto": "auto",
    "Auto Detect": "auto",
    "Automatic": "auto",
}

# Reverse mapping from backend codes to display names
LANGUAGE_CODE_TO_NAME: Dict[str, str] = {
    # Reverse of the above mapping
    "english": "English",
    "english_uk": "English (UK)",
    "chinese_simplified": "Chinese (Simplified)",
    "chinese_traditional": "Chinese (Traditional)",
    "japanese": "Japanese",
    "korean": "Korean",
    "french": "French",
    "german": "German",
    "spanish": "Spanish",
    "italian": "Italian",
    "portuguese": "Portuguese",
    "portuguese_brazil": "Portuguese (Brazil)",
    "portuguese_portugal": "Portuguese (Portugal)",
    "russian": "Russian",
    "arabic": "Arabic",
    "hindi": "Hindi",
    "thai": "Thai",
    "vietnamese": "Vietnamese",
    "indonesian": "Indonesian",
    "malay": "Malay",
    "filipino": "Filipino",
    "dutch": "Dutch",
    "polish": "Polish",
    "turkish": "Turkish",
    "ukrainian": "Ukrainian",
    "greek": "Greek",
    "hebrew": "Hebrew",
    "swedish": "Swedish",
    "norwegian": "Norwegian",
    "danish": "Danish",
    "finnish": "Finnish",
    "czech": "Czech",
    "hungarian": "Hungarian",
    "romanian": "Romanian",
    "bulgarian": "Bulgarian",
    "croatian": "Croatian",
    "serbian": "Serbian",
    "slovak": "Slovak",
    "slovenian": "Slovenian",
    "lithuanian": "Lithuanian",
    "latvian": "Latvian",
    "estonian": "Estonian",
    "icelandic": "Icelandic",
    "auto": "Auto",
}


def map_display_name_to_code(display_name: Optional[str]) -> str:
    """
    Convert frontend display name to backend language code.

    Args:
        display_name: Display name from frontend (e.g., "Chinese (Simplified)")

    Returns:
        Backend language code (e.g., "chinese_simplified")

    Examples:
        >>> map_display_name_to_code("Chinese (Simplified)")
        'chinese_simplified'
        >>> map_display_name_to_code("Japanese")
        'japanese'
        >>> map_display_name_to_code("Auto Detect")
        'auto'
        >>> map_display_name_to_code("unknown_language")
        'unknown_language'
    """
    if not display_name:
        return "auto"

    # Direct lookup
    normalized = display_name.strip()
    if normalized in LANGUAGE_NAME_TO_CODE:
        return LANGUAGE_NAME_TO_CODE[normalized]

    # Case-insensitive lookup
    normalized_lower = normalized.lower()
    for name, code in LANGUAGE_NAME_TO_CODE.items():
        if name.lower() == normalized_lower:
            return code

    # If already a code format (contains underscore), return as-is
    if "_" in normalized:
        return normalized

    # Return original if no mapping found
    return normalized


def map_code_to_display_name(language_code: Optional[str]) -> str:
    """
    Convert backend language code to frontend display name.

    Args:
        language_code: Backend language code (e.g., "chinese_simplified")

    Returns:
        Display name for frontend (e.g., "Chinese (Simplified)")

    Examples:
        >>> map_code_to_display_name("chinese_simplified")
        'Chinese (Simplified)'
        >>> map_code_to_display_name("japanese")
        'Japanese'
        >>> map_code_to_display_name("auto")
        'Auto'
    """
    if not language_code:
        return "Auto"

    # Direct lookup
    if language_code in LANGUAGE_CODE_TO_NAME:
        return LANGUAGE_CODE_TO_NAME[language_code]

    # Case-insensitive lookup
    code_lower = language_code.lower()
    for code, name in LANGUAGE_CODE_TO_NAME.items():
        if code.lower() == code_lower:
            return name

    # Capitalize and return as display name
    return language_code.replace("_", " ").title()


def validate_language_code(language_code: Optional[str]) -> bool:
    """
    Validate if a language code is recognized.

    Args:
        language_code: Backend language code to validate

    Returns:
        True if the code is valid, False otherwise

    Examples:
        >>> validate_language_code("chinese_simplified")
        True
        >>> validate_language_code("invalid_code")
        False
    """
    if not language_code:
        return False

    return language_code in LANGUAGE_CODE_TO_NAME


def get_supported_languages() -> Dict[str, str]:
    """
    Get all supported language mappings.

    Returns:
        Dictionary mapping display names to language codes
    """
    return LANGUAGE_NAME_TO_CODE.copy()


def normalize_language_input(language_input: Optional[str]) -> str:
    """
    Normalize any language input to a valid backend code.

    Handles both display names and language codes, validates the result,
    and returns a safe default if invalid.

    Args:
        language_input: Either a display name or language code

    Returns:
        Normalized backend language code

    Examples:
        >>> normalize_language_input("Chinese (Simplified)")
        'chinese_simplified'
        >>> normalize_language_input("chinese_simplified")
        'chinese_simplified'
        >>> normalize_language_input("invalid")
        'auto'
    """
    if not language_input:
        return "auto"

    # Try as display name first
    code = map_display_name_to_code(language_input)

    # Validate the result
    if validate_language_code(code):
        return code

    # If invalid, return safe default
    return "auto"
