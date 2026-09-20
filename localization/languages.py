"""
localization/languages.py — Authoritative catalog of the 22 Scheduled Indian Languages,
ISO codes, native script names, and localized Sources headings.
"""

from typing import TypedDict


class LanguageInfo(TypedDict):
    code: str              # ISO 639-1 / Bhashini language code
    name: str              # English name
    native_name: str       # Native script name
    script: str            # Script family
    sources_heading: str   # Localized "Sources" heading


# 22 Eighth Schedule Languages of the Republic of India + English + Hinglish
SCHEDULED_LANGUAGES: dict[str, LanguageInfo] = {
    "en": {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "script": "Latin",
        "sources_heading": "Sources:",
    },
    "hi": {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "script": "Devanagari",
        "sources_heading": "स्रोतः",
    },
    "hinglish": {
        "code": "hinglish",
        "name": "Hinglish",
        "native_name": "Hinglish (Romanized)",
        "script": "Latin",
        "sources_heading": "Sources:",
    },
    "bn": {
        "code": "bn",
        "name": "Bengali",
        "native_name": "বাংলা",
        "script": "Bengali",
        "sources_heading": "উৎসসমূহ:",
    },
    "te": {
        "code": "te",
        "name": "Telugu",
        "native_name": "తెలుగు",
        "script": "Telugu",
        "sources_heading": "మూలాలు:",
    },
    "mr": {
        "code": "mr",
        "name": "Marathi",
        "native_name": "मराठी",
        "script": "Devanagari",
        "sources_heading": "स्रोत:",
    },
    "ta": {
        "code": "ta",
        "name": "Tamil",
        "native_name": "தமிழ்",
        "script": "Tamil",
        "sources_heading": "மூலங்கள்:",
    },
    "ur": {
        "code": "ur",
        "name": "Urdu",
        "native_name": "اردو",
        "script": "Perso-Arabic",
        "sources_heading": "ذرائع:",
    },
    "gu": {
        "code": "gu",
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "script": "Gujarati",
        "sources_heading": "સ્રોતો:",
    },
    "kn": {
        "code": "kn",
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "script": "Kannada",
        "sources_heading": "ಮೂಲಗಳು:",
    },
    "ml": {
        "code": "ml",
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "script": "Malayalam",
        "sources_heading": "ഉറവിടങ്ങൾ:",
    },
    "or": {
        "code": "or",
        "name": "Odia",
        "native_name": "ଓଡ଼ିଆ",
        "script": "Odia",
        "sources_heading": "ଉତ୍ସଗୁଡ଼ିକ:",
    },
    "pa": {
        "code": "pa",
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ",
        "script": "Gurmukhi",
        "sources_heading": "ਸਰੋਤ:",
    },
    "as": {
        "code": "as",
        "name": "Assamese",
        "native_name": "অসমীয়া",
        "script": "Bengali-Assamese",
        "sources_heading": "উৎসসমূহ:",
    },
    "ma": {
        "code": "mai",
        "name": "Maithili",
        "native_name": "मैथिली",
        "script": "Devanagari",
        "sources_heading": "स्रोत:",
    },
    "sa": {
        "code": "sa",
        "name": "Sanskrit",
        "native_name": "संस्कृतम्",
        "script": "Devanagari",
        "sources_heading": "स्रोतांसि:",
    },
    "ks": {
        "code": "ks",
        "name": "Kashmiri",
        "native_name": "کٲشُر",
        "script": "Perso-Arabic",
        "sources_heading": "ذرائع:",
    },
    "ne": {
        "code": "ne",
        "name": "Nepali",
        "native_name": "नेपाली",
        "script": "Devanagari",
        "sources_heading": "स्रोतहरू:",
    },
    "sd": {
        "code": "sd",
        "name": "Sindhi",
        "native_name": "سنڌي",
        "script": "Perso-Arabic",
        "sources_heading": "ذرائع:",
    },
    "kok": {
        "code": "kok",
        "name": "Konkani",
        "native_name": "कोंकणी",
        "script": "Devanagari",
        "sources_heading": "स्रोत:",
    },
    "doi": {
        "code": "doi",
        "name": "Dogri",
        "native_name": "डोगरी",
        "script": "Devanagari",
        "sources_heading": "स्रोत:",
    },
    "mni": {
        "code": "mni",
        "name": "Manipuri (Meitei)",
        "native_name": "মৈতৈলোন্",
        "script": "Meitei Mayek",
        "sources_heading": "উৎসশিং:",
    },
    "brx": {
        "code": "brx",
        "name": "Bodo",
        "native_name": "बर'",
        "script": "Devanagari",
        "sources_heading": "फुंखामफोर:",
    },
    "sat": {
        "code": "sat",
        "name": "Santali",
        "native_name": "ᱥᱟᱱᱛᱟᱲᱤ",
        "script": "Ol Chiki",
        "sources_heading": "ᱯᱷᱮᱰᱟᱛ:",
    },
}


def get_sources_heading(lang_code_or_name: str) -> str:
    """Resolve the localized 'Sources' heading for any given language code or name."""
    query = lang_code_or_name.strip().lower()

    # Match by key code
    if query in SCHEDULED_LANGUAGES:
        return SCHEDULED_LANGUAGES[query]["sources_heading"]

    # Match by name or native name
    for lang in SCHEDULED_LANGUAGES.values():
        if query in lang["name"].lower() or query in lang["native_name"].lower():
            return lang["sources_heading"]

    return "Sources:"


def get_language_info(lang_code_or_name: str) -> LanguageInfo:
    """Resolve full LanguageInfo dictionary."""
    query = lang_code_or_name.strip().lower()
    if query in SCHEDULED_LANGUAGES:
        return SCHEDULED_LANGUAGES[query]

    for lang in SCHEDULED_LANGUAGES.values():
        if query in lang["name"].lower() or query in lang["native_name"].lower():
            return lang

    return SCHEDULED_LANGUAGES["en"]
