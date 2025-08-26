# main.py

import uvicorn
import config
from fastapi import FastAPI
from api.routes import router as api_router

logger = config.setup_logging()
app = FastAPI(title=config.API_TITLE)
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)