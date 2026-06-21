# backend/rag/config.py

RAG_CONFIG = {
    # Same values from the notebook
    "chunk_size": 512,
    "chunk_overlap": 64,

    "top_k": 5,
    #NVIDIA Llama embedding model
    "embedding_model": "nvidia/llama-nemotron-embed-1b-v2",
    # Phase 3 NVIDIA Llama question generator
    # You said you want to use Llama.
    "chat_model": "meta/llama-3.3-70b-instruct",

    # Question generation
    "questions_per_generation": 10,

    # Multi-LLM answer generation
    "generator_models": {
        "llama_3b": "meta/llama-3.2-3b-instruct",
        "llama_8b": "meta/llama-3.1-8b-instruct",
        "llama_70b": "meta/llama-3.3-70b-instruct",
        "mistral_small": "mistralai/mistral-small-4-119b-2603",
        "qwen_397b": "qwen/qwen3.5-397b-a17b",
    },

    # Judge model
    #"judge_model": "mistralai/mistral-large-3-675b-instruct-2512",
    "judge_model": "openai/gpt-oss-120b",
    #"judge_model":"qwen/qwen3.5-397b-a17b",

    "judge_temperature": 0.0,
    #"judge_max_tokens": 2048,
    "judge_max_tokens": 2048,
    "temperature": 0.0,
    "max_tokens": 512,
    
    # ranking weights
    # "evaluation_weights": {
    #     "faithfulness": 0.25,
    #     "answer_relevancy": 0.25,
    #     "context_precision": 0.25,
    #     "context_recall": 0.25,
    #     "context_sufficiency": 0.25,
    # },
    # Number of questions generated per selected chunk
    "questions_per_chunk": 3,
}