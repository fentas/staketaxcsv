from juno.config import localconfig
from common.progress import Progress as CommonProgress

SECONDS_PER_PAGE = 5.0


class Progress(CommonProgress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
