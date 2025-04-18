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

    # Center statistics
    center_count = EvacuationCenter.query.count()
    active_center_count = EvacuationCenter.query.filter_by(status='active').count()

    # Evacuee and family statistics
    evacuee_count = Evacuee.query.count()
    family_count = Family.query.count()

    # Donation statistics
    donation_count = Donation.query.count()
    pending_donation_count = Donation.query.filter_by(status='pending').count()

    # Inventory statistics
    inventory_count = InventoryItem.query.count()
    expiring_inventory_count = InventoryItem.query.filter(
        InventoryItem.type == 'food',
        InventoryItem.expiry_date <= (datetime.now() + timedelta(days=7)).date(),
        InventoryItem.status == 'available'
    ).count()

    # Recent users for the table
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # Recent activities
    recent_centers = EvacuationCenter.query.order_by(EvacuationCenter.created_at.desc()).limit(5).all()
    recent_evacuees = Evacuee.query.order_by(Evacuee.created_at.desc()).limit(5).all()
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(5).all()

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

    # Prepare center data for occupancy chart
    centers_data = []
    for center in EvacuationCenter.query.filter_by(status='active').all():
        centers_data.append({
            'name': center.name,
            'current_occupancy': center.current_occupancy,
            'capacity': center.capacity
        })

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
        recent_centers=recent_centers,
        recent_evacuees=recent_evacuees,
        recent_donations=recent_donations,
        centers_data=centers_data
    )

# Evacuation Center Management
@admin_bp.route('/centers')
@login_required
def centers():
    centers = EvacuationCenter.query.all()
    search_form = SearchForm()
    form = EvacuationCenterForm()

    if search_form.validate_on_submit():
        search_term = search_form.query.data
        centers = EvacuationCenter.query.filter(
            EvacuationCenter.name.ilike(f'%{search_term}%') | 
            EvacuationCenter.address.ilike(f'%{search_term}%')
        ).all()

    return render_template('admin/centers.html', search_form=search_form, form=form, centers=centers)

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
    form = EvacuationCenterForm(obj=center)  # Prepopulate the form with the center's data

    if form.validate_on_submit():
        # Update the center's attributes with the form data
        center.name = form.name.data
        center.address = form.address.data
        center.capacity = form.capacity.data
        center.status = form.status.data
        center.contact_person = form.contact_person.data
        center.contact_number = form.contact_number.data

        db.session.commit()  # Commit the changes to the database

        flash('Evacuation center updated successfully!', 'success')
        return redirect(url_for('admin.centers'))  # Redirect to the centers list

    # If the request method is GET or the form is invalid, render the edit template
    return render_template('admin/edit_center.html', form=form, center=center)

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
@admin_bp.route('/evacuees', methods=['GET', 'POST'])
@login_required
def evacuees():
    # Start with base query
    query = Evacuee.query
    search_form = SearchForm() #Added search form

    # Create both forms
    evacuee_form = EvacueeForm()  # Form for the modal dialog

    # Load data for dropdowns
    families = Family.query.all()
    centers = EvacuationCenter.query.all()

    # Load families and centers for form dropdowns
    evacuee_form.family_id.choices = [(0, 'No Family')] + [(f.id, f.family_name) for f in families]
    evacuee_form.evacuation_center_id.choices = [(c.id, c.name) for c in centers]

    # Handle search query
    if request.args.get('query'):
        search_term = request.args.get('query')
        query = query.filter(
            Evacuee.first_name.ilike(f'%{search_term}%') | 
            Evacuee.last_name.ilike(f'%{search_term}%')
        )

    # Handle status filter
    if request.args.get('status'):
        query = query.filter(Evacuee.status == request.args.get('status'))

    # Handle center filter
    if request.args.get('center'):
        query = query.filter(Evacuee.evacuation_center_id == request.args.get('center'))

    # Execute query
    evacuees = query.all()

    return render_template('admin/evacuees.html', 
                         evacuees=evacuees,
                         form=evacuee_form,
                         search_form=search_form,
                         families=families,
                         centers=centers)

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

    return render_template('admin/edit_evacuee.html', form=form, evacuee=evacuee)

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
    search_form = SearchForm()
    form = FamilyForm()  # For the add/edit modal

    evacuees = Evacuee.query.all()
    form.head_of_family_id.choices = [(0, 'None')] + [(e.id, f"{e.first_name} {e.last_name}") for e in evacuees]

    if search_form.validate_on_submit():
        search_term = search_form.query.data
        families = Family.query.filter(Family.family_name.ilike(f'%{search_term}%')).all()

    return render_template('admin/families.html', 
                         families=families, 
                         search_form=search_form,
                         form=form)

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

    return render_template('admin/edit_family.html', form=form, family=family)

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
    search_form = SearchForm()
    donation_form = DonationForm()  # Add this form for the modal
    
    # Load centers for dropdown
    donation_form.evacuation_center_id.choices = [(c.id, c.name) for c in EvacuationCenter.query.filter_by(status='active').all()]

    if search_form.validate_on_submit():
        search_term = search_form.query.data
        donations = Donation.query.filter(Donation.description.ilike(f'%{search_term}%')).all()

    return render_template('admin/donations.html', 
                         donations=donations, 
                         search_form=search_form,
                         form=donation_form)  # Pass donation_form as form for the modal

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
    show_inventory = True  # We're in the inventory view
    inventory_items = InventoryItem.query.all()
    search_form = SearchForm()
    form = InventoryItemForm()  # For the add/edit modal
        
    # Populate evacuation center choices
    centers = EvacuationCenter.query.filter_by(status='active').all()
    form.evacuation_center_id.choices = [(c.id, c.name) for c in centers]

    # Start with base query
    query = InventoryItem.query if show_inventory else Donation.query

    # Handle search
    search_term = request.args.get('query')
    if search_term:
        query = query.filter(
            InventoryItem.description.ilike(f'%{search_term}%') if show_inventory 
            else Donation.description.ilike(f'%{search_term}%')
        )

    # Handle type filter
    item_type = request.args.get('type')
    if item_type in ['food', 'non-food']:
        query = query.filter_by(type=item_type)

    # Handle status filter
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    # Execute query
    items = query.all()
    
    return render_template('admin/donations.html',
                         inventory_items=items if show_inventory else None,
                         donations=items if not show_inventory else None,
                         search_form=search_form,
                         form=form,
                         show_inventory=True)

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
    
    # Get all active evacuation centers
    centers = EvacuationCenter.query.filter_by(status='active').all()
    
    # Populate evacuation center dropdown options
    form.evacuation_center_id.choices = [(c.id, c.name) for c in centers]

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

    return render_template('admin/donations.html', 
                         form=form, 
                         editing_inventory=True, 
                         inventory_item=inventory_item, 
                         show_inventory=True,
                         centers=centers)  # Pass centers to the template

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
    search_form = SearchForm()

    if search_form.validate_on_submit():
        search_term = search_form.query.data
        users = User.query.filter(
            User.username.ilike(f'%{search_term}%') | 
            User.email.ilike(f'%{search_term}%') |
            User.first_name.ilike(f'%{search_term}%') |
            User.last_name.ilike(f'%{search_term}%')
        ).all()

    return render_template('admin/users.html', users=users, search_form=search_form)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserManagementForm(obj=user)
    search_form = SearchForm()

    if form.validate_on_submit():
        user.role = form.role.data
        user.is_active = form.is_active.data

        db.session.commit()

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', form=form, user=user)

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