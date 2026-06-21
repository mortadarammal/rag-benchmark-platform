"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost } from "../../../lib/api";

type Question = {
  id: number;
  question: string;
  selected: boolean;
  status: string;
};

type GeneratorModel = {
  model_key: string;
  model_name: string;
};

type ModelAnswer = {
  id: number;
  benchmark_run: number;
  model_key: string;
  model_name: string;
  question: string;
  answer: string;
  retrieved_contexts: unknown[];
  full_context: string;
  latency_ms: number | null;
  status: string;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

type BenchmarkRun = {
  id: number;
  project: number;
  question: number;
  question_text: string;
  status: string;
  error_message: string | null;
  answers: ModelAnswer[];
  created_at: string;
  completed_at: string | null;
};

export default function AnswersPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(
    null,
  );

  const [models, setModels] = useState<GeneratorModel[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);

  const [runs, setRuns] = useState<BenchmarkRun[]>([]);

  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function fetchQuestions() {
    const data = await apiGet<Question[]>(
      `/benchmarks/projects/${projectId}/questions/`,
    );

    setQuestions(data);

    const selected = data.find((q) => q.selected);
    setSelectedQuestion(selected ?? null);
  }

  async function fetchModels() {
    const data = await apiGet<{ models: GeneratorModel[] }>(
      "/benchmarks/generator-models/",
    );

    setModels(data.models);

    if (selectedModels.length === 0) {
      setSelectedModels(data.models.map((model) => model.model_key));
    }
  }

  async function fetchRuns() {
    const data = await apiGet<BenchmarkRun[]>(
      `/benchmarks/projects/${projectId}/runs/`,
    );

    setRuns(data);
  }

  async function loadPageData() {
    try {
      setLoading(true);
      setError("");

      await Promise.all([fetchQuestions(), fetchModels(), fetchRuns()]);
    } catch (err) {
      console.error(err);
      setError("Could not load answer page data.");
    } finally {
      setLoading(false);
    }
  }

  function toggleModel(modelKey: string) {
    setSelectedModels((current) =>
      current.includes(modelKey)
        ? current.filter((key) => key !== modelKey)
        : [...current, modelKey],
    );
  }

  function selectAllModels() {
    setSelectedModels(models.map((model) => model.model_key));
  }

  function clearModels() {
    setSelectedModels([]);
  }

  async function generateAnswers() {
    if (!selectedQuestion) {
      setError("No question selected. Go to the questions page first.");
      return;
    }

    if (selectedModels.length === 0) {
      setError("Select at least one model.");
      return;
    }

    try {
      setStarting(true);
      setMessage("");
      setError("");

      await apiPost("/benchmarks/answers/generate/", {
        question_id: selectedQuestion.id,
        selected_model_keys: selectedModels,
      });

      setMessage(
        "Answer generation started. Wait a few seconds, then refresh.",
      );

      setTimeout(fetchRuns, 7000);
    } catch (err) {
      console.error(err);
      setError("Could not start answer generation.");
    } finally {
      setStarting(false);
    }
  }

  useEffect(() => {
    if (projectId) {
      loadPageData();
    }
  }, [projectId]);

  return (
    <main className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}`}
          className="text-sm underline text-white"
        >
          ← Back to project
        </Link>

        <h1 className="text-3xl font-bold mt-4">Multi-LLM Answers</h1>
      </div>

      {message && (
        <div className="border rounded bg-green-50 border-green-600 text-green-800 p-4 mb-6">
          {message}
        </div>
      )}

      {error && (
        <div className="border rounded bg-red-50 border-red-600 text-red-800 p-4 mb-6">
          {error}
        </div>
      )}

      {loading && (
        <div className="border rounded bg-white p-6 mb-6">
          Loading answer page...
        </div>
      )}

      {!loading && !selectedQuestion && (
        <div className="border rounded bg-yellow-50 border-yellow-500 p-6 mb-8">
          <h2 className="font-semibold mb-2 text-black">
            No selected question
          </h2>

          <p className="text-black mb-4">
            You need to select one generated question before generating model
            answers.
          </p>

          <Link
            href={`/projects/${projectId}/questions`}
            className="px-4 py-2 rounded bg-black text-white inline-block"
          >
            Go to questions
          </Link>
        </div>
      )}

      {selectedQuestion && (
        <div className="border rounded bg-white p-6 mb-8">
          <h2 className="font-semibold text-xl mb-2 text-black">
            Selected question
          </h2>

          <p className="text-black">{selectedQuestion.question}</p>

          <div className="text-sm text-black mt-2">
            Question ID: {selectedQuestion.id}
          </div>
        </div>
      )}

      <div className="border rounded bg-white p-6 mb-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-4">
          <div>
            <h2 className="font-semibold text-xl text-black">Choose models</h2>
            <p className="text-black text-sm">
              Select which LLMs should answer the question.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={selectAllModels}
              className="px-3 py-2 rounded border text-sm text-black"
            >
              Select all
            </button>

            <button
              onClick={clearModels}
              className="px-3 py-2 rounded border text-sm text-red-600"
            >
              Clear
            </button>
          </div>
        </div>

        {models.length === 0 ? (
          <p className="text-black">No generator models found.</p>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {models.map((model) => (
              <label
                key={model.model_key}
                className={`border rounded p-4 cursor-pointer ${
                  selectedModels.includes(model.model_key)
                    ? "border-blue-600 bg-blue-50"
                    : "bg-white"
                }`}
              >
                <div className="flex gap-3">
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.model_key)}
                    onChange={() => toggleModel(model.model_key)}
                  />

                  <div>
                    <div className="font-semibold text-black">
                      {model.model_key}
                    </div>
                    <div className="text-sm text-gray-400">
                      {model.model_name}
                    </div>
                  </div>
                </div>
              </label>
            ))}
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <button
            onClick={generateAnswers}
            disabled={
              !selectedQuestion || selectedModels.length === 0 || starting
            }
            className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          >
            {starting ? "Starting..." : "Generate Answers"}
          </button>

          <button onClick={fetchRuns} className="px-4 py-2 rounded border">
            Refresh runs
          </button>
        </div>
      </div>

      <div className="border rounded bg-white">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="font-semibold text text-black">Benchmark runs</h2>

          <span className="text-sm text-black">{runs.length} run(s)</span>
        </div>

        {runs.length === 0 ? (
          <div className="p-6 text-black">No answer generation runs yet.</div>
        ) : (
          <div className="divide-y">
            {runs.map((run) => (
              <div key={run.id} className="p-6">
                <div className="flex flex-col md:flex-row md:justify-between gap-4 mb-4">
                  <div>
                    <p className="mt-2 text-black">{run.question_text}</p>
                  </div>

                  <div className="flex gap-2 h-fit">
                    <Link
                      href={`/projects/${projectId}/ranking`}
                      className="px-4 py-2 rounded bg-green-700 text-white text-sm"
                    >
                      Judge / Rank
                    </Link>
                  </div>
                </div>

                {run.error_message && (
                  <p className="text-red-700 mb-4">{run.error_message}</p>
                )}

                {run.answers.length === 0 ? (
                  <div className="text-gray-600">
                    No answers saved for this run yet. Refresh after Celery
                    finishes.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {run.answers.map((answer) => (
                      <div
                        key={answer.id}
                        className="border rounded p-4 bg-gray-50"
                      >
                        <div className="flex flex-col md:flex-row md:justify-between gap-2 mb-3">
                          <div>
                            <h4 className="font-semibold text-black">
                              {answer.model_key}
                            </h4>

                            <p className="text-sm text-gray-600">
                              {answer.model_name}
                            </p>
                          </div>

                          <div className="text-sm text-black">
                            {answer.status}
                            {answer.latency_ms
                              ? ` · ${(answer.latency_ms / 1000).toFixed(2)}s`
                              : ""}
                          </div>
                        </div>

                        {answer.error_message ? (
                          <p className="text-red-700">{answer.error_message}</p>
                        ) : answer.answer ? (
                          <p className="whitespace-pre-wrap text-blue-500">{answer.answer}</p>
                        ) : (
                          <p className="text-black">Waiting for answer...</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
