from .helpers import get_pull_requests, get_cached_data
from .helpers import PullRequestProcessorBase
from parsers import PullRequestDataParser
from nested_lookup import nested_lookup
import logging


class MessageMerged(PullRequestProcessorBase):
    def __init__(self, slack_client, github_client, local_client, args_config, worker_queue):
        super().__init__(slack_client, github_client, local_client)

        self.args_config = args_config
        self.worker_queue = worker_queue

        self.name = "IfMerged"
        self.reaction = self.args_config.merged_reaction_name

    def run(self):
        while True:
            message = self.worker_queue.get()
            if message is None:
                break

            pull_request_states = []
            pull_requests_cache = []
            is_merged = False
            pull_requests = get_pull_requests(message)

            for pull_request in pull_requests:
                local_cache_path = f"{pull_request.api_route}/details"
                pull_requests_cache.append(local_cache_path)

                local_cache_data = get_cached_data(self.local_client,
                                                   local_cache_path)
                if local_cache_data:
                    parser = PullRequestDataParser(local_cache_data)
                    is_merged = parser.get_details_merged()

                if local_cache_data and is_merged:
                    pull_request_states.append(is_merged)
                    continue

                if local_cache_data and not is_merged:
                    last_modified = nested_lookup("Last-Modified", local_cache_data)
                    pull_request.params.update({
                        "last_modified": str(last_modified[-1])
                    })
                    logging.info(f"new pull request params: "
                                 f"{pull_request.params}")

                github_api_params = pull_request.params
                pull_request_data = self.github_client.get_pull_request_details(
                    **github_api_params)

                if pull_request_data:
                    parser = PullRequestDataParser(pull_request_data)
                    is_merged = parser.get_details_merged()

                    self.local_client.save(pull_request_data,
                                           local_cache_path)

                pull_request_states.append(is_merged)

            if all(state for state in pull_request_states):
                self.slack_client.add_message_reaction(
                    self.args_config.slack_channel_id,
                    self.reaction,
                    message["ts"],
                    self.args_config.dry_run)

                for cache_path in pull_requests_cache:
                    self.local_client.delete(cache_path)

            self.worker_queue.task_done()
