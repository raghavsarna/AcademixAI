from pydantic import BaseModel

class NewsletterBase(BaseModel):
    summary_id: int
    title: str
    picture: str
    description: str

    class Config:
        orm_mode = True