from functools import wraps
from utils import sleep_until
import logging
import requests
import json
from requests.adapters import HTTPAdapter


def api_rate_control(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            result = func(*args, **kwargs)
            limit = result.headers.get(
                "x-ratelimit-limit")
            remaining = result.headers.get(
                "x-ratelimit-remaining")
            reset_time = result.headers.get(
                "x-ratelimit-reset")
            used = result.headers.get(
                "x-ratelimit-used"
            )
            if remaining == 0:
                logging.warning("api rate limit hit")
                time_wait = float(reset_time)
                sleep_until(time_wait)
                continue
            else:
                logging.info(f"github api quota used:"
                             f" {used} / limit {limit}")
                logging.info(f"github api quota remaining:"
                             f" {remaining}")
                return result
    return wrapper


class GitHubClient:
    """ GitHub client class """

    def __init__(self, api_token, api_host=None, max_retries=1):
        self.api_host = api_host if api_host else "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {api_token}"
        }
        self.client = requests.Session()
        self.client.mount(self.api_host, HTTPAdapter(max_retries=max_retries))

    @api_rate_control
    def api_call(self, api_url=None, api_route=None, verb=None,
                 headers: dict = None, query: dict = None, data: dict = None):
        headers = {**self.headers, **(headers or {})}
        if verb is None:
            verb = "POST" if data else "GET"
        if api_url is None:
            api_url = f"{self.api_host}/{api_route}"
        try:
            logging.info(f"calling api url {api_url}")
            res = self.client.request(method=verb, url=api_url,
                                      headers=headers,
                                      params=query, json=data)
            res.raise_for_status()
            return res
        except requests.exceptions.RequestException as err:
            logging.warning(f"GH API client error: {err}")
            return {}

    def get_pull_request_details(self, repo_owner, repo_name, number,
                                 entity_tag=None, last_modified=None):
        api_route = f"repos/{repo_owner}/{repo_name}/pulls/{number}"
        headers = {
            "If-None-Match": entity_tag,
            "If-Modified-Since": last_modified
        }
        res = self.api_call(api_route=api_route,
                            verb="GET",
                            headers=headers)
        if (entity_tag or last_modified) and res.status_code == 304:
            logging.info("requested object was not modified")
            return {}
        details = {"headers": dict(res.headers),
                   "details": res.json()}
        return details

    def get_pull_request_reviews(self, repo_owner, repo_name, number, page=None,
                                 entity_tag=None, last_modified=None):
        api_route = f"repos/{repo_owner}/{repo_name}/pulls/{number}/reviews"
        api_query = {"page": page, "per_page": 100}
        headers = {
            "If-None-Match": entity_tag,
            "If-Modified-Since": last_modified
        }
        res = self.api_call(api_route=f"{api_route}",
                            verb="GET",
                            query=api_query,
                            headers=headers)

        if (entity_tag or last_modified) and res.status_code == 304:
            logging.info("requested object was not modified")
            return {}

        reviews = {"reviews": []}
        response_json = json.loads(res.text)
        content = {"headers": dict(res.headers),
                   "review": response_json}
        reviews["reviews"].append(content)

        if page is None:
            while "next" in res.links.keys():
                res = self.api_call(api_url=res.links["next"]["url"],
                                    verb="GET",
                                    query=api_query,
                                    headers=headers)
                response_json = json.loads(res.text)
                content = {"headers": dict(res.headers),
                           "review": response_json}
                reviews["reviews"].append(content)
        return reviews
