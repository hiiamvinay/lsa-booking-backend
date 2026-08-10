from datetime import datetime, timezone

from app import create_app
from app.extensions import db
from app.models.parent import Parent
from app.models.lsa import LSAProfile
from app.models.skill import Skill
from app.models.booking import BookingRequest            



def seed_database():
    app = create_app()

    with app.app_context():

        # -------------------------------------------------
        # 1. Prevent accidental duplicate seed data
        # -------------------------------------------------
        if Parent.query.first():
            print("Database already contains data.")
            print("Seed operation skipped.")
            return

        # -------------------------------------------------
        # 2. Create Skills
        # -------------------------------------------------
        skill_names = [
            "Autism",
            "Dyslexia",
            "ADHD",
            "Reading Support",
            "Mathematics",
            "Speech Support",
        ]

        skills = {}

        for name in skill_names:
            skill = Skill(name=name)
            db.session.add(skill)
            skills[name] = skill

        # Flush so Skill objects receive database IDs
        db.session.flush()

        # -------------------------------------------------
        # 3. Create Parents
        # -------------------------------------------------
        parents = [
            Parent(
                name="Rahul Sharma",
                email="rahul@example.com",
                phone="9876543210",
            ),
            Parent(
                name="Priya Verma",
                email="priya@example.com",
                phone="9876543211",
            ),
            Parent(
                name="Amit Patel",
                email="amit@example.com",
                phone="9876543212",
            ),
        ]

        db.session.add_all(parents)

        # -------------------------------------------------
        # 4. Create LSA Profiles
        # -------------------------------------------------
        lsa_1 = LSAProfile(
            name="Amit Kumar",
            email="amit.lsa@example.com",
            hourly_rate=800,
            is_active=True,
        )

        lsa_2 = LSAProfile(
            name="Neha Singh",
            email="neha.lsa@example.com",
            hourly_rate=900,
            is_active=True,
        )

        lsa_3 = LSAProfile(
            name="Ravi Mehta",
            email="ravi.lsa@example.com",
            hourly_rate=750,
            is_active=True,
        )

        lsa_4 = LSAProfile(
            name="Sneha Patel",
            email="sneha.lsa@example.com",
            hourly_rate=850,
            is_active=True,
        )

        # -------------------------------------------------
        # 5. Assign skills to LSAs
        # -------------------------------------------------

        lsa_1.skills = [
            skills["Autism"],
            skills["Reading Support"],
        ]

        lsa_2.skills = [
            skills["Dyslexia"],
            skills["Mathematics"],
        ]

        lsa_3.skills = [
            skills["Autism"],
            skills["ADHD"],
            skills["Reading Support"],
        ]

        lsa_4.skills = [
            skills["Speech Support"],
            skills["Autism"],
        ]

        db.session.add_all([
            lsa_1,
            lsa_2,
            lsa_3,
            lsa_4,
        ])

        # -------------------------------------------------
        # 6. Commit Parent, LSA and Skill data
        # -------------------------------------------------

        db.session.commit()

        print("Database seeded successfully!")
        print()
        print("Created:")
        print(f"  Parents: {len(parents)}")
        print(f"  Skills: {len(skills)}")
        print(f" LSA Profiles: {4}")


if __name__ == "__main__":
    seed_database()