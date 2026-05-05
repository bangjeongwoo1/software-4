"""LLM parser package for scholarship notices."""


def run(*args, **kwargs):
    from .llm_runner import run as runner_run

    return runner_run(*args, **kwargs)

__all__ = ["run"]
