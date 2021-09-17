# app/models.py

from flask_login import UserMixin, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from flask import request
from sqlalchemy.orm import backref
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from werkzeug.security import generate_password_hash, check_password_hash

from flask import current_app
from flask import request
#from . import db

from datetime import datetime
import hashlib


from app import db, login_manager

EXPIRATION = 3600

class Permission:
    SEE_OWNERS = 1
    SEE_MY_LOGS = 2
    SEE_ALL_LOGS = 4
    EDIT_OWNERS = 8
    ADMINISTRATOR = 16

@login_manager.user_loader
def load_user(id):
    return Owner.query.get(id)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions): 
        return False
    def is_administrator(self): 
        return False

login_manager.anonymous_user = AnonymousUser

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    default_role = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    owners = db.relationship('Owner', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None: self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'Guest': [Permission.SEE_OWNERS, Permission.SEE_MY_LOGS],
            'Regulars': [Permission.SEE_OWNERS, Permission.SEE_MY_LOGS, Permission.SEE_ALL_LOGS],
            'Administrator': [Permission.SEE_OWNERS, Permission.SEE_MY_LOGS, Permission.SEE_ALL_LOGS, Permission.EDIT_OWNERS, Permission.ADMINISTRATOR]
        }

        default_role = 'Guest'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None: role = Role(name=r)
            
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            
            
            role.default_role = (role.name == default_role)
            db.session.add(role)

        db.session.commit()

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def __repr__(self):
        return '<Role {}>'.format(self.name)

class Ownership(UserMixin, db.Model):
    __tablename__ = 'ownerships'

    ownership_id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime(), default=datetime.now())
    end_date = db.Column(db.DateTime(), default=None)
    doors = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.id'))
    card_uid = db.Column(db.String(60), db.ForeignKey('rfidcards.card_uid'))
    logs = db.relationship('Log', backref='logs', lazy='dynamic')

    def __repr__(self):
        return '<Ownership {}>'.format(self.ownership_id)
    

class Owner(UserMixin, db.Model):
    __tablename__ = 'owners'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), unique=True, index=True)
    owner_name = db.Column(db.String(60), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    avatar_hash = db.Column(db.String(32))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    passcode_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20), unique=True)
    

    def __init__(self, **kwargs):
        super(Owner, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None: 
                self.role = Role.query.filter_by(default_role=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    @property
    def passcode(self):
        raise AttributeError('Passcode is NOT a readable attribute')

    @passcode.setter
    def passcode(self, passcode):
        self.passcode_hash = generate_password_hash(passcode, salt_length=1)

    def verify_passcode(self, passcode):
        return check_password_hash(self.passcode_hash, passcode)

    @property
    def password(self):
        raise AttributeError('Password is NOT a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, salt_length=1)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_email_change_token(self, new_email, expiration=EXPIRATION):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email':new_email}).decode('utf-8')

    def generate_confirmation_token(self, expiration=EXPIRATION):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try: data = s.loads(token.encode('utf-8'))
        except: return False

        if data.get('change_email') != self.id: return False

        new_email = data.get('new_email')
        if new_email is None: return False
        if self.query.filter_by(email=new_email).first() is not None: return False

        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)

        return True

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try: data = s.loads(token.encode('utf-8'))
        except: return False

        if data.get('confirm') != self.id: return False

        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=EXPIRATION):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.email}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try: data = s.loads(token.encode('utf-8'))
        except: return False

        owner = Owner.query.get(data.get('reset'))
        if owner is None: return False

        owner.password = new_password
        db.session.add(owner)

        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTRATOR)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure: url = 'https://secure.gravatar.com/avatar'
        else: url = 'http://www.gravatar.com/avatar'

        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return '<Owner {}>'.format(self.owner_name)


class RFIDCard(db.Model): 
    __tablename__ = 'rfidcards'

    card_uid = db.Column(db.String(60), primary_key=True)
    active = db.Column(db.Boolean, default=False)
    lost = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<RFIDCard {}>'.format(self.card_uid)


class Log(UserMixin, db.Model):
    __tablename__ = 'logs'

    log_id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(), default=datetime.now())
    door = db.Column(db.Integer)
    ownership_id = db.Column(db.Integer, db.ForeignKey('ownerships.ownership_id'))
    
    def __repr__(self):
        return '<Log {}>'.format(self.log_id)

class Door(db.Model):
    __tablename__ = 'doors'

    door_id = db.Column(db.Integer, primary_key=True)
    door_name = db.Column(db.String(60), unique=True, index=True)

    def __repr__(self):
        return '<Door {}>'.format(self.door_id)