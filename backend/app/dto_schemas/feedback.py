from datetime import datetime

from pydantic import BaseModel


class FeedbackBase(BaseModel):
    text: str
    rating: int

    class Config:
        from_attributes = True


class FeedbackResponseModel(FeedbackBase):
    username: str
    date_created: datetime
