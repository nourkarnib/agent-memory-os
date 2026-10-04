import functools
import inspect
import time
from typing import Any, Callable, Optional
from .client import MemoryOS


def remember(client: MemoryOS, input_keys: Optional[list] = None, tags: list = [], memory_type: str = "episodic"):
    """
    Decorator that automatically captures function inputs/outputs as memories.

    Usage:
        memory = MemoryOS(api_key="...", agent_id="pricing-agent", base_url="...")

        @remember(memory, tags=["pricing", "discount"])
        def decide_discount(customer: dict, order: dict) -> dict:
            return {"decision": "approve", "discount": 0.15}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            if input_keys:
                input_data = {k: bound.arguments.get(k) for k in input_keys}
            else:
                input_data = dict(bound.arguments)
            input_data = _safe_serialize(input_data)

            start = time.perf_counter()
            outcome = "success"
            output_data = {}

            try:
                result = func(*args, **kwargs)
                output_data = _safe_serialize(result) if not isinstance(result, dict) else result
                return result
            except Exception as e:
                outcome = "failure"
                output_data = {"error": str(e), "type": type(e).__name__}
                raise
            finally:
                latency_ms = int((time.perf_counter() - start) * 1000)
                try:
                    client.store(
                        input=input_data, output=output_data, outcome=outcome,
                        memory_type=memory_type, tags=tags, latency_ms=latency_ms,
                    )
                except Exception:
                    pass  # never let memory storage break the agent

        return wrapper
    return decorator


def _safe_serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_safe_serialize(i) for i in obj]
    elif hasattr(obj, "__dict__"):
        return _safe_serialize(obj.__dict__)
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)
