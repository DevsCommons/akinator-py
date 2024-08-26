# akinator-py

A Python library for interacting with the Akinator game API. This library provides both synchronous and asynchronous methods to interact with the Akinator game, allowing users to start a game, answer questions, and navigate back to previous questions.

## Installation

You can install the library using pip:

```bash
pip install akinatorpy
```

## Usage

### Synchronous Usage

```python
from akinator import Akinator, Answer, Language

aki = Akinator(language=Language.English)
start_result = aki.start_game()

if start_result.ok:
    print(f"First question: {start_result.result.question}")
```

### Asynchronous Usage

```python
import asyncio
from akinator import AsyncAkinator, Answer, Language

async def main():
    aki = AsyncAkinator(language=Language.English)
    start_result = await aki.start_game()

    if start_result.ok:
        print(f"First question: {start_result.result.question}")

asyncio.run(main())
```

## Features

-   Supports both synchronous and asynchronous interaction with the Akinator API.
-   Caching mechanism to store game state and optimize API calls.
-   Simple and intuitive API design for ease of use.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING](CONTRIBUTING.md) file for guidelines.

## Support

If you have any questions or issues, please open an issue on the [GitHub repository](https://github.com/DevsCommons/akinator-py/issues).
