from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from models import (
    User, EvacuationCenter, Evacuee, Family, 
    Donation, InventoryItem
)

from forms import (
    EvacuationCenterForm, FamilyForm, EvacueeForm,
    DonationForm, InventoryItemForm, UserApprovalForm,
    DonationStatusForm
)

# Create blueprints
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
volunteer_bp = Blueprint('volunteer', __name__, url_prefix='/volunteer')
donor_bp = Blueprint('donor', __name__, url_prefix='/donor')

# Custom decorators for role-based access control
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def volunteer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'volunteer']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def donor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'donor']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Main routes
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('index.html')

# Error handlers
@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('index.html', error="Access Forbidden: You don't have permission to access this resource."), 403

@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page Not Found: The requested page does not exist."), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('index.html', error="Internal Server Error: Something went wrong on our end."), 500

# Admin routes
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Getting stats for dashboard
    active_centers = len(EvacuationCenter.get_all(active_only=True))
    total_evacuees = len(Evacuee.get_all(status='active'))
    pending_donations = len(Donation.get_all(status='pending'))
    pending_users = len([u for u in User.get_all() if not u.approved])
    
    # Get evacuation centers with high occupancy (>80%)
    centers = EvacuationCenter.get_all(active_only=True)
    high_occupancy_centers = [c for c in centers if c.occupancy_percentage > 80]
    
    # Get expiring donations
    expiring_donations = Donation.get_expiring_soon()
    
    return render_template(
        'admin/dashboard.html', 
        active_centers=active_centers,
        total_evacuees=total_evacuees,
        pending_donations=pending_donations,
        pending_users=pending_users,
        high_occupancy_centers=high_occupancy_centers,
        expiring_donations=expiring_donations
    )

@admin_bp.route('/evacuation-centers')
@login_required
@admin_required
def evacuation_centers():
    centers = EvacuationCenter.get_all()
    return render_template('admin/evacuation_centers.html', centers=centers)

