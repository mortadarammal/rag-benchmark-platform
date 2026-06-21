"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "../../lib/api";

type Project = {
  id: number;
  name: string;
  description: string;
};

export default function NewProjectPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function createProject() {
    if (!name.trim()) return;

    const project = await apiPost<Project>("/projects/", {
      name,
      description,
    });

    router.push(`/projects/${project.id}`);
  }

  return (
    <main className="max-w-2xl mx-auto p-8">
      <h1 className="text-3xl font-bold  mb-2">New Project</h1>

      <div className="border rounded bg-white p-6 space-y-4">
        <div>
          <label className="block font-semibold text-black mb-2">
            Project name
          </label>
          <input
            className="border rounded px-3 py-2 w-full text-black placeholder:text-black"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="NEW project"
          />
        </div>

        <div>
          <label className="block font-semibold  text-black mb-2">
            Description
          </label>
          <textarea
            className="border rounded px-3 py-2 w-full text-black placeholder:text-black"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder=" description"
            rows={4}
          />
        </div>

        <button
          onClick={createProject}
          disabled={!name.trim()}
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
        >
          Create Project
        </button>
      </div>
    </main>
  );
}
