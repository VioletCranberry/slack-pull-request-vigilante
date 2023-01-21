## PR-vigilante

### Description:
Python application to track down and automatically mark pull request messages  
in Slack channel as approved or merged after reviewing/merging  
associated pull request in GitHub. If multiple PRs are found in a single message   
it will be marked as approved or merged after all the pull requests will be approved/merged.  

Application is built around [Python Slack SDK](https://slack.dev/python-slack-sdk/).  
GitHub API caching is implemented based on conditional requests and local cache client.

### Requited Slack token permissions:
`channels:history`, `groups:history`, `im:history`, `mpim:history`,  
`reactions:read` and `reactions:write` are required scopes for Slack API token

### Things to consider:
1. Slack API rate limit tiers - based on methods used, e.g.  
    https://api.slack.com/methods/conversations.history and  
    https://api.slack.com/methods/reactions.add etc
2. GitHub API rate limits

### Application structure:
```
├── clients    - clients (github, slack, local cache etc)
├── main.py    - main entrypoint
├── parsers    - slack / github data parsers
├── processors - message processors
├── utils.py   - shared functions 
```

### Contribution:
1. Define new parsers in `/parsers` directory
2. Define new worker thread in `/processors`
3. Add new thread and queue into `main.py`

### High-level of processing:
```
                    --> [ Queue ] -- processors.MessageApproved 
                  / ..
SlackMessageThread ---> [ Queue ] -- processors.MessageMerged
                  \ ..
                    --> [ Queue ] -- consumer TBD
                    
Where parsing of messages based on conditions happens before populating consumers' queue
```


### Build and publish:
```commandline
image_tag='slack-tools:<version>'
ecr_repository='<my_repository>'
platform='linux/amd64'

docker buildx build --platform "$platform" -t "$image_tag" .
docker tag "$image_tag" "$ecr_repository/$image_tag"
docker push "$ecr_repository/$image_tag"
```
change Helm `version` and `appVersion` accordingly

### Apply & Delete:
```
helmfile apply --interactive --kube-context <context> (uses current context by default)
helmfile delete --interactive
```

### Run locally:
```commandline
python3 main.py --slack_api_token <slack_api_token>     `
                `--github_api_token <github_api_token>  `
                `--slack_channel_id <slack_channel_id>  `
                `--slack_time_window_seconds 4000       `
                `--sleep_period_seconds 30 `
                `--dry_run `
                `--debug
```

### TODO:
- [x] Support lookup of PRs inside of slack threads
- [x] Replace GHApi with own GitHub Client to support Etags
- [x] GitHub API caching based on conditional requests (eTags)
- [x] Local FileCache client
- [x] Pub-sub thread model instead of Async workarounds
- [x] Config file support
- [x] Additional reaction based on merged PR state
- [x] New Helm chart allowing persistence
- [ ] Load worker threads dynamically (app -> framework)
- [ ] Add configmap support to the Helm chart


### Not Tested:
- Caching of conditional requests with pagination (large GitHub reviews)
