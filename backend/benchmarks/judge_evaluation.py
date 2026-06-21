# # backend/benchmarks/judge_evaluation.py

# import json
# import re
# from typing import Any
# import time
# from llms.nvidia_client import get_nvidia_judge_model
# from rag.config import RAG_CONFIG


# def clean_json_from_llm(text: str) -> str:
#     text = text.strip()

#     fenced_match = re.search(
#         r"```(?:json)?\s*(.*?)```",
#         text,
#         flags=re.DOTALL | re.IGNORECASE,
#     )

#     if fenced_match:
#         return fenced_match.group(1).strip()

#     start = text.find("{")
#     end = text.rfind("}")

#     if start != -1 and end != -1 and end > start:
#         return text[start : end + 1].strip()

#     return text


# def safe_json_loads(text: str) -> dict[str, Any]:
#     cleaned = clean_json_from_llm(text)
#     return json.loads(cleaned)


# def clamp_score(value: Any) -> float:
#     try:
#         score = float(value)
#     except Exception:
#         return 0.000

#     return max(0.000, min(1.000, score))


# def format_context_chunks(retrieved_contexts: list[dict]) -> str:
#     parts = []

#     for index, chunk in enumerate(retrieved_contexts, start=1):
#         text = chunk.get("text", "")
#         source = chunk.get("source", "unknown")
#         score = chunk.get("score", None)

#         parts.append(
#             f"Chunk {index}\n"
#             f"Source: {source}\n"
#             f"Retrieval score: {score}\n"
#             f"Text:\n{text}"
#         )

#     return "\n\n---\n\n".join(parts)


# JUDGE_PROMPT = """
# You are an expert evaluator for Retrieval-Augmented Generation systems.

# You must evaluate one model answer using RAGAS-style metrics.

# Use only:
# - the user question
# - the retrieved context chunks
# - the model answer

# Do not use outside knowledge.

# === Question ===
# {question}

# === Retrieved Context Chunks ===
# {context}

# === Model Answer ===
# {answer}

# Evaluate these 4 metrics from 0.000 to 1.000:

# 1. faithfulness:
# Does the answer make claims that are supported by the retrieved context?
# - 1.000 = all claims are supported
# - 0.000 = most claims are unsupported or hallucinated

# 2. answer_relevancy:
# Does the answer directly address the question?
# - 1.000 = fully answers the question
# - 0.000 = irrelevant or avoids the question

# 3. context_precision:
# Were the retrieved chunks useful for answering the question?
# Consider relevance and ranking.
# - 1.000 = top chunks are highly relevant
# - 0.000 = chunks are mostly irrelevant

# 4. context_recall:
# Does the retrieved context contain enough evidence to answer the question?
# This is a practical RAGAS-style recall proxy because no human ground-truth answer is available.
# - 1.000 = context contains sufficient evidence
# - 0.000 = context lacks important evidence

# Return ONLY valid JSON.
# No markdown.
# No backticks.

# Use exactly this structure:

# {{
#   "faithfulness": {{
#     "score": 0.000,
#     "reasoning": ""
#   }},
#   "answer_relevancy": {{
#     "score": 0.000,
#     "reasoning": ""
#   }},
#   "context_precision": {{
#     "score": 0.000,
#     "reasoning": ""
#   }},
#   "context_recall": {{
#     "score": 0.000,
#     "reasoning": ""
#   }}
# }}
# """


# def compute_final_score(
#     faithfulness: float,
#     answer_relevancy: float,
#     context_precision: float,
#     context_recall: float,
# ) -> float:
#     weights = RAG_CONFIG["evaluation_weights"]

#     return (
#         weights["faithfulness"] * faithfulness
#         + weights["answer_relevancy"] * answer_relevancy
#         + weights["context_precision"] * context_precision
#         + weights["context_recall"] * context_recall
#     )


# def evaluate_answer_with_judge(
#     question: str,
#     answer: str,
#     retrieved_contexts: list[dict],
# ) -> dict:
#     """
#     Evaluates one model answer using the NVIDIA judge LLM.

#     This is the Django version of your notebook's judge/RAGAS evaluation.
#     """

#     judge = get_nvidia_judge_model()

