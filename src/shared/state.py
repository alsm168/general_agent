"""Shared functions for state management."""

import hashlib
import uuid
from typing import Any, Literal, Optional, Union

from langchain_core.documents import Document


def _generate_uuid(page_content: str) -> str:
    """
        根据文档的page_content内容生成一个 UUID。
        
        Args:
            page_content (str): 文档Document的page_content内容。
        
        Returns:
            str: 生成的 UUID 字符串。
    """
    md5_hash = hashlib.md5(page_content.encode()).hexdigest()
    return str(uuid.UUID(md5_hash))


def reduce_docs(
    existing: Optional[list[Document]],
    new: Union[
        list[Document],
        list[dict[str, Any]],
        list[str],
        str,
        Literal["delete"],
    ],
) -> list[Document]:
    """根据输入类型对文档进行归约和处理。

    此函数处理多种输入类型，并将它们转换为 Document 对象序列。
    它可以删除现有文档，从字符串或字典创建新文档，或返回现有文档。
    它还会根据文档 ID 将现有文档与新文档合并。

    Args:
        existing (Optional[Sequence[Document]]): 状态中已存在的文档（如果有）。
        new (Union[Sequence[Document], Sequence[dict[str, Any]], Sequence[str], str, Literal["delete"]]):
            待处理的新输入。可以是 Document 序列、字典序列、字符串序列、单个字符串，
            或字面量 "delete"。
    """
    if new == "delete":
        return []

    existing_list = list(existing) if existing else []
    if isinstance(new, str):
        return existing_list + [
            Document(page_content=new, metadata={"uuid": _generate_uuid(new)})
        ]

    new_list = []
    if isinstance(new, list):
        existing_ids = set(doc.metadata.get("uuid") for doc in existing_list)
        for item in new:
            if isinstance(item, str):
                item_id = _generate_uuid(item)
                new_list.append(Document(page_content=item, metadata={"uuid": item_id}))
                existing_ids.add(item_id)

            elif isinstance(item, dict):
                metadata = item.get("metadata", {})
                item_id = metadata.get("uuid") or _generate_uuid(
                    item.get("page_content", "")
                )

                if item_id not in existing_ids:
                    new_list.append(
                        Document(**{**item, "metadata": {**metadata, "uuid": item_id}})
                    )
                    existing_ids.add(item_id)

            elif isinstance(item, Document):
                item_id = item.metadata.get("uuid", "")
                if not item_id:
                    item_id = _generate_uuid(item.page_content)
                    new_item = item.copy(deep=True)
                    new_item.metadata["uuid"] = item_id
                else:
                    new_item = item

                if item_id not in existing_ids:
                    new_list.append(new_item)
                    existing_ids.add(item_id)

    return existing_list + new_list
