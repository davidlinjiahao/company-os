"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function LoginForm() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    if (res.ok) {
      const from = searchParams.get("from") || "/";
      router.push(from);
      router.refresh();
    } else {
      setError("Incorrect password");
      setPassword("");
    }
  }

  return (
    <div className="min-h-screen bg-[#111114] flex items-center justify-center">
      <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
        <input
          type="password"
          value={password}
          onChange={(e) => { setPassword(e.target.value); setError(""); }}
          placeholder="Password"
          autoFocus
          className="bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-[#ccc] w-60 text-center outline-none focus:border-white/20 placeholder:text-[#444]"
        />
        {error && <p className="text-red-400 text-xs">{error}</p>}
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#111114] flex items-center justify-center">
        <input
          type="password"
          placeholder="Password"
          disabled
          className="bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-[#ccc] w-60 text-center outline-none placeholder:text-[#444]"
        />
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
