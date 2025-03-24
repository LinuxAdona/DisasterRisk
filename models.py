from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='donor')  # 'admin', 'volunteer', 'donor'
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with donations (for donor)
    donations = db.relationship('Donation', backref='donor', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
        
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class EvacuationCenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'closed'
    contact_person = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    evacuees = db.relationship('Evacuee', backref='evacuation_center', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='evacuation_center', lazy=True)
    donations = db.relationship('Donation', backref='evacuation_center', lazy=True)
    
    def __repr__(self):
        return f'<EvacuationCenter {self.name}>'
    
    @property
    def current_occupancy(self):
        return len(self.evacuees)
    
    @property
    def available_capacity(self):
        return self.capacity - self.current_occupancy

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_name = db.Column(db.String(100), nullable=False)
    head_of_family_id = db.Column(db.Integer, db.ForeignKey('evacuee.id'), nullable=True)
    address = db.Column(db.String(200))
    contact_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    members = db.relationship('Evacuee', backref='family', lazy=True, foreign_keys='Evacuee.family_id')
    head_of_family = db.relationship('Evacuee', lazy=True, foreign_keys=[head_of_family_id])
    
    def __repr__(self):
        return f'<Family {self.family_name}>'
    
    @property
    def member_count(self):
        return len(self.members)

class Evacuee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    status = db.Column(db.String(20), default='present')  # 'present', 'relocated', 'missing', 'deceased'
    special_needs = db.Column(db.Text)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=True)
    evacuation_center_id = db.Column(db.Integer, db.ForeignKey('evacuation_center.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Evacuee {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'food', 'non-food'
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # 'kg', 'pcs', etc.
    expiry_date = db.Column(db.Date, nullable=True)  # Only for food items
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    evacuation_center_id = db.Column(db.Integer, db.ForeignKey('evacuation_center.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'received', 'distributed'
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship with inventory items created from this donation
    inventory_items = db.relationship('InventoryItem', backref='donation', lazy=True)
    
    def __repr__(self):
        return f'<Donation {self.type} - {self.description}>'
    
    @property
    def is_expiring_soon(self):
        if self.type == 'food' and self.expiry_date:
            days_to_expiry = (self.expiry_date - datetime.now().date()).days
            return days_to_expiry <= 7 and days_to_expiry >= 0
        return False
    
    @property
    def is_expired(self):
        if self.type == 'food' and self.expiry_date:
            return self.expiry_date < datetime.now().date()
        return False

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'food', 'non-food'
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # 'kg', 'pcs', etc.
    expiry_date = db.Column(db.Date, nullable=True)  # Only for food items
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=True)
    evacuation_center_id = db.Column(db.Integer, db.ForeignKey('evacuation_center.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # 'available', 'distributed', 'expired'
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<InventoryItem {self.type} - {self.description}>'
    
    @property
    def is_expiring_soon(self):
        if self.type == 'food' and self.expiry_date:
            days_to_expiry = (self.expiry_date - datetime.now().date()).days
            return days_to_expiry <= 7 and days_to_expiry >= 0
        return False
    
    @property
    def is_expired(self):
        if self.type == 'food' and self.expiry_date:
            return self.expiry_date < datetime.now().date()
        return False
