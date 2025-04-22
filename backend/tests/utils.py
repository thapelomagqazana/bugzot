def register(client, email, password, full_name=None):
    payload = {"email": email.strip(), "password": password}
    if full_name is not None:
        payload["full_name"] = full_name
    return client.post("/api/v1/auth/register", json=payload)

def get_user_from_db(db, email):
    from app.models.users.user import User
    return db.query(User).filter(User.email == email.lower()).first()
