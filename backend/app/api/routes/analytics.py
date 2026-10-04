from fastapi import APIRouter, Depends
from app.schemas.schemas import AnalyticsSummary
from app.core.deps import get_db, get_org_id
from datetime import datetime, timezone, timedelta

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(db=Depends(get_db), org_id: str = Depends(get_org_id)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    total_mem = await db.table("memories").select("id", count="exact").eq("org_id", org_id).execute()
    total_agents = await db.table("agents").select("id", count="exact").eq("org_id", org_id).execute()
    today_mem = await db.table("memories").select("id", count="exact").eq("org_id", org_id).gte("created_at", today.isoformat()).execute()

    outcomes = await db.table("memories").select("outcome").eq("org_id", org_id).execute()
    outcome_map: dict = {}
    success_count = 0
    for r in outcomes.data:
        o = r["outcome"]
        outcome_map[o] = outcome_map.get(o, 0) + 1
        if o == "success":
            success_count += 1
    total = total_mem.count or 1
    success_rate = round(success_count / total * 100, 1)

    types = await db.table("memories").select("memory_type").eq("org_id", org_id).execute()
    type_map: dict = {}
    for r in types.data:
        t = r["memory_type"]
        type_map[t] = type_map.get(t, 0) + 1

    latency = await db.table("memories").select("latency_ms").eq("org_id", org_id).not_.is_("latency_ms", "null").execute()
    avg_latency = None
    if latency.data:
        vals = [r["latency_ms"] for r in latency.data if r["latency_ms"]]
        avg_latency = round(sum(vals) / len(vals), 0) if vals else None

    agent_counts = await db.table("memories").select("agent_id").eq("org_id", org_id).execute()
    agent_map: dict = {}
    for r in agent_counts.data:
        a = r["agent_id"]
        agent_map[a] = agent_map.get(a, 0) + 1
    top_agents = sorted([{"agent_id": k, "count": v} for k, v in agent_map.items()], key=lambda x: x["count"], reverse=True)[:5]

    daily = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = await db.table("memories").select("id", count="exact").eq("org_id", org_id).gte("created_at", day.isoformat()).lt("created_at", next_day.isoformat()).execute()
        daily.append({"date": day.strftime("%Y-%m-%d"), "count": count.count or 0})

    return AnalyticsSummary(
        total_memories=total_mem.count or 0, total_agents=total_agents.count or 0,
        memories_today=today_mem.count or 0, success_rate=success_rate, avg_latency_ms=avg_latency,
        top_agents=top_agents, memory_type_breakdown=type_map, outcome_breakdown=outcome_map, daily_volume=daily,
    )
