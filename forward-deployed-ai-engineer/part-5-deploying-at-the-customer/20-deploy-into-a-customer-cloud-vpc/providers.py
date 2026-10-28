"""providers.py: one function that returns "the brain", wherever the customer allows it to live.

    LLM_PROVIDER=anthropic   Claude API (needs outbound HTTPS to api.anthropic.com, usually through the customer's proxy)
    LLM_PROVIDER=bedrock     Claude in Amazon Bedrock, inside the customer's AWS account (IAM role, no API key)
    LLM_PROVIDER=vertex      Claude on Google Cloud Vertex AI, inside the customer's GCP project (service account)
    LLM_PROVIDER=ollama      an open model on the customer's own servers (lesson 21), OpenAI-compatible API
    LLM_PROVIDER=fake        no model: canned answers (tests, smoke tests in a locked-down network)
"""
import os
from pathlib import Path

import httpx

SYSTEM = ("You help Northwind support agents answer customers about shipments. "
          "Be short and factual. If you don't know, say so.")


def read_secret(name: str) -> str | None:
    """Secrets come from a FILE when possible (Docker/Kubernetes mount them under /run/secrets),
    else from an environment variable. Files don't show up in `docker inspect` or crash dumps."""
    folder = Path(os.getenv("SECRETS_DIR", "/run/secrets"))
    file = folder / name.lower()
    if file.is_file():
        return file.read_text(encoding="utf-8").strip()
    return os.getenv(name.upper())


class Brain:
    """Same tiny interface for every provider: ask(question) -> answer text."""

    def __init__(self, name: str, client=None, model: str = ""):
        self.name, self.client, self.model = name, client, model

    def ask(self, question: str) -> str:
        if self.name == "fake":
            return f"(FAKE) I would look up the shipment and answer: {question[:80]}"
        if self.name == "ollama":
            r = self.client.post("/chat/completions", json={"model": self.model, "messages": [
                {"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        response = self.client.messages.create(model=self.model, max_tokens=2000, system=SYSTEM,
                                               output_config={"effort": "low"},
                                               messages=[{"role": "user", "content": question}])
        if response.stop_reason == "refusal":
            return "The model declined this request."
        return "".join(b.text for b in response.content if b.type == "text")


def get_brain() -> Brain:
    import anthropic
    name = os.getenv("LLM_PROVIDER", "fake").lower()
    if name == "fake":
        return Brain("fake")
    if name == "anthropic":
        key = read_secret("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("No ANTHROPIC_API_KEY secret (file /run/secrets/anthropic_api_key or env var)")
        return Brain(name, anthropic.Anthropic(api_key=key), os.getenv("CLAUDE_MODEL", "claude-opus-5-5"))
    if name == "bedrock":
        # No API key: the SDK signs requests with the AWS credentials of the machine's IAM ROLE.
        # BEDROCK_BASE_URL lets you point at a private (VPC endpoint) DNS name if your network needs it.
        kwargs = {"aws_region": os.getenv("AWS_REGION", "eu-central-1")}
        if os.getenv("BEDROCK_BASE_URL"):
            kwargs["base_url"] = os.environ["BEDROCK_BASE_URL"]
        return Brain(name, anthropic.AnthropicBedrockMantle(**kwargs),
                     os.getenv("BEDROCK_MODEL", "anthropic.claude-opus-5-5"))
    if name == "vertex":
        # No API key: Google's "Application Default Credentials" (the VM's or pod's service account).
        return Brain(name, anthropic.AnthropicVertex(project_id=os.environ["GCP_PROJECT"],
                                                     region=os.getenv("GCP_REGION", "europe-west1")),
                     os.getenv("VERTEX_MODEL", "claude-opus-5-5"))
    if name == "ollama":
        return Brain(name, httpx.Client(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), timeout=300),
                     os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
    raise RuntimeError(f"Unknown LLM_PROVIDER {name!r}")
