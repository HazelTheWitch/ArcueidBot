__all__ = [
    'plural',
    'titleCapitalization'
]


def plural(number: int, singular: str, plural: str) -> str:
    if number == 1:
        return f'{number} {singular}'
    return f'{number} {plural}'


def titleCapitalization(string: str) -> str:
    words = string.split(' ')

    titleWords = []

    for i, word in enumerate(words):
        if i == 0 or len(word) >= 4:
            titleWords.append(word[0].upper() + word[1:])
        else:
            titleWords.append(word)

    return ' '.join(titleWords)
