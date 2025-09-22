"""Shared utility functions used in the project.

Functions:
    format_docs: Convert documents to an xml-formatted string.
    load_chat_model: Load a chat model from a model name.
"""

from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage
from langchain_community.document_loaders import (UnstructuredExcelLoader, UnstructuredWordDocumentLoader,
                                                  UnstructuredPDFLoader, UnstructuredImageLoader,
                                                  UnstructuredPowerPointLoader, UnstructuredCSVLoader,
                                                  UnstructuredMarkdownLoader, TextLoader)


def _format_doc(doc: Document) -> str:
    """将单个文档格式化为 XML 字符串。

    Args:
        doc (Document): 要格式化的文档。

    Returns:
        str: 格式化后的文档作为 XML 字符串。
    """
    metadata = doc.metadata or {}
    meta = "".join(f" {k}={v!r}" for k, v in metadata.items())
    if meta:
        meta = f" {meta}"

    return f"<document{meta}>\n{doc.page_content}\n</document>"


def format_docs(docs: Optional[list[Document]]) -> str:
    """将文档列表格式化为 XML 字符串。

    此函数将 Document 对象列表格式化为单个 XML 字符串。

    Args:
        docs (Optional[list[Document]]): 要格式化的 Document 对象列表，或 None。

    Returns:
        str: 包含格式化文档的 XML 字符串。

    Examples:
        >>> docs = [Document(page_content="Hello"), Document(page_content="World")]
        >>> print(format_docs(docs))
        <documents>
        <document>
        Hello
        </document>
        <document>
        World
        </document>
        </documents>

        >>> print(format_docs(None))
        <documents></documents>
    """
    if not docs:
        return "<documents></documents>"
    formatted = "\n".join(_format_doc(doc) for doc in docs)
    return f"""<documents>
{formatted}
</documents>"""


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = ""
        model = fully_specified_name
    return init_chat_model(model, model_provider=provider)


def load_word(file_path, **kwargs):
    """
    加载Word文件
    mode: 加载模式 'single', 'elements', 'paged'
    param file_path: 文件路径
    param kwargs: 其他参数
    """
    loader = UnstructuredWordDocumentLoader(file_path, mode='single', **kwargs)
    documents = loader.load()
    return documents

def load_pdf(file_path, **kwargs):
    """
    加载pdf文件
    mode: 加载模式 'single', 'elements', 'paged'
    strategy: 加载策略  'auto', 'fast', 'ocr_only'【会把pdf转为图片进行Ocr】,
    ocr_languages: 语言 None, "eng+chi_sim"
    param file_path: 文件路径
    param kwargs: 其他参数
    """
    loader = UnstructuredPDFLoader(file_path, mode='single', strategy='auto', ocr_languages="eng+chi_sim",
                                        **kwargs)
    documents = loader.load()
    return documents

def load_txt(file_path, **kwargs):
    """
    加载txt文件
    txt_encoding: None, 'utf-8'
    param file_path: 文件路径
    param kwargs: 其他参数
    """
    loader = TextLoader(file_path, encoding=None, autodetect_encoding=True)
    documents = loader.load()
    return documents

def get_message_text(msg: AnyMessage) -> str:
    """从消息对象中提取文本内容。

    此函数从不同格式的消息对象中提取文本内容。

    Args:
        msg (AnyMessage): 要提取文本的消息对象。

    Returns:
        str: 消息对象的文本内容。

    Examples:
        >>> from langchain_core.messages import HumanMessage
        >>> get_message_text(HumanMessage(content="Hello"))
        'Hello'
        >>> get_message_text(HumanMessage(content={"text": "World"}))
        'World'
        >>> get_message_text(HumanMessage(content=[{"text": "Hello"}, " ", {"text": "World"}]))
        'Hello World'
    """
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()
