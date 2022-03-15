__all__ = [
    'plural'
]


def plural(number: int, singular: str, plural: str) -> str:
    if number == 1:
        return f'{number} {singular}'
    return f'{number} {plural}'
