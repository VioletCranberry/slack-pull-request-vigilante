from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.http_retry.builtin_handlers import ConnectionErrorRetryHandler
from datetime import datetime, timedelta
from functools import wraps
from utils import sleep_until
import logging


def set_oldest_ts(minutes: int):
    init_time = datetime.now()
    oldest = init_time - timedelta(
        minutes=minutes)
    return str(oldest.timestamp())


def set_conv_params(channel: str, minutes: int, latest_ts: str = None):
    # set oldest_ts ts based on minutes to look back
    oldest_ts = set_oldest_ts(minutes)
    # set latest_ts to current time if not provided
    latest_ts = latest_ts if latest_ts else str(datetime.now().timestamp())
    params = {
        "latest": latest_ts,
        "oldest": oldest_ts,
        "channel": channel,
        "limit": 100,
        "inclusive": True
    }
    return params


def api_rate_control(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        while True:
            try:
                result = func(self, *args, **kwargs)
                return result
            except SlackApiError as err:
                if err.response.status_code == 429:
                    logging.warning("api rate limit hit!")
                    time_wait = float(err.response["headers"]["Retry-After"])
                    sleep_until(time_wait)
                    continue
                else:
                    break
    return wrapper


class SlackClient:
    """ Slack client class """

    def __init__(self, api_token: str, max_retries=1):
        self.client = WebClient(api_token)

        conn_error_handler = ConnectionErrorRetryHandler(
            max_retry_count=max_retries)
        self.client.retry_handlers.append(conn_error_handler)

    @api_rate_control
    def add_message_reaction(self, channel: str, reaction: str, timestamp: str, dry_run: bool):
        if not dry_run:
            try:
                logging.info(f"adding reaction '{reaction}' to message")
                self.client.reactions_add(channel=channel, name=reaction, timestamp=timestamp)
                return True
            except SlackApiError as err:
                logging.info(f"error reacting to message: {err}")
                return False
        else:
            logging.info(f"dry-run: adding reaction '{reaction}' to message")
            return True

    @api_rate_control
    def _get_conversation_history(self, channel: str, minutes: int, latest_ts: str = None):
        params = set_conv_params(channel, minutes, latest_ts)
        try:
            history = self.client.conversations_history(**params)
            return history
        except SlackApiError as err:
            logging.info(f"error loading conv. history: {err}")
            return []

    def get_conversation_history(self, channel: str, minutes: int):
        history = self._get_conversation_history(channel, minutes)
        messages = history["messages"]

        while history.get("has_more"):
            last_ts = history["messages"][-1]["ts"]
            history = self._get_conversation_history(
                channel, minutes, last_ts)
            messages.extend(history["messages"])
        logging.info(f"fetched {len(messages)} messages")
        return messages

    @api_rate_control
    def _get_conversation_replies(self, channel: str, minutes: int, ts: str, latest_ts: str = None):
        params = set_conv_params(channel, minutes, latest_ts)
        params["ts"] = ts
        try:
            threads = self.client.conversations_replies(**params)
            return threads
        except SlackApiError as err:
            logging.info(f"error loading message replies: {err}")
            return []

    def get_conversation_replies(self, channel: str, minutes: int, ts: str):
        history = self._get_conversation_replies(channel, minutes, ts)
        replies = history["messages"]

        while history.get("has_more"):
            last_ts = history["messages]"][-1]["ts"]
            history = self._get_conversation_replies(
                channel, minutes, ts, last_ts)
            replies.extend(history["messages"])
        if len(replies) > 1:
            logging.info(f"fetched {len(replies)} replies for message {ts}")
        return replies
