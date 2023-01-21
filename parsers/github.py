import logging
import os.path
from urllib import parse


class PullRequestUrlParser:
    """ Pull Request URL Parser """

    def __init__(self, pull_request_url):
        logging.info(f"parsing pull request url {pull_request_url} using {self.__class__.__name__}")
        self.url = pull_request_url

        self.params = self.generate_pr_params()
        if self.params:
            logging.info(f"params: {self.params}")
            self.api_route = f"repos/" \
                             f"{self.params['repo_owner']}/" \
                             f"{self.params['repo_name']}/" \
                             f"pulls/{self.params['number']}"

    def generate_pr_params(self):
        url = parse.urlparse(self.url).path.split("/")
        try:
            params = {"repo_owner": url[1], "repo_name": url[2], "number": url[4]}
            logging.debug(f"url {self.url} params: {params}")
            return params
        except IndexError:
            logging.warning(f"unable to generate params for {self.url}")
            return None


class PullRequestDataParser:
    """ Pull Request Data Parser """

    def __init__(self, pull_request_data):
        self.data = pull_request_data
        if self.data:
            logging.info(f"parsing pull request data using {self.__class__.__name__}")

    def get_details_merged(self):
        if self.data and self.data.get("details"):
            details = self.data.get("details")
            if details["merged"] is True:
                logging.info("pull request is merged")
                return True
        logging.info("pull request is not merged")
        return False

    def get_reviews_approved(self):
        if self.data and self.data.get("reviews"):
            states = [rev["state"] for review in self.data["reviews"] for rev in review["review"]]
            if states and states[-1] == "APPROVED":
                logging.info("pull request is approved")
                return True
        logging.info("pull request is not approved")
        return False
