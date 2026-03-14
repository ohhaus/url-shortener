from arq.worker import run_worker

from src.logging import setup_logging
from src.worker.tasks import WorkerSettings


def main() -> None:
    logger = setup_logging()
    logger.info('Starting ARQ worker...')
    run_worker(WorkerSettings)


if __name__ == '__main__':
    main()
