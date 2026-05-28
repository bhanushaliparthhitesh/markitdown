# MarkItDown Backend API Example

This example provides a minimal backend API that accepts a document upload and converts it to Markdown using the `MarkItDown` Python API.

## Features (backend only)

- `POST /api/convert` endpoint for multipart uploads
- `GET /` health endpoint
- Validation for file extension, MIME type, and max size (20 MB)
- Stream-only conversion via `MarkItDown.convert_stream(...)`
- User-friendly conversion error messages

## Run locally

```bash
cd /tmp/workspace/bhanushaliparthhitesh/markitdown
python -m venv .venv
source .venv/bin/activate
pip install flask
pip install -e 'packages/markitdown[all]'
python examples/webapp/app.py
```

## API usage

```bash
curl -X POST http://127.0.0.1:8000/api/convert \
  -F "document=@/absolute/path/to/file.pdf"
```

Response:

```json
{
  "markdown": "...",
  "output_filename": "file.md"
}
```

## Security notes

- This app only accepts uploaded files and does not process user-provided URLs.
- It validates file type/size before conversion.
- It uses `convert_stream()` instead of permissive URL conversion methods.
