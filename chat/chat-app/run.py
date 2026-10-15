import uvicorn

from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="debug" if Config.DEBUG else "info",
    )
