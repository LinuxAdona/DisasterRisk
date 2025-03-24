import uuid
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager

# In-memory storage for the MVP
USERS = {}
EVACUATION_CENTERS = {}
EVACUEES = {}
FAMILIES = {}
DONATIONS = {}
INVENTORY_ITEMS = {}

def init_db():
    """Initialize the in-memory database with an admin user"""
    # Create admin user if it doesn't exist
    if not any(user.role == 'admin' for user in USERS.values()):
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        admin.save()

class User(UserMixin):
    def __init__(self, username=None, email=None, role=None):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = None
        self.role = role  # 'admin', 'volunteer', or 'donor'
        self.created_at = datetime.now()
        self.approved = role == 'admin'  # Admin is auto-approved

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        USERS[self.id] = self
        return self

    @staticmethod
    def get_by_id(user_id):
        return USERS.get(user_id)

    @staticmethod
    def get_by_username(username):
        for user in USERS.values():
            if user.username == username:
                return user
        return None

    @staticmethod
    def get_by_email(email):
        for user in USERS.values():
            if user.email == email:
                return user
        return None

    @staticmethod
    def get_all():
        return list(USERS.values())

    @staticmethod
    def get_all_by_role(role):
        return [user for user in USERS.values() if user.role == role]

    @staticmethod
    def approve_user(user_id):
        user = USERS.get(user_id)
        if user:
            user.approved = True
            return True
        return False


