from .helpers import get_pull_requests, get_cached_data
from .helpers import PullRequestProcessorBase
from parsers import PullRequestDataParser
from nested_lookup import nested_lookup
import logging


class MessageApproved(PullRequestProcessorBase):
    def __init__(self, slack_client, github_client, local_client, args_config, worker_queue):
        super().__init__(slack_client, github_client, local_client)

        self.args_config = args_config
        self.worker_queue = worker_queue

        self.name = "ifApproved"
        self.reaction = self.args_config.approved_reaction_name

    def run(self):
        while True:
            message = self.worker_queue.get()
            if message is None:
                break

            pull_request_states = []
            pull_requests_cache = []
            is_approved = False
            pull_requests = get_pull_requests(message)

            for pull_request in pull_requests:
                local_cache_path = f"{pull_request.api_route}/reviews"
                pull_requests_cache.append(local_cache_path)

                local_cache_data = get_cached_data(self.local_client,
                                                   local_cache_path)
                if local_cache_data:
                    parser = PullRequestDataParser(local_cache_data)
                    is_approved = parser.get_reviews_approved()

                if local_cache_data and is_approved:
                    pull_request_states.append(is_approved)
                    continue

                if local_cache_data and not is_approved:
                    entity_tags = nested_lookup("ETag", local_cache_data)
                    pull_request.params.update({
                        "entity_tag": str(entity_tags[-1])
                    })
                    logging.info(f"new pull request params: "
                                 f"{pull_request.params}")

                github_api_params = pull_request.params
                pull_request_data = self.github_client.get_pull_request_reviews(
                    **github_api_params)

                if pull_request_data:
                    parser = PullRequestDataParser(pull_request_data)
                    is_approved = parser.get_reviews_approved()

                    self.local_client.save(pull_request_data,
                                           local_cache_path)

                pull_request_states.append(is_approved)

            if all(state for state in pull_request_states):
                self.slack_client.add_message_reaction(
                    self.args_config.slack_channel_id,
                    self.reaction,
                    message["ts"],
                    self.args_config.dry_run)

                for cache_path in pull_requests_cache:
                    self.local_client.delete(cache_path)

            self.worker_queue.task_done()
