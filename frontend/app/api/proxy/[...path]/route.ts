import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

async function handler(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const search = new URL(req.url).search;
  const target = `${BACKEND}/${path.join('/')}/${search}`;

  try {
    const isBody = !['GET', 'HEAD'].includes(req.method);
    const forwardHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const apiKey = req.headers.get('x-api-key');
    if (apiKey) forwardHeaders['X-Api-Key'] = apiKey;

    const upstream = await fetch(target, {
      method: req.method,
      headers: forwardHeaders,
      body: isBody ? await req.text() : undefined,
    });
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('[proxy] error →', target, err);
    return NextResponse.json(
      { error: 'backend_unavailable', detail: String(err) },
      { status: 503 }
    );
  }
}

export const GET    = handler;
export const POST   = handler;
export const PUT    = handler;
export const DELETE = handler;
