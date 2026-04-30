import random
from datetime import datetime, timedelta


def generate_sample_logs(n_normal: int = 100, n_anomalous: int = 10) -> str:
    """Generate realistic-looking server logs with injected anomalies."""

    normal_templates = [
        "INFO     User login successful for user_id={}",
        "INFO     GET /api/products 200 {}ms",
        "INFO     POST /api/orders 201 {}ms",
        "DEBUG    Cache hit for key=session:{}",
        "INFO     Payment processed for order_id={} amount=₹{}",
        "INFO     Database query completed in {}ms rows={}",
        "INFO     Health check passed",
        "DEBUG    Queue depth: {} messages",
        "INFO     GET /api/users/{} 200 12ms",
        "INFO     Scheduled job 'cleanup' completed successfully",
    ]

    anomaly_templates = [
        "ERROR    Connection refused to database host=db-primary port=5432 after 3 retries",
        "CRITICAL Unhandled exception in payment gateway: NullPointerException at PaymentService.java:142",
        "ERROR    GET /api/checkout 503 timeout after 30000ms",
        "ERROR    Memory usage exceeded 95% threshold — heap dump initiated",
        "CRITICAL Traceback (most recent call last): File 'worker.py' line 88 KeyError: 'transaction_id'",
        "ERROR    Redis connection pool exhausted max_connections=50",
        "ERROR    Failed to process webhook event_id={} after 5 retries — dead letter queue",
        "CRITICAL Disk I/O wait > 80% on /dev/sda1 — possible disk failure",
        "ERROR    JWT token validation failed: signature expired for user_id={}",
        "ERROR    Rate limit exceeded for IP 192.168.1.{} — 429 responses sent",
    ]

    lines = []
    base_time = datetime.now() - timedelta(hours=2)

    for i in range(n_normal):
        ts = base_time + timedelta(seconds=i * 5 + random.randint(0, 4))
        template = random.choice(normal_templates)
        msg = template.format(
            random.randint(1000, 9999),
            random.randint(5, 250),
            random.randint(1, 500)
        )
        lines.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {msg}")

    # Inject anomalies spread across the log
    anomaly_positions = sorted(random.sample(range(n_normal, n_normal + n_anomalous * 10), n_anomalous))

    for i, pos in enumerate(anomaly_positions):
        ts = base_time + timedelta(seconds=pos * 5)
        template = random.choice(anomaly_templates)
        msg = template.format(random.randint(100, 999))
        lines.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {msg}")

    # Sort by timestamp
    lines.sort()
    return "\n".join(lines)


if __name__ == "__main__":
    logs = generate_sample_logs(n_normal=200, n_anomalous=15)
    with open("logs/sample.log", "w") as f:
        f.write(logs)
    print(f"Generated {len(logs.splitlines())} log lines → logs/sample.log")
