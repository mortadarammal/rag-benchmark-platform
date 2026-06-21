// frontend/app/components/Navbar.tsx

import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="border-b bg-white">
      <div className="max-w-6xl mx-auto px-8 py-4 flex justify-between items-center">
        <Link href="/" className="font-bold text-xl text-black">
          LLM Benchmark Platform
        </Link>

        <div className="flex gap-4 text-sm">
          <Link href="/" className="hover:underline text-black">
            Dashboard
          </Link>
          <Link href="/projects/new" className="hover:underline text-black">
            New Project
          </Link>
        </div>
      </div>
    </nav>
  );
}
