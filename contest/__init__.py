"""ContestKorea crawler package."""

from __future__ import annotations


def run(*args, **kwargs):
    """Run the crawler without importing the CLI module during package init."""

    from .contest_crawler import crawl

    return crawl(*args, **kwargs)


__all__ = ["run"]
