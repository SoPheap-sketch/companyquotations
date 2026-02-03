# app/routes/work_instructions.py
from fastapi import APIRouter, Path, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime

from app.db import SessionLocal
from app.models import WorkInstruction, Project, Attachment
from app.utils.audit import write_audit_log
import os

router = APIRouter()

@router.post("/projects/{project_id}/instructions/create")
def create_work_instruction(
    request: Request,
    project_id: int,
    title: str = Form(...),
    description: str = Form(...),
    assigned_to: int | None = Form(None),
    due_date: str | None = Form(None)
):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if role not in ["admin", "manager", "ceo"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404)

        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")

        instruction = WorkInstruction(
            project_id=project_id,
            created_by=user_id,
            assigned_to=assigned_to,
            title=title,
            description=description,
            status="pending",
            due_date=parsed_due_date
        )

        db.add(instruction)
        try:
            db.commit()
            
            # If your audit log also writes to the DB, it shares the session
            write_audit_log(
                request=request,
                action="CREATE_WORK_INSTRUCTION",
                description=f"Created work instruction for Project #{project_id}",
                target_user_id=user_id,
            )
        except Exception as commit_exc:
            db.rollback() # Release the lock if the commit fails
            print(f"Commit failed: {commit_exc}")
            raise HTTPException(status_code=500, detail="Database busy, please try again.")

        return RedirectResponse(
            f"/projects/{project_id}",
            status_code=303
        )
    finally:
        db.close()

@router.get("/projects/{project_id}/instructions")
def list_instructions(project_id: int):
    db = SessionLocal()
    try:
        instructions = (
            db.query(WorkInstruction)
            .filter(WorkInstruction.project_id == project_id)
            .order_by(WorkInstruction.created_at.desc())
            .all()
        )
        return instructions
    finally:
        db.close()

@router.post("/instructions/{instruction_id}/status")
def update_instruction_status(
    request: Request,
    instruction_id: int,
    status: str = Form(...)
):
    if status not in ["pending", "in_progress", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    db = SessionLocal()
    try:
        instruction = db.query(WorkInstruction).filter(
            WorkInstruction.id == instruction_id
        ).first()

        if not instruction:
            raise HTTPException(status_code=404)
        if (role not in ["admin", "manager", "ceo"]
            and instruction.assigned_to != user_id
        ):
            raise HTTPException(status_code=403, detail="Not allowed")
        
        instruction.status = status
        try:
            db.commit()
            write_audit_log(
                request=request,
                action="UPDATE_WORK_INSTRUCTION",
                description=f"Updated instruction #{instruction_id} status to {status}",
                target_user_id=request.session.get("user_id"),
            )
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database busy")

        return {"message": "Status updated"}
    finally:
        db.close()
@router.post("/instructions/{instruction_id}/delete")
def delete_work_instruction(request: Request, instruction_id: int):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id:
        raise HTTPException(401)

    db = SessionLocal()
    try:
        instruction = db.query(WorkInstruction).get(instruction_id)
        if not instruction:
            raise HTTPException(404)

        # 🔐 permission: admin OR creator
        if role not in ["admin", "manager", "ceo"] and instruction.created_by != user_id:
            raise HTTPException(403)

        project_id = instruction.project_id

        # 🔥 delete attachments first
        attachments = db.query(Attachment).filter(
            Attachment.work_instruction_id == instruction_id
        ).all()

        for a in attachments:
            if a.file_path:
                path = Path("app") / a.file_path.lstrip("/")
                if os.path.exists(path):
                    os.remove(path)
            db.delete(a)
        db.delete(instruction)
        db.commit()

        write_audit_log(
            request=request,
            action="DELETE_WORK_INSTRUCTION",
            description=f"Deleted instruction #{instruction_id}",
            target_user_id=user_id,
        )

        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    except:
        db.rollback()
        raise
    finally:
        db.close()
