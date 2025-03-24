from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta

from app import db
from models import User, EvacuationCenter, Evacuee, Family, Donation, InventoryItem
from forms import (EvacuationCenterForm, EvacueeForm, FamilyForm, 
                  DonationForm, InventoryItemForm, UserManagementForm, SearchForm)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Ensure user is admin
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('common.index'))
    
    # Get summary data for dashboard
    total_centers = EvacuationCenter.query.count()
    total_evacuees = Evacuee.query.count()
    total_families = Family.query.count()
    total_donations = Donation.query.count()
    
    # Get recent activities
    recent_centers = EvacuationCenter.query.order_by(EvacuationCenter.created_at.desc()).limit(5).all()
    recent_evacuees = Evacuee.query.order_by(Evacuee.created_at.desc()).limit(5).all()
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(5).all()
    
    # Get users pending approval
    pending_users = User.query.filter_by(is_active=False).all()
    
    # Get centers at capacity
    centers_at_capacity = []
    for center in EvacuationCenter.query.all():
        if center.current_occupancy >= center.capacity * 0.9:  # 90% or more capacity
            centers_at_capacity.append(center)
    
    # Get soon-to-expire food items
    expiring_food = InventoryItem.query.filter(
        InventoryItem.type == 'food',
        InventoryItem.expiry_date <= (datetime.now() + timedelta(days=7)).date(),
        InventoryItem.expiry_date >= datetime.now().date(),
        InventoryItem.status == 'available'
    ).order_by(InventoryItem.expiry_date).all()
    
    # Get evacuee count by status
    evacuee_status = db.session.query(
        Evacuee.status, func.count(Evacuee.id)
    ).group_by(Evacuee.status).all()
    
    # Get donation count by type
    donation_types = db.session.query(
        Donation.type, func.count(Donation.id)
    ).group_by(Donation.type).all()
    
    return render_template(
        'admin/dashboard.html', 
        total_centers=total_centers,
        total_evacuees=total_evacuees,
        total_families=total_families,
        total_donations=total_donations,
        recent_centers=recent_centers,
        recent_evacuees=recent_evacuees,
        recent_donations=recent_donations,
        pending_users=pending_users,
        centers_at_capacity=centers_at_capacity,
        expiring_food=expiring_food,
        evacuee_status=dict(evacuee_status),
        donation_types=dict(donation_types)
    )

# Evacuation Center Management
@admin_bp.route('/centers')
@login_required
def centers():
    centers = EvacuationCenter.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        centers = EvacuationCenter.query.filter(
            EvacuationCenter.name.ilike(f'%{search_term}%') | 
            EvacuationCenter.address.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/centers.html', centers=centers, form=form)

@admin_bp.route('/centers/add', methods=['GET', 'POST'])
@login_required
def add_center():
    form = EvacuationCenterForm()
    
    if form.validate_on_submit():
        center = EvacuationCenter(
            name=form.name.data,
            address=form.address.data,
            capacity=form.capacity.data,
            status=form.status.data,
            contact_person=form.contact_person.data,
            contact_number=form.contact_number.data
        )
        
        db.session.add(center)
        db.session.commit()
        
        flash('Evacuation center added successfully!', 'success')
        return redirect(url_for('admin.centers'))
    
    return render_template('admin/centers.html', form=form, adding=True)

@admin_bp.route('/centers/edit/<int:center_id>', methods=['GET', 'POST'])
@login_required
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
        
        db.session.commit()
        
        flash('Evacuation center updated successfully!', 'success')
        return redirect(url_for('admin.centers'))
    
    return render_template('admin/centers.html', form=form, editing=True, center=center)

@admin_bp.route('/centers/delete/<int:center_id>', methods=['POST'])
@login_required
def delete_center(center_id):
    center = EvacuationCenter.query.get_or_404(center_id)
    
    # Check if center has evacuees
    if center.evacuees:
        flash('Cannot delete center with evacuees. Please relocate evacuees first.', 'danger')
        return redirect(url_for('admin.centers'))
    
    db.session.delete(center)
    db.session.commit()
    
    flash('Evacuation center deleted successfully!', 'success')
    return redirect(url_for('admin.centers'))

# Evacuee Management
@admin_bp.route('/evacuees')
@login_required
def evacuees():
    evacuees = Evacuee.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        evacuees = Evacuee.query.filter(
            Evacuee.first_name.ilike(f'%{search_term}%') | 
            Evacuee.last_name.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/evacuees.html', evacuees=evacuees, form=form)

@admin_bp.route('/evacuees/add', methods=['GET', 'POST'])
@login_required
def add_evacuee():
    form = EvacueeForm()
    
    # Populate dropdown options
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.filter_by(status='active').all()]
    form.family_id.choices = [(0, 'None')] + [(f.id, f.family_name) for f in Family.query.all()]
    
    if form.validate_on_submit():
        family_id = form.family_id.data if form.family_id.data != 0 else None
        
        evacuee = Evacuee(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            status=form.status.data,
            special_needs=form.special_needs.data,
            family_id=family_id,
            evacuation_center_id=form.evacuation_center_id.data
        )
        
        db.session.add(evacuee)
        db.session.commit()
        
        flash('Evacuee added successfully!', 'success')
        return redirect(url_for('admin.evacuees'))
    
    return render_template('admin/evacuees.html', form=form, adding=True)

@admin_bp.route('/evacuees/edit/<int:evacuee_id>', methods=['GET', 'POST'])
@login_required
def edit_evacuee(evacuee_id):
    evacuee = Evacuee.query.get_or_404(evacuee_id)
    form = EvacueeForm(obj=evacuee)
    
    # Populate dropdown options
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.filter_by(status='active').all()]
    form.family_id.choices = [(0, 'None')] + [(f.id, f.family_name) for f in Family.query.all()]
    
    if form.validate_on_submit():
        evacuee.first_name = form.first_name.data
        evacuee.last_name = form.last_name.data
        evacuee.date_of_birth = form.date_of_birth.data
        evacuee.gender = form.gender.data
        evacuee.status = form.status.data
        evacuee.special_needs = form.special_needs.data
        evacuee.family_id = form.family_id.data if form.family_id.data != 0 else None
        evacuee.evacuation_center_id = form.evacuation_center_id.data
        
        db.session.commit()
        
        flash('Evacuee updated successfully!', 'success')
        return redirect(url_for('admin.evacuees'))
    
    # Set correct family value for the form
    if evacuee.family_id:
        form.family_id.data = evacuee.family_id
    else:
        form.family_id.data = 0
    
    return render_template('admin/evacuees.html', form=form, editing=True, evacuee=evacuee)

