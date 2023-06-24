import os
from typing import Type

from pydantic import BaseModel, Field

from superagi.tools.base_tool import BaseTool
from superagi.config.config import get_config


class ReadFileSchema(BaseModel):
    """Input for CopyFileTool."""
    file_name: str = Field(..., description="Path of the file to read")


class ReadFileTool(BaseTool):
    """
    Read File tool

    Attributes:
        name : The name.
        description : The description.
        args_schema : The args schema.
    """
    name: str = "Read File"
    args_schema: Type[BaseModel] = ReadFileSchema
    description: str = "Reads the file content in a specified location"

    def _execute(self, file_name: str):
        """
        Execute the read file tool.

        Args:
            file_name : The name of the file to read.

        Returns:
            The file content
        """
        input_root_dir = get_config('RESOURCES_INPUT_ROOT_DIR')
        output_root_dir = get_config('RESOURCES_OUTPUT_ROOT_DIR')
        final_path = None

        # Check in input_root_dir and its subdirectories
        for dirpath, dirnames, filenames in os.walk(input_root_dir):
            if file_name in filenames:
                final_path = os.path.join(dirpath, file_name)
                break

        # If not found, check in output_root_dir and its subdirectories
        if final_path is None:
            for dirpath, dirnames, filenames in os.walk(output_root_dir):
                if file_name in filenames:
                    final_path = os.path.join(dirpath, file_name)
                    break

        if final_path is None:
            raise FileNotFoundError(f"File '{file_name}' not found.")

        with open(final_path, 'r') as file:
            file_content = file.read()

        return file_content[:2000]
