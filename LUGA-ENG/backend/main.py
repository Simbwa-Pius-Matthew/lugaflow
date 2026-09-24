import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dictionary_loader import load_dictionary, save_translation
from translations import LUGANDA_WORD_PHRASES, WORD_PHRASES

app = FastAPI(title="LugaFlow API", version="0.1.0")
PHRASES = load_dictionary()
GOOGLE_TRANSLATE_API_URL = "https://translation.googleapis.com/language/translate/v2"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    source: str = Field(default="lg", pattern="^(lg|en)$")
    target: str = Field(default="en", pattern="^(lg|en)$")


class TranslationResponse(BaseModel):
    source: str
    translation: str
    confidence: str
    provider: str


def normalize_phrase(text: str) -> str:
    cleaned = re.sub(r"[^\w\s']", "", text.casefold(), flags=re.UNICODE)
    return " ".join(cleaned.split())


def refresh_dictionary() -> None:
    PHRASES.update(load_dictionary())


def google_translate(source: str, source_language: str, target_language: str) -> str | None:
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not api_key:
        return None

    payload = json.dumps({
        "q": source,
        "source": source_language,
        "target": target_language,
        "format": "text",
    }).encode("utf-8")
    request = UrlRequest(
        f"https://translation.googleapis.com/language/translate/v2?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["data"]["translations"][0]["translatedText"]
    except (HTTPError, URLError, KeyError, IndexError, json.JSONDecodeError):
        return None


def translate_word_by_word(
    source: str, source_language: str, target_language: str
) -> tuple[str, int, int]:
    if source_language == "lg":
        word_map = {
            key: value for key, value in PHRASES.items() if " " not in key
        }
        word_map.update(LUGANDA_WORD_PHRASES)
    else:
        word_map = {
            normalize_phrase(value): key
            for key, value in PHRASES.items()
            if " " not in normalize_phrase(value)
        }
        word_map.update(WORD_PHRASES)

    translated_words = 0
    unresolved_words = 0
    output = []
    for token in re.findall(r"\w+|[^\w\s]", source, flags=re.UNICODE):
        normalized_token = normalize_phrase(token)
        if not normalized_token or not re.search(r"\w", token, flags=re.UNICODE):
            output.append(token)
            continue

        translated = word_map.get(normalized_token)
        if not translated:
            translated = google_translate(
                token, source_language, target_language)
        if translated:
            output.append(translated)
            translated_words += 1
        else:
            output.append(token)
            unresolved_words += 1

    return " ".join(output).replace(" ,", ",").replace(" .", ".").replace(" ?", "?").replace(" !", "!"), translated_words, unresolved_words


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "lugaflow",
        "google_translate": bool(os.getenv("GOOGLE_TRANSLATE_API_KEY")),
        "dictionary_entries": len(PHRASES),
        "translation_api_url": "http://127.0.0.1:8000/api/translate",
        "google_translation_url": GOOGLE_TRANSLATE_API_URL,
    }


@app.get("/api/dictionary")
def dictionary(query: str = Query(default="", max_length=100)):
    refresh_dictionary()
    normalized_query = normalize_phrase(query)
    entries = [
        {"luganda": luganda, "english": english}
        for luganda, english in PHRASES.items()
        if not normalized_query or normalized_query in luganda
    ]
    return {"entries": entries, "count": len(entries)}


@app.post("/api/translate", response_model=TranslationResponse)
def translate(request: TranslationRequest):
    refresh_dictionary()
    source = request.text.strip()
    if not source:
        raise HTTPException(
            status_code=422, detail="Enter some Luganda text first.")

    if request.source == request.target:
        raise HTTPException(
            status_code=400, detail="Choose two different languages.")

    if request.source == "lg":
        translation = PHRASES.get(normalize_phrase(source))
    else:
        translation = next(
            (luganda for luganda, english in PHRASES.items()
             if normalize_phrase(english) == normalize_phrase(source)),
            None,
        )
    if translation:
        return TranslationResponse(
            source=source,
            translation=translation,
            confidence="known",
            provider="LugaFlow dictionary",
        )

    translation = google_translate(source, request.source, request.target)
    if translation:
        if request.source == "lg":
            save_translation(source, translation)
            PHRASES[normalize_phrase(source)] = translation
        else:
            save_translation(translation, source)
            PHRASES[normalize_phrase(translation)] = source
        return TranslationResponse(
            source=source,
            translation=translation,
            confidence="google",
            provider="Google Cloud Translation",
        )

    partial_translation, translated_words, unresolved_words = translate_word_by_word(
        source, request.source, request.target
    )
    if translated_words:
        return TranslationResponse(
            source=source,
            translation=partial_translation,
            confidence="partial" if unresolved_words else "known",
            provider="LugaFlow word dictionary",
        )

    return TranslationResponse(
        source=source,
        translation="We do not have a confident translation for this phrase yet.",
        confidence="review",
        provider="LugaFlow review queue",
    )
