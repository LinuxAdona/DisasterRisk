from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta

from app import db
from models import User, EvacuationCenter, Evacuee, Family, Donation, InventoryItem
from forms import (EvacuationCenterForm, EvacueeForm, FamilyForm, 
                  DonationForm, InventoryItemForm, UserManagementForm, SearchForm)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator for admin-only routes
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('common.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Get counts for dashboard stats
    center_count = EvacuationCenter.query.count()
    active_center_count = EvacuationCenter.query.filter_by(status='active').count()
    evacuee_count = Evacuee.query.count()
    family_count = Family.query.count()
    donation_count = Donation.query.count()
    pending_donation_count = Donation.query.filter_by(status='pending').count()
    inventory_count = InventoryItem.query.count()
    expiring_inventory_count = InventoryItem.query.filter(
        InventoryItem.type == 'food',
        InventoryItem.expiry_date <= (datetime.now() + timedelta(days=7)),
        InventoryItem.expiry_date >= datetime.now()
    ).count()
    
    # Get recent data for display in dashboard
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_evacuees = Evacuee.query.order_by(Evacuee.created_at.desc()).limit(5).all()
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(5).all()
    recent_centers = EvacuationCenter.query.order_by(EvacuationCenter.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        center_count=center_count,
        active_center_count=active_center_count,
        evacuee_count=evacuee_count,
        family_count=family_count,
        donation_count=donation_count,
        pending_donation_count=pending_donation_count,
        inventory_count=inventory_count,
        expiring_inventory_count=expiring_inventory_count,
        recent_users=recent_users,
        recent_evacuees=recent_evacuees,
        recent_donations=recent_donations,
        recent_centers=recent_centers
    )

# Center management routes
@admin_bp.route('/centers', methods=['GET', 'POST'])
@admin_required
def centers():
    centers = EvacuationCenter.query.all()
    
    # Create both forms
    search_form = SearchForm()
    center_form = EvacuationCenterForm()  # Form for the modal dialog
    
    if request.method == 'GET' and request.args.get('query'):
        search_term = request.args.get('query')
        centers = EvacuationCenter.query.filter(
            EvacuationCenter.name.ilike(f'%{search_term}%') | 
            EvacuationCenter.address.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/centers.html', centers=centers, form=center_form, search_form=search_form)

@admin_bp.route('/centers/add', methods=['GET', 'POST'])
@admin_required
def add_center():
    form = EvacuationCenterForm()
    
    if form.validate_on_submit():
        center = EvacuationCenter(
            name=form.name.data,
            address=form.address.data,
            capacity=form.capacity.data,
            status=form.status.data,
            contact_person=form.contact_person.data,
            contact_number=form.contact_number.data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(center)
        db.session.commit()
        flash('Evacuation center added successfully!', 'success')
        return redirect(url_for('admin.centers'))
    
    return render_template('admin/add_center.html', form=form)

@admin_bp.route('/centers/edit/<int:center_id>', methods=['GET', 'POST'])
@admin_required
def edit_center(center_id):
    center = EvacuationCenter.query.get_or_404(center_id)
    form = EvacuationCenterForm(obj=center)
    
    if form.validate_on_submit():
        center.name = form.name.data
        center.address = form.address.data
        center.capacity = form.capacity.data
        center.status = form.status.data
        center.contact_person = form.contact_person.data
        center.contact_number = form.contact_number.data
        center.updated_at = datetime.now()
        
        db.session.commit()
        flash('Evacuation center updated successfully!', 'success')
        return redirect(url_for('admin.centers'))
    
    return render_template('admin/edit_center.html', form=form, center=center)

@admin_bp.route('/centers/delete/<int:center_id>', methods=['POST'])
@admin_required
def delete_center(center_id):
    center = EvacuationCenter.query.get_or_404(center_id)
    
    # Check if center has evacuees
    if len(center.evacuees) > 0:
        flash('Cannot delete center with evacuees. Please relocate evacuees first.', 'danger')
        return redirect(url_for('admin.centers'))
    
    db.session.delete(center)
    db.session.commit()
    flash('Evacuation center deleted successfully!', 'success')
    return redirect(url_for('admin.centers'))

# Evacuee management routes
@admin_bp.route('/evacuees', methods=['GET', 'POST'])
@admin_required
def evacuees():
    evacuees = Evacuee.query.all()
    
    # Create both forms
    search_form = SearchForm()
    evacuee_form = EvacueeForm()  # Form for the modal dialog
    
    # Load families and centers for dropdowns
    evacuee_form.family_id.choices = [(0, 'No Family')] + [(f.id, f.family_name) for f in Family.query.all()]
    evacuee_form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if request.method == 'GET' and request.args.get('query'):
        search_term = request.args.get('query')
        evacuees = Evacuee.query.filter(
            Evacuee.first_name.ilike(f'%{search_term}%') | 
            Evacuee.last_name.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/evacuees.html', evacuees=evacuees, form=evacuee_form, search_form=search_form)

@admin_bp.route('/evacuees/add', methods=['GET', 'POST'])
@admin_required
def add_evacuee():
    form = EvacueeForm()
    
    # Load families and centers for dropdowns
    form.family_id.choices = [(0, 'No Family')] + [(f.id, f.family_name) for f in Family.query.all()]
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if form.validate_on_submit():
        # Process family_id (handle the 0 case)
        family_id = form.family_id.data if form.family_id.data != 0 else None
        
        evacuee = Evacuee(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            status=form.status.data,
            special_needs=form.special_needs.data,
            family_id=family_id,
            evacuation_center_id=form.evacuation_center_id.data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(evacuee)
        db.session.commit()
        flash('Evacuee added successfully!', 'success')
        return redirect(url_for('admin.evacuees'))
    
    return render_template('admin/add_evacuee.html', form=form)

@admin_bp.route('/evacuees/edit/<int:evacuee_id>', methods=['GET', 'POST'])
@admin_required
def edit_evacuee(evacuee_id):
    evacuee = Evacuee.query.get_or_404(evacuee_id)
    form = EvacueeForm(obj=evacuee)
    
    # Load families and centers for dropdowns
    form.family_id.choices = [(0, 'No Family')] + [(f.id, f.family_name) for f in Family.query.all()]
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if form.validate_on_submit():
        # Process family_id (handle the 0 case)
        family_id = form.family_id.data if form.family_id.data != 0 else None
        
        evacuee.first_name = form.first_name.data
        evacuee.last_name = form.last_name.data
        evacuee.date_of_birth = form.date_of_birth.data
        evacuee.gender = form.gender.data
        evacuee.status = form.status.data
        evacuee.special_needs = form.special_needs.data
        evacuee.family_id = family_id
        evacuee.evacuation_center_id = form.evacuation_center_id.data
        evacuee.updated_at = datetime.now()
        
        db.session.commit()
        flash('Evacuee updated successfully!', 'success')
        return redirect(url_for('admin.evacuees'))
    
    return render_template('admin/edit_evacuee.html', form=form, evacuee=evacuee)

@admin_bp.route('/evacuees/delete/<int:evacuee_id>', methods=['POST'])
@admin_required
def delete_evacuee(evacuee_id):
    evacuee = Evacuee.query.get_or_404(evacuee_id)
    
    # Check if evacuee is head of a family
    family = Family.query.filter_by(head_of_family_id=evacuee.id).first()
    if family:
        flash('Cannot delete evacuee. They are listed as head of a family.', 'danger')
        return redirect(url_for('admin.evacuees'))
    
    db.session.delete(evacuee)
    db.session.commit()
    flash('Evacuee deleted successfully!', 'success')
    return redirect(url_for('admin.evacuees'))

# Family management routes
@admin_bp.route('/families', methods=['GET', 'POST'])
@admin_required
def families():
    families = Family.query.all()
    
    # Create both forms
    search_form = SearchForm()
    family_form = FamilyForm()  # Form for the modal dialog
    
    # Add a blank choice for head of family
    family_form.head_of_family_id.choices = [(0, 'Select Head of Family')] + [
        (e.id, f"{e.first_name} {e.last_name}") for e in Evacuee.query.all()
    ]
    
    if request.method == 'GET' and request.args.get('query'):
        search_term = request.args.get('query')
        families = Family.query.filter(
            Family.family_name.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/families.html', families=families, form=family_form, search_form=search_form)

@admin_bp.route('/families/add', methods=['GET', 'POST'])
@admin_required
def add_family():
    form = FamilyForm()
    
    # Add a blank choice for head of family
    form.head_of_family_id.choices = [(0, 'Select Head of Family')] + [
        (e.id, f"{e.first_name} {e.last_name}") for e in Evacuee.query.all()
    ]
    
    if form.validate_on_submit():
        # Process head_of_family_id (handle the 0 case)
        head_of_family_id = form.head_of_family_id.data if form.head_of_family_id.data != 0 else None
        
        family = Family(
            family_name=form.family_name.data,
            head_of_family_id=head_of_family_id,
            address=form.address.data,
            contact_number=form.contact_number.data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(family)
        db.session.commit()
        
        # If a head of family was selected, update their family_id
        if head_of_family_id:
            head = Evacuee.query.get(head_of_family_id)
            if head:
                head.family_id = family.id
                db.session.commit()
        
        flash('Family added successfully!', 'success')
        return redirect(url_for('admin.families'))
    
    return render_template('admin/add_family.html', form=form)

@admin_bp.route('/families/edit/<int:family_id>', methods=['GET', 'POST'])
@admin_required
def edit_family(family_id):
    family = Family.query.get_or_404(family_id)
    form = FamilyForm(obj=family)
    
    # Add a blank choice for head of family
    form.head_of_family_id.choices = [(0, 'Select Head of Family')] + [
        (e.id, f"{e.first_name} {e.last_name}") for e in Evacuee.query.all()
    ]
    
    if form.validate_on_submit():
        # Process head_of_family_id (handle the 0 case)
        head_of_family_id = form.head_of_family_id.data if form.head_of_family_id.data != 0 else None
        
        # If head of family is changing, update the old head's family_id if needed
        if family.head_of_family_id and family.head_of_family_id != head_of_family_id:
            old_head = Evacuee.query.get(family.head_of_family_id)
            if old_head and old_head.family_id == family.id:
                old_head.family_id = None
        
        family.family_name = form.family_name.data
        family.head_of_family_id = head_of_family_id
        family.address = form.address.data
        family.contact_number = form.contact_number.data
        family.updated_at = datetime.now()
        
        db.session.commit()
        
        # If a head of family was selected, update their family_id
        if head_of_family_id:
            head = Evacuee.query.get(head_of_family_id)
            if head:
                head.family_id = family.id
                db.session.commit()
        
        flash('Family updated successfully!', 'success')
        return redirect(url_for('admin.families'))
    
    return render_template('admin/edit_family.html', form=form, family=family)

@admin_bp.route('/families/delete/<int:family_id>', methods=['POST'])
@admin_required
def delete_family(family_id):
    family = Family.query.get_or_404(family_id)
    
    # Check if family has members
    if len(family.members) > 0:
        flash('Cannot delete family with members. Please remove members first.', 'danger')
        return redirect(url_for('admin.families'))
    
    db.session.delete(family)
    db.session.commit()
    flash('Family deleted successfully!', 'success')
    return redirect(url_for('admin.families'))

# Donation management routes
@admin_bp.route('/donations', methods=['GET', 'POST'])
@admin_required
def donations():
    donations = Donation.query.all()
    
    # Create both forms
    search_form = SearchForm()
    donation_form = DonationForm()  # Form for the modal dialog
    
    # Load centers for dropdown
    donation_form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if request.method == 'GET' and request.args.get('query'):
        search_term = request.args.get('query')
        donations = Donation.query.filter(
            Donation.description.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/donations.html', donations=donations, form=donation_form, search_form=search_form)

@admin_bp.route('/donations/add', methods=['GET', 'POST'])
@admin_required
def add_donation():
    form = DonationForm()
    
    # Load centers for dropdown
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if form.validate_on_submit():
        donation = Donation(
            type=form.type.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            expiry_date=form.expiry_date.data if form.type.data == 'food' else None,
            donor_id=current_user.id,
            evacuation_center_id=form.evacuation_center_id.data,
            status='pending',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(donation)
        db.session.commit()
        flash('Donation added successfully!', 'success')
        return redirect(url_for('admin.donations'))
    
    return render_template('admin/add_donation.html', form=form)

@admin_bp.route('/donations/update-status/<int:donation_id>', methods=['POST'])
@admin_required
def update_donation_status(donation_id):
    donation = Donation.query.get_or_404(donation_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'received', 'distributed']:
        donation.status = new_status
        donation.updated_at = datetime.now()
        
        # If status is changed to 'received', create inventory items
        if new_status == 'received' and len(donation.inventory_items) == 0:
            inventory_item = InventoryItem(
                type=donation.type,
                description=donation.description,
                quantity=donation.quantity,
                unit=donation.unit,
                expiry_date=donation.expiry_date,
                donation_id=donation.id,
                evacuation_center_id=donation.evacuation_center_id,
                status='available',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(inventory_item)
        
        db.session.commit()
        flash('Donation status updated successfully!', 'success')
    else:
        flash('Invalid status.', 'danger')
    
    return redirect(url_for('admin.donations'))

# Inventory management routes
@admin_bp.route('/inventory', methods=['GET', 'POST'])
@admin_required
def inventory():
    inventory_items = InventoryItem.query.all()
    
    # Create both forms
    search_form = SearchForm()
    inventory_form = InventoryItemForm()  # Form for the modal dialog
    
    # Load centers for dropdown
    inventory_form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if request.method == 'GET' and request.args.get('query'):
        search_term = request.args.get('query')
        inventory_items = InventoryItem.query.filter(
            InventoryItem.description.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/inventory.html', inventory_items=inventory_items, form=inventory_form, search_form=search_form)

@admin_bp.route('/inventory/add', methods=['GET', 'POST'])
@admin_required
def add_inventory_item():
    form = InventoryItemForm()
    
    # Load centers for dropdown
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if form.validate_on_submit():
        item = InventoryItem(
            type=form.type.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            expiry_date=form.expiry_date.data if form.type.data == 'food' else None,
            evacuation_center_id=form.evacuation_center_id.data,
            status=form.status.data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(item)
        db.session.commit()
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('admin.inventory'))
    
    return render_template('admin/add_inventory_item.html', form=form)

@admin_bp.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_required
def edit_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    form = InventoryItemForm(obj=item)
    
    # Load centers for dropdown
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.all()]
    
    if form.validate_on_submit():
        item.type = form.type.data
        item.description = form.description.data
        item.quantity = form.quantity.data
        item.unit = form.unit.data
        item.expiry_date = form.expiry_date.data if form.type.data == 'food' else None
        item.evacuation_center_id = form.evacuation_center_id.data
        item.status = form.status.data
        item.updated_at = datetime.now()
        
        db.session.commit()
        flash('Inventory item updated successfully!', 'success')
        return redirect(url_for('admin.inventory'))
    
    return render_template('admin/edit_inventory_item.html', form=form, item=item)

@admin_bp.route('/inventory/delete/<int:item_id>', methods=['POST'])
@admin_required
def delete_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    
    db.session.delete(item)
    db.session.commit()
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('admin.inventory'))

# User management routes
@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    users = User.query.all()
    
    # Create search form
    search_form = SearchForm()
    
    if request.method == 'GET' and request.args.get('query'):
        search_term = request.args.get('query')
        users = User.query.filter(
            User.username.ilike(f'%{search_term}%') | 
            User.email.ilike(f'%{search_term}%') |
            User.first_name.ilike(f'%{search_term}%') |
            User.last_name.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/users.html', users=users, search_form=search_form)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserManagementForm(obj=user)
    
    if form.validate_on_submit():
        # Prevent changing admin role if it's the last admin
        if user.role == 'admin' and form.role.data != 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                flash('Cannot change role. This is the last admin user.', 'danger')
                return redirect(url_for('admin.users'))
        
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/activate/<int:user_id>', methods=['POST'])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'User {user.username} has been activated.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/deactivate/<int:user_id>', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating the last admin
    if user.role == 'admin':
        active_admins = User.query.filter_by(role='admin', is_active=True).count()
        if active_admins <= 1:
            flash('Cannot deactivate the last admin user.', 'danger')
            return redirect(url_for('admin.users'))
    
    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} has been deactivated.', 'danger')
    return redirect(url_for('admin.users'))