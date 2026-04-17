from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings


app = FastAPI(title="AI Used Car Decision Copilot API", version="0.1.0")
app.include_router(router)


def main() -> None:
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)


if __name__ == "__main__":
    main()

