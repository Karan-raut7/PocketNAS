from pydantic import BaseModel

class userlogin(BaseModel):
    username: str
    password: str

