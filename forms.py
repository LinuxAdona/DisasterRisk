from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField, DateField, SubmitField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from datetime import date

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[Optional()])
    role = SelectField('Role', choices=[('donor', 'Donor'), ('volunteer', 'Volunteer')], default='donor')
    submit = SubmitField('Register')

class EvacuationCenterForm(FlaskForm):
    name = StringField('Center Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('closed', 'Closed')], default='active')
    contact_person = StringField('Contact Person', validators=[Optional()])
    contact_number = StringField('Contact Number', validators=[Optional()])
    submit = SubmitField('Save Center')

class EvacueeForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
    status = SelectField('Status', choices=[
        ('present', 'Present'), 
        ('relocated', 'Relocated'), 
        ('missing', 'Missing'), 
        ('deceased', 'Deceased')
    ], default='present')
    special_needs = TextAreaField('Special Needs', validators=[Optional()])
    family_id = SelectField('Family', coerce=int, validators=[Optional()])
    evacuation_center_id = SelectField('Evacuation Center', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Evacuee')
    
    def validate_date_of_birth(self, field):
        if field.data and field.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')

class FamilyForm(FlaskForm):
    family_name = StringField('Family Name', validators=[DataRequired()])
    head_of_family_id = SelectField('Head of Family', coerce=int, validators=[Optional()])
    address = StringField('Home Address', validators=[Optional()])
    contact_number = StringField('Contact Number', validators=[Optional()])
    submit = SubmitField('Save Family')

class DonationForm(FlaskForm):
    type = SelectField('Donation Type', choices=[('food', 'Food'), ('non-food', 'Non-Food')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    unit = StringField('Unit (e.g., kg, pcs)', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date (for food items)', validators=[Optional()])
    evacuation_center_id = SelectField('Evacuation Center', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit Donation')
    
    def validate_expiry_date(self, field):
        if self.type.data == 'food' and not field.data:
            raise ValidationError('Expiry date is required for food donations.')
        if field.data and field.data < date.today():
            raise ValidationError('Expiry date cannot be in the past.')

class InventoryItemForm(FlaskForm):
    type = SelectField('Item Type', choices=[('food', 'Food'), ('non-food', 'Non-Food')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    unit = StringField('Unit (e.g., kg, pcs)', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date (for food items)', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('available', 'Available'),
        ('distributed', 'Distributed'),
        ('expired', 'Expired')
    ], default='available')
    evacuation_center_id = SelectField('Evacuation Center', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Item')
    
    def validate_expiry_date(self, field):
        if self.type.data == 'food' and not field.data:
            raise ValidationError('Expiry date is required for food items.')

class UserManagementForm(FlaskForm):
    role = SelectField('Role', choices=[
        ('admin', 'Admin'),
        ('volunteer', 'Volunteer'),
        ('donor', 'Donor')
    ], validators=[DataRequired()])
    is_active = BooleanField('Active')
    submit = SubmitField('Update User')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')
