import re


def clean_title(title: str) -> str:
    """Clean the title from any score computed in a previous evaluation.

    Example:
        "[85] This is an article title (TS: 4)" -> "This is an article title"

    This also cleans multiple scores, if a previous inference run messed up the titles:
        "[85] [90] This is an article title (TS: 4) (TS: 5)" -> "This is an article title"

    Args:
        title: The article title.

    Returns:
        The cleaned title.
    """
    new_title = re.sub(r"\[\d+\]\s*", "", title)
    new_title = re.sub(r"\s*\(TS:\s*\d+\)\s*$", "", new_title)

    return new_title
