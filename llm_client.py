"""Minimal LLM adapters for Groq and Hugging Face Inference API."""
import os
import requests

class LLMError(RuntimeError):
    pass

def generate(messages):
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider == "mock":
        last = messages[-1]["content"] if messages else ""
        return ("[Modo demostración] Recibí tu consulta. Para activar un modelo remoto, configurá "
                "LLM_PROVIDER y el token correspondiente en .env. Consulta: " + last[:500])
    if provider == "groq":
        token = os.getenv("GROQ_API_KEY", "").strip()
        if not token:
            raise LLMError("Falta GROQ_API_KEY en .env.")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.2},
                timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise LLMError(f"Error al consultar Groq: {e}") from e
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError("Respuesta inesperada de Groq.") from e
    if provider == "huggingface":
        token = os.getenv("HF_TOKEN", "").strip()
        if not token:
            raise LLMError("Falta HF_TOKEN en .env.")
        model = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
        url = f"https://router.huggingface.co/v1/chat/completions"
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {token}",
                "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.2},
                timeout=90)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise LLMError(f"Error al consultar Hugging Face: {e}") from e
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError("Respuesta inesperada de Hugging Face.") from e
    raise LLMError("LLM_PROVIDER debe ser mock, groq o huggingface.")
