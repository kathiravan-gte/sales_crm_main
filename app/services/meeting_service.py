import json
from sqlalchemy.orm import Session
from app.models.meeting import Meeting, MeetingInsight
from app.schemas.meeting import MeetingCreate
from app.schemas.activity import ActivityCreate
from app.services import activity as activity_service
from app.services import llm_service

_EXTRACT_SYSTEM = """\
You are an expert CRM assistant. Extract meeting insights from the provided transcript.
Reply with ONLY a JSON object — no prose, no markdown, no explanation.

Expected JSON structure:
{
  "summary": "3-sentence executive summary",
  "tasks": [
    {"content": "Description of the task", "deadline": "Optional deadline (e.g. 'Next Friday')", "owner": "Optional owner name"}
  ],
  "points": [
    {"content": "Key discussion point or decision"}
  ]
}
"""

def process_transcript(text: str):
    """
    LLM-powered extraction to identify Summary, Tasks and Discussion Points.
    Falls back to rule-based logic if LLM fails.
    """
    try:
        raw = llm_service._call(_EXTRACT_SYSTEM, f"Transcript:\n{text}", max_tokens=1000)
        if raw:
            # Clean possible markdown fences
            clean_raw = raw.strip()
            if clean_raw.startswith("```"):
                import re
                clean_raw = re.sub(r"^```(?:json)?\s*", "", clean_raw)
                clean_raw = re.sub(r"\s*```$", "", clean_raw)
            
            data = json.loads(clean_raw)
            summary = data.get("summary", "")
            tasks = data.get("tasks", [])
            points = data.get("points", [])
            return summary, tasks, points
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("[Meeting] LLM extraction failed, falling back: %s", e)
    
    # Simple rule-based fallback if LLM is unavailable or fails
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
    return "Summary unavailable (AI fallback).", [], [{"content": l} for l in lines[:5]]

def process_meeting(db: Session, meeting_in: MeetingCreate, user_id: int):
    # Enforce performance rule: max 10000 chars (upscaled for LLM)
    transcript = meeting_in.transcript[:10000]
    
    # 1. Save Meeting
    db_meeting = Meeting(title=meeting_in.title, transcript=transcript, created_by=user_id)
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    
    # 2. Extract Insights (LLM-powered)
    summary, tasks, points = process_transcript(transcript)
    
    # 3. Store Insights and Create Activities
    
    # Store Summary as a special insight type
    if summary:
        sum_insight = MeetingInsight(meeting_id=db_meeting.id, type="summary", content=summary)
        db.add(sum_insight)

    for p in points:
        content = p.get("content", "") if isinstance(p, dict) else str(p)
        if content:
            insight = MeetingInsight(meeting_id=db_meeting.id, type="point", content=content)
            db.add(insight)
        
    for t in tasks:
        if not isinstance(t, dict): continue
        content = t.get("content", "")
        deadline = t.get("deadline")
        owner = t.get("owner")
        
        insight = MeetingInsight(meeting_id=db_meeting.id, type="task", content=content, deadline=deadline, owner=owner)
        db.add(insight)
        
        # Link to Activity Module
        owner_text = f"Assigned to {owner}: " if owner and owner.lower() not in ["i", "we", "they"] else ""
        deadline_text = f" [Due: {deadline}]" if deadline else ""
        
        activity_desc = f"{owner_text}{content}{deadline_text} (From Meeting: {db_meeting.title})"
        
        from app.schemas.activity import ActivityCreate
        activity_service.create_activity(db, ActivityCreate(
            activity_type="Task",
            description=activity_desc
        ))
        
    db.commit()
    db.refresh(db_meeting)
    return db_meeting
