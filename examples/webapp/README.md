# MarkItDown Web App Example

This example provides a minimal website that uploads a document and converts it to Markdown using the `MarkItDown` Python API.

## Features

- File upload form + convert button
- Backend `/api/convert` endpoint
- Validation for file extension, MIME type, and max size (20 MB)
- Stream-only conversion via `MarkItDown.convert_stream(...)`
- User-friendly conversion error messages
- Client-side `.md` download button

## Run locally

```bash
cd /tmp/workspace/bhanushaliparthhitesh/markitdown
python -m venv .venv
source .venv/bin/activate
pip install flask
pip install -e 'packages/markitdown[all]'
python examples/webapp/app.py
```

Open: `http://127.0.0.1:8000`

## Security notes

- This app only accepts uploaded files and does not process user-provided URLs.
- It validates file type/size before conversion.
- It uses `convert_stream()` instead of permissive URL conversion methods.
