import json5
from abc import ABC, abstractmethod
from typing import Dict, List, NamedTuple
from superagi.helper.json_cleaner import JsonCleaner
from superagi.lib.logger import logger


class AgentGPTAction(NamedTuple):
    name: str
    args: Dict


class AgentTasks(NamedTuple):
    tasks: List[Dict] = []
    error: str = ""


class BaseOutputParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> AgentGPTAction:
        """Return AgentGPTAction"""


class AgentOutputParser(BaseOutputParser):
    def log_field(self, field, value):
        format_prefix_yellow = "\033[93m\033[1m"
        format_suffix_yellow = "\033[0m\033[0m"
        logger.info(f"{format_prefix_yellow}{field}: {format_suffix_yellow}{value}")
        
    def parse(self, text: str) -> AgentGPTAction:
        text = JsonCleaner.check_and_clean_json(text)
        
        try:
            parsed = json5.loads(text)
        except json5.JSONDecodeError:
            raise ValueError(f"Could not parse invalid json: {text}")

        try:
            logger.info("\033[92m\033[1mIntelligence : \033[0m\033[0m")
            for field in ["text", "reasoning", "plan", "criticism"]:
                if field in parsed["thoughts"]:
                    self.log_field(field.capitalize(), parsed["thoughts"][field])
                    
            logger.info("\033[92m\033[1mAction : \033[0m\033[0m")
            if parsed["tool"] is None or not parsed["tool"]:
                return AgentGPTAction(name="", args="")
            if "name" in parsed["tool"]:
                self.log_field("Tool", parsed["tool"]["name"])
            
            args = parsed["tool"].get("args", {})
            return AgentGPTAction(
                name=parsed["tool"]["name"],
                args=args,
            )
        except (KeyError, TypeError):
            raise ValueError(f"Incomplete tool args: {parsed}")

    def parse_tasks(self, text: str) -> AgentTasks:
        preprocessed_text = JsonCleaner.preprocess_json_input(text)
        
        try:
            parsed = json5.loads(preprocessed_text, strict=False)
        except Exception:
            raise ValueError(f"Could not parse invalid json: {text}")

        try:
            logger.info("Tasks: ", parsed["tasks"])
            return AgentTasks(
                tasks=parsed["tasks"]
            )
        except (KeyError, TypeError):
            raise ValueError(f"Incomplete tool args: {parsed}")
