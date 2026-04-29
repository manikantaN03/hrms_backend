from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.setup.salary_and_deductions.overtime_repo import OvertimePolicyRepository, OvertimeRuleRepository


policy_repo = OvertimePolicyRepository()
rule_repo = OvertimeRuleRepository()


class OvertimePolicyService:
    def list(self, db: Session, business_id: int):
        return policy_repo.list(db, business_id)

    def create(self, db: Session, data):
        # Create policy using explicit business_id injected by caller
        try:
            business_id = data.business_id
        except Exception:
            # If caller passed business_id separately, the endpoint should inject it
            return policy_repo.create(db, data)
        return policy_repo.create(db, data)
    
    def create_with_business(self, db: Session, business_id: int, data):
        payload = data.dict()
        payload["business_id"] = business_id
        return policy_repo.create(db, type('X', (), {'dict': lambda self: payload})())

    def update(self, db: Session, policy_id: int, business_id: int, data):
        obj = policy_repo.get(db, policy_id, business_id)
        if not obj:
            raise HTTPException(404, "Policy not found")
        return policy_repo.update(db, obj, data)

    def delete(self, db: Session, policy_id: int, business_id: int):
        obj = policy_repo.get(db, policy_id, business_id)
        if not obj:
            raise HTTPException(404, "Policy not found")
        return policy_repo.delete(db, obj)


class OvertimeRuleService:
    def list(self, db: Session, policy_id: int, business_id: int):
        return rule_repo.list_by_policy(db, policy_id, business_id)

    def create(self, db: Session, business_id: int, policy_id: int, data):
        # Create an overtime rule using explicit business_id and policy_id
        policy = policy_repo.get(db, policy_id, business_id)
        if not policy:
            raise HTTPException(400, "Referenced overtime policy not found for this business")

        # inject path params into payload dict before creating
        payload = data.dict()
        payload["business_id"] = business_id
        payload["policy_id"] = policy_id
        return rule_repo.create(db, type('X', (), {'dict': lambda self: payload})())

    def update(self, db: Session, rule_id: int, business_id: int, data):
        obj = rule_repo.get(db, rule_id, business_id)
        if not obj:
            raise HTTPException(404, "Rule not found")
        return rule_repo.update(db, obj, data)

    def delete(self, db: Session, rule_id: int, business_id: int):
        obj = rule_repo.get(db, rule_id, business_id)
        if not obj:
            raise HTTPException(404, "Rule not found")
        return rule_repo.delete(db, obj)


policy_service = OvertimePolicyService()
rule_service = OvertimeRuleService()
