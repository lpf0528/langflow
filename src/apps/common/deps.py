from sqlmodel import Session
from fastapi import Depends
from typing import Annotated
from .db import get_session
SessionDep = Annotated[Session, Depends(get_session)]