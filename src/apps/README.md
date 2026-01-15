# alembic
<!-- 数据库迁移 -->
```shell
# 初始化
alembic init -t async alembic
```

```python
# 修改 alembic/env.py 中的数据库连接字符串
import sys
import asyncio
# 支持win
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 配置 Alembic 数据库连接字符串， 或者在 alembic.ini 中配置
config = context.config
config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))

# 导入模型
from system.models.user import UserModel
target_metadata = UserModel.metadata
```


```shell
# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```