#     context = format_context_chunks(retrieved_contexts)

#     prompt = JUDGE_PROMPT.format(
#         question=question,
#         context=context,
#         answer=answer,
#     )

#     response = judge.invoke(prompt)
#     raw = response.content if hasattr(response, "content") else str(response)

#     try:
#         data = safe_json_loads(raw)
#     except Exception:
#         data = {
#             "faithfulness": {
#                 "score": 0.000,
#                 "reasoning": "Judge output could not be parsed.",
#             },
#             "answer_relevancy": {
#                 "score": 0.000,
#                 "reasoning": "Judge output could not be parsed.",
#             },
#             "context_precision": {
#                 "score": 0.000,
#                 "reasoning": "Judge output could not be parsed.",
#             },
#             "context_recall": {
#                 "score": 0.000,
#                 "reasoning": "Judge output could not be parsed.",
#             },
#             "raw": raw,
#         }

#     faithfulness = clamp_score(data.get("faithfulness", {}).get("score", 0.000))
#     answer_relevancy = clamp_score(data.get("answer_relevancy", {}).get("score", 0.000))
#     context_precision = clamp_score(data.get("context_precision", {}).get("score", 0.000))
#     context_recall = clamp_score(data.get("context_recall", {}).get("score", 0.000))

#     final_score = compute_final_score(
#         faithfulness=faithfulness,
#         answer_relevancy=answer_relevancy,
#         context_precision=context_precision,
#         context_recall=context_recall,
#     )

#     return {
#         "faithfulness": faithfulness,
#         "answer_relevancy": answer_relevancy,
#         "context_precision": context_precision,
#         #"context_recall": context_recall,
#         "context_sufficiency": context_recall,
#         "final_score": final_score,
#         "faithfulness_reasoning": data.get("faithfulness", {}).get("reasoning", ""),
#         "answer_relevancy_reasoning": data.get("answer_relevancy", {}).get("reasoning", ""),
#         "context_precision_reasoning": data.get("context_precision", {}).get("reasoning", ""),
#         #"context_recall_reasoning": data.get("context_recall", {}).get("reasoning", ""),
#         "context_sufficiency_reasoning": data.get("context_sufficiency", {}).get("reasoning", ""),
#         "raw_judge_output": data,
#     }
# backend/benchmarks/judge_evaluation.py

import json
import re
import time
from typing import Any

from llms.nvidia_client import get_nvidia_judge_model

from benchmarks.ragas_custom.runner import evaluate_answer_with_custom_ragas

# # ---------------------------------------------------------------------
# # JSON parsing helpers
# # ---------------------------------------------------------------------

# def clean_json_from_llm(text: str) -> str:
#     text = str(text).strip()

#     text = re.sub(r"```json", "", text, flags=re.IGNORECASE).strip()
#     text = re.sub(r"```", "", text).strip()

#     start = text.find("{")
#     end = text.rfind("}")

#     if start != -1 and end != -1 and end > start:
#         return text[start : end + 1].strip()

#     return text


# def safe_json_loads(text: str) -> dict[str, Any]:
#     cleaned = clean_json_from_llm(text)
#     return json.loads(cleaned)


# def clamp_score(value: Any) -> float:
#     try:
#         score = float(value)
#     except Exception:
#         return 0.0

#     return max(0.0, min(1.0, score))


# def parse_metric_output(raw: str) -> dict:
#     """
#     Expected output:
#     {
#       "score": 0.0,
#       "explanation": ""
#     }

#     Context precision can also return:
#     {
#       "score": 0.0,
#       "verdicts": [1, 0, 1],
#       "explanation": ""
#     }
#     """

#     text = str(raw).strip()

#     try:
#         data = safe_json_loads(text)

#         return {
#             "score": clamp_score(data.get("score", 0.0)),
#             "explanation": str(data.get("explanation", "")),
#             "verdicts": data.get("verdicts", []),
#             "raw": data,
#         }

#     except Exception:
#         score_match = re.search(r'"score"\s*:\s*([0-9]*\.?[0-9]+)', text)

#         if score_match:
#             return {
#                 "score": clamp_score(score_match.group(1)),
#                 "explanation": "Score extracted from judge output.",
#                 "verdicts": [],
#                 "raw": {"raw": text[:1000]},
#             }

