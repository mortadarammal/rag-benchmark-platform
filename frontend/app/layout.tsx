// frontend/app/layout.tsx

import "./globals.css";
import Navbar from "./components/Navbar";

export const metadata = {
  title: "RAG Benchmark",
  description: "LLM-as-a-judge RAG benchmark platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-700">
        <Navbar />
        {children}
      </body>
    </html>
  );
}
