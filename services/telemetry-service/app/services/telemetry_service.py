# /telemetry-service/app/services/telemetry_service.py
from typing import List
from redis import Redis
from celery import Celery

from app.schemas.schemas import SidecarMetrics

class TelemetryService:
    AI_COOLDOWN_SECONDS = 120
    MAX_BUFFER_LINES = 50
    TRIGGER_WORDS = ["error", "exception", "failed", "timeout", "critical", "crash"]
    METRICS_TTL = 60

    def __init__(self, redis_client: Redis, celery_app: Celery):
        self.redis = redis_client
        self.celery = celery_app

    def process_logs(self, server_id: str, logs: List[str]):
        log_key = f"server_logs:{server_id}"
        cooldown_key = f"ai_cooldown:{server_id}"
        
        ai_triggered = False
        triggered_line = ""

        if logs:
            self.redis.rpush(log_key, *logs)
            self.redis.ltrim(log_key, -self.MAX_BUFFER_LINES, -1)

            for line in logs:
                if any(word in line.lower() for word in self.TRIGGER_WORDS):
                    ai_triggered = True
                    triggered_line = line
                    break

        ai_task_id = None

        if ai_triggered:
            can_trigger = self.redis.set(
                cooldown_key, 
                "active", 
                nx=True, 
                ex=self.AI_COOLDOWN_SECONDS
            )
            
            if can_trigger:
                context_logs = self.redis.lrange(log_key, 0, -1)
                # Ensure this matches the task name registered in your standalone worker container
                task = self.celery.send_task(
                    "analyze_logs_with_rag", 
                    args=[server_id, context_logs, triggered_line]
                )
                ai_task_id = task.id

        return {
            "status": "logs_received", 
            "lines_processed": len(logs),
            "ai_task_id": ai_task_id
        }

    def process_metrics(self, server_id: str, metrics: SidecarMetrics):
        stats_key = f"server_stats:{server_id}"
        self.redis.hset(stats_key, mapping=metrics.dict())
        self.redis.expire(stats_key, self.METRICS_TTL)
        return {"status": "recorded"}