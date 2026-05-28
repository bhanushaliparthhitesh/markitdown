from __future__ import annotations

import io
import os
from pathlib import Path

from flask import Flask, jsonify, request

from markitdown import (
    FailedConversionAttempt,
    FileConversionException,
    MarkItDown,
    MissingDependencyException,
    StreamInfo,
    UnsupportedFormatException,
)

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".json",
    ".xml",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".zip",
    ".epub",
}
ALLOWED_MIME_PREFIXES = (
    "application/",
    "text/",
    "image/",
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE_BYTES
markitdown = MarkItDown()


def _is_allowed_upload(filename: str, mimetype: str | None) -> bool:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False
    if mimetype is None:
        return True
    return mimetype.startswith(ALLOWED_MIME_PREFIXES)


@app.get("/")
def health():
    return jsonify(
        {
            "status": "ok",
            "message": "Use POST /api/convert with form-data key 'document'.",
        }
    )


@app.post("/api/convert")
def convert():
    uploaded = request.files.get("document")
    if uploaded is None or uploaded.filename == "":
        return jsonify({"error": "No file provided."}), 400

    filename = os.path.basename(uploaded.filename)
    mimetype = uploaded.mimetype
    if not _is_allowed_upload(filename, mimetype):
        return (
            jsonify(
                {
                    "error": "Unsupported file type. Please upload an allowed document format."
                }
            ),
            400,
        )

    file_bytes = uploaded.read()
    if len(file_bytes) == 0:
        return jsonify({"error": "Uploaded file is empty."}), 400
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        return jsonify({"error": "File is too large (max 20MB)."}), 413

    stream = io.BytesIO(file_bytes)
    stream_info = StreamInfo(
        filename=filename,
        extension=Path(filename).suffix.lower() or None,
        mimetype=mimetype or None,
    )

    try:
        result = markitdown.convert_stream(stream, stream_info=stream_info)
    except MissingDependencyException:
        return (
            jsonify(
                {
                    "error": "Missing optional dependency for this file type. Install the required MarkItDown extras."
                }
            ),
            400,
        )
    except (
        UnsupportedFormatException,
        FailedConversionAttempt,
        FileConversionException,
    ):
        return (
            jsonify(
                {
                    "error": "Could not convert this file. Ensure the document is valid and supported."
                }
            ),
            400,
        )
    except Exception:
        return jsonify({"error": "Unexpected conversion error."}), 500

    output_name = f"{Path(filename).stem or 'document'}.md"
    return jsonify({"markdown": result.markdown, "output_filename": output_name})


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    app.run(host="127.0.0.1", port=8000, debug=debug_mode)
