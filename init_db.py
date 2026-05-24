"""Initialize PostgreSQL schema and seed sample dietician data.

Run from project root:
    python init_db.py
"""
from __future__ import annotations

from decimal import Decimal

from backend.database import Base, SessionLocal, engine
from backend.models import (  # noqa: F401  - imported for metadata registration
    ActivityLog,
    ChatHistory,
    Consultation,
    DieticianProfile,
    MealLog,
    User,
)
from backend.models.user import UserRole
from backend.utils.auth_utils import hash_password


SAMPLE_DIETICIANS = [
    {
        "name": "Dr. Aarav Mehta",
        "username": "aarav_mehta",
        "email": "aarav@nutrifit.ai",
        "mobile_number": "9810000001",
        "password": "Welcome@123",
        "speciality": "Clinical Nutrition · Diabetes",
        "per_hour_charge": Decimal("1500"),
        "per_two_hour_charge": Decimal("2700"),
        "bio": "10+ years guiding patients with Type 2 diabetes and metabolic syndrome through evidence-based diets.",
        "location": "Bengaluru, IN",
    },
    {
        "name": "Dr. Sara Khan",
        "username": "sara_khan",
        "email": "sara@nutrifit.ai",
        "mobile_number": "9810000002",
        "password": "Welcome@123",
        "speciality": "Sports Nutrition · Weight Training",
        "per_hour_charge": Decimal("1800"),
        "per_two_hour_charge": Decimal("3300"),
        "bio": "Sports dietitian working with amateur athletes and lifters; macro-first, performance-driven plans.",
        "location": "Mumbai, IN",
    },
    {
        "name": "Dr. Priya Nair",
        "username": "priya_nair",
        "email": "priya@nutrifit.ai",
        "mobile_number": "9810000003",
        "password": "Welcome@123",
        "speciality": "PCOS · Hormonal Health",
        "per_hour_charge": Decimal("1700"),
        "per_two_hour_charge": Decimal("3100"),
        "bio": "Helps women manage PCOS, thyroid and hormonal weight gain through low-GI Indian meal plans.",
        "location": "Kochi, IN",
    },
    {
        "name": "Dr. Rohan Iyer",
        "username": "rohan_iyer",
        "email": "rohan@nutrifit.ai",
        "mobile_number": "9810000004",
        "password": "Welcome@123",
        "speciality": "Cardiac · Renal Nutrition",
        "per_hour_charge": Decimal("2000"),
        "per_two_hour_charge": Decimal("3700"),
        "bio": "Hospital-trained dietitian specializing in heart-healthy and kidney-friendly meal planning.",
        "location": "Pune, IN",
    },
]


def main() -> None:
    print("Creating tables (if not exist) …")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == UserRole.dietician).count()
        if existing >= len(SAMPLE_DIETICIANS):
            print(f"Already have {existing} dieticians, skipping seed.")
            return

        for d in SAMPLE_DIETICIANS:
            if db.query(User).filter(User.email == d["email"]).first():
                continue
            user = User(
                name=d["name"],
                username=d["username"],
                email=d["email"],
                mobile_number=d["mobile_number"],
                hashed_password=hash_password(d["password"]),
                role=UserRole.dietician,
            )
            db.add(user)
            db.flush()
            db.add(
                DieticianProfile(
                    user_id=user.id,
                    speciality=d["speciality"],
                    per_hour_charge=d["per_hour_charge"],
                    per_two_hour_charge=d["per_two_hour_charge"],
                    bio=d["bio"],
                    location=d["location"],
                    is_available=True,
                )
            )
        db.commit()
        print(f"Seeded {len(SAMPLE_DIETICIANS)} dieticians.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
