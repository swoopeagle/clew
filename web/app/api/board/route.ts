import { createHmac, timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function validSignature(org: string, sig: string): boolean {
  const secret = process.env.CLEW_BOARD_SECRET;
  if (!secret) return true; // signing not configured — open board (single-org dev)
  const expected = createHmac("sha256", secret)
    .update(org)
    .digest("hex")
    .slice(0, 20);
  if (sig.length !== expected.length) return false;
  return timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
}

export async function GET(request: NextRequest) {
  const apiUrl = process.env.CLEW_API_URL;
  if (!apiUrl) {
    return NextResponse.json(
      { error: "CLEW_API_URL is not configured" },
      { status: 503 },
    );
  }

  const org = request.nextUrl.searchParams.get("org") ?? "";
  const sig = request.nextUrl.searchParams.get("sig") ?? "";
  if (process.env.CLEW_BOARD_SECRET && (!org || !validSignature(org, sig))) {
    return NextResponse.json(
      { error: "invalid_board_link" },
      { status: 403 },
    );
  }

  const headers: Record<string, string> = {};
  if (process.env.CLEW_API_TOKEN) {
    headers.Authorization = `Bearer ${process.env.CLEW_API_TOKEN}`;
  }

  const upstream = new URL(`${apiUrl.replace(/\/$/, "")}/api/board`);
  if (org) upstream.searchParams.set("team", org);

  try {
    const res = await fetch(upstream, { headers, cache: "no-store" });
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
