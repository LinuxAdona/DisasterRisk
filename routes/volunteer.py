from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app import db
from models import EvacuationCenter, Evacuee, Family, Donation, InventoryItem
from forms import EvacueeForm, DonationForm, SearchForm

volunteer_bp = Blueprint('volunteer', __name__, url_prefix='/volunteer')

@volunteer_bp.route('/dashboard')
@login_required
def dashboard():
    # Ensure user is volunteer
    if current_user.role != 'volunteer':
        flash('Access denied. Volunteer privileges required.', 'danger')
        return redirect(url_for('common.index'))
    
    # Get summary data for dashboard
    total_centers = EvacuationCenter.query.count()
    total_evacuees = Evacuee.query.count()
    total_donations = Donation.query.count()
    
    # Get recent activities relevant to volunteers
    recent_evacuees = Evacuee.query.order_by(Evacuee.created_at.desc()).limit(5).all()
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(5).all()
    
    # Get centers at capacity
    centers_at_capacity = []
    for center in EvacuationCenter.query.filter_by(status='active').all():
        if center.current_occupancy >= center.capacity * 0.9:  # 90% or more capacity
            centers_at_capacity.append(center)
    
    # Get soon-to-expire food items
    expiring_food = InventoryItem.query.filter(
        InventoryItem.type == 'food',
        InventoryItem.expiry_date <= (datetime.now() + timedelta(days=7)).date(),
        InventoryItem.expiry_date >= datetime.now().date(),
        InventoryItem.status == 'available'
    ).order_by(InventoryItem.expiry_date).all()
    
    return render_template(
        'volunteer/dashboard.html', 
        total_centers=total_centers,
        total_evacuees=total_evacuees,
        total_donations=total_donations,
        recent_evacuees=recent_evacuees,
        recent_donations=recent_donations,
        centers_at_capacity=centers_at_capacity,
        expiring_food=expiring_food
    )

# Evacuee Management for Volunteers
@volunteer_bp.route('/evacuees')
@login_required
def evacuees():
    query = request.args.get('query', '')
    status = request.args.get('status', '')
    center_id = request.args.get('center_id', '')
    
    evacuees_query = Evacuee.query
    
    if query:
        evacuees_query = evacuees_query.filter(
            Evacuee.first_name.ilike(f'%{query}%') |
            Evacuee.last_name.ilike(f'%{query}%') |
            Evacuee.special_needs.ilike(f'%{query}%')
        )
    
    if status:
        evacuees_query = evacuees_query.filter(Evacuee.status == status)
        
    if center_id:
        evacuees_query = evacuees_query.filter(Evacuee.evacuation_center_id == center_id)
    
    evacuees = evacuees_query.all()
    centers = EvacuationCenter.query.all()
    families = Family.query.all()
    search_form = SearchForm()
    evacuee_form = EvacueeForm()
    
    # Load form choices
    evacuee_form.evacuation_center_id.choices = [(c.id, c.name) for c in centers]
    evacuee_form.family_id.choices = [(0, 'No Family')] + [(f.id, f.family_name) for f in families]
    
    return render_template('volunteer/evacuees.html',
                         evacuees=evacuees,
                         centers=centers,
                         families=families,
                         search_form=search_form,
                         form=evacuee_form)

@volunteer_bp.route('/evacuees/add', methods=['GET', 'POST'])
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
        return redirect(url_for('volunteer.evacuees'))
    
    return render_template('volunteer/evacuees.html', form=form, adding=True)

@volunteer_bp.route('/evacuees/edit/<int:evacuee_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('volunteer.evacuees'))
    
    # Set correct family value for the form
    if evacuee.family_id:
        form.family_id.data = evacuee.family_id
    else:
        form.family_id.data = 0
    
    return render_template('volunteer/evacuees.html', form=form, editing=True, evacuee=evacuee)

@volunteer_bp.route('/evacuees/update_status/<int:evacuee_id>', methods=['POST'])
@login_required
def update_evacuee_status(evacuee_id):
    evacuee = Evacuee.query.get_or_404(evacuee_id)
    new_status = request.form.get('status')
    
    if new_status in ['present', 'relocated', 'missing', 'deceased']:
        evacuee.status = new_status
        db.session.commit()
        
        flash('Evacuee status updated successfully!', 'success')
    else:
        flash('Invalid status!', 'danger')
    
    return redirect(url_for('volunteer.evacuees'))

# Donation Management for Volunteers
@volunteer_bp.route('/donations')
@login_required
def donations():
    donations = Donation.query.all()
    inventory_items = InventoryItem.query.all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        donations = Donation.query.filter(Donation.description.ilike(f'%{search_term}%')).all()
        inventory_items = InventoryItem.query.filter(InventoryItem.description.ilike(f'%{search_term}%')).all()
    
    return render_template('volunteer/donations.html', 
                          donations=donations, 
                          inventory_items=inventory_items, 
                          form=form)

@volunteer_bp.route('/donations/receive/<int:donation_id>', methods=['POST'])
@login_required
def receive_donation(donation_id):
    donation = Donation.query.get_or_404(donation_id)
    
    if donation.status != 'pending':
        flash('This donation has already been processed!', 'warning')
        return redirect(url_for('volunteer.donations'))
    
    donation.status = 'received'
    
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
    
    flash('Donation received and added to inventory!', 'success')
    return redirect(url_for('volunteer.donations'))

@volunteer_bp.route('/inventory/distribute/<int:item_id>', methods=['POST'])
@login_required
def distribute_inventory(item_id):
    inventory_item = InventoryItem.query.get_or_404(item_id)
    
    if inventory_item.status != 'available':
        flash('This item is not available for distribution!', 'warning')
        return redirect(url_for('volunteer.donations'))
    
    inventory_item.status = 'distributed'
    db.session.commit()
    
    # If this item is from a donation, update the donation status too
    if inventory_item.donation:
        inventory_item.donation.status = 'distributed'
        db.session.commit()
    
    flash('Inventory item has been distributed!', 'success')
    return redirect(url_for('volunteer.donations'))

@volunteer_bp.route('/inventory/report_expiring', methods=['GET'])
@login_required
def report_expiring():
    # Get soon-to-expire food items
    expiring_food = InventoryItem.query.filter(
        InventoryItem.type == 'food',
        InventoryItem.expiry_date <= (datetime.now() + timedelta(days=7)).date(),
        InventoryItem.expiry_date >= datetime.now().date(),
        InventoryItem.status == 'available'
    ).order_by(InventoryItem.expiry_date).all()
    
    return render_template('volunteer/donations.html', 
                          expiring_food=expiring_food,
                          showing_expiring=True)
