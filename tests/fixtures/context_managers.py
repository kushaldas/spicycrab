"""Test file for context managers and error handling."""


class FileHandler:
    """A simple file-like context manager."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.content = ""

    def __enter__(self) -> object:
        """Open the file."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Close the file."""
        pass

    def write(self, data: str) -> None:
        """Write data."""
        self.content = self.content + data


def write_to_file(filename: str, data: str) -> None:
    """Use context manager to write to file."""
    with FileHandler(filename) as f:
        f.write(data)


def divide(a: int, b: int) -> int:
    """Divide two numbers with error handling."""
    if b == 0:
        return 0
    return a // b


def main() -> None:
    """Test context managers and error handling."""
    write_to_file("test.txt", "Hello")

    result: int = divide(10, 2)
    print(result)

    result2: int = divide(10, 0)
    print(result2)
