"""Manage the configuration of various retrievers.

This module provides functionality to create and manage retrievers for different
vector store backends, specifically Elasticsearch, Pinecone, and MongoDB.
"""

import os
from contextlib import contextmanager
from typing import Generator

from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableConfig
from langchain_core.vectorstores import VectorStoreRetriever

from shared.configuration import BaseConfiguration

## Encoder constructors


def make_text_encoder(model: str) -> Embeddings:
    """创建文本编码器。

    该函数根据配置的模型名称，连接到相应的文本编码器。
    支持的模型包括 OpenAI、Ollama、Cohere 等。

    Args:
        model (str): 模型名称，格式为 "provider/model_name"，例如 "openai/text-embedding-3-small"。

    Returns:
        Embeddings: 配置的文本编码器实例。

    Raises:
        ValueError: 如果模型名称的格式错误或不支持的模型提供者。
    """
    provider, model = model.split("/", maxsplit=1)
    match provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings
        
            return OpenAIEmbeddings(model=model)
        case "ollama":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(model=model)
        case "cohere":
            from langchain_cohere import CohereEmbeddings

            return CohereEmbeddings(model=model)  # type: ignore
        case _:
            raise ValueError(f"Unsupported embedding provider: {provider}")


## RAG Retriever constructors


@contextmanager
def make_elastic_retriever(
    configuration: BaseConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """创建 Elasticsearch 检索器。

    该函数根据配置的 Elasticsearch 索引和检索器提供者，创建一个 Elasticsearch 检索器。
    支持本地 Elasticsearch 实例和 Elastic Cloud 实例。

    Args:
        configuration (BaseConfiguration): 配置对象，包含索引名称、检索器提供者和搜索参数。
        embedding_model (Embeddings): 文本编码器，用于将查询转换为向量。

    Yields:
        VectorStoreRetriever: 配置的 Elasticsearch 检索器实例。

    Raises:
        ValueError: 如果配置的检索器提供者不是 "elastic-local" 或 "elastic"。
    """
    from langchain_elasticsearch import ElasticsearchStore

    connection_options = {}
    if configuration.retriever_provider == "elastic-local":
        connection_options = {
            "es_user": os.environ["ELASTICSEARCH_USER"],
            "es_password": os.environ["ELASTICSEARCH_PASSWORD"],
        }

    else:
        connection_options = {"es_api_key": os.environ["ELASTICSEARCH_API_KEY"]}

    
    # Properly handle SSL certificate verification
    # For production, verify certificates. For local development, can be disabled.
    verify_certs = os.environ.get("ELASTICSEARCH_VERIFY_CERTS", "true").lower() == "true"
    es_params = {
        "verify_certs": verify_certs,
        "ssl_show_warn": not verify_certs,
    }
    
    # If using custom CA certificate, add the path
    if verify_certs and "ELASTICSEARCH_CA_CERTS" in os.environ:
        es_params["ca_certs"] = os.environ["ELASTICSEARCH_CA_CERTS"]

    vstore = ElasticsearchStore(
        **connection_options,  # type: ignore
        es_url=os.environ["ELASTICSEARCH_URL"],
        index_name=configuration.index_name,
        embedding=embedding_model,
        es_params=es_params, # 新增
    )

    yield vstore.as_retriever(search_kwargs=configuration.search_kwargs)


@contextmanager
def make_pinecone_retriever(
    configuration: BaseConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """创建 Pinecone 检索器。

    该函数根据配置的 Pinecone 索引和检索器提供者，创建一个 Pinecone 检索器。

    Args:
        configuration (BaseConfiguration): 配置对象，包含索引名称、检索器提供者和搜索参数。
        embedding_model (Embeddings): 文本编码器，用于将查询转换为向量。

    Yields:
        VectorStoreRetriever: 配置的 Pinecone 检索器实例。

    Raises:
        ValueError: 如果配置的检索器提供者不是 "pinecone"。
    """
    from langchain_pinecone import PineconeVectorStore

    vstore = PineconeVectorStore.from_existing_index(
        os.environ["PINECONE_INDEX_NAME"], embedding=embedding_model
    )
    yield vstore.as_retriever(search_kwargs=configuration.search_kwargs)


@contextmanager
def make_mongodb_retriever(
    configuration: BaseConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """创建 MongoDB Atlas 检索器。

    该函数根据配置的 MongoDB Atlas 索引和检索器提供者，创建一个 MongoDB Atlas 检索器。

    Args:
        configuration (BaseConfiguration): 配置对象，包含索引名称、检索器提供者和搜索参数。
        embedding_model (Embeddings): 文本编码器，用于将查询转换为向量。

    Yields:
        VectorStoreRetriever: 配置的 MongoDB Atlas 检索器实例。

    Raises:
        ValueError: 如果配置的检索器提供者不是 "mongodb"。
    """
    from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch

    vstore = MongoDBAtlasVectorSearch.from_connection_string(
        os.environ["MONGODB_URI"],
        namespace="langgraph_retrieval_agent.default",
        embedding=embedding_model,
    )
    yield vstore.as_retriever(search_kwargs=configuration.search_kwargs)


@contextmanager
def make_retriever(
    config: RunnableConfig,
) -> Generator[VectorStoreRetriever, None, None]:
    """创建检索器。

    该函数根据当前配置，创建一个检索器。支持 Elasticsearch、Pinecone 和 MongoDB Atlas 检索器。

    Args:
        config (RunnableConfig): 运行配置对象，包含当前的索引名称、检索器提供者和搜索参数。

    Yields:
        VectorStoreRetriever: 配置的检索器实例。

    Raises:
        ValueError: 如果配置的检索器提供者不是 "elastic", "elastic-local", "pinecone" 或 "mongodb"。
    """
    configuration = BaseConfiguration.from_runnable_config(config)
    embedding_model = make_text_encoder(configuration.embedding_model)
    match configuration.retriever_provider:
        case "elastic" | "elastic-local":
            with make_elastic_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case "pinecone":
            with make_pinecone_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case "mongodb":
            with make_mongodb_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case _:
            raise ValueError(
                "Unrecognized retriever_provider in configuration. "
                f"Expected one of: {', '.join(BaseConfiguration.__annotations__['retriever_provider'].__args__)}\n"
                f"Got: {configuration.retriever_provider}"
            )
