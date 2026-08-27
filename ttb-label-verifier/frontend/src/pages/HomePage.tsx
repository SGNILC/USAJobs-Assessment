import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-16 text-center text-black">
      <h1 className="mb-6 text-5xl font-black underline decoration-blue-700 decoration-8">
        TTB Label Verification
      </h1>
      <p className="mb-12 text-2xl font-bold text-gray-900">
        Automated compliance engine for federal alcohol label submissions.
      </p>

      <nav className="grid gap-8 sm:grid-cols-2">
        <Link
          to="/review"
          className="flex flex-col items-center justify-center rounded-3xl border-4 border-black bg-blue-800 p-8 shadow-xl hover:bg-blue-900 active:scale-95 text-white"
        >
          <span className="text-4xl font-black mb-2"> 🕵🏿 Inspector Review</span>
          <span className="text-xl font-medium">Verify single label applications <br /> side-by-side</span>
        </Link>

        <Link
          to="/batch"
          className="flex flex-col items-center justify-center rounded-3xl border-4 border-black bg-gray-900 p-8 shadow-xl hover:bg-black active:scale-95 text-white"
        >
          <span className="text-4xl font-black mb-2">📁 Batch Queue</span>
          <span className="text-xl font-medium">Process up to 300 labels in bulk asynchronously</span>
        </Link>
      </nav>
    </main>
  );
}