from typing import Any


def sanitize_args(args: Any) -> str:
    """
    清理工具调用参数以防止特殊字符问题。
    Args: Args：工具调用参数字符串
    返回：str：净化后的参数字符串
    """
    if not isinstance(args, str):
        return ""
    else:
        return (
            args.replace("[", "&#91;")
            .replace("]", "&#93;")
            .replace("{", "&#123;")
            .replace("}", "&#125;")
        )