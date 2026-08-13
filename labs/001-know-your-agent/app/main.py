from fastapi import FastAPI

from loader import load_desk_policy, load_registry
from models import EvaluateRequest, EvaluateResponse
from policy_engine import evaluate

app = FastAPI(
    title="Know Your Agent",
    description=(
        "Fictional paper-desk policy gate. Identify the agent, apply the desk "
        "policy, and allow or deny a proposed action. Not investment guidance."
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/registry")
def registry():
    return load_registry()


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate_action(request: EvaluateRequest) -> EvaluateResponse:
    return evaluate(request, load_registry(), load_desk_policy())
