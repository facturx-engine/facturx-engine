import os
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import nacl.signing
import nacl.encoding

"""
Low-Touch Sales Automation for Factur-X Engine.
This is a standalone webhook listener designed to be deployed on AWS Lambda, Vercel, or a tiny VPS.
It listens to Lemon Squeezy order webhooks, generates an Ed25519 License Key, and emails it to the customer.
"""

app = FastAPI(title="Factur-X Lemon Squeezy Webhook")

# --- SECRETS (Configure in Environment Variables) ---
LEMON_SQUEEZY_WEBHOOK_SECRET = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "super-secret-webhook-key")
# The Private Key for Ed25519 (Must exactly match the verified public key in Factur-X Engine)
ED25519_PRIVATE_KEY_HEX = os.getenv("ED25519_PRIVATE_KEY_HEX") 

def verify_lemon_squeezy_signature(payload: bytes, signature: str) -> bool:
    """Verifies the webhook signature from Lemon Squeezy."""
    mac = hmac.new(LEMON_SQUEEZY_WEBHOOK_SECRET.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

def generate_license_key(customer_name: str, tier: str, days_valid: int) -> str:
    """Generates an Ed25519 signed license key in Base64."""
    if not ED25519_PRIVATE_KEY_HEX:
        raise ValueError("Server missing ED25519_PRIVATE_KEY_HEX")
        
    signing_key = nacl.signing.SigningKey(ED25519_PRIVATE_KEY_HEX, encoder=nacl.encoding.HexEncoder)
    
    expiry_date = datetime.now(timezone.utc) + timedelta(days=days_valid)
    
    payload = {
        "sub": customer_name,
        "tier": tier, 
        "exp": expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    signed_payload = signing_key.sign(payload_json.encode('utf-8'))
    return base64.b64encode(signed_payload).decode('utf-8')

def send_license_email(email: str, license_key: str, tier: str):
    """
    Simulated Email Delivery.
    In production, hook this to Resend, Sendgrid, or Postmark.
    """
    subject = f"Your Factur-X Engine {tier} License Key"
    body = f"""
    Welcome to Factur-X Engine!
    
    Here is your air-gapped license key for the {tier} Edition:
    
    {license_key}
    
    To activate your Docker container, inject it as an environment variable:
    docker run -e LICENSE_KEY='{license_key}' facturxengine/facturx-engine
    
    Documentation: https://facturx-engine.github.io/
    """
    print(f"📧 EMAILING {email}...\nSubject: {subject}\nBody: {body}")
    # TODO: Implement actual SMTP/API email sending here.

@app.post("/webhooks/lemon-squeezy")
async def handle_lemon_squeezy_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives events from Lemon Squeezy (e.g. order_created, subscription_created).
    """
    signature = request.headers.get("X-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Signature header")
        
    payload_bytes = await request.body()
    
    if not verify_lemon_squeezy_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    try:
        data = json.loads(payload_bytes)
        event_name = data.get("meta", {}).get("event_name")
        
        # We only care about new orders
        if event_name == "order_created":
            attributes = data["data"]["attributes"]
            customer_email = attributes["user_email"]
            customer_name = attributes["user_name"]
            first_order_item = attributes.get("first_order_item", {})
            product_name = first_order_item.get("product_name", "").lower()
            
            # Tier Routing Logic (Based on Lemon Squeezy Product Name)
            if any(x in product_name for x in ["evaluation", "trial", "test"]):
                tier = "Evaluation"
                days_valid = 30
            elif "enterprise" in product_name:
                tier = "Enterprise"
                days_valid = 365
            elif "pro" in product_name or "business" in product_name:
                tier = "Business"
                days_valid = 365
            else:
                # Default fallback
                tier = "Business"
                days_valid = 365
                
            # Generate Key
            license_key = generate_license_key(customer_name, tier, days_valid)
            
            # Send Email asynchronously so we return 200 OK fast to Lemon Squeezy
            background_tasks.add_task(send_license_email, customer_email, license_key, tier)
            
            return {"status": "success", "message": "License key generated and queued for delivery"}
            
    except Exception as e:
        print(f"Webhook Error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")
        
    return {"status": "ignored", "message": "Event not handled"}

# Run locally for testing: uvicorn deploy.lemon_squeezy_webhook:app --reload
