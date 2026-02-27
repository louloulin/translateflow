"""
Payment processing service for Stripe integration.
"""

import os
from typing import Optional, Dict, Any

try:
    import stripe
except ImportError:
    stripe = None

from ModuleFolders.Service.Auth.models import SubscriptionPlan


class PaymentProcessor:
    """Handle payment processing with Stripe."""
    
    def __init__(self):
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if stripe and self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
    
    def create_customer(self, user_id: str, email: str, metadata: Optional[Dict] = None) -> str:
        """Create a Stripe customer for a user."""
        if not stripe:
            raise ValueError("Stripe is not configured")
        
        customer = stripe.Customer.create(
            email=email,
            metadata={
                "user_id": user_id,
                **(metadata or {})
            }
        )
        
        return customer.id
    
    def create_checkout_session(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription."""
        if not stripe:
            raise ValueError("Stripe is not configured")
        
        price_ids = {
            SubscriptionPlan.STARTER: os.getenv("STRIPE_PRICE_STARTER"),
            SubscriptionPlan.PRO: os.getenv("STRIPE_PRICE_PRO"),
            SubscriptionPlan.ENTERPRISE: os.getenv("STRIPE_PRICE_ENTERPRISE"),
        }
        
        price_id = price_ids.get(plan)
        if not price_id:
            raise ValueError(f"No price ID configured for plan: {plan}")
        
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id},
        )
        
        return {
            "session_id": session.id,
            "url": session.url,
        }
    
    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        """Create a Stripe customer portal session."""
        if not stripe:
            raise ValueError("Stripe is not configured")
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        
        return session.url