#         return {
#             "score": 0.0,
#             "explanation": f"Judge output could not be parsed: {text[:300]}",
#             "verdicts": [],
#             "raw": {"raw": text[:1000]},
#         }


# # ---------------------------------------------------------------------
# # Context formatting
# # ---------------------------------------------------------------------

# def format_context_chunks(
#     retrieved_contexts: list[dict],
#     max_chunks: int = 5,
#     max_chars_per_chunk: int = 1500,
# ) -> str:
#     """
#     Format retrieved chunks in ranking order.

#     This is important for context precision because the metric checks
#     whether useful chunks appear early.
#     """

#     parts = []

#     for index, chunk in enumerate(retrieved_contexts[:max_chunks], start=1):
#         text = chunk.get("text", "")

#         if len(text) > max_chars_per_chunk:
#             text = text[:max_chars_per_chunk] + "..."

#         source = chunk.get("source", "unknown")
#         score = chunk.get("score", None)

#         parts.append(
#             f"Chunk {index}\n"
#             f"Source: {source}\n"
#             f"Retrieval score: {score}\n"
#             f"Text:\n{text}"
#         )

#     return "\n\n---\n\n".join(parts)


# # ---------------------------------------------------------------------
# # Customized metric prompts
# # Generalized from the notebook prompts
# # ---------------------------------------------------------------------

# JUDGE_PROMPT_FAITHFULNESS = """\
# You are an expert evaluator specialized in retrieval-augmented generation evaluation.

# Your task is to evaluate FAITHFULNESS AND ANSWER CORRECTNESS FROM CONTEXT.

# This metric checks two things:
# 1. Faithfulness: Are the factual claims in the generated answer supported by the retrieved contexts?
# 2. Correctness: Does the final answer or conclusion correctly follow from the retrieved contexts?

# You must judge ONLY based on the retrieved contexts.
# Do NOT use outside knowledge.
# Do NOT reward an answer just because it sounds plausible or well-written.

# === Question ===
# {question}

# === Retrieved Contexts ===
# {contexts}

# === Generated Answer ===
# {answer}

# Evaluation rules:
# 1. Identify the main conclusion required by the question.
# 2. Identify the important factual claims made in the generated answer.
# 3. Check whether each important claim is directly supported by the retrieved contexts.
# 4. For yes/no or decision-based questions, determine whether the correct conclusion from the contexts is yes, no, mixed/nuanced, or insufficient evidence.
# 5. Compare the generated answer's conclusion with the conclusion supported by the contexts.
# 6. If the generated answer gives the opposite conclusion from the retrieved contexts, the score must be 0.4 or lower.
# 7. If the answer is relevant but the final conclusion is wrong, the score must be low.
# 8. If the retrieved contexts are insufficient and the answer correctly states that evidence is insufficient, give a high score.
# 9. If the retrieved contexts are insufficient but the answer invents a strong conclusion, give a low score.
# 10. Absence of evidence in the retrieved contexts is not evidence of absence. If the answer gives a negative conclusion only because the retrieved contexts do not mention the information, treat it as an unsupported conclusion unless the answer clearly states that the contexts are insufficient.
# 11. Penalize unsupported explanations, causal claims, interpretations, implications, or recommendations that are not clearly stated or justified in the contexts.
# 12. If the answer is mostly supported but misses an important nuance, give a medium-high score.
# 13. If the answer contains both supported and unsupported claims, give a partial score.

# Scoring instructions:
# Assign a decimal score between 0 and 1 based on the degree of support and correctness.
# Use any decimal value between 0 and 1 when appropriate.

# The score should reflect:
# - how many important claims in the generated answer are supported by the retrieved contexts,
# - whether the final conclusion correctly follows from the retrieved contexts,
# - whether the answer contains unsupported or contradicted information,
# - whether the answer is overconfident when the contexts are insufficient,
# - whether important nuances are missing.

# Return ONLY valid compact JSON.
# Do NOT use markdown.
# Do NOT wrap the answer in ```json.
# Do NOT use bullet points.
# Do NOT use multiline explanations.
# The explanation must be a short single-line string.

