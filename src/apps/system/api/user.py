
from src.apps.common.deps import SessionDep
from src.apps.system.models.user import UserModel
from src.apps.system.schemas.system_schema import UserCreator
from fastapi import APIRouter


router = APIRouter(tags=["system_user"], prefix="/user")


@router.post('')
async def create_user(session: SessionDep, creator: UserCreator):
    data = creator.model_dump(exclude_unset=True)
    user_model = UserModel.model_validate(data)
    # print()
    session.add(user_model)
    return user_model