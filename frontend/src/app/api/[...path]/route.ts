import { NextRequest, NextResponse } from "next/server";

const DEFAULT_BACKEND = "https://zomato-ai-recommendation-engine-backend.onrender.com";

function getTargetUrl(request: NextRequest, pathSegments: string[]): string {
  const envUrl = process.env.FASTAPI_BACKEND_URL?.trim();
  const base = (envUrl && envUrl.length > 0 ? envUrl : DEFAULT_BACKEND).replace(/\/+$/, "");
  const subpath = pathSegments.join("/");
  const search = request.nextUrl.search; // preserves ?q=... etc
  return `${base}/api/${subpath}${search}`;
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const targetUrl = getTargetUrl(request, path);

  try {
    const res = await fetch(targetUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }

    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": contentType || "text/plain" },
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Backend proxy error", detail: err?.message || String(err) },
      { status: 503 }
    );
  }
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  const targetUrl = getTargetUrl(request, path);

  try {
    const body = await request.json();
    const res = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Backend proxy error", detail: err?.message || String(err) },
      { status: 503 }
    );
  }
}
