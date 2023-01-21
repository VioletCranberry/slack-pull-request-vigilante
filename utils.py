from datetime import datetime, timedelta
from time import sleep
from schedule import Scheduler
from traceback import format_exc
import configargparse
import logging


class SafeScheduler(Scheduler):
    def __init__(self, reschedule_on_failure=True, minutes_after_failure=0, seconds_after_failure=0):
        self.reschedule_on_failure = reschedule_on_failure
        self.minutes_after_failure = minutes_after_failure
        self.seconds_after_failure = seconds_after_failure
        super().__init__()

    def _run_job(self, job):
        try:
            super()._run_job(job)
        except Exception:
            logging.error(format_exc())
            if self.reschedule_on_failure:
                if self.minutes_after_failure != 0 or self.seconds_after_failure != 0:
                    logging.warning("Rescheduled in %s minutes and %s seconds." % (
                        self.minutes_after_failure, self.seconds_after_failure))
                    job.last_run = None
                    job.next_run = datetime.now() + timedelta(minutes=self.minutes_after_failure,
                                                              seconds=self.seconds_after_failure)
                else:
                    logging.warning("Rescheduled.")
                    job.last_run = datetime.now()
                    job._schedule_next_run()
            else:
                logging.warning("Job canceled.")
                self.cancel_job(job)


def get_arguments():
    parser = configargparse.ArgParser(default_config_files=["./config.yaml"])

    parser.add_argument("--config_file",
                        action="store",
                        is_config_file=True,
                        type=str,
                        required=False)

    parser.add_argument("--slack_api_token",
                        action="store",
                        type=str,
                        required=True,
                        env_var="SLACK_API_TOKEN")
    parser.add_argument("--slack_channel_id",
                        action="store",
                        type=str,
                        required=True,
                        env_var="CHANNEL_ID")
    parser.add_argument("--slack_time_window_minutes",
                        action="store",
                        type=int,
                        required=False,
                        env_var="TIME_WINDOW_MINUTES")
    parser.add_argument("--approved_reaction_name",
                        action="store",
                        type=str,
                        required=False,
                        default="white_check_mark",
                        env_var="APPROVED_REACTION_NAME")
    parser.add_argument("--merged_reaction_name",
                        action="store",
                        type=str,
                        required=False,
                        default="merged",
                        env_var="MERGED_REACTION_NAME")
    parser.add_argument("--github_api_token",
                        action="store",
                        type=str,
                        required=True,
                        env_var="GITHUB_API_TOKEN")
    parser.add_argument("--cache_folder_path",
                        action="store",
                        type=str,
                        required=False,
                        default="./cache",
                        env_var="CACHE_FOLDER_PATH")
    parser.add_argument("--sleep_period_minutes",
                        action="store",
                        type=int,
                        required=True,
                        env_var="SLEEP_PERIOD_MINUTES")
    parser.add_argument("--max_retries",
                        action="store",
                        type=int,
                        required=False,
                        default=5,
                        env_var="MAX_RETRIES")
    parser.add_argument("--dry_run",
                        action="store_true",
                        required=False,
                        env_var="DRY_RUN")
    parser.add_argument("--debug",
                        action="store_true",
                        required=False,
                        env_var="DEBUG")
    return parser.parse_args()


def sleep_until(timestamp: float):
    time_now = datetime.now()
    ts = datetime.fromtimestamp(timestamp)
    delta = ts - time_now
    if delta > timedelta(0):
        sleep(delta.total_seconds())
        return True
