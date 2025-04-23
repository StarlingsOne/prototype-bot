from typing import Optional, Union


def has_valid_keys(data: dict) -> bool:
    """Ensure exactly 'assessment' and 'conviction' keys exist."""
    return set(data.keys()) == {'assessment', 'conviction'}


def values_are_floats(data: dict) -> bool:
    """Ensure both values are of type float."""
    return all(isinstance(data.get(k), float) for k in ('assessment', 'conviction'))


def floats_are_in_range(data: dict) -> bool:
    """Ensure float values are within [0.0, 1.0]."""
    return all(0.0 <= data[k] <= 1.0 for k in ('assessment', 'conviction'))


def validate_sentiment_output(data: dict) -> Union[dict, bool]:
    """
    Validates that data is a JSON-like dict with:
    - exactly 'assessment' and 'conviction' keys
    - float values only
    - float values in [0.0, 1.0]
    
    Returns:
        dict if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False

    if not has_valid_keys(data):
        return False

    if not values_are_floats(data):
        return False

    if not floats_are_in_range(data):
        return False

    return data
