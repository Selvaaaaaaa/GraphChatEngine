"""
api/utils/file_helpers.py
-------------------------
GraphChatEngine – File Utility Helpers

Lightweight, stateless helper functions used by the ingest service.
Keeping these separate from business logic makes them easy to unit-test
in isolation.
"""

import logging

logger = logging.getLogger(__name__)

# The only file extension we accept
ALLOWED_EXTENSION = ".csv"


def is_csv_filename(filename: str) -> bool:
    """
    Return True if *filename* ends with `.csv` (case-insensitive).

    Parameters
    ----------
    filename : str
        The original filename as reported by the client.

    Returns
    -------
    bool
        True when the extension is `.csv`, False otherwise.

    Examples
    --------
    >>> is_csv_filename("data.csv")
    True
    >>> is_csv_filename("report.PDF")
    False
    """
    return filename.lower().endswith(ALLOWED_EXTENSION)


def bytes_to_kb(size_bytes: int, ndigits: int = 2) -> float:
    """
    Convert a byte count to kilobytes, rounded to *ndigits* decimal places.

    Parameters
    ----------
    size_bytes : int
        File size in bytes.
    ndigits : int, optional
        Number of decimal places (default 2).

    Returns
    -------
    float
        Size expressed in KB.
    """
    return round(size_bytes / 1024, ndigits)
