"""Example Python file for testing crabpy."""



def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def greet(name: str, times: int = 1) -> str:
    """Greet someone multiple times."""
    result: str = ""
    for i in range(times):
        result += f"Hello, {name}!\n"
    return result


def find_max(numbers: list[int]) -> int | None:
    """Find the maximum number in a list."""
    if not numbers:
        return None

    max_val: int = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val


class Counter:
    """A simple counter class."""

    count: int

    def __init__(self, start: int = 0) -> None:
        self.count = start

    def increment(self) -> int:
        self.count += 1
        return self.count

    def decrement(self) -> int:
        self.count -= 1
        return self.count


def process_data(data: dict[str, int]) -> list[str]:
    """Process a dictionary and return keys with positive values."""
    result: list[str] = []
    for key in data:
        if data[key] > 0:
            result.append(key)
    return result
