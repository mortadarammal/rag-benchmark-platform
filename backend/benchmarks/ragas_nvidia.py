import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper


NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]

JUDGE_MODEL = "mistralai/mistral-large-2-instruct"
EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"


def get_ragas_judge_llm():
    """
    Same idea as the notebook judge LLM.
    This prevents RAGAS from trying to use its own default LLM.
    """
    raw_llm = ChatNVIDIA(
        model=JUDGE_MODEL,
        api_key=NVIDIA_API_KEY,
        temperature=0,
        max_tokens=1024,
    )

    return LangchainLLMWrapper(raw_llm)


def get_ragas_embeddings():
    """
    Same NVIDIA embedding setup as the notebook.
    This prevents RAGAS from trying to use default embeddings.
    """
    raw_embeddings = NVIDIAEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=NVIDIA_API_KEY,
    )

    return LangchainEmbeddingsWrapper(raw_embeddings)


def get_raw_judge_llm():

    return ChatNVIDIA(
        model=JUDGE_MODEL,
        api_key=NVIDIA_API_KEY,
        temperature=0,
        max_tokens=1024,
    )