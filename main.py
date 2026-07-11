from fastapi import FastAPI

app = FastAPI(
    title="Project RISING API",
    description=(
        "AI-powered health intelligence API for ASEAN public-health "
        "analytics and climate resilience."
    ),
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Project RISING",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}