from __future__ import annotations

import io
import os
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

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

HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MarkItDown Web Converter</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; max-width: 960px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
    textarea { width: 100%; min-height: 360px; margin-top: 1rem; }
    .row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
    .error { color: #b00020; margin-top: 0.8rem; }
    .muted { color: #666; font-size: 0.95rem; }
    button { cursor: pointer; }
  </style>
</head>
<body>
  <h1>Document → Markdown</h1>
  <p class="muted">Upload a document and convert it to Markdown with MarkItDown.</p>

  <div class="card">
    <form id="upload-form" class="row">
      <input type="file" id="document" name="document" required>
      <button type="submit">Convert</button>
      <button type="button" id="download-btn" disabled>Download .md</button>
    </form>
    <div id="error" class="error"></div>
    <textarea id="markdown" placeholder="Converted markdown will appear here..." readonly></textarea>
  </div>

  <script>
    const form = document.getElementById("upload-form");
    const input = document.getElementById("document");
    const output = document.getElementById("markdown");
    const error = document.getElementById("error");
    const downloadBtn = document.getElementById("download-btn");

    let downloadName = "document.md";

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      error.textContent = "";
      output.value = "";
      downloadBtn.disabled = true;

      if (!input.files || input.files.length === 0) {
        error.textContent = "Please choose a file.";
        return;
      }

      const payload = new FormData();
      payload.append("document", input.files[0]);

      const response = await fetch("/api/convert", { method: "POST", body: payload });
      const data = await response.json();

      if (!response.ok) {
        error.textContent = data.error || "Failed to convert document.";
        return;
      }

      output.value = data.markdown;
      downloadName = data.output_filename || "document.md";
      downloadBtn.disabled = false;
    });

    downloadBtn.addEventListener("click", () => {
      const blob = new Blob([output.value], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = downloadName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
  </script>
</body>
</html>
"""

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
def index():
    return render_template_string(HTML_PAGE)


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
