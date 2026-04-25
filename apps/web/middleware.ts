import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const adminUsername = process.env.ADMIN_USERNAME ?? process.env.WEB_ADMIN_USERNAME;
const adminPassword = process.env.ADMIN_PASSWORD ?? process.env.WEB_ADMIN_PASSWORD;

function unauthorized() {
  return new NextResponse("Authentication required.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Used Car Copilot Admin", charset="UTF-8"',
    },
  });
}

export function middleware(request: NextRequest) {
  if (!adminUsername || !adminPassword) {
    return new NextResponse("Admin credentials are not configured. Set ADMIN_USERNAME and ADMIN_PASSWORD in .env.", {
      status: 503,
    });
  }

  const header = request.headers.get("authorization");
  if (!header?.startsWith("Basic ")) {
    return unauthorized();
  }

  try {
    const decoded = atob(header.slice("Basic ".length));
    const separatorIndex = decoded.indexOf(":");
    if (separatorIndex === -1) {
      return unauthorized();
    }

    const username = decoded.slice(0, separatorIndex);
    const password = decoded.slice(separatorIndex + 1);

    if (username === adminUsername && password === adminPassword) {
      return NextResponse.next();
    }
  } catch {
    return unauthorized();
  }

  return unauthorized();
}

export const config = {
  matcher: ["/admin/:path*"],
};
