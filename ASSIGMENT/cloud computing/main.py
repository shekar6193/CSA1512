import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting CampusPulse Cloud Platform on http://{host}:{port}")
    print(f"Interactive OpenAPI Docs available at http://{host}:{port}/docs")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
