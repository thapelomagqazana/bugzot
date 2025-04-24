import re
import dns.resolver

def validate_email_mx(email: str) -> bool:
    """
    Validate email by checking MX DNS records for domain.
    """
    domain = email.split("@")[-1]
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False


def is_disposable_email(email: str, blocklist: set[str]) -> bool:
    """
    Check if email belongs to known disposable domain list.
    """
    domain = email.split("@")[-1]
    return domain.lower() in blocklist


def sanitize_text(text: str) -> str:
    """
    Remove tags and special symbols to prevent XSS/SQLi via names.
    """
    clean = re.sub(r"<[^>]+>", "", text)  # strip HTML
    clean = re.sub(r"[^\w\s\-'.]", "", clean)  # strip unsafe chars
    return clean.strip()


def check_honeypot_field(value: str | None) -> bool:
    """
    Honeypot field: must be empty. Bots usually fill all fields.
    """
    return value in ("", None, " ")