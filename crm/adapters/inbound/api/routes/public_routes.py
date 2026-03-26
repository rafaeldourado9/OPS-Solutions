"""Public routes — no authentication required.

Handles waitlist/beta signup with email confirmation via Resend.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.email.resend_gateway import beta_welcome_email, send_email
from adapters.outbound.persistence.database import get_session
from adapters.outbound.persistence.models.waitlist_model import WaitlistEntry

router = APIRouter(prefix="/api/v1/public", tags=["public"])


class WaitlistRequest(BaseModel):
    email: EmailStr
    name: str = ""
    plan: str = ""
    source: str = "landing"


class WaitlistResponse(BaseModel):
    message: str
    email_sent: bool


@router.post("/waitlist", response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    body: WaitlistRequest,
    session: AsyncSession = Depends(get_session),
):
    """Register email for beta access and send welcome email."""
    # Check duplicate
    existing = await session.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == body.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado na lista de espera.",
        )

    # Save entry
    entry = WaitlistEntry(
        email=body.email,
        name=body.name or None,
        plan=body.plan or None,
        source=body.source or "landing",
    )
    session.add(entry)

    # Send welcome email
    html = beta_welcome_email(name=body.name, plan=body.plan or None)
    email_sent = await send_email(
        to=body.email,
        subject="Bem-vindo ao beta da OPS Solutions! 🎉",
        html=html,
    )

    entry.email_sent = email_sent
    await session.commit()

    return WaitlistResponse(
        message="Cadastro realizado com sucesso! Verifique seu e-mail.",
        email_sent=email_sent,
    )