@admin_bp.route('/evacuees/delete/<int:evacuee_id>', methods=['POST'])
@login_required
def delete_evacuee(evacuee_id):
    evacuee = Evacuee.query.get_or_404(evacuee_id)
    
    # Check if evacuee is a head of family
    families_headed = Family.query.filter_by(head_of_family_id=evacuee_id).all()
    if families_headed:
        flash('Cannot delete evacuee who is head of family. Please update family records first.', 'danger')
        return redirect(url_for('admin.evacuees'))
    
    db.session.delete(evacuee)
    db.session.commit()
    
    flash('Evacuee deleted successfully!', 'success')
    return redirect(url_for('admin.evacuees'))

# Family Management
@admin_bp.route('/families')
@login_required
def families():
    families = Family.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        families = Family.query.filter(Family.family_name.ilike(f'%{search_term}%')).all()
    
    return render_template('admin/evacuees.html', families=families, form=form, show_families=True)

@admin_bp.route('/families/add', methods=['GET', 'POST'])
@login_required
def add_family():
    form = FamilyForm()
    
    # Populate head of family dropdown options
    form.head_of_family_id.choices = [(0, 'None')] + [(e.id, f"{e.first_name} {e.last_name}") for e in Evacuee.query.all()]
    
    if form.validate_on_submit():
        head_of_family_id = form.head_of_family_id.data if form.head_of_family_id.data != 0 else None
        
        family = Family(
            family_name=form.family_name.data,
            head_of_family_id=head_of_family_id,
            address=form.address.data,
            contact_number=form.contact_number.data
        )
        
        db.session.add(family)
        db.session.commit()
        
        flash('Family added successfully!', 'success')
        return redirect(url_for('admin.families'))
    
    return render_template('admin/evacuees.html', form=form, adding_family=True, show_families=True)

@admin_bp.route('/families/edit/<int:family_id>', methods=['GET', 'POST'])
@login_required
def edit_family(family_id):
    family = Family.query.get_or_404(family_id)
    form = FamilyForm(obj=family)
    
    # Populate head of family dropdown options
    form.head_of_family_id.choices = [(0, 'None')] + [(e.id, f"{e.first_name} {e.last_name}") for e in Evacuee.query.all()]
    
    if form.validate_on_submit():
        family.family_name = form.family_name.data
        family.head_of_family_id = form.head_of_family_id.data if form.head_of_family_id.data != 0 else None
        family.address = form.address.data
        family.contact_number = form.contact_number.data
        
        db.session.commit()
        
        flash('Family updated successfully!', 'success')
        return redirect(url_for('admin.families'))
    
    # Set correct head of family value for the form
    if family.head_of_family_id:
        form.head_of_family_id.data = family.head_of_family_id
    else:
        form.head_of_family_id.data = 0
    
    return render_template('admin/evacuees.html', form=form, editing_family=True, family=family, show_families=True)

@admin_bp.route('/families/delete/<int:family_id>', methods=['POST'])
@login_required
def delete_family(family_id):
    family = Family.query.get_or_404(family_id)
    
    # Update evacuees belonging to this family
    for evacuee in family.members:
        evacuee.family_id = None
    
    db.session.delete(family)
    db.session.commit()
    
    flash('Family deleted successfully!', 'success')
    return redirect(url_for('admin.families'))

