\
# backend/benchmarks/ragas_custom/prompts.py

"""
Custom judge prompts copied/generalized from notebook Phase 3.

"""

JUDGE_PROMPT_FAITHFULNESS = """\
You are an expert evaluator specialized in retrieval-augmented generation evaluation.

Your task is to evaluate FAITHFULNESS AND ANSWER CORRECTNESS FROM CONTEXT.

This metric checks two things:
1. Faithfulness: Are the factual claims in the generated answer supported by the retrieved contexts?
2. Correctness: Does the final answer or conclusion correctly follow from the retrieved contexts?

You must judge ONLY based on the retrieved contexts.
Do NOT use outside knowledge.
Do NOT reward an answer just because it sounds plausible or well-written.

=== Question ===
{question}

=== Retrieved Contexts ===
{contexts}

=== Generated Answer ===
{answer}

Evaluation rules:
1. Identify the main conclusion required by the question.
2. Identify the important factual claims made in the generated answer.
3. Check whether each important claim is directly supported by the retrieved contexts.
4. For yes/no or decision-based questions, determine whether the correct conclusion from the contexts is yes, no, mixed/nuanced, or insufficient evidence.
5. Compare the generated answer's conclusion with the conclusion supported by the contexts.
6. If the generated answer gives the opposite conclusion from the retrieved contexts, the score must be 0.4 or lower.
7. If the answer is relevant but the final conclusion is wrong, the score must be low.
8. If the retrieved contexts are insufficient and the answer correctly states that evidence is insufficient, give a high score.
9. If the retrieved contexts are insufficient but the answer invents a strong conclusion, give a low score.
10. Absence of evidence in the retrieved contexts is not evidence of absence. If the answer gives a negative conclusion only because the retrieved contexts do not mention the information, treat it as an unsupported conclusion unless the answer clearly states that the contexts are insufficient.
11. Penalize unsupported explanations, causal claims, interpretations, implications, or recommendations that are not clearly stated or justified in the contexts.
12. If the answer is mostly supported but misses an important nuance, give a medium-high score.
13. If the answer contains both supported and unsupported claims, give a partial score.

Scoring instructions:
Assign a decimal score between 0 and 1 based on the degree of support and correctness.
Use any decimal value between 0 and 1 when appropriate.

The score should reflect:
- how many important claims in the generated answer are supported by the retrieved contexts,
- whether the final conclusion correctly follows from the retrieved contexts,
- whether the answer contains unsupported or contradicted information,
- whether the answer is overconfident when the contexts are insufficient,
- whether important nuances are missing.

Return ONLY valid compact JSON.
Do NOT use markdown.
Do NOT wrap the answer in ```json.
Do NOT use bullet points.
Do NOT use multiline explanations.
The explanation must be a short single-line string.

Return exactly this format:
{{
  "score": <float between 0 and 1>,
  "explanation": "<short single-line explanation>"
}}
"""


JUDGE_PROMPT_ANSWER_RELEVANCY = """\
You are an expert evaluator specialized in question answering evaluation.

Your task is to evaluate ANSWER RELEVANCY.

Answer relevancy means:
Does the generated answer directly address the question being asked?

Important:
This metric is NOT only about topic similarity.
The answer must respond to the specific question, including the correct entities, concepts, constraints, conditions, methods, events, outcomes, comparisons, or requested information.

=== Question ===
{question}

=== Generated Answer ===
{answer}

Evaluation rules:
1. Check whether the answer directly answers the question.
2. For yes/no or decision-based questions, the answer should clearly provide a yes/no, decision, or equivalent conclusion when possible.
3. The answer must address the specific entities, concepts, constraints, or requested details mentioned in the question.
4. Penalize answers that are generic, vague, off-topic, or only repeat background information.
5. Penalize answers that discuss the correct broad topic but miss the specific focus, condition, method, comparison, outcome, or requested detail.
6. If the answer gives an unsupported strong conclusion, the score must not exceed 0.6.
7. If the answer gives a conclusion that is clearly inconsistent with the question, the score must not exceed 0.6.
8. If the answer says the context is insufficient, this can still be relevant if it directly explains why the question cannot be answered.
9. Do NOT reward long answers automatically. A concise direct answer can receive a high score.

Scoring instructions:
Assign a decimal score between 0 and 1 based on how directly and specifically the answer addresses the question.
Use any decimal value between 0 and 1 when appropriate.

The score should reflect:
- whether the answer directly responds to the exact question,
- whether the answer addresses the correct entities, concepts, constraints, or requested details,
- whether the answer covers the required condition, method, comparison, outcome, or requested information,
- whether the answer is specific rather than generic,
- whether the answer avoids unsupported strong conclusions.

Return ONLY valid compact JSON.
Do NOT use markdown.
Do NOT wrap the answer in ```json.
Do NOT use bullet points.
Do NOT use multiline explanations.
The explanation must be a short single-line string.

Return exactly this format:
{{
  "score": <float between 0 and 1>,
  "explanation": "<short single-line explanation>"
}}
"""


