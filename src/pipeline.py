import logging

logger = logging.getLogger(__name__)


def run():
    from src.load_data import run_pipeline
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("care-operations-analytics pipeline starting")
    run_pipeline()


if __name__ == "__main__":
    run()
