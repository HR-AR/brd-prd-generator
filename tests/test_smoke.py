"""Smoke test to verify basic project setup."""


def test_basic_math():
    """Basic sanity check."""
    assert 1 + 1 == 2, "basic math should hold"


def test_imports():
    """Verify core dependencies can be imported."""
    try:
        import fastapi  # noqa: F401
        import pydantic  # noqa: F401

        assert True
    except ImportError as e:
        assert False, f"Failed to import core dependencies: {e}"


if __name__ == "__main__":
    test_basic_math()
    test_imports()
    print("✓ smoke tests passed")
