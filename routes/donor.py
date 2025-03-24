from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from models import Donation, EvacuationCenter
from forms import DonationForm, SearchForm

donor_bp = Blueprint('donor', __name__, url_prefix='/donor')

@donor_bp.route('/dashboard')
@login_required
def dashboard():
    # Ensure user is donor
    if current_user.role != 'donor':
        flash('Access denied. Donor privileges required.', 'danger')
        return redirect(url_for('common.index'))
    
    # Get count of donations made by this donor
    total_donations = Donation.query.filter_by(donor_id=current_user.id).count()
    
    # Get donation history for this donor
    donation_history = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    
    # Get active evacuation centers
    active_centers = EvacuationCenter.query.filter_by(status='active').all()
    
    return render_template(
        'donor/dashboard.html', 
        total_donations=total_donations,
        donation_history=donation_history,
        active_centers=active_centers
    )

@donor_bp.route('/donations')
@login_required
def donations():
    # Get donation history for this donor
    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    form = SearchForm()
    
    if form.validate_on_submit():
        search_term = form.query.data
        donations = Donation.query.filter_by(donor_id=current_user.id).filter(
            Donation.description.ilike(f'%{search_term}%')
        ).order_by(Donation.created_at.desc()).all()
    
    return render_template('donor/donations.html', donations=donations, form=form)

@donor_bp.route('/donations/add', methods=['GET', 'POST'])
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
            status='pending'  # Donations start as pending
        )
        
        db.session.add(donation)
        db.session.commit()
        
        flash('Thank you for your donation! It has been submitted and is awaiting processing.', 'success')
        return redirect(url_for('donor.donations'))
    
    return render_template('donor/donations.html', form=form, adding=True)