class EvacuationCenter:
    def __init__(self, name=None, address=None, capacity=0, contact=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.address = address
        self.capacity = capacity
        self.contact = contact
        self.active = True
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def save(self):
        self.updated_at = datetime.now()
        EVACUATION_CENTERS[self.id] = self
        return self

    def update(self, data):
        self.name = data.get('name', self.name)
        self.address = data.get('address', self.address)
        self.capacity = data.get('capacity', self.capacity)
        self.contact = data.get('contact', self.contact)
        self.active = data.get('active', self.active)
        self.updated_at = datetime.now()
        EVACUATION_CENTERS[self.id] = self
        return self

    @property
    def current_occupancy(self):
        return len([e for e in EVACUEES.values() if e.center_id == self.id and e.status == 'active'])

    @property
    def occupancy_percentage(self):
        if self.capacity == 0:
            return 0
        return min(round((self.current_occupancy / self.capacity) * 100), 100)

    @staticmethod
    def get_by_id(center_id):
        return EVACUATION_CENTERS.get(center_id)

    @staticmethod
    def get_all(active_only=False):
        if active_only:
            return [c for c in EVACUATION_CENTERS.values() if c.active]
        return list(EVACUATION_CENTERS.values())


class Family:
    def __init__(self, name=None, head_name=None, contact=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.head_name = head_name
        self.contact = contact
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def save(self):
        self.updated_at = datetime.now()
        FAMILIES[self.id] = self
        return self

    def update(self, data):
        self.name = data.get('name', self.name)
        self.head_name = data.get('head_name', self.head_name)
        self.contact = data.get('contact', self.contact)
        self.updated_at = datetime.now()
        FAMILIES[self.id] = self
        return self

    @property
    def members(self):
        return [e for e in EVACUEES.values() if e.family_id == self.id]

    @property
    def member_count(self):
        return len(self.members)

    @staticmethod
    def get_by_id(family_id):
        return FAMILIES.get(family_id)

    @staticmethod
    def get_all():
        return list(FAMILIES.values())


class Evacuee:
    def __init__(self, name=None, age=None, gender=None, family_id=None, center_id=None, special_needs=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.gender = gender
        self.family_id = family_id
        self.center_id = center_id
        self.special_needs = special_needs
        self.status = 'active'  # active, relocated, missing, deceased
        self.arrival_date = datetime.now()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def save(self):
        self.updated_at = datetime.now()
        EVACUEES[self.id] = self
        return self

    def update(self, data):
        self.name = data.get('name', self.name)
        self.age = data.get('age', self.age)
        self.gender = data.get('gender', self.gender)
        self.family_id = data.get('family_id', self.family_id)
        self.center_id = data.get('center_id', self.center_id)
        self.special_needs = data.get('special_needs', self.special_needs)
        self.status = data.get('status', self.status)
        self.updated_at = datetime.now()
        EVACUEES[self.id] = self
        return self

    @property
    def family(self):
        return Family.get_by_id(self.family_id) if self.family_id else None

    @property
    def center(self):
        return EvacuationCenter.get_by_id(self.center_id) if self.center_id else None

    @staticmethod
    def get_by_id(evacuee_id):
        return EVACUEES.get(evacuee_id)

    @staticmethod
    def get_all(status=None, center_id=None):
        evacuees = list(EVACUEES.values())
        if status:
            evacuees = [e for e in evacuees if e.status == status]
        if center_id:
            evacuees = [e for e in evacuees if e.center_id == center_id]
        return evacuees

    @staticmethod
    def get_by_family(family_id):
        return [e for e in EVACUEES.values() if e.family_id == family_id]

    @staticmethod
    def get_by_center(center_id):
        return [e for e in EVACUEES.values() if e.center_id == center_id]


class Donation:
    def __init__(self, donor_id=None, center_id=None, type=None, description=None, quantity=None, expiry_date=None):
        self.id = str(uuid.uuid4())
        self.donor_id = donor_id
        self.center_id = center_id
        self.type = type  # food, clothing, hygiene, medicine, other
        self.description = description
        self.quantity = quantity
        self.expiry_date = expiry_date
        self.status = 'pending'  # pending, received, distributed, expired
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.received_at = None
        self.distributed_at = None

    def save(self):
        self.updated_at = datetime.now()
        DONATIONS[self.id] = self
        return self

    def update(self, data):
        self.donor_id = data.get('donor_id', self.donor_id)
        self.center_id = data.get('center_id', self.center_id)
        self.type = data.get('type', self.type)
        self.description = data.get('description', self.description)
        self.quantity = data.get('quantity', self.quantity)
        self.expiry_date = data.get('expiry_date', self.expiry_date)
        self.status = data.get('status', self.status)
        
        if self.status == 'received' and not self.received_at:
            self.received_at = datetime.now()
        if self.status == 'distributed' and not self.distributed_at:
            self.distributed_at = datetime.now()
            
        self.updated_at = datetime.now()
        DONATIONS[self.id] = self
        return self

    @property
    def donor(self):
        return User.get_by_id(self.donor_id) if self.donor_id else None

    @property
    def center(self):
        return EvacuationCenter.get_by_id(self.center_id) if self.center_id else None

    @property
    def is_expiring_soon(self):
        if not self.expiry_date or self.status in ['distributed', 'expired']:
            return False
        return (self.expiry_date - datetime.now()).days <= 7

    @staticmethod
    def get_by_id(donation_id):
        return DONATIONS.get(donation_id)

    @staticmethod
    def get_all(status=None, donor_id=None, center_id=None, type=None):
        donations = list(DONATIONS.values())
        if status:
            donations = [d for d in donations if d.status == status]
        if donor_id:
            donations = [d for d in donations if d.donor_id == donor_id]
        if center_id:
            donations = [d for d in donations if d.center_id == center_id]
        if type:
            donations = [d for d in donations if d.type == type]
        return donations

    @staticmethod
    def get_expiring_soon():
        now = datetime.now()
        week_from_now = now + timedelta(days=7)
        return [
            d for d in DONATIONS.values() 
            if d.expiry_date and d.expiry_date <= week_from_now 
            and d.status not in ['distributed', 'expired']
        ]


class InventoryItem:
    def __init__(self, center_id=None, type=None, name=None, quantity=None, expiry_date=None):
        self.id = str(uuid.uuid4())
        self.center_id = center_id
        self.type = type  # food, clothing, hygiene, medicine, other
        self.name = name
        self.quantity = quantity
        self.expiry_date = expiry_date
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def save(self):
        self.updated_at = datetime.now()
        INVENTORY_ITEMS[self.id] = self
        return self

    def update(self, data):
        self.center_id = data.get('center_id', self.center_id)
        self.type = data.get('type', self.type)
        self.name = data.get('name', self.name)
        self.quantity = data.get('quantity', self.quantity)
        self.expiry_date = data.get('expiry_date', self.expiry_date)
        self.updated_at = datetime.now()
        INVENTORY_ITEMS[self.id] = self
        return self

    @property
    def center(self):
        return EvacuationCenter.get_by_id(self.center_id) if self.center_id else None

    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        return (self.expiry_date - datetime.now()).days <= 7

    @staticmethod
    def get_by_id(item_id):
        return INVENTORY_ITEMS.get(item_id)

    @staticmethod
    def get_all(center_id=None, type=None):
        items = list(INVENTORY_ITEMS.values())
        if center_id:
            items = [i for i in items if i.center_id == center_id]
        if type:
            items = [i for i in items if i.type == type]
        return items

    @staticmethod
    def get_expiring_soon(center_id=None):
        now = datetime.now()
        week_from_now = now + timedelta(days=7)
        items = [
            i for i in INVENTORY_ITEMS.values() 
            if i.expiry_date and i.expiry_date <= week_from_now
        ]
        if center_id:
            items = [i for i in items if i.center_id == center_id]
        return items


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)
