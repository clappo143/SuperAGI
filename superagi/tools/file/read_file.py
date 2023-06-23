import os
from typing import Type, Optional

from pydantic import BaseModel, Field

from superagi.helper.resource_helper import ResourceHelper
from superagi.resource_manager.file_manager import FileManager
from superagi.tools.base_tool import BaseTool


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
    agent_id: int = None
    args_schema: Type[BaseModel] = ReadFileSchema
    description: str = "Reads the file content in a specified location"
    resource_manager: Optional[FileManager] = None

    def _update_path(self, path: str) -> str:
        if "{agent_id}" in path:
            path = path.replace("{agent_id}", str(self.agent_id))
        return path

    def _execute(self, file_name: str):
        """
        Execute the read file tool.

        Args:
            file_name : The name of the file to read.

        Returns:
            The file content and the file name
        """
        input_root_dir = ResourceHelper.get_root_input_dir()
        output_root_dir = ResourceHelper.get_root_output_dir()

        # Attempt to locate the file in the input directory
        final_path = self._update_path(input_root_dir + file_name)

        if not os.path.exists(final_path) and output_root_dir is not None:
            # If not found, attempt to locate the file in the output directory
            final_path = self._update_path(output_root_dir + file_name)

        if not os.path.exists(final_path):
            raise FileNotFoundError(f"File '{file_name}' not found.")

        with open(final_path, 'r') as file:
            file_content = file.read()
        file_content = ' '.join(file_content.split(" ")[:1000])  # Limit to the first 1000 words
        return file_content + "\n File " + file_name + " read successfully."
