from pydantic import BaseModel

class Createuser(BaseModel):
    username: str
    password: str

