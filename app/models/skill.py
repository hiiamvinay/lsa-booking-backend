from app.extensions import db


class LSASkill(db.Model):
    __tablename__ = "lsa_skills"

    lsa_id = db.Column(
        db.Integer,
        db.ForeignKey("lsa_profiles.id", ondelete="CASCADE"),
        primary_key=True
    )

    skill_id = db.Column(
        db.Integer,
        db.ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True
    )


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True
    )

    lsas = db.relationship(
        "LSAProfile",
        secondary="lsa_skills",
        back_populates="skills"
    )

    def __repr__(self):
        return f"<Skill {self.name}>"