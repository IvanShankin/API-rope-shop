import asyncio

import uvicorn

from src.modules.api.app import init_fastapi_app

app = init_fastapi_app()


async def main():
    config = getattr(app.state, "config", None)
    is_prod = config and getattr(config.env, "mode", "").upper() in ("PROD", "PRODUCTION")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8018,
        reload=not is_prod,
    )

if __name__ == '__main__':
    asyncio.run(main())
