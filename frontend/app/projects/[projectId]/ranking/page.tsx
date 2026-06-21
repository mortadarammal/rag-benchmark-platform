"use client";

import { useEffect, useMemo, useState } from "react";
import { exportUrl } from "../../../lib/api";
import { useParams } from "next/navigation";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
} from "recharts";
import Link from "next/link";

type BenchmarkRun = {
  id: number;
  question_text: string;
  status: string;
  created_at: string;
};

type RankingRow = {
  rank: number;
  model_key: string;
  model_name: string;
  answer_id: number;
  final_score: number;
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  // context_recall: number;
  context_sufficiency: number;
  latency_ms: number | null;
  answer: string;
};

type RankingResponse = {
  benchmark_run_id: number;
  question: string;
  ranking: RankingRow[];
};

type ChartType = "radar" | "metrics_bar";

const API_BASE_URL = "http://127.0.0.1:8000/api";

export default function RankingPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [ranking, setRanking] = useState<RankingResponse | null>(null);

  const [evaluating, setEvaluating] = useState(false);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [loadingRanking, setLoadingRanking] = useState(false);
  const [error, setError] = useState("");

  const [selectedChartModelKey, setSelectedChartModelKey] = useState("");
  const [chartType, setChartType] = useState<ChartType>("radar");

  const [headToHeadA, setHeadToHeadA] = useState("");
  const [headToHeadB, setHeadToHeadB] = useState("");

  async function fetchRuns() {
    try {
      setLoadingRuns(true);
      setError("");

      const res = await fetch(
        `${API_BASE_URL}/benchmarks/projects/${projectId}/runs/`,
      );

      if (!res.ok) {
        throw new Error("Could not fetch benchmark runs.");
      }

      const data: BenchmarkRun[] = await res.json();
      setRuns(data);

      if (data.length > 0 && !selectedRunId) {
        setSelectedRunId(data[0].id);
      }
    } catch (err) {
      console.error(err);
      setError("Could not load benchmark runs.");
    } finally {
      setLoadingRuns(false);
    }
  }

  async function evaluateRun() {
    if (!selectedRunId) return;

    try {
      setEvaluating(true);
      setError("");

      const res = await fetch(
        `${API_BASE_URL}/benchmarks/runs/${selectedRunId}/evaluate/`,
        {
          method: "POST",
        },
      );

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }

      setTimeout(fetchRanking, 8000);
    } catch (err) {
      console.error(err);
      setError("Could not start judge evaluation.");
    } finally {
      setEvaluating(false);
    }
  }

  async function fetchRanking() {
    if (!selectedRunId) return;

    try {
      setLoadingRanking(true);
      setError("");

      const res = await fetch(
        `${API_BASE_URL}/benchmarks/runs/${selectedRunId}/ranking/`,
      );

      if (!res.ok) {
        throw new Error("Could not fetch ranking.");
      }

      const data: RankingResponse = await res.json();
      setRanking(data);
    } catch (err) {
      console.error(err);
      setError("Could not load ranking results.");
    } finally {
      setLoadingRanking(false);
    }
  }

  useEffect(() => {
    if (projectId) {
      fetchRuns();
    }
  }, [projectId]);

  useEffect(() => {
    if (selectedRunId) {
      fetchRanking();
    }
  }, [selectedRunId]);

  const allModels = ranking?.ranking ?? [];
  const bestModel = allModels.length > 0 ? allModels[0] : null;

  useEffect(() => {
    if (allModels.length > 0) {
      if (!selectedChartModelKey) {
        setSelectedChartModelKey(allModels[0].model_key);
      }

      if (!headToHeadA) {
        setHeadToHeadA(allModels[0].model_key);
      }

      if (!headToHeadB && allModels.length > 1) {
        setHeadToHeadB(allModels[1].model_key);
      }
    }
  }, [allModels, selectedChartModelKey, headToHeadA, headToHeadB]);

  function formatScore(score: number) {
    return score.toFixed(3);
  }

  function getModelByKey(modelKey: string) {
    return allModels.find((model) => model.model_key === modelKey) ?? null;
  }

  const selectedChartModel = getModelByKey(selectedChartModelKey);
  const headToHeadModelA = getModelByKey(headToHeadA);
  const headToHeadModelB = getModelByKey(headToHeadB);

  const finalScoreData = allModels.map((row) => ({
    model: row.model_key,
    final_score: Number(row.final_score.toFixed(3)),
  }));

  const selectedModelMetricData = selectedChartModel
    ? [
        {
          metric: "Faithfulness",
          score: Number(selectedChartModel.faithfulness.toFixed(3)),
        },
        {
          metric: "Relevancy",
          score: Number(selectedChartModel.answer_relevancy.toFixed(3)),
        },
        {
          metric: "Precision",
          score: Number(selectedChartModel.context_precision.toFixed(3)),
        },
        // {
        //   metric: "Recall",
        //   score: Number(selectedChartModel.context_recall.toFixed(3)),
        // },
        {
          metric: "Sufficiency",
          score: Number(selectedChartModel.context_sufficiency.toFixed(3)),
        },
      ]
    : [];

  const headToHeadData =
    headToHeadModelA && headToHeadModelB
      ? [
          {
            metric: "Final",
            [headToHeadModelA.model_key]: Number(
              headToHeadModelA.final_score.toFixed(3),
            ),
            [headToHeadModelB.model_key]: Number(
              headToHeadModelB.final_score.toFixed(3),
            ),
          },
          {
            metric: "Faithfulness",
            [headToHeadModelA.model_key]: Number(
              headToHeadModelA.faithfulness.toFixed(3),
            ),
            [headToHeadModelB.model_key]: Number(
              headToHeadModelB.faithfulness.toFixed(3),
            ),
          },
          {
            metric: "Relevancy",
            [headToHeadModelA.model_key]: Number(
              headToHeadModelA.answer_relevancy.toFixed(3),
            ),
            [headToHeadModelB.model_key]: Number(
              headToHeadModelB.answer_relevancy.toFixed(3),
            ),
          },
          {
            metric: "Precision",
            [headToHeadModelA.model_key]: Number(
              headToHeadModelA.context_precision.toFixed(3),
            ),
            [headToHeadModelB.model_key]: Number(
              headToHeadModelB.context_precision.toFixed(3),
            ),
          },
          // {
          //   metric: "Recall",
          //   [headToHeadModelA.model_key]: Number(
          //     headToHeadModelA.context_recall.toFixed(3),
          //   ),
          //   [headToHeadModelB.model_key]: Number(
          //     headToHeadModelB.context_recall.toFixed(3),
          //   ),
          // },
          {
            metric: "Sufficiency",
            [headToHeadModelA.model_key]: Number(
              headToHeadModelA.context_sufficiency.toFixed(3),
            ),
            [headToHeadModelB.model_key]: Number(
              headToHeadModelB.context_sufficiency.toFixed(3),
            ),
          },
        ]
      : [];

  const fastestModel = useMemo(() => {
    const modelsWithLatency = allModels.filter((model) => model.latency_ms);

    if (modelsWithLatency.length === 0) return null;

    return [...modelsWithLatency].sort(
      (a, b) => (a.latency_ms ?? 0) - (b.latency_ms ?? 0),
    )[0];
  }, [allModels]);

  return (
    <main className="max-w-7xl mx-auto p-8">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}`}
          className="text-sm underline text-white"
        >
          ← Back to project
        </Link>

        <h1 className="text-3xl font-bold mt-4">Benchmark Ranking</h1>

        <p className="text-white/80 mt-2">
          Compare all evaluated models using custom RAGAS-style metrics, visual
          charts, and head-to-head analysis.
        </p>
      </div>

      {error && (
        <div className="border border-red-500 bg-red-50 text-red-700 rounded p-4 mb-6">
          {error}
        </div>
      )}

      <section className="border rounded bg-white text-black p-5 mb-8">
        <label className="block font-semibold mb-2">Benchmark run</label>

        <select
          value={selectedRunId ?? ""}
          onChange={(e) => setSelectedRunId(Number(e.target.value))}
          className="border rounded px-3 py-2 w-full mb-4 text-black bg-white"
        >
          {runs.map((run) => (
            <option key={run.id} value={run.id}>
              Run #{run.id} — {run.question_text}
            </option>
          ))}
        </select>

        {ranking && (
          <div className="border rounded bg-gray-50 p-4 mb-4">
            <p className="text-sm font-semibold text-gray-600 mb-1">
              Evaluated question
            </p>
            <p className="text-black">{ranking.question}</p>
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          <button
            onClick={evaluateRun}
            disabled={!selectedRunId || evaluating}
            className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          >
            {evaluating ? "Starting evaluation..." : "Run Judge Evaluation"}
          </button>

          <button
            onClick={fetchRanking}
            disabled={!selectedRunId || loadingRanking}
            className="px-4 py-2 rounded border text-black bg-white"
          >
            {loadingRanking ? "Refreshing..." : "Refresh Ranking"}
          </button>

          {selectedRunId && (
            <>
              <a
                href={exportUrl(
                  `/benchmarks/runs/${selectedRunId}/export/csv/`,
                )}
                className="px-4 py-2 rounded bg-green-700 text-white"
              >
                Export CSV
              </a>

              <a
                href={exportUrl(
                  `/benchmarks/runs/${selectedRunId}/export/json/`,
                )}
                className="px-4 py-2 rounded bg-blue-700 text-white"
              >
                Export JSON
              </a>
            </>
          )}
        </div>
      </section>

      {loadingRuns && (
        <div className="border rounded bg-white text-black p-6">
          Loading benchmark runs...
        </div>
      )}

      {ranking && (
        <>
          {allModels.length === 0 ? (
            <div className="border rounded bg-white text-black p-6">
              No evaluation results yet. Run judge evaluation first.
            </div>
          ) : (
            <>
              <section className="grid md:grid-cols-3 gap-4 mb-8">
                <div className="border rounded bg-white text-black p-5">
                  <p className="text-sm text-gray-600">Best model</p>
                  <p className="text-2xl font-bold mt-1">
                    {bestModel?.model_key}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    Rank #{bestModel?.rank}
                  </p>
                </div>

                <div className="border rounded bg-white text-black p-5">
                  <p className="text-sm text-gray-600">Best score</p>
                  <p className="text-2xl font-bold mt-1">
                    {bestModel ? formatScore(bestModel.final_score) : "-"}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    Weighted score from all metrics
                  </p>
                </div>

                <div className="border rounded bg-white text-black p-5">
                  <p className="text-sm text-gray-600">Fastest model</p>
                  <p className="text-2xl font-bold mt-1">
                    {fastestModel?.model_key ?? "-"}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    {fastestModel?.latency_ms
                      ? `${(fastestModel.latency_ms / 1000).toFixed(2)}s`
                      : "No latency available"}
                  </p>
                </div>
              </section>

              <section className="grid lg:grid-cols-2 gap-6 mb-8">
                <div className="border rounded bg-white text-black p-5">
                  <h2 className="font-semibold text-lg mb-2">
                    Final Score by Model
                  </h2>

                  <p className="text-sm text-gray-600 mb-4">
                    Shows the final weighted benchmark score for every evaluated
                    model.
                  </p>

                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={finalScoreData}>
                        <XAxis dataKey="model" tick={{ fill: "black" }} />
                        <YAxis domain={[0, 1]} tick={{ fill: "black" }} />
                        <Tooltip
                          contentStyle={{ color: "black" }}
                          labelStyle={{ color: "black" }}
                        />
                        <Bar dataKey="final_score" name="Final Score" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="border rounded bg-white text-black p-5">
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
                    <div>
                      <h2 className="font-semibold text-lg">
                        Model Metric Profile
                      </h2>
                      <p className="text-sm text-gray-600 mt-1">
                        Select a model and choose how to visualize its metric
                        profile.
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <select
                        value={selectedChartModelKey}
                        onChange={(e) =>
                          setSelectedChartModelKey(e.target.value)
                        }
                        className="border rounded px-3 py-2 bg-white text-black text-sm"
                      >
                        {allModels.map((model) => (
                          <option key={model.model_key} value={model.model_key}>
                            {model.model_key}
                          </option>
                        ))}
                      </select>

                      <select
                        value={chartType}
                        onChange={(e) =>
                          setChartType(e.target.value as ChartType)
                        }
                        className="border rounded px-3 py-2 bg-white text-black text-sm"
                      >
                        <option value="radar">Spider chart</option>
                        <option value="metrics_bar">Metric bars</option>
                      </select>
                    </div>
                  </div>

                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      {chartType === "radar" ? (
                        <RadarChart data={selectedModelMetricData}>
                          <PolarGrid />
                          <PolarAngleAxis
                            dataKey="metric"
                            tick={{ fill: "black" }}
                          />
                          <PolarRadiusAxis
                            domain={[0, 1]}
                            tick={{ fill: "black" }}
                          />
                          <Radar
                            dataKey="score"
                            name={selectedChartModel?.model_key ?? "Model"}
                            fillOpacity={0.35}
                          />
                          <Tooltip
                            contentStyle={{ color: "black" }}
                            labelStyle={{ color: "black" }}
                          />
                          <Legend />
                        </RadarChart>
                      ) : (
                        <BarChart data={selectedModelMetricData}>
                          <XAxis dataKey="metric" tick={{ fill: "black" }} />
                          <YAxis domain={[0, 1]} tick={{ fill: "black" }} />
                          <Tooltip
                            contentStyle={{ color: "black" }}
                            labelStyle={{ color: "black" }}
                          />
                          <Bar dataKey="score" name="Metric Score" />
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                </div>
              </section>

              <section className="border rounded bg-white text-black p-5 mb-8">
                <h2 className="font-semibold text-lg mb-4">
                  Complete Model Ranking
                </h2>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-black">
                    <thead className="bg-gray-100 text-black">
                      <tr>
                        <th className="text-left p-3">Rank</th>
                        <th className="text-left p-3">Model</th>
                        <th className="text-left p-3">Final</th>
                        <th className="text-left p-3">Faithfulness</th>
                        <th className="text-left p-3">Relevancy</th>
                        <th className="text-left p-3">Precision</th>
                        {/* <th className="text-left p-3">Recall</th> */}
                        <th className="text-left p-3">Sufficiency</th>
                        <th className="text-left p-3">Latency</th>
                      </tr>
                    </thead>

                    <tbody>
                      {allModels.map((row) => (
                        <tr key={row.answer_id} className="border-t text-black">
                          <td className="p-3 font-bold">#{row.rank}</td>

                          <td className="p-3">
                            <div className="font-semibold">{row.model_key}</div>
                          </td>

                          <td className="p-3 font-semibold">
                            {formatScore(row.final_score)}
                          </td>

                          <td className="p-3">
                            {formatScore(row.faithfulness)}
                          </td>

                          <td className="p-3">
                            {formatScore(row.answer_relevancy)}
                          </td>

                          <td className="p-3">
                            {formatScore(row.context_precision)}
                          </td>

                          {/* <td className="p-3">
                            {formatScore(row.context_recall)}
                          </td> */}
                          <td className="p-3">
                            {formatScore(row.context_sufficiency)}
                          </td>
                          <td className="p-3">
                            {row.latency_ms
                              ? `${(row.latency_ms / 1000).toFixed(2)}s`
                              : "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="border rounded bg-white text-black p-5 mb-8">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
                  <div>
                    <h2 className="font-semibold text-lg">
                      Head-to-Head Comparison
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      Compare two models directly across final score and all
                      evaluation metrics.
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <select
                      value={headToHeadA}
                      onChange={(e) => setHeadToHeadA(e.target.value)}
                      className="border rounded px-3 py-2 bg-white text-black text-sm"
                    >
                      {allModels.map((model) => (
                        <option key={model.model_key} value={model.model_key}>
                          {model.model_key}
                        </option>
                      ))}
                    </select>

                    <select
                      value={headToHeadB}
                      onChange={(e) => setHeadToHeadB(e.target.value)}
                      className="border rounded px-3 py-2 bg-white text-black text-sm"
                    >
                      {allModels.map((model) => (
                        <option key={model.model_key} value={model.model_key}>
                          {model.model_key}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {headToHeadModelA && headToHeadModelB ? (
                  <div className="grid lg:grid-cols-2 gap-6">
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={headToHeadData}>
                          <XAxis dataKey="metric" tick={{ fill: "black" }} />
                          <YAxis domain={[0, 1]} tick={{ fill: "black" }} />
                          <Tooltip
                            contentStyle={{ color: "black" }}
                            labelStyle={{ color: "black" }}
                          />
                          <Legend />
                          <Bar
                            dataKey={headToHeadModelA.model_key}
                            name={headToHeadModelA.model_key}
                            fill="#1F77B4"
                          />
                          <Bar
                            dataKey={headToHeadModelB.model_key}
                            name={headToHeadModelB.model_key}
                            fill="#FF7F0E"
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <ModelComparisonCard model={headToHeadModelA} />
                      <ModelComparisonCard model={headToHeadModelB} />
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-600">Select two models to compare.</p>
                )}
              </section>

              <section className="border rounded bg-white text-black p-5">
                <h2 className="font-semibold text-lg mb-4">
                  Generated Answers
                </h2>

                <p className="text-sm text-gray-600 mb-4">
                  The table and charts above summarize the benchmark. Use this
                  section only when you need to inspect the actual generated
                  answers.
                </p>

                <div className="space-y-3">
                  {allModels.map((row) => (
                    <details
                      key={row.answer_id}
                      className="border rounded p-4 bg-gray-50"
                    >
                      <summary className="cursor-pointer font-semibold">
                        #{row.rank} — {row.model_key} · Final score{" "}
                        {formatScore(row.final_score)}
                      </summary>

                      <p className="whitespace-pre-wrap mt-4 text-black">
                        {row.answer}
                      </p>
                    </details>
                  ))}
                </div>
              </section>
            </>
          )}
        </>
      )}
    </main>
  );
}

function ModelComparisonCard({ model }: { model: RankingRow }) {
  return (
    <div className="border rounded p-4 bg-gray-50">
      <h3 className="font-bold text-lg mb-1">{model.model_key}</h3>

      <p className="text-sm text-gray-500 mb-4">Rank #{model.rank}</p>

      <div className="space-y-2 text-sm">
        <MetricRow label="Final" value={model.final_score} />
        <MetricRow label="Faithfulness" value={model.faithfulness} />
        <MetricRow label="Relevancy" value={model.answer_relevancy} />
        <MetricRow label="Precision" value={model.context_precision} />
        {/* <MetricRow label="Recall" value={model.context_recall} /> */}
        <MetricRow label="Sufficiency" value={model.context_sufficiency} />
      </div>

      <div className="text-sm text-gray-600 mt-4">
        Latency:{" "}
        {model.latency_ms ? `${(model.latency_ms / 1000).toFixed(2)}s` : "-"}
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between border-b pb-1">
      <span>{label}</span>
      <span className="font-semibold">{value.toFixed(3)}</span>
    </div>
  );
}
