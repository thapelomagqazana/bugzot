from fastapi import Header, HTTPException
from typing import Optional

def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Extracts the token from Authorization header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    return authorization.split(" ")[1]
