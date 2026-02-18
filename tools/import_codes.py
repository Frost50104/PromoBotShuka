"""CLI tool for importing promo codes."""

import asyncio
import sys
from pathlib import Path

from app.database.session import async_session_maker, init_db
from app.services import PromoService
from app.utils.logging import setup_logging, get_logger
from app.config import config

setup_logging(config.LOG_LEVEL)
logger = get_logger(__name__)


async def import_from_file(file_path: str) -> None:
    """
    Import promo codes from file.

    Args:
        file_path: Path to file with codes (one per line)
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("File not found", file_path=file_path)
        sys.exit(1)

    # Read codes from file
    codes = []
    with open(path, "r") as f:
        for line in f:
            code = line.strip()
            if code and not code.startswith("#"):
                codes.append(code)

    if not codes:
        logger.error("No codes found in file", file_path=file_path)
        sys.exit(1)

    logger.info("Found codes in file", count=len(codes), file_path=file_path)

    # Initialize database
    await init_db()

    # Import codes
    async with async_session_maker() as session:
        added, skipped = await PromoService.add_codes(session, codes)

    logger.info(
        "Import completed",
        added=added,
        skipped=skipped,
        total=len(codes),
    )

    print(f"\n✅ Import completed:")
    print(f"   Added: {added}")
    print(f"   Skipped (duplicates): {skipped}")
    print(f"   Total: {len(codes)}")


async def import_test_codes() -> None:
    """Import test codes."""
    test_codes = [
        "987651527138080",
        "987652589596192",
        "987652691640275",
        "987652924328984",
        "987658164637059",
    ]

    logger.info("Importing test codes", count=len(test_codes))

    # Initialize database
    await init_db()

    # Import codes
    async with async_session_maker() as session:
        added, skipped = await PromoService.add_codes(session, test_codes)

    logger.info(
        "Test codes import completed",
        added=added,
        skipped=skipped,
        total=len(test_codes),
    )

    print(f"\n✅ Test codes import completed:")
    print(f"   Added: {added}")
    print(f"   Skipped (duplicates): {skipped}")
    print(f"   Total: {len(test_codes)}")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m tools.import_codes --file <path>  # Import from file")
        print("  python -m tools.import_codes --test         # Import test codes")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--file":
        if len(sys.argv) < 3:
            print("Error: File path required")
            print("Usage: python -m tools.import_codes --file <path>")
            sys.exit(1)
        file_path = sys.argv[2]
        asyncio.run(import_from_file(file_path))

    elif command == "--test":
        asyncio.run(import_test_codes())

    else:
        print(f"Unknown command: {command}")
        print("Use --file <path> or --test")
        sys.exit(1)


if __name__ == "__main__":
    main()
