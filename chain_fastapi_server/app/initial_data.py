import logging

from sqlmodel import Session

from app.core.db import engine, init_db
from app.services.demo_seed_service import DemoSeedService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        DemoSeedService.seed_all(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
