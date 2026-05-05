import { NextRequest, NextResponse } from "next/server";

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const backendOrigin = configuredApiBaseUrl
    ? configuredApiBaseUrl.replace(/\/api\/?$/, "")
    : process.env.NODE_ENV === "development"
        ? "http://localhost:8001"
        : "https://capstone-app-hqi3.vercel.app";

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
    const targetUrl = new URL(`${backendOrigin}/api/${pathSegments.join("/")}`);
    targetUrl.search = request.nextUrl.search;

    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("content-length");

    const response = await fetch(targetUrl, {
        method: request.method,
        headers,
        body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
        redirect: "follow",
    });

    const proxiedHeaders = new Headers(response.headers);
    proxiedHeaders.delete("content-encoding");
    proxiedHeaders.delete("transfer-encoding");
    proxiedHeaders.delete("content-length");

    return new NextResponse(response.body, {
        status: response.status,
        headers: proxiedHeaders,
    });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function OPTIONS(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}