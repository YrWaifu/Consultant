import html
import re
from typing import Optional

try:
    import markdown as _markdown_lib  # type: ignore
except Exception:  # pragma: no cover - fallback when dependency missing
    _markdown_lib = None


_DEFAULT_EXTENSIONS = [
    "extra",       # tables, code fences, etc.
    "sane_lists",  # better list handling
    "smarty",      # smart quotes/dashes
]


def render_markdown(source: Optional[str]) -> str:
    """
    Convert Markdown to HTML. Falls back to a minimal renderer if the markdown
    package is unavailable so links/lists still display properly.
    """
    if not source:
        return ""

    text = source.strip()
    if not text:
        return ""

    '''
    if _markdown_lib:
        print('_markdown_lib')
        return _markdown_lib.markdown(
            text,
            extensions=_DEFAULT_EXTENSIONS,
            output_format="html5",
        )
    '''
    # Minimal fallback supporting paragraphs, bullet lists, and links
    lines = text.splitlines()
    html_lines = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.lstrip()

        if not stripped:
            close_list()
            continue

        print('striped', stripped)
        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = html.escape(stripped[2:].strip())
            print(f"<li>{_convert_links(item)}</li>")
            html_lines.append(f"<li>-  {_convert_links(item)}</li>")
        else:
            close_list()
            paragraph = html.escape(line.strip())
            html_lines.append(f"<p>{_convert_links(paragraph)}</p>")

    close_list()
    return "\n".join(html_lines)


def _convert_links(text: str) -> str:
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def replace(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        href = html.escape(match.group(2), quote=True)
        return (
            f'<a href="{href}" target="_blank" rel="noopener noreferrer">'
            f"{label}</a>"
        )

    return link_pattern.sub(replace, text)