@admin_bp.route('/evacuation-centers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_evacuation_center():
    form = EvacuationCenterForm()
    if form.validate_on_submit():
        center = EvacuationCenter(
            name=form.name.data,
            address=form.address.data,
            capacity=form.capacity.data,
            contact=form.contact.data
        )
        center.save()
        flash('Evacuation center added successfully!', 'success')
        return redirect(url_for('admin.evacuation_centers'))
    return render_template('admin/evacuation_centers.html', form=form)

@admin_bp.route('/evacuation-centers/<center_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_evacuation_center(center_id):
    center = EvacuationCenter.get_by_id(center_id)
    if not center:
        flash('Evacuation center not found!', 'danger')
        return redirect(url_for('admin.evacuation_centers'))
    
    form = EvacuationCenterForm(obj=center)
    if form.validate_on_submit():
        center.update({
            'name': form.name.data,
            'address': form.address.data,
            'capacity': form.capacity.data,
            'contact': form.contact.data,
            'active': form.active.data
        })
        flash('Evacuation center updated successfully!', 'success')
        return redirect(url_for('admin.evacuation_centers'))
    
    return render_template('admin/evacuation_centers.html', form=form, center=center)

@admin_bp.route('/evacuees')
@login_required
@admin_required
def evacuees():
    evacuees_list = Evacuee.get_all()
    return render_template('admin/evacuees.html', evacuees=evacuees_list)

@admin_bp.route('/evacuees/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_evacuee():
    form = EvacueeForm()
    # Populate dropdown choices
    form.family_id.choices = [('', 'None')] + [(f.id, f.name) for f in Family.get_all()]
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        evacuee = Evacuee(
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            family_id=form.family_id.data if form.family_id.data else None,
            center_id=form.center_id.data,
            special_needs=form.special_needs.data
        )
        evacuee.save()
        flash('Evacuee added successfully!', 'success')
        return redirect(url_for('admin.evacuees'))
    
    return render_template('admin/evacuees.html', form=form)

@admin_bp.route('/evacuees/<evacuee_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_evacuee(evacuee_id):
    evacuee = Evacuee.get_by_id(evacuee_id)
    if not evacuee:
        flash('Evacuee not found!', 'danger')
        return redirect(url_for('admin.evacuees'))
    
    form = EvacueeForm(obj=evacuee)
    # Populate dropdown choices
    form.family_id.choices = [('', 'None')] + [(f.id, f.name) for f in Family.get_all()]
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        evacuee.update({
            'name': form.name.data,
            'age': form.age.data,
            'gender': form.gender.data,
            'family_id': form.family_id.data if form.family_id.data else None,
            'center_id': form.center_id.data,
            'special_needs': form.special_needs.data,
            'status': form.status.data
        })
        flash('Evacuee updated successfully!', 'success')
        return redirect(url_for('admin.evacuees'))
    
    return render_template('admin/evacuees.html', form=form, evacuee=evacuee)

@admin_bp.route('/families')
@login_required
@admin_required
def families():
    families_list = Family.get_all()
    return render_template('admin/families.html', families=families_list)

@admin_bp.route('/families/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_family():
    form = FamilyForm()
    if form.validate_on_submit():
        family = Family(
            name=form.name.data,
            head_name=form.head_name.data,
            contact=form.contact.data
        )
        family.save()
        flash('Family added successfully!', 'success')
        return redirect(url_for('admin.families'))
    
    return render_template('admin/families.html', form=form)

@admin_bp.route('/families/<family_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_family(family_id):
    family = Family.get_by_id(family_id)
    if not family:
        flash('Family not found!', 'danger')
        return redirect(url_for('admin.families'))
    
    form = FamilyForm(obj=family)
    if form.validate_on_submit():
        family.update({
            'name': form.name.data,
            'head_name': form.head_name.data,
            'contact': form.contact.data
        })
        flash('Family updated successfully!', 'success')
        return redirect(url_for('admin.families'))
    
    return render_template('admin/families.html', form=form, family=family)

@admin_bp.route('/donations')
@login_required
@admin_required
def donations():
    donations_list = Donation.get_all()
    return render_template('admin/donations.html', donations=donations_list)

@admin_bp.route('/donations/update-status', methods=['POST'])
@login_required
@admin_required
def update_donation_status():
    form = DonationStatusForm()
    if form.validate_on_submit():
        donation = Donation.get_by_id(form.donation_id.data)
        if donation:
            donation.update({
                'status': form.status.data
            })
            flash('Donation status updated successfully!', 'success')
        else:
            flash('Donation not found!', 'danger')
    
    return redirect(url_for('admin.donations'))

@admin_bp.route('/inventory')
@login_required
@admin_required
def inventory():
    inventory_items = InventoryItem.get_all()
    return render_template('admin/inventory.html', inventory_items=inventory_items)

@admin_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_inventory_item():
    form = InventoryItemForm()
    # Populate dropdown choices
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        item = InventoryItem(
            center_id=form.center_id.data,
            type=form.type.data,
            name=form.name.data,
            quantity=form.quantity.data,
            expiry_date=form.expiry_date.data
        )
        item.save()
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('admin.inventory'))
    
    return render_template('admin/inventory.html', form=form)

@admin_bp.route('/inventory/<item_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_inventory_item(item_id):
    item = InventoryItem.get_by_id(item_id)
    if not item:
        flash('Inventory item not found!', 'danger')
        return redirect(url_for('admin.inventory'))
    
    form = InventoryItemForm(obj=item)
    # Populate dropdown choices
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        item.update({
            'center_id': form.center_id.data,
            'type': form.type.data,
            'name': form.name.data,
            'quantity': form.quantity.data,
            'expiry_date': form.expiry_date.data
        })
        flash('Inventory item updated successfully!', 'success')
        return redirect(url_for('admin.inventory'))
    
    return render_template('admin/inventory.html', form=form, item=item)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users_list = User.get_all()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/approve', methods=['POST'])
@login_required
@admin_required
def approve_user():
    form = UserApprovalForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        approved = form.approved.data == 'true'
        
        user = User.get_by_id(user_id)
        if user:
            user.approved = approved
            flash(f'User {user.username} has been {"approved" if approved else "rejected"}!', 'success')
        else:
            flash('User not found!', 'danger')
    
    return redirect(url_for('admin.users'))

# Volunteer routes
@volunteer_bp.route('/dashboard')
@login_required
@volunteer_required
def dashboard():
    # Getting stats for dashboard
    active_centers = len(EvacuationCenter.get_all(active_only=True))
    total_evacuees = len(Evacuee.get_all(status='active'))
    pending_donations = len(Donation.get_all(status='pending'))
    
    # Get evacuation centers with high occupancy (>80%)
    centers = EvacuationCenter.get_all(active_only=True)
    high_occupancy_centers = [c for c in centers if c.occupancy_percentage > 80]
    
    # Get expiring donations
    expiring_donations = Donation.get_expiring_soon()
    
    return render_template(
        'volunteer/dashboard.html', 
        active_centers=active_centers,
        total_evacuees=total_evacuees,
        pending_donations=pending_donations,
        high_occupancy_centers=high_occupancy_centers,
        expiring_donations=expiring_donations
    )

@volunteer_bp.route('/evacuees')
@login_required
@volunteer_required
def evacuees():
    evacuees_list = Evacuee.get_all()
    return render_template('volunteer/evacuees.html', evacuees=evacuees_list)

@volunteer_bp.route('/evacuees/add', methods=['GET', 'POST'])
@login_required
@volunteer_required
def add_evacuee():
    form = EvacueeForm()
    # Populate dropdown choices
    form.family_id.choices = [('', 'None')] + [(f.id, f.name) for f in Family.get_all()]
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        evacuee = Evacuee(
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            family_id=form.family_id.data if form.family_id.data else None,
            center_id=form.center_id.data,
            special_needs=form.special_needs.data
        )
        evacuee.save()
        flash('Evacuee added successfully!', 'success')
        return redirect(url_for('volunteer.evacuees'))
    
    return render_template('volunteer/evacuees.html', form=form)

@volunteer_bp.route('/evacuees/<evacuee_id>/edit', methods=['GET', 'POST'])
@login_required
@volunteer_required
def edit_evacuee(evacuee_id):
    evacuee = Evacuee.get_by_id(evacuee_id)
    if not evacuee:
        flash('Evacuee not found!', 'danger')
        return redirect(url_for('volunteer.evacuees'))
    
    form = EvacueeForm(obj=evacuee)
    # Populate dropdown choices
    form.family_id.choices = [('', 'None')] + [(f.id, f.name) for f in Family.get_all()]
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        evacuee.update({
            'name': form.name.data,
            'age': form.age.data,
            'gender': form.gender.data,
            'family_id': form.family_id.data if form.family_id.data else None,
            'center_id': form.center_id.data,
            'special_needs': form.special_needs.data,
            'status': form.status.data
        })
        flash('Evacuee updated successfully!', 'success')
        return redirect(url_for('volunteer.evacuees'))
    
    return render_template('volunteer/evacuees.html', form=form, evacuee=evacuee)

@volunteer_bp.route('/families')
@login_required
@volunteer_required
def families():
    families_list = Family.get_all()
    return render_template('volunteer/families.html', families=families_list)

@volunteer_bp.route('/families/add', methods=['GET', 'POST'])
@login_required
@volunteer_required
def add_family():
    form = FamilyForm()
    if form.validate_on_submit():
        family = Family(
            name=form.name.data,
            head_name=form.head_name.data,
            contact=form.contact.data
        )
        family.save()
        flash('Family added successfully!', 'success')
        return redirect(url_for('volunteer.families'))
    
    return render_template('volunteer/families.html', form=form)

@volunteer_bp.route('/donations')
@login_required
@volunteer_required
def donations():
    donations_list = Donation.get_all()
    return render_template('volunteer/donations.html', donations=donations_list)

@volunteer_bp.route('/donations/update-status', methods=['POST'])
@login_required
@volunteer_required
def update_donation_status():
    form = DonationStatusForm()
    if form.validate_on_submit():
        donation = Donation.get_by_id(form.donation_id.data)
        if donation:
            donation.update({
                'status': form.status.data
            })
            flash('Donation status updated successfully!', 'success')
        else:
            flash('Donation not found!', 'danger')
    
    return redirect(url_for('volunteer.donations'))

@volunteer_bp.route('/inventory')
@login_required
@volunteer_required
def inventory():
    inventory_items = InventoryItem.get_all()
    return render_template('volunteer/inventory.html', inventory_items=inventory_items)

# Donor routes
@donor_bp.route('/dashboard')
@login_required
@donor_required
def dashboard():
    # Get stats for donor dashboard
    donations = Donation.get_all(donor_id=current_user.id)
    pending_donations = len([d for d in donations if d.status == 'pending'])
    received_donations = len([d for d in donations if d.status == 'received'])
    distributed_donations = len([d for d in donations if d.status == 'distributed'])
    
    # Get active evacuation centers for making donations
    active_centers = EvacuationCenter.get_all(active_only=True)
    
    return render_template(
        'donor/dashboard.html',
        pending_donations=pending_donations,
        received_donations=received_donations,
        distributed_donations=distributed_donations,
        active_centers=active_centers
    )

@donor_bp.route('/donations')
@login_required
@donor_required
def donations():
    donations_list = Donation.get_all(donor_id=current_user.id)
    return render_template('donor/donations.html', donations=donations_list)

@donor_bp.route('/donations/add', methods=['GET', 'POST'])
@login_required
@donor_required
def add_donation():
    form = DonationForm()
    # Populate dropdown choices
    form.center_id.choices = [(c.id, c.name) for c in EvacuationCenter.get_all(active_only=True)]
    
    if form.validate_on_submit():
        donation = Donation(
            donor_id=current_user.id,
            center_id=form.center_id.data,
            type=form.type.data,
            description=form.description.data,
            quantity=form.quantity.data,
            expiry_date=form.expiry_date.data
        )
        donation.save()
        flash('Donation added successfully! Thank you for your contribution.', 'success')
        return redirect(url_for('donor.donations'))
    
    return render_template('donor/donations.html', form=form)

# API routes for charts and data tables
@main_bp.route('/api/evacuation-centers')
@login_required
def api_evacuation_centers():
    centers = EvacuationCenter.get_all(active_only=True)
    data = [
        {
            'id': c.id,
            'name': c.name,
            'current_occupancy': c.current_occupancy,
            'capacity': c.capacity,
            'occupancy_percentage': c.occupancy_percentage
        }
        for c in centers
    ]
    return jsonify(data)

@main_bp.route('/api/evacuee-stats')
@login_required
def api_evacuee_stats():
    evacuees = Evacuee.get_all()
    
    # Count by status
    status_counts = {
        'active': 0,
        'relocated': 0,
        'missing': 0,
        'deceased': 0
    }
    
    for e in evacuees:
        if e.status in status_counts:
            status_counts[e.status] += 1
    
    # Count by gender
    gender_counts = {
        'male': 0,
        'female': 0,
        'other': 0
    }
    
    for e in evacuees:
        if e.gender in gender_counts:
            gender_counts[e.gender] += 1
    
    # Count by age group
    age_groups = {
        '0-12': 0,
        '13-18': 0,
        '19-30': 0,
        '31-45': 0,
        '46-60': 0,
        '60+': 0
    }
    
    for e in evacuees:
        if e.age <= 12:
            age_groups['0-12'] += 1
        elif e.age <= 18:
            age_groups['13-18'] += 1
        elif e.age <= 30:
            age_groups['19-30'] += 1
        elif e.age <= 45:
            age_groups['31-45'] += 1
        elif e.age <= 60:
            age_groups['46-60'] += 1
        else:
            age_groups['60+'] += 1
    
    return jsonify({
        'status': status_counts,
        'gender': gender_counts,
        'age_groups': age_groups
    })

@main_bp.route('/api/donation-stats')
@login_required
def api_donation_stats():
    donations = Donation.get_all()
    
    # Count by type
    type_counts = {
        'food': 0,
        'clothing': 0,
        'hygiene': 0,
        'medicine': 0,
        'other': 0
    }
    
    for d in donations:
        if d.type in type_counts:
            type_counts[d.type] += 1
    
    # Count by status
    status_counts = {
        'pending': 0,
        'received': 0,
        'distributed': 0,
        'expired': 0
    }
    
    for d in donations:
        if d.status in status_counts:
            status_counts[d.status] += 1
    
    return jsonify({
        'type': type_counts,
        'status': status_counts
    })

# Register all blueprints with the app
def register_routes(app):
    from auth import auth_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(volunteer_bp)
    app.register_blueprint(donor_bp)
