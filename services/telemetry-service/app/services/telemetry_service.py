# /telemetry-service/app/services/telemetry_service.py
from typing import List
import redis.asyncio as aioredis
from arq.connections import ArqRedis

from app.schemas.schemas import SidecarMetrics

class TelemetryService:
    AI_COOLDOWN_SECONDS = 120
    MAX_BUFFER_LINES = 50
    TRIGGER_WORDS = ["error", "exception", "failed", "timeout", "critical", "crash"]
    METRICS_TTL = 60

    def __init__(self, redis_client: aioredis.Redis, arq_pool: ArqRedis):
        self.redis = redis_client
        self.arq_pool = arq_pool

    async def process_logs(self, server_id: str, logs: List[str]):
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
            can_trigger = await self.redis.set(
                cooldown_key, 
                "active", 
                nx=True, 
                ex=self.AI_COOLDOWN_SECONDS
            )
            
            if can_trigger:
                context_logs = await self.redis.lrange(log_key, 0, -1)
                # Ensure this matches the task name registered in your standalone worker container
                job = await self.arq_pool.enqueue_job(
                    "analyze_logs_with_rag", 
                    server_id,
                    context_logs,
                    triggered_line
                )
                if job:
                    ai_task_id = job.job_id

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