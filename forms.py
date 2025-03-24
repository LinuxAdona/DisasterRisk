from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, DateField, RadioField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('volunteer', 'Volunteer'), ('donor', 'Donor')])

class EvacuationCenterForm(FlaskForm):
    name = StringField('Center Name', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1)])
    contact = StringField('Contact Information', validators=[DataRequired()])
    active = BooleanField('Active', default=True)

class FamilyForm(FlaskForm):
    name = StringField('Family Name', validators=[DataRequired()])
    head_name = StringField('Head of Family', validators=[DataRequired()])
    contact = StringField('Contact Information', validators=[DataRequired()])

class EvacueeForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    family_id = SelectField('Family', validators=[Optional()], coerce=str)
    center_id = SelectField('Evacuation Center', validators=[DataRequired()], coerce=str)
    special_needs = TextAreaField('Special Needs', validators=[Optional()])
    status = SelectField('Status', 
                         choices=[('active', 'Active'), 
                                  ('relocated', 'Relocated'), 
                                  ('missing', 'Missing'), 
                                  ('deceased', 'Deceased')],
                         default='active')

class DonationForm(FlaskForm):
    center_id = SelectField('Evacuation Center', validators=[DataRequired()], coerce=str)
    type = SelectField('Donation Type', 
                       choices=[('food', 'Food'), 
                                ('clothing', 'Clothing'), 
                                ('hygiene', 'Hygiene'), 
                                ('medicine', 'Medicine'), 
                                ('other', 'Other')])
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    expiry_date = DateField('Expiry Date (if applicable)', validators=[Optional()])

class InventoryItemForm(FlaskForm):
    center_id = SelectField('Evacuation Center', validators=[DataRequired()], coerce=str)
    type = SelectField('Item Type', 
                       choices=[('food', 'Food'), 
                                ('clothing', 'Clothing'), 
                                ('hygiene', 'Hygiene'), 
                                ('medicine', 'Medicine'), 
                                ('other', 'Other')])
    name = StringField('Item Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    expiry_date = DateField('Expiry Date (if applicable)', validators=[Optional()])

class UserApprovalForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    approved = HiddenField('Approved', validators=[DataRequired()])

class DonationStatusForm(FlaskForm):
    donation_id = HiddenField('Donation ID', validators=[DataRequired()])
    status = SelectField('Status', 
                         choices=[('pending', 'Pending'), 
                                  ('received', 'Received'), 
                                  ('distributed', 'Distributed'), 
                                  ('expired', 'Expired')])
