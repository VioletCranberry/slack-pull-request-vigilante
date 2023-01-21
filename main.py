from clients import SlackClient, GitHubClient
from clients import LocalCacheClient
from utils import get_arguments, SafeScheduler
from processors import MessageApproved, MessageMerged
from processors.helpers import get_pull_requests, get_reactions
from threading import Thread
import queue
import logging
import time


class SlackMessageThread(Thread):
    def __init__(self, slack_client, config, queue_req_approval, queue_req_merging):
        super().__init__()
        self.name = "slack messages"

        self.client = slack_client
        self.args_config = config

        self.queue_req_approval = queue_req_approval
        self.queue_req_merging = queue_req_merging

    def run(self):
        messages = self.client.get_conversation_history(
            self.args_config.slack_channel_id,
            self.args_config.slack_time_window_minutes)
        for message in messages:
            message_replies = self.client.get_conversation_replies(
                self.args_config.slack_channel_id,
                self.args_config.slack_time_window_minutes,
                message["ts"])

            for reply in message_replies:
                pull_requests = get_pull_requests(reply)

                if pull_requests and not get_reactions(
                        reply, self.args_config.approved_reaction_name):
                    self.queue_req_approval.put(reply)
                if pull_requests and not get_reactions(
                        reply, self.args_config.merged_reaction_name):
                    self.queue_req_merging.put(reply)

        self.queue_req_approval.join()
        self.queue_req_merging.join()


def run_threaded(slack_client, config, queue_req_approval, queue_req_merging):
    message_thread = SlackMessageThread(slack_client,
                                        config,
                                        queue_req_approval,
                                        queue_req_merging)
    message_thread.start()
    message_thread.join()


def main():
    args = get_arguments()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s - "
                               "%(threadName)s - "
                               "%(levelname)s "
                               "%(message)s")

    scheduler = SafeScheduler(reschedule_on_failure=True)

    slack_client = SlackClient(args.slack_api_token,
                               max_retries=args.max_retries)
    github_client = GitHubClient(args.github_api_token,
                                 max_retries=args.max_retries)

    local_client = LocalCacheClient(args.cache_folder_path)

    queue_req_approval = queue.Queue()
    queue_req_merging = queue.Queue()

    processors_approved = MessageApproved(slack_client,
                                          github_client,
                                          local_client,
                                          args,
                                          queue_req_approval)
    processors_approved.start()

    processors_merged = MessageMerged(slack_client,
                                      github_client,
                                      local_client,
                                      args,
                                      queue_req_merging)
    processors_merged.start()

    scheduler.every(args.sleep_period_minutes).minutes.do(
        run_threaded, slack_client, args, queue_req_approval, queue_req_merging)
    scheduler.run_all()
    while True:
        scheduler.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