# Donation Management
@admin_bp.route('/donations')
@login_required
def donations():
    donations = Donation.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        donations = Donation.query.filter(Donation.description.ilike(f'%{search_term}%')).all()
    
    return render_template('admin/donations.html', donations=donations, form=form)

@admin_bp.route('/donations/add', methods=['GET', 'POST'])
@login_required
def add_donation():
    form = DonationForm()
    
    # Populate evacuation center dropdown options
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        donation = Donation(
            type=form.type.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            expiry_date=form.expiry_date.data if form.type.data == 'food' else None,
            donor_id=current_user.id,
            evacuation_center_id=form.evacuation_center_id.data,
            status='received'  # Admin directly adds as received
        )
        
        db.session.add(donation)
        db.session.commit()
        
        # Create inventory item from this donation
        inventory_item = InventoryItem(
            type=donation.type,
            description=donation.description,
            quantity=donation.quantity,
            unit=donation.unit,
            expiry_date=donation.expiry_date,
            donation_id=donation.id,
            evacuation_center_id=donation.evacuation_center_id,
            status='available'
        )
        
        db.session.add(inventory_item)
        db.session.commit()
        
        flash('Donation added and inventory updated successfully!', 'success')
        return redirect(url_for('admin.donations'))
    
    return render_template('admin/donations.html', form=form, adding=True)

@admin_bp.route('/donations/update/<int:donation_id>', methods=['POST'])
@login_required
def update_donation_status(donation_id):
    donation = Donation.query.get_or_404(donation_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'received', 'distributed']:
        donation.status = new_status
        db.session.commit()
        
        flash('Donation status updated successfully!', 'success')
    else:
        flash('Invalid status!', 'danger')
    
    return redirect(url_for('admin.donations'))

# Inventory Management
@admin_bp.route('/inventory')
@login_required
def inventory():
    inventory_items = InventoryItem.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        inventory_items = InventoryItem.query.filter(InventoryItem.description.ilike(f'%{search_term}%')).all()
    
    return render_template('admin/donations.html', inventory_items=inventory_items, form=form, show_inventory=True)

@admin_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory_item():
    form = InventoryItemForm()
    
    # Populate evacuation center dropdown options
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        inventory_item = InventoryItem(
            type=form.type.data,
            description=form.description.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            expiry_date=form.expiry_date.data if form.type.data == 'food' else None,
            evacuation_center_id=form.evacuation_center_id.data,
            status=form.status.data
        )
        
        db.session.add(inventory_item)
        db.session.commit()
        
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('admin.inventory'))
    
    return render_template('admin/donations.html', form=form, adding_inventory=True, show_inventory=True)

@admin_bp.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_inventory_item(item_id):
    inventory_item = InventoryItem.query.get_or_404(item_id)
    form = InventoryItemForm(obj=inventory_item)
    
    # Populate evacuation center dropdown options
    form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.filter_by(status='active').all()]
    
    if form.validate_on_submit():
        inventory_item.type = form.type.data
        inventory_item.description = form.description.data
        inventory_item.quantity = form.quantity.data
        inventory_item.unit = form.unit.data
        inventory_item.expiry_date = form.expiry_date.data if form.type.data == 'food' else None
        inventory_item.evacuation_center_id = form.evacuation_center_id.data
        inventory_item.status = form.status.data
        
        db.session.commit()
        
        flash('Inventory item updated successfully!', 'success')
        return redirect(url_for('admin.inventory'))
    
    return render_template('admin/donations.html', form=form, editing_inventory=True, inventory_item=inventory_item, show_inventory=True)

@admin_bp.route('/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_inventory_item(item_id):
    inventory_item = InventoryItem.query.get_or_404(item_id)
    
    db.session.delete(inventory_item)
    db.session.commit()
    
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('admin.inventory'))

# User Management
@admin_bp.route('/users')
@login_required
def users():
    users = User.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        users = User.query.filter(
            User.username.ilike(f'%{search_term}%') | 
            User.email.ilike(f'%{search_term}%') |
            User.first_name.ilike(f'%{search_term}%') |
            User.last_name.ilike(f'%{search_term}%')
        ).all()
    
    return render_template('admin/users.html', users=users, form=form)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserManagementForm(obj=user)
    
    if form.validate_on_submit():
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/users.html', form=form, editing=True, user=user)

@admin_bp.route('/users/activate/<int:user_id>', methods=['POST'])
@login_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    user.is_active = True
    db.session.commit()
    
    flash(f'User {user.username} has been activated!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/deactivate/<int:user_id>', methods=['POST'])
@login_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Cannot deactivate oneself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account!', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = False
    db.session.commit()
    
    flash(f'User {user.username} has been deactivated!', 'success')
    return redirect(url_for('admin.users'))
