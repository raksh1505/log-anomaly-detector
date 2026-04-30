import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and DevOps specialist.
You will be given a set of anomalous server log entries detected by an ML model.
Your job is to:
1. Identify the likely root cause
2. Explain what went wrong in plain English (2-3 sentences max)
3. Suggest 2-3 concrete fix steps

Always respond in this exact JSON format:
{
  "root_cause": "Brief root cause title",
  "explanation": "Plain English explanation of what went wrong",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "suggested_fixes": ["Fix step 1", "Fix step 2", "Fix step 3"]
}
"""


def explain_anomalies(anomalous_logs: list[dict]) -> dict:
    """
    Send anomalous logs to OpenAI and get a root cause explanation.
    Returns a dict with root_cause, explanation, severity, suggested_fixes.
    """
    if not anomalous_logs:
        return {
            "root_cause": "No anomalies detected",
            "explanation": "All log entries appear normal.",
            "severity": "LOW",
            "suggested_fixes": []
        }

    # Format logs for the prompt
    log_text = "\n".join([
        f"[{log['timestamp']}] [{log['level']}] {log['message']} (anomaly_score: {log['anomaly_score']})"
        for log in anomalous_logs[:20]  # cap at 20 to stay within token limits
    ])

    user_message = f"Analyze these anomalous log entries and explain what went wrong:\n\n{log_text}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


def explain_single_anomaly(log: dict) -> dict:
    """Explain a single anomalous log entry."""
    return explain_anomalies([log])