# Return exactly this format:
# {{
#   "score": <float between 0 and 1>,
#   "explanation": "<short single-line explanation>"
# }}
# """


# JUDGE_PROMPT_ANSWER_RELEVANCY = """\
# You are an expert evaluator specialized in question answering evaluation.

# Your task is to evaluate ANSWER RELEVANCY.

# Answer relevancy means:
# Does the generated answer directly address the question being asked?

# Important:
# This metric is NOT only about topic similarity.
# The answer must respond to the specific question, including the correct entities, concepts, constraints, conditions, methods, events, outcomes, comparisons, or requested information.

# === Question ===
# {question}

# === Generated Answer ===
# {answer}

# Evaluation rules:
# 1. Check whether the answer directly answers the question.
# 2. For yes/no or decision-based questions, the answer should clearly provide a yes/no, decision, or equivalent conclusion when possible.
# 3. The answer must address the specific entities, concepts, constraints, or requested details mentioned in the question.
# 4. Penalize answers that are generic, vague, off-topic, or only repeat background information.
# 5. Penalize answers that discuss the correct broad topic but miss the specific focus, condition, method, comparison, outcome, or requested detail.
# 6. If the answer gives an unsupported strong conclusion, the score must not exceed 0.6.
# 7. If the answer gives a conclusion that is clearly inconsistent with the question, the score must not exceed 0.6.
# 8. If the answer says the context is insufficient, this can still be relevant if it directly explains why the question cannot be answered.
# 9. Do NOT reward long answers automatically. A concise direct answer can receive a high score.

# Scoring instructions:
# Assign a decimal score between 0 and 1 based on how directly and specifically the answer addresses the question.
# Use any decimal value between 0 and 1 when appropriate.

# The score should reflect:
# - whether the answer directly responds to the exact question,
# - whether the answer addresses the correct entities, concepts, constraints, or requested details,
# - whether the answer covers the required condition, method, comparison, outcome, or requested information,
# - whether the answer is specific rather than generic,
# - whether the answer avoids unsupported strong conclusions.

# Return ONLY valid compact JSON.
# Do NOT use markdown.
# Do NOT wrap the answer in ```json.
# Do NOT use bullet points.
# Do NOT use multiline explanations.
# The explanation must be a short single-line string.

# Return exactly this format:
# {{
#   "score": <float between 0 and 1>,
#   "explanation": "<short single-line explanation>"
# }}
# """



# JUDGE_PROMPT_CONTEXT_PRECISION = """\
# You are an expert evaluator specialized in RAG retrieval quality.

# Your task is to evaluate CONTEXT PRECISION.

# Context precision means:
# Were the retrieved contexts that are useful for answering the question ranked early?

# You must evaluate each retrieved context in order.

# === Question ===
# {question}

# === Retrieved Contexts in Ranking Order ===
# {contexts}

# Evaluation rules:

# For each context, decide whether it is useful for answering the exact question.

# A context is useful if it contains evidence directly related to:
# - the main entities, concepts, events, objects, or variables in the question,
# - the condition, method, process, comparison, or constraint in the question,
# - the outcome, result, explanation, or conclusion requested by the question,
# - or a direct fact needed to answer the question.

# A context is NOT useful if:
# - it is only general background,
# - it mentions the broad topic but not the specific question,
# - it is about a different entity, event, object, method, domain, or outcome,
# - it is only methodological or descriptive and does not help answer the question,
# - it is irrelevant text from another source or topic.

# Use binary verdicts:
# - 1 = useful for answering the question
# - 0 = not useful for answering the question

# Important:
# Useful contexts ranked earlier should improve the score.
# Useful contexts ranked late should reduce the score.
# Irrelevant contexts before useful contexts should reduce the score.

# Steps:
# 1. Assign verdict 1 or 0 to each context.
# 2. Compute precision at each rank where verdict = 1.
# 3. Average these precision values.
# 4. If there are no useful contexts, score = 0.

# Scoring instructions:
# Assign a decimal score between 0 and 1 based on how well the useful contexts are ranked.
# Use any decimal value between 0 and 1 when appropriate.

