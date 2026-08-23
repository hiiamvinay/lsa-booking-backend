from flask import Blueprint, jsonify, request
from sqlalchemy.orm import selectinload

from app.models.lsa import LSAProfile
from app.models.skill import Skill

lsa_bp = Blueprint("lsa", __name__, url_prefix="/api/lsas")


def serialize_lsa(lsa):
    return {
        "id": lsa.id,
        "name": lsa.name,
        "email": lsa.email,
        "hourly_rate": float(lsa.hourly_rate),
        "is_active": lsa.is_active,
        "created_at": lsa.created_at.isoformat(),
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
            }
            for skill in sorted(lsa.skills, key=lambda item: item.name.lower())
        ],
    }


@lsa_bp.get("/search")
def list_lsas():
    skill_name = request.args.get("skill")
    skill_id = request.args.get("skill_id", type=int)
    include_inactive = request.args.get("include_inactive", "").lower() == "true"
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if per_page > 50:
        per_page = 50  

    query = LSAProfile.query.options(selectinload(LSAProfile.skills))

    if not include_inactive:
        query = query.filter(LSAProfile.is_active.is_(True))

    if skill_id is not None:
        query = query.join(LSAProfile.skills).filter(Skill.id == skill_id)
    elif skill_name:
        query = query.join(LSAProfile.skills).filter(Skill.name.ilike(skill_name.strip()))

    lsas = query.order_by(LSAProfile.name.asc()).paginate(page=page, per_page=per_page).items
    return jsonify(
        {
            "data": [serialize_lsa(lsa) for lsa in lsas],
            "count": len(lsas),
            "page": page,
            "per_page": per_page,
        }
    )
