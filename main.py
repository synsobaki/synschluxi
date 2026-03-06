"""Project entrypoint for local launch without module mode."""

import asyncio

from src.main import main


if __name__ == "__main__":
    asyncio.run(main())
