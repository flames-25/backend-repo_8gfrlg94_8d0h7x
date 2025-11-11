import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import create_document, get_documents
from schemas import Lead
import requests

app = FastAPI(title="A Plus Charge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "A Plus Charge Backend Running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

class LeadIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    source: Optional[str] = "website"
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

@app.post("/api/leads")
def create_lead(lead: LeadIn):
    """
    Store lead in MongoDB and send auto-response email if configured.
    Set environment variables for email:
    - MAILGUN_API_KEY and MAILGUN_DOMAIN or
    - RESEND_API_KEY
    Also set NOTIFY_EMAIL to receive internal notifications.
    """
    try:
        # Save to DB
        lead_id = create_document("lead", lead.model_dump())

        # Prepare email content
        subject = "Thanks for contacting A Plus Charge"
        html_body = f"""
        <div style='font-family:Inter,Arial,sans-serif'>
        <h2>Hi {lead.name},</h2>
        <p>Thanks for reaching out to A Plus Charge. Our team will get back to you shortly.</p>
        <p><strong>Summary:</strong></p>
        <ul>
            <li>Email: {lead.email}</li>
            {f"<li>Phone: {lead.phone}</li>" if lead.phone else ''}
            {f"<li>Company: {lead.company}</li>" if lead.company else ''}
            {f"<li>City/State: {lead.city or ''} {lead.state or ''}</li>"}
        </ul>
        <p>Regards,<br/>A Plus Charge Team</p>
        </div>
        """

        send_auto_email(to_email=lead.email, subject=subject, html=html_body)

        # Internal notification
        notify_email = os.getenv("NOTIFY_EMAIL")
        if notify_email:
            send_auto_email(
                to_email=notify_email,
                subject=f"New Lead: {lead.name}",
                html=f"New website lead:<br/><pre>{lead.model_dump()}</pre>"
            )

        return {"status": "success", "id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def send_auto_email(to_email: str, subject: str, html: str):
    """Send email using Mailgun or Resend if API keys are set. Silently no-op if none."""
    resend_api_key = os.getenv("RESEND_API_KEY")
    mailgun_api_key = os.getenv("MAILGUN_API_KEY")
    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    from_email = os.getenv("FROM_EMAIL", "noreply@apluscharge.com")

    try:
        if resend_api_key:
            # Resend API
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"},
                json={
                    "from": f"A Plus Charge <{from_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html
                },
                timeout=10,
            )
            resp.raise_for_status()
            return
        if mailgun_api_key and mailgun_domain:
            # Mailgun API
            resp = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=("api", mailgun_api_key),
                data={
                    "from": f"A Plus Charge <{from_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return
    except Exception:
        # We don't fail lead creation if email fails
        pass


# Simple ROI calculation logic for EV charger installations
class ROICalcIn(BaseModel):
    daily_sessions: float
    avg_kwh_per_session: float
    tariff_per_kwh: float
    cost_per_kwh: float
    station_cost: float
    opex_per_month: float = 0

class ROICalcOut(BaseModel):
    monthly_revenue: float
    monthly_cost: float
    monthly_profit: float
    payback_months: Optional[float]

@app.post("/api/roi", response_model=ROICalcOut)
def calculate_roi(payload: ROICalcIn):
    sessions_per_month = payload.daily_sessions * 30
    energy_sold = sessions_per_month * payload.avg_kwh_per_session
    revenue = energy_sold * payload.tariff_per_kwh
    energy_cost = energy_sold * payload.cost_per_kwh
    monthly_cost = energy_cost + payload.opex_per_month
    profit = revenue - monthly_cost
    payback_months = None
    if profit > 0 and payload.station_cost > 0:
        payback_months = round(payload.station_cost / profit, 2)
    return ROICalcOut(
        monthly_revenue=round(revenue, 2),
        monthly_cost=round(monthly_cost, 2),
        monthly_profit=round(profit, 2),
        payback_months=payback_months,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
