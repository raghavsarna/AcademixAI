from pydantic import BaseModel

class NewsletterBase(BaseModel):
    summary_id: int
    title: str
    picture: str
    description: str
    content: str


    class Config:
        orm_mode = True