JUDGE_PROMPT_CONTEXT_PRECISION = """\
You are an expert evaluator specialized in RAG retrieval quality.

Your task is to evaluate CONTEXT PRECISION.

Context precision means:
Were the retrieved contexts that are useful for answering the question ranked early?

You must evaluate each retrieved context in order.

=== Question ===
{question}

=== Retrieved Contexts in Ranking Order ===
{contexts}

Evaluation rules:

For each context, decide whether it is useful for answering the exact question.

A context is useful if it contains evidence directly related to:
- the main entities, concepts, events, objects, or variables in the question,
- the condition, method, process, comparison, or constraint in the question,
- the outcome, result, explanation, or conclusion requested by the question,
- or a direct fact needed to answer the question.

A context is NOT useful if:
- it is only general background,
- it mentions the broad topic but not the specific question,
- it is about a different entity, event, object, method, domain, or outcome,
- it is only methodological or descriptive and does not help answer the question,
- it is irrelevant text from another source or topic.

Use binary verdicts:
- 1 = useful for answering the question
- 0 = not useful for answering the question

Important:
Useful contexts ranked earlier should improve the score.
Useful contexts ranked late should reduce the score.
Irrelevant contexts before useful contexts should reduce the score.

Steps:
1. Assign verdict 1 or 0 to each context.
2. Compute precision at each rank where verdict = 1.
3. Average these precision values.
4. If there are no useful contexts, score = 0.

Scoring instructions:
Assign a decimal score between 0 and 1 based on how well the useful contexts are ranked.
Use any decimal value between 0 and 1 when appropriate.

The score should reflect:
- the number of useful contexts,
- whether useful contexts appear early in the ranking,
- whether irrelevant contexts appear before useful contexts,
- whether the retrieved contexts are directly useful for answering the exact question.

Return ONLY valid compact JSON.
Do NOT use markdown.
Do NOT wrap the answer in ```json.
Do NOT use bullet points.
Do NOT use multiline explanations.
The explanation must be a short single-line string.

Return exactly this format:
{{
  "score": <float between 0 and 1>,
  "verdicts": [0 or 1 for each context],
  "explanation": "<short single-line explanation>"
}}
"""


JUDGE_PROMPT_CONTEXT_SUFFICIENCY = """\
You are an expert evaluator specialized in retrieval-augmented generation evaluation.

Your task is to evaluate CONTEXT SUFFICIENCY.

Context sufficiency means:
Do the retrieved contexts contain enough information to answer the question correctly?

You must judge ONLY the retrieved contexts.
Do NOT use outside knowledge.

=== Question ===
{question}

=== Retrieved Contexts ===
{contexts}

Evaluation rules:
1. Determine the key elements required to answer the question.
   These may include:
   - main entities, concepts, events, objects, or variables,
   - condition, method, process, comparison, or constraint,
   - population, system, product, case, or scenario if relevant,
   - outcome, result, explanation, or conclusion,
   - direction of effect, relationship, or difference,
   - yes/no, decision, or final conclusion when required.

2. Check whether the retrieved contexts contain evidence for these key elements.

3. For yes/no or decision-based questions, the context is sufficient only if it supports the final conclusion.

4. If the question asks about a specific mechanism, cause, method, comparison, or relationship, the contexts must mention or clearly support that specific element.
   If that key element is missing, the score should usually be 0.5 or lower.

5. If the context only provides background but not the information needed to answer, the score should be low.

6. If the context contains some relevant entities or concepts but does not allow a correct final answer, the score should be moderate or low.

7. If the context contains irrelevant chunks but also enough clear evidence to answer the question, the score can still be high.

8. Do NOT penalize because the generated answer is bad. This metric evaluates only whether the retrieved contexts are sufficient.

Scoring instructions:
Assign a decimal score between 0 and 1 based on whether the retrieved contexts contain enough evidence to answer the question correctly.
Use any decimal value between 0 and 1 when appropriate.

The score should reflect:
- whether the retrieved contexts contain the key entities, concepts, constraints, or details required by the question,
- whether the contexts contain the necessary outcome, method, comparison, relationship, or direction of effect,
- whether the contexts support the final conclusion when the question requires one,
- whether important evidence is missing,
- whether irrelevant chunks reduce the overall sufficiency of the retrieved evidence.

Return ONLY valid compact JSON.
Do NOT use markdown.
Do NOT wrap the answer in ```json.
Do NOT use bullet points.
Do NOT use multiline explanations.
The explanation must be a short single-line string.

Return exactly this format:
{{
  "score": <float between 0 and 1>,
  "explanation": "<short single-line explanation>"
}}
"""
