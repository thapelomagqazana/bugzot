def send_activation_email(email: str, token: str):
    """
    Sends email with account activation link.
    Replace print with real SMTP/SendGrid integration.
    """
    link = f"https://yourdomain.com/api/v1/auth/verify?token={token}"
    subject = "Activate your account"
    body = f"""
    Hi,

    Thank you for signing up!

    Please activate your account by clicking this link:
    {link}

    This link will expire in 30 minutes.

    Blessings,
    The BugZot Team
    """

    # Replace this with actual email service
    print(f"[EMAIL SENT]\nTo: {email}\nSubject: {subject}\n\n{body}")