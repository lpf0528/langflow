import hashlib 
from .config import settings

def default_md5_pwd():
    m = hashlib.md5()
    password = settings.DEFAULT_PWD
    m.update(password.encode("utf-8"))
    return m.hexdigest()