import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 text-center">
      <h1 className="mb-4 text-4xl font-bold">TTB Label Verification</h1>
      <p className="mb-10 text-xl text-gray-700">
        Automated compliance checks for COLA label submissions.
      </p>
      <nav className="flex flex-col items-center gap-6 sm:flex-row sm:justify-center">
        <Link
          to="/review"
          className="rounded-xl bg-blue-700 px-8 py-4 text-xl font-bold text-white hover:bg-blue-800"
        >
          Inspector Review
        </Link>
        <Link
          to="/batch"
          className="rounded-xl bg-gray-800 px-8 py-4 text-xl font-bold text-white hover:bg-black"
        >
          Batch Queue
        </Link>
      </nav>
    </main>
  );
}
