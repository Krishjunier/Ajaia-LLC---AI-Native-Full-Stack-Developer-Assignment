from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Share, User
from schemas import ShareRequest, ShareResponse, ShareOut
from services.auth_service import get_current_user
from utils.permissions import get_document_or_404, require_owner

router = APIRouter(prefix="/documents", tags=["sharing"])


@router.get("/{doc_id}/shares", response_model=List[ShareOut])
def list_shares(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    require_owner(doc, current_user)
    return [ShareOut(user=s.user, permission=s.permission) for s in doc.shares]


@router.post("/{doc_id}/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def share_document(
    doc_id: int,
    payload: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    require_owner(doc, current_user)

    if payload.permission not in ("viewer", "editor"):
        raise HTTPException(status_code=400, detail="permission must be 'viewer' or 'editor'")

    if payload.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share a document with yourself")

    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    existing = db.query(Share).filter(
        Share.document_id == doc_id, Share.user_id == payload.user_id
    ).first()

    if existing:
        existing.permission = payload.permission
        db.commit()
        db.refresh(existing)
        return ShareResponse(
            document_id=existing.document_id,
            user_id=existing.user_id,
            permission=existing.permission,
        )

    share = Share(document_id=doc_id, user_id=payload.user_id, permission=payload.permission)
    db.add(share)
    db.commit()
    db.refresh(share)
    return ShareResponse(document_id=share.document_id, user_id=share.user_id, permission=share.permission)


@router.delete("/{doc_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    doc_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = get_document_or_404(doc_id, db)
    require_owner(doc, current_user)

    share = db.query(Share).filter(
        Share.document_id == doc_id, Share.user_id == user_id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    db.delete(share)
    db.commit()
