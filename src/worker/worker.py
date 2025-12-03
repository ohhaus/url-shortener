import logging

from arq.worker import run_worker

from src.worker.tasks import WorkerSettings


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    logging.getLogger(__name__).info('Starting ARQ worker...')

    run_worker(WorkerSettings)


if __name__ == '__main__':
    main()
