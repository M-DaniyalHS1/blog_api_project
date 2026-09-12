from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

#token create
def create_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp":expire
    })
    return jwt.encode(to_encode,secret_key,algorithm=algorithm)

def verify_token(token:str = Depends(oauth2_schema)):
    try:
        payload = jwt.decode(token = token,key = secret_key,algorithms=algorithm)
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="invalid token")
