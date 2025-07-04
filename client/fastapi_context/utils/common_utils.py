import inspect
from datetime import date, datetime
import json
from decimal import Decimal
from typing import Any, Dict, ForwardRef, Callable

from pydantic.v1.typing import evaluate_forwardref

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"
DATE_FORMAT = "%Y-%m-%d"


class JsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime(DATETIME_FORMAT)
        elif isinstance(obj, date):
            return obj.strftime(DATE_FORMAT)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, set):
            return list(obj)
        else:
            return super().default(obj)


def get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return annotation


def get_typed_return_annotation(call: Callable[..., Any]) -> Any:
    signature = inspect.signature(call)
    annotation = signature.return_annotation

    if annotation is inspect.Signature.empty:
        return None

    globalns = getattr(call, "__globals__", {})
    return get_typed_annotation(annotation, globalns)
