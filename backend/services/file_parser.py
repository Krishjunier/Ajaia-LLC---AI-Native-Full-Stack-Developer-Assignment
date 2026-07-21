"""
File parser service: converts uploaded files to sanitized HTML
Supported: .txt, .md, .docx
"""
import io
from typing import Tuple

import bleach
import markdown2
import docx

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "code", "pre",
    "a", "span",
]
ALLOWED_ATTRS = {"a": ["href", "title"], "span": ["class"]}

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_file(filename: str, size: int) -> Tuple[bool, str]:
    """Return (ok, error_message)."""
    ext = _get_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed: .txt, .md, .docx"
    if size > MAX_FILE_SIZE:
        return False, f"File exceeds 5 MB limit (received {size / 1024 / 1024:.1f} MB)"
    return True, ""


def parse_to_html(filename: str, content: bytes) -> str:
    """Convert file bytes to sanitized HTML."""
    ext = _get_extension(filename)

    if ext == ".txt":
        raw_html = _txt_to_html(content)
    elif ext == ".md":
        raw_html = _md_to_html(content)
    elif ext == ".docx":
        raw_html = _docx_to_html(content)
    else:
        raise ValueError(f"Unsupported extension: {ext}")

    return _sanitize(raw_html)


def _get_extension(filename: str) -> str:
    import os
    return os.path.splitext(filename.lower())[1]


def _txt_to_html(content: bytes) -> str:
    text = content.decode("utf-8", errors="replace")
    lines = text.splitlines()
    paragraphs = [f"<p>{line if line.strip() else '&nbsp;'}</p>" for line in lines]
    return "\n".join(paragraphs)


def _md_to_html(content: bytes) -> str:
    text = content.decode("utf-8", errors="replace")
    return markdown2.markdown(text, extras=["fenced-code-blocks", "tables"])


def _docx_to_html(content: bytes) -> str:
    doc = docx.Document(io.BytesIO(content))
    parts = []
    for para in doc.paragraphs:
        style = para.style.name.lower()
        text = para.text.strip()
        if not text:
            parts.append("<p>&nbsp;</p>")
            continue

        if "heading 1" in style:
            parts.append(f"<h1>{text}</h1>")
        elif "heading 2" in style:
            parts.append(f"<h2>{text}</h2>")
        elif "heading 3" in style:
            parts.append(f"<h3>{text}</h3>")
        else:
            # Inline formatting
            runs_html = ""
            for run in para.runs:
                r = run.text
                if run.bold:
                    r = f"<strong>{r}</strong>"
                if run.italic:
                    r = f"<em>{r}</em>"
                if run.underline:
                    r = f"<u>{r}</u>"
                runs_html += r
            parts.append(f"<p>{runs_html}</p>")
    return "\n".join(parts)


def _sanitize(html: str) -> str:
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
