"""Statistical power analysis for secret-loyalty audit detection rates."""


def main() -> None:
    """Entry point for the package CLI."""
    from .sources.lamerton_roger_2026 import validate

    validate()