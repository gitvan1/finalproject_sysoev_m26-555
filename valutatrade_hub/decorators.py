import functools
import logging

logger = logging.getLogger("valutatrade")

def log_action(action: str, verbose: bool = True):
    """Логирует доменную операцию на уровне INFO."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                _log(action, kwargs, "ERROR", error=exc)
                raise
            _log(action, kwargs, "OK", result_data=result, verbose=verbose)
            return result

        return wrapper

    return decorator


def _log(action, kwargs, result, error=None, result_data=None, verbose=False):
    parts = [action]

    # user
    if "username" in kwargs:
        parts.append(f"user='{kwargs['username']}'")
    elif isinstance(result_data, dict) and result_data.get("username"):
        parts.append(f"user='{result_data['username']}'")

    # валюта / amount / rate / base
    if "currency_code" in kwargs:
        parts.append(f"currency='{kwargs['currency_code'].upper()}'")
    if "amount" in kwargs:
        parts.append(f"amount={float(kwargs['amount']):.4f}")
    if "from_code" in kwargs and "to_code" in kwargs:
        parts.append(f"from='{kwargs['from_code'].upper()}' "
                     f"to='{kwargs['to_code'].upper()}'")

    if isinstance(result_data, dict):
        if "rate" in result_data:
            parts.append(f"rate={float(result_data['rate']):.2f}")
            parts.append("base='USD'")
        # опция verbose
        if verbose and "balance_before" in result_data:
            parts.append(
                f"wallet={result_data['balance_before']:.4f}"
                f"→{result_data['balance_after']:.4f}"
            )

    parts.append(f"result={result}")

    if error is not None:
        parts.append(f"error_type={type(error).__name__}")
        parts.append(f"error_message={str(error)!r}")

    logger.info(" ".join(parts))