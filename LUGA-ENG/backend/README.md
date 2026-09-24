# LugaFlow backend

FastAPI service for the Luganda-to-English frontend.

## Start the API

From this directory:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

The API runs at `http://127.0.0.1:8000`.

## Enable Google Cloud Translation

1. Enable the Cloud Translation API in a Google Cloud project.
2. Create an API key with access to that API.
3. Set the key in the backend process environment:

```powershell
$env:GOOGLE_TRANSLATE_API_KEY = "your-key"
python -m uvicorn main:app --reload --port 8000
```

The service uses the local dictionary first, then Google Cloud Translation for phrases that are not in the catalog. The key is never sent to the frontend.

## Import 100,000+ vetted entries

Use a vetted English-Luganda corpus from your chosen provider, then import it with the CSV command below. Large corpora should stay outside git and be imported during setup.

Prepare a UTF-8 CSV with exactly these columns:

```csv
luganda,english
webale nnyo,Thank you very much
```

Import it from the backend directory:

```powershell
python import_dictionary.py path\to\luganda-english.csv
```

The entries are stored in `dictionary_data.json`, loaded into memory when the API starts, and searched before Google. Successful Google translations are also cached in `translation_cache.json`, so the dictionary grows over time. Do not generate fake rows to reach a count: use a vetted corpus so translations remain trustworthy.

## Endpoints

- `GET /api/health` checks that the service is running.
- `POST /api/translate` accepts `{ "text": "Webale nnyo", "source": "lg", "target": "en" }` and returns the source, translation, confidence level, and provider.
- `GET /api/dictionary?query=webale` searches the local Luganda dictionary.

The live app translation URL is `http://127.0.0.1:8000/api/translate`. Google fallback uses `https://translation.googleapis.com/language/translate/v2` when `GOOGLE_TRANSLATE_API_KEY` is configured.

Unknown phrases return a review message when Google Cloud Translation is not configured or cannot answer.
