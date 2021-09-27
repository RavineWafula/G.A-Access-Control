from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.core import SelectMultipleField, SelectField
from wtforms.validators import DataRequired, Regexp

from ..models import Door, Owner, Role, RFIDCard

class AssignRoleForm(FlaskForm):
    owner = QuerySelectField(query_factory=lambda: Owner.query.filter_by(role_id=None), get_label="owner_name")
    role = QuerySelectField(query_factory=lambda: Role.query.all(), get_label="name")
    submit = SubmitField('Assign')

class RFIDCardForm(FlaskForm):
    card_uid = StringField('Card UID', validators=[DataRequired(), Regexp('^[A-Za-z0-9]*$', 0,'Card UID must have only letters or numbers')])
    submit = SubmitField('Submit')

class OwnershipForm(FlaskForm):
    owner = QuerySelectField(query_factory=lambda: Owner.query.all(), get_label="owner_name")
    rfidcard = QuerySelectField(query_factory=lambda: RFIDCard.query.filter_by(active=False), get_label='card_uid')
    doors = SelectMultipleField('Select Doors', coerce=int)
    submit = SubmitField('Submit')

"""
class UserDetails(Form):
    group_id = SelectField(u'Group', coerce=int)

def edit_user(request, id):
    user = User.query.get(id)
    form = UserDetails(request.POST, obj=user)
    form.group_id.choices = [(g.id, g.name) for g in Group.query.order_by('name')]

    #choices=[(1, 'Door1'),(2, 'Door2'),(3, 'Door3'),(4, 'Door4'),(5, 'Door5'),(6, 'Door6'),(7, 'Door7')]
"""
