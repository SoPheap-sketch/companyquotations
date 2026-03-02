from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Form # Added Form
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path as FsPath
from datetime import datetime

from app.db import SessionLocal
from app.models import Attachment, WorkInstruction
from app.utils.audit import write_audit_log
import os

router = APIRouter(prefix="/attachments")

UPLOAD_DIR = FsPath("app/static/uploads/instructions")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/instructions/{instruction_id}/upload")
def upload_instruction_attachment(
    request: Request,
    instruction_id: int,
    file: UploadFile = File(...)
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401)

    db = SessionLocal()
    try:
        instruction = (
            db.query(WorkInstruction)
            .filter(WorkInstruction.id == instruction_id)
            .first()
        )

        if not instruction:
            raise HTTPException(status_code=404, detail="Instruction not found")
        
        filename = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
        real_file_path = UPLOAD_DIR / filename
    
        # FIXED: Removed the "wbthis " typo
        with open(real_file_path, "wb") as f:
            f.write(file.file.read())

        attachment = Attachment(
            project_id=instruction.project_id,    
            work_instruction_id=instruction.id,
            uploaded_by=user_id,
            file_name=file.filename,
            file_path=f"/static/uploads/instructions/{filename}",
            file_type=file.content_type,
        )

        db.add(attachment)
        db.commit()

        write_audit_log(
            request=request,
            action="UPLOAD_ATTACHMENT",
            description=f"Uploaded attachment to instruction #{instruction_id}",
            target_user_id=user_id,
        )

        return RedirectResponse(
            request.headers.get("referer", "/"),
            status_code=303
        )

    finally:
        db.close()

@router.post("/{attachment_id}/delete")
def delete_attachment(request: Request, attachment_id: int):
    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id:
        raise HTTPException(401)

    db = SessionLocal()
    try:
        attachment = db.query(Attachment).get(attachment_id)
        if not attachment:
            raise HTTPException(404)

        if role not in ["admin", "manager", "ceo"] and attachment.uploaded_by != user_id:
            raise HTTPException(403)

        if attachment.file_path:
            real_path = FsPath("app") / attachment.file_path.replace("/static/", "")
            if real_path.exists():
                real_path.unlink()

        db.delete(attachment)
        db.commit()

        write_audit_log(
            request=request,
            action="DELETE_ATTACHMENT",
            description=f"Deleted attachment #{attachment_id}",
            target_user_id=user_id,
        )

        return RedirectResponse(
            request.headers.get("referer", "/"),
            status_code=303
        )
    finally:
        db.close()

@router.get("/{attachment_id}/download")
def download_attachment(request: Request, attachment_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401)

    db = SessionLocal()
    try:
        attachment = db.query(Attachment).get(attachment_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")

        real_path = FsPath("app") / attachment.file_path.lstrip("/")
        if not real_path.exists():
            raise HTTPException(status_code=404, detail="File missing")

        write_audit_log(
            request=request,
            action="DOWNLOAD_ATTACHMENT",
            description=f"Downloaded attachment: {attachment.file_name}",
            target_user_id=user_id,
        )

        return FileResponse(
            path=real_path,
            filename=attachment.file_name,
            media_type=attachment.file_type,
        )

    finally:
        db.close()

@router.post("/{instruction_id}/status")
def update_instruction_status(request: Request, instruction_id: int, status: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401)

    db = SessionLocal()
    try:
        instruction = db.query(WorkInstruction).get(instruction_id)
        if not instruction:
            raise HTTPException(status_code=404)

        instruction.status = status
        db.commit()

        write_audit_log(
            request=request,
            action="UPDATE_STATUS",
            description=f"Changed instruction #{instruction_id} status to {status}",
            target_user_id=user_id,
        )

        # REDIRECT logic to fix the JSON screen issue
        return RedirectResponse(
            url=request.headers.get("referer", f"/projects/{instruction.project_id}"), 
            status_code=303
        )
    finally:
        db.close()