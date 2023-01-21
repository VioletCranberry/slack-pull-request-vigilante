from parsers import MessagePullRequestParser
from parsers import PullRequestUrlParser
from parsers import MessageReactionsParser
from threading import Thread
from clients import NoCachedData


def get_pull_requests(message):
    parser = MessagePullRequestParser(message)
    if parser.pull_requests:
        return [PullRequestUrlParser(pr)
                for pr in parser.pull_requests]
    return


def get_reactions(message, reaction):
    parser = MessageReactionsParser(message)
    if parser.reactions:
        return parser.lookup_reaction(reaction)
    return


def get_cached_data(local_client, _path):
    try:
        cached_data = local_client.load(_path)
        return cached_data
    except NoCachedData:
        return None


class PullRequestProcessorBase(Thread):
    def __init__(self, slack_client, github_client, local_client):
        super().__init__()

        self.daemon = True
        self.slack_client = slack_client
        self.github_client = github_client
        self.local_client = local_client

    def run(self):
        pass
