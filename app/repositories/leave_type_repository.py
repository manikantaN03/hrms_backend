from sqlalchemy.orm import Session
from app.models.leave_type import LeaveType


class LeaveTypeRepository:

    def get_all(self, db: Session, business_id: int = None):
        query = db.query(LeaveType)
        if business_id:
            query = query.filter(LeaveType.business_id == business_id)
        return query.order_by(LeaveType.id).all()

    def get_by_id(self, db: Session, leave_type_id: int, business_id: int = None):
        query = db.query(LeaveType).filter(LeaveType.id == leave_type_id)
        if business_id:
            query = query.filter(LeaveType.business_id == business_id)
        return query.first()

    def get_by_alias(self, db: Session, alias: str, business_id: int = None):
        query = db.query(LeaveType).filter(LeaveType.alias == alias)
        if business_id:
            query = query.filter(LeaveType.business_id == business_id)
        return query.first()

    def create(self, db: Session, data: dict):
        leave = LeaveType(**data)
        db.add(leave)
        db.commit()
        db.refresh(leave)
        return leave

    def update(self, db: Session, leave: LeaveType, data: dict):
        for key, value in data.items():
            setattr(leave, key, value)
        db.commit()
        db.refresh(leave)
        return leave

    def delete(self, db: Session, leave: LeaveType):
        db.delete(leave)
        db.commit()
        return True