# The score should reflect:
# - the number of useful contexts,
# - whether useful contexts appear early in the ranking,
# - whether irrelevant contexts appear before useful contexts,
# - whether the retrieved contexts are directly useful for answering the exact question.

# Return ONLY valid compact JSON.
# Do NOT use markdown.
# Do NOT wrap the answer in ```json.
# Do NOT use bullet points.
# Do NOT use multiline explanations.
# The explanation must be a short single-line string.

# Return exactly this format:
# {{
#   "score": <float between 0 and 1>,
#   "verdicts": [0 or 1 for each context],
#   "explanation": "<short single-line explanation>"
# }}
# """


# JUDGE_PROMPT_CONTEXT_SUFFICIENCY = """\
# You are an expert evaluator specialized in retrieval-augmented generation evaluation.

# Your task is to evaluate CONTEXT SUFFICIENCY.

# Context sufficiency means:
# Do the retrieved contexts contain enough information to answer the question correctly?

# You must judge ONLY the retrieved contexts.
# Do NOT use outside knowledge.

# === Question ===
# {question}

# === Retrieved Contexts ===
# {contexts}

# Evaluation rules:
# 1. Determine the key elements required to answer the question.
#    These may include:
#    - main entities, concepts, events, objects, or variables,
#    - condition, method, process, comparison, or constraint,
#    - population, system, product, case, or scenario if relevant,
#    - outcome, result, explanation, or conclusion,
#    - direction of effect, relationship, or difference,
#    - yes/no, decision, or final conclusion when required.

# 2. Check whether the retrieved contexts contain evidence for these key elements.

# 3. For yes/no or decision-based questions, the context is sufficient only if it supports the final conclusion.

# 4. If the question asks about a specific mechanism, cause, method, comparison, or relationship, the contexts must mention or clearly support that specific element.
#    If that key element is missing, the score should usually be 0.5 or lower.

# 5. If the context only provides background but not the information needed to answer, the score should be low.

# 6. If the context contains some relevant entities or concepts but does not allow a correct final answer, the score should be moderate or low.

# 7. If the context contains irrelevant chunks but also enough clear evidence to answer the question, the score can still be high.

# 8. Do NOT penalize because the generated answer is bad. This metric evaluates only whether the retrieved contexts are sufficient.

# Scoring instructions:
# Assign a decimal score between 0 and 1 based on whether the retrieved contexts contain enough evidence to answer the question correctly.
# Use any decimal value between 0 and 1 when appropriate.

# The score should reflect:
# - whether the retrieved contexts contain the key entities, concepts, constraints, or details required by the question,
# - whether the contexts contain the necessary outcome, method, comparison, relationship, or direction of effect,
# - whether the contexts support the final conclusion when the question requires one,
# - whether important evidence is missing,
# - whether irrelevant chunks reduce the overall sufficiency of the retrieved evidence.

# Return ONLY valid compact JSON.
# Do NOT use markdown.
# Do NOT wrap the answer in ```json.
# Do NOT use bullet points.
# Do NOT use multiline explanations.
# The explanation must be a short single-line string.

# Return exactly this format:
# {{
#   "score": <float between 0 and 1>,
#   "explanation": "<short single-line explanation>"
# }}
# """


# # ---------------------------------------------------------------------
# # Judge execution
# # ---------------------------------------------------------------------

# def call_judge(prompt: str, retries: int = 2, wait_seconds: int = 10) -> str:
#     judge = get_nvidia_judge_model()
#     last_error = None

#     for attempt in range(1, retries + 1):
#         try:
#             response = judge.invoke(prompt)
#             return response.content if hasattr(response, "content") else str(response)

#         except Exception as e:
#             last_error = str(e)

#             if attempt < retries:
#                 time.sleep(wait_seconds)

#     return json.dumps(
#         {
#             "score": 0.0,
#             "explanation": f"Judge call failed after {retries} attempts: {last_error}",
#         }
#     )


# def run_metric_prompt(prompt: str) -> dict:
#     raw = call_judge(prompt)
#     parsed = parse_metric_output(raw)
#     parsed["raw_text"] = raw
#     return parsed


# # ---------------------------------------------------------------------
# # Final score
# # ---------------------------------------------------------------------

