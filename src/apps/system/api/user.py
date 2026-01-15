
from src.apps.common.deps import SessionDep
from src.apps.system.models.user import UserModel
from src.apps.system.schemas.system_schema import UserCreator
from fastapi import APIRouter
from src.apps.system.crud.user import check_account_exists
from fastapi.exceptions import HTTPException

router = APIRouter(tags=["system_user"], prefix="/user")


@router.post('')
async def create_user(session: SessionDep, creator: UserCreator):

    if check_account_exists(session=session, account=creator.account):
        raise HTTPException(status_code=400, detail="Account already exists")

    data = creator.model_dump(exclude_unset=True)
    user_model = UserModel.model_validate(data)
    # print()
    session.add(user_model)
    return user_model