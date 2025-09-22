"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Literal, Optional, Type, TypeVar

from langchain_core.runnables import RunnableConfig, ensure_config


@dataclass(kw_only=True)
class BaseConfiguration:
    """用于索引和RAG检索操作的配置类。

    该类定义了配置索引和检索过程所需的参数，包括嵌入模型的选择、检索器提供者的选择以及搜索参数。
    """

    embedding_model: Annotated[
        str,
        {"__template_metadata__": {"kind": "embeddings"}},
    ] = field(
        # #"openai/text-embedding-3-small"
        default="ollama/zyw0605688/gte-large-zh",
        metadata={
            "description": "Name of the embedding model to use. Must be a valid embedding model name."
        },
    )

    retriever_provider: Annotated[
        Literal["elastic-local", "elastic", "pinecone", "mongodb"],
        {"__template_metadata__": {"kind": "retriever"}},
    ] = field(
        default="elastic-local",
        metadata={
            "description": "The vector store provider to use for retrieval. Options are 'elastic', 'pinecone', or 'mongodb'."
        },
    )

    index_name: Annotated[
        str,
        {"__template_metadata__": {"kind": "index_name"}},
    ] = field(
        default="home_doing_index",
        metadata={
            "description": "Name of the index to use for retrieval. Options are 'elastic', 'pinecone', or 'mongodb'."
        },
    )

    search_kwargs: dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "description": "Additional keyword arguments to pass to the search function of the retriever."
        },
    )

    @classmethod
    def from_runnable_config(
        cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """从 RunnableConfig 对象创建一个 BaseConfiguration 实例。

        Args:
            cls (Type[T]): 类本身。
            config (Optional[RunnableConfig]): 要使用的配置对象。

        Returns:
            T: 带有指定配置的 BaseConfiguration 实例。
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


T = TypeVar("T", bound=BaseConfiguration)
