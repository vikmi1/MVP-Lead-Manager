from fastapi import Header, HTTPException
import config


def verify_api_key(x_api_key: str = Header(...)) -> str:
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    return x_api_key
