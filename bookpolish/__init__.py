"""Context-aware copy editor for machine-translated fiction."""

from bookpolish.engine import (
    POLICY,
    BookDB,
    Edit,
    ModelError,
    Run,
    Segment,
    Server,
    Term,
    accept_edit,
    apply_glossary,
    load_chapter,
    load_glossary,
    parse_labels,
    polish,
    preview,
    verify_edits,
)
from bookpolish.verify import SystemOneVerifier

__version__ = "0.1.0"

__all__ = [
    "POLICY",
    "BookDB",
    "Edit",
    "SystemOneVerifier",
    "ModelError",
    "Run",
    "Segment",
    "Server",
    "Term",
    "accept_edit",
    "apply_glossary",
    "load_chapter",
    "load_glossary",
    "parse_labels",
    "polish",
    "preview",
    "verify_edits",
]
