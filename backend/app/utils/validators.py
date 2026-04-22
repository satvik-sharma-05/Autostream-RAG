"""Input validation utilities."""
import re


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def sanitize_name(name: str) -> str:
    """Strip and title-case a name."""
    return name.strip().title()