# def compute_final_score(
#     faithfulness: float,
#     answer_relevancy: float,
#     context_precision: float,
#     context_sufficiency: float,
# ) -> float:
#     """
#     Same principle as the notebook:
#     final score = mean of the custom metric scores.

#     No arbitrary manual weights.
#     """

#     scores = [
#         faithfulness,
#         answer_relevancy,
#         context_precision,
#         context_sufficiency,
#     ]

#     return sum(scores) / len(scores)


# ---------------------------------------------------------------------
# Main function used by Celery
# ---------------------------------------------------------------------

# def evaluate_answer_with_judge(
#     question: str,
#     answer: str,
#     retrieved_contexts: list[dict],
# ) -> dict:
#     """
#     Fullstack implementation of the notebook's customized metrics.

#     It evaluates:
#     - CustomFaithfulness
#     - CustomAnswerRelevancy
#     - CustomContextPrecision
#     - CustomContextSufficiency

#     It does not use default RAGAS metrics.
#     """

#     contexts = format_context_chunks(
#         retrieved_contexts=retrieved_contexts,
#         max_chunks=5,
#         max_chars_per_chunk=1500,
#     )

#     if len(answer) > 3000:
#         answer = answer[:3000] + "..."

#     faithfulness_result = run_metric_prompt(
#         JUDGE_PROMPT_FAITHFULNESS.format(
#             question=question,
#             contexts=contexts,
#             answer=answer,
#         )
#     )

#     answer_relevancy_result = run_metric_prompt(
#         JUDGE_PROMPT_ANSWER_RELEVANCY.format(
#             question=question,
#             answer=answer,
#         )
#     )

#     context_precision_result = run_metric_prompt(
#         JUDGE_PROMPT_CONTEXT_PRECISION.format(
#             question=question,
#             contexts=contexts,
#         )
#     )

#     context_sufficiency_result = run_metric_prompt(
#         JUDGE_PROMPT_CONTEXT_SUFFICIENCY.format(
#             question=question,
#             contexts=contexts,
#         )
#     )

#     faithfulness = faithfulness_result["score"]
#     answer_relevancy = answer_relevancy_result["score"]
#     context_precision = context_precision_result["score"]
#     context_sufficiency = context_sufficiency_result["score"]

#     final_score = compute_final_score(
#         faithfulness=faithfulness,
#         answer_relevancy=answer_relevancy,
#         context_precision=context_precision,
#         context_sufficiency=context_sufficiency,
#     )

#     return {
#         "faithfulness": faithfulness,
#         "answer_relevancy": answer_relevancy,
#         "context_precision": context_precision,
#         "context_sufficiency": context_sufficiency,

        
#         #"context_recall": context_sufficiency,

#         "final_score": final_score,

#         "faithfulness_reasoning": faithfulness_result["explanation"],
#         "answer_relevancy_reasoning": answer_relevancy_result["explanation"],
#         "context_precision_reasoning": context_precision_result["explanation"],
#         "context_sufficiency_reasoning": context_sufficiency_result["explanation"],

#         #"context_recall_reasoning": context_sufficiency_result["explanation"],

#         "raw_judge_output": {
#             "faithfulness": faithfulness_result["raw"],
#             "answer_relevancy": answer_relevancy_result["raw"],
#             "context_precision": context_precision_result["raw"],
#             "context_sufficiency": context_sufficiency_result["raw"],
#             "context_precision_verdicts": context_precision_result.get("verdicts", []),
#         },
#     }


def evaluate_answer_with_judge(
    question: str,
    answer: str,
    retrieved_contexts: list[dict],
) -> dict:
    
    """
    Evaluate one model answer using custom RAGAS SingleTurnMetric classes.

    This DOES use RAGAS:
    - SingleTurnSample
    - EvaluationDataset
    - custom SingleTurnMetric subclasses
    - ragas.evaluate(...)

    This does NOT use RAGAS default metrics:
    - no default AnswerRelevancy
    - no default ContextPrecision
    - no default ContextRecall

    The metric logic is the custom prompt-based logic from notebook Phase 3.
    """
    return evaluate_answer_with_custom_ragas(
        question=question,
        answer=answer,
        retrieved_contexts=retrieved_contexts,
    )