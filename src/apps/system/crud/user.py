from src.apps.system.models.user import UserModel
from sqlmodel import func, select
from src.apps.common.deps import SessionDep


def check_account_exists(*, session: SessionDep, account: str) -> bool:
    return session.exec(select(func.count()).select_from(UserModel).where(UserModel.account == account)).one() > 0