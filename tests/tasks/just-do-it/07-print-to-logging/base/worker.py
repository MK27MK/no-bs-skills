import logging
import time

log = logging.getLogger(__name__)


def run(jobs):
    for job in jobs:
        print("starting", job)
        try:
            job()
        except:
            pass
        print("finished", job)
        time.sleep(1)
