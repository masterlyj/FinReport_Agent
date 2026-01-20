"""
网页搜索工具模块

该模块提供网页搜索和内容提取功能。
它从子模块导入并公开主要的搜索工具。
"""

from ..base import ToolResult
from pydantic import Field

class SearchResult(ToolResult):
    """网络搜索结果的容器。"""
    query: str = Field("", description="Search query")
    link: str = Field("", description="URL link")

    def __str__(self):
        format_output = f'Search Result for {self.query}\n'
        format_output += f"Title: {self.name}\n"
        format_output += f"Summary: {self.description}\n"
        format_output += f"Link: {self.link}\n\n"
        return format_output

    def __repr__(self):
        return self.__str__()


class ImageSearchResult(SearchResult):
    """图像搜索结果的容器。"""

    def __str__(self):
        format_output = f'Image Search Result for {self.query}\n'
        format_output += f"Title: {self.name}\n"
        format_output += f"Summary: {self.description}\n"
        format_output += f"Image Link: {self.data['image_url']}\n\n"
        format_output += f"Page Link: {self.data['page_url']}\n\n"
        return format_output

    def __repr__(self):
        return self.__str__()
