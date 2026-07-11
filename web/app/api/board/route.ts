import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const apiUrl = process.env.CLEW_API_URL;
  if (!apiUrl) {
    return NextResponse.json(
      { error: "CLEW_API_URL is not configured" },
      { status: 503 },
    );
  }

  const headers: Record<string, string> = {};
  if (process.env.CLEW_API_TOKEN) {
    headers.Authorization = `Bearer ${process.env.CLEW_API_TOKEN}`;
  }

  try {
    const res = await fetch(`${apiUrl.replace(/\/$/, "")}/api/board`, {
      headers,
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: `Upstream returned ${res.status}` },
        { status: 502 },
      );
    }
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json(
      { error: "Clew's Slack app is unreachable" },
      { status: 502 },
    );
  }
}
