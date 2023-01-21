import logging
import re


class MessageElementParser:
    """ Slack Message Element Parser """

    def __init__(self, message: dict):
        logging.info(f"parsing {message.get('ts')} using {self.__class__.__name__}")
        self.message = message

        self.layout_blocks = [block for block in self.message["blocks"]] if "blocks" in self.message.keys() else []
        self.elements = self.get_layout_elements()
        if self.elements:
            logging.info(f"message contains {len(self.elements)} elements")

    def get_block_elements(self, message_block: dict, block_elements: [] = None):
        block_elements = block_elements if block_elements else []

        if message_block.get("elements"):
            for block_element in message_block.get("elements"):
                if "elements" not in block_element.keys():
                    block_elements.append(block_element)
                else:
                    for element in block_element.get("elements"):
                        if "elements" not in element.keys():
                            block_elements.append(element)
                        else:
                            self.get_block_elements(element, block_elements)
        return block_elements

    def get_layout_elements(self):
        if self.layout_blocks:
            layout_elements = []
            for layout_block in self.layout_blocks:
                block_elements = self.get_block_elements(layout_block)
                layout_elements.extend(block_elements)
            logging.debug(f"message layout elements: {layout_elements}")
            return layout_elements
        else:
            logging.info("message does not contain any layout elements")
            return []


class MessagePullRequestParser(MessageElementParser):
    """ Slack Message Pull Request parser """

    def __init__(self, message: dict):
        super().__init__(message)
        logging.info(f"parsing {message.get('ts')} using {self.__class__.__name__}")

        self.urls = [message_element.get("url") for message_element in self.elements
                     if message_element.get("type") == "link"]
        self.pull_requests = self.get_pull_requests()
        if self.pull_requests:
            logging.info(f"message contains {len(self.pull_requests)} pull requests")

    def get_pull_requests(self):
        re_pattern = r"http[s]://github.com/.+/pull/\d+"
        if self.urls:
            urls = [match.group() for url in self.urls
                    if (match := re.search(re_pattern, url))]
            logging.debug(f"message pr urls: {urls}")
            return urls
        else:
            logging.info("message does not contain pull requests")
            return []


class MessageReactionsParser:
    """ Slack Message Reactions Parser """

    def __init__(self, message: dict):
        logging.info(f"parsing {message.get('ts')} using {self.__class__.__name__}")
        self.message = message

        self.reactions = self.get_message_reactions()
        if self.reactions:
            logging.info(f"message contains {len(self.reactions)} user reactions")

    def get_message_reactions(self):
        if "reactions" in self.message.keys():
            reactions = [reaction.get("name") for reaction in self.message.get("reactions")]
            logging.debug(f"message reactions: {reactions}")
            return reactions
        else:
            logging.info("message has no user reactions")
        return []

    def lookup_reaction(self, reaction):
        if self.reactions and reaction in self.reactions:
            logging.info(f"reaction {reaction} was found")
            return True
        else:
            logging.info(f"reaction {reaction} was not found")
            return False
