from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user

from .forms import AssignRoleForm, RFIDCardForm, OwnershipForm
from . import main
from .. import db

from .. import mqtt, socketio, log_list
from ..models import Permission, Log, Role, Owner, Ownership, RFIDCard

from datetime import datetime
import json
import eventlet
import os

import hashlib

from flask_socketio import send, emit

eventlet.monkey_patch()

@main.route('/')
def homepage():
    return render_template('main/index.html', title="Welcome")

@main.route('/dashboard')
@login_required
def dashboard():
    owners = Owner.query.all()
    return render_template('main/dashboard.html', title="Dashboard")


@main.route('/users/see_my_logs')
@login_required
def see_my_logs():
    if not current_user.can(Permission.SEE_MY_LOGS):
        abort(403)
    
    logs = Log.query.filter_by(ownership_id=current_user.id)
    return render_template('main/users/see_my_logs.html', logs=logs[::-1], owner_name = current_user.owner_name, title="My Logs")

@main.route('/users/see_all_logs')
@login_required
def see_all_logs():
    if not current_user.can(Permission.SEE_ALL_LOGS):
        abort(403)
    
    logs = Log.query.all()
    time = datetime.now()
    log_entries = []
    for log in logs:
        ownership = Ownership.query.filter_by(ownership_id=log.ownership_id).first()
        owner = Owner.query.filter_by(id=ownership.owner_id).first()
        log_entries.append([log, owner])

    return render_template('main/users/see_all_logs.html', log_entries = log_entries[::-1], title="All Logs")

@main.route('/users/list_roles')
@login_required
def list_roles():
    if not current_user.can(Permission.EDIT_OWNERS):
        abort(403)
    
    roles = []
    owners = Owner.query.all()
    for owner in owners:
        try: role = Role.query.filter_by(id = owner.role_id).first()
        except: role = None
        roles.append([owner, role])

    return render_template('main/users/users.html', roles = roles, title='Owners')

@main.route('/users/assign_user_role/<int:id>', methods=['GET', 'POST'])
@login_required
def assign_user_role(id):
    if not current_user.can(Permission.EDIT_OWNERS):
        abort(403)

    user = Owner.query.filter_by(id = id).first()
    user.role_id = None

    form = AssignRoleForm()
    if form.validate_on_submit():
        role_data = form.role.data
        role_name = list(str(role_data).split())[-1][:-1]
        # print("------------------", role_name)
        role = Role.query.filter_by(name = role_name).first()
        
        name_data = form.owner.data
        owner_name = str(name_data)[7:-1]
        owner = Owner.query.filter_by(owner_name = owner_name).first()
    
        owner.role_id = role.id

        db.session.add(owner)
        db.session.commit()
        flash('You have successfully assigned a role')

        return redirect(url_for('main.list_roles'))
    else: owner = Owner.query.filter_by(id = id).first()

    return render_template('main/users/user.html', owner=owner, form=form, title='Assign User')


@main.route('/users/list_users')
@login_required
def list_users():
    if not current_user.can(Permission.ADMINISTRATOR):
        abort(403)
    
    all_users = Ownership.query.all()
    users = []
    for user in all_users:
        owner = Owner.query.filter_by(id = user.owner_id).first()
        if user.end_date is not None and user.end_date<datetime.now():
            delete_user(user.ownership_id)
        else: 
            try: role = Role.query.filter_by(id = owner.role_id).first()
            except: role = None
            users.append([user,owner,role])

    return render_template('main/users/list_users.html', ownership_list=users, title="Active Users")

@main.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    if not current_user.can(Permission.ADMINISTRATOR) or not current_user.can(Permission.EDIT_OWNERS):
        abort(403)
    
    user = Ownership.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()

    flash('The user is no longer valid')

    return redirect(url_for('main.list_users'))

@main.route('/cards/list_cards')
@login_required
def list_cards():
    if not current_user.can(Permission.ADMINISTRATOR):
        abort(403)

    rfidcards = RFIDCard.query.all()

    return render_template('/main/cards/list_cards.html', rfidcards = rfidcards, title="RFID Cards")


@main.route('/cards/add_card', methods=['GET', 'POST'])
@login_required
def add_card():
    if not current_user.can(Permission.ADMINISTRATOR):
        abort(403)

    add_card = True

    form = RFIDCardForm()
    if form.validate_on_submit():
        rfidcard = RFIDCard(card_uid=form.card_uid.data)

        try:
            db.session.add(rfidcard)
            db.session.commit()
            flash('You have successfully added an RFID Card')

        except: flash('Error: RFID Card already exists!')

        return redirect(url_for('main.list_cards'))

    return render_template('/main/cards/card.html', add_card=add_card, form=form, title='Add RFID Card')

@main.route('/cards/assign_cards')
@login_required
def assign_cards():
    if not current_user.can(Permission.ADMINISTRATOR) or not current_user.can(Permission.EDIT_OWNERS):
        abort(403)

    assign_cards = True

    form = OwnershipForm()
    if form.validate_on_submit():
        owner = Owner.query.filter_by(owner_name = form.owner.data).first()
        ownership = Ownership(owner_id = owner.id,
                              start_data = datetime.now(),
                              end_date = None,
                              doors = form.doors.data,
                              card_uid = form.rfidcard.data)

        db.session.add(ownership)
        db.session.commit()
        flash("You have successfully added an Ownership")

        return redirect(url_for('main.list_users'))

    else: owner = Owner.query.filter_by(id = 2)

    return render_template('/main/users/owner.html', owner=owner, form=form, assign_cards=assign_cards, title='Add Ownerships')

@main.route('/users/add_owners', methods=['GET', 'POST'])
@login_required
def add_owner():
    if not current_user.can(Permission.ADMINISTRATOR):
        abort(403)

    add_owner = True

    form = OwnershipForm()
    if form.validate_on_submit():
        owner_data = form.owner.data
        owner_name = str(owner_data)[7:-1]

        rfid_data = form.rfidcard.data
        card_uid = str(rfid_data)[10:-1]

        doors = 0
        for door in form.doors.data:
            doors+=(1<<(door-1))

        owner = Owner.query.filter_by(owner_name = owner_name).first()
        
        ownership = Ownership(owner_id=owner.id,
                              card_uid = card_uid,
                              doors = doors)

        db.session.add(ownership)

        rfid = RFIDCard.query.filter_by(card_uid=card_uid).first()
        rfid.active = True
        db.session.add(rfid)

        db.session.commit()
        flash('You have successfully added an Ownership')

        return redirect(url_for('main.list_users'))

    return render_template('/main/users/owner.html', add_owner=add_owner, form=form, title='Add Ownership')


def check_rfidtag(card_uid, door_number):
    ownership = Ownership.query.filter_by(card_uid=card_uid).first()
    if ownership is not None:
        owner = Owner.query.filter_by(id = ownership.owner_id).first()
        print('111111111111', owner.owner_name)
        if ownership.end_date is None:
            if (ownership.doors)>>(door_number-1) & 1:
                reply = '1#'+str(door_number)
                mqtt.publish('receive',reply, 1)
            
                time = datetime.now()

                log = Log(time=time, ownership_id = owner.id, door=door_number)
                db.session.add(log)
                db.session.commit()
                return 1
            return 0

        elif ownership.end_date>datetime.now():
            if (ownership.doors)>>(door_number-1) & 1:
                reply = '1#'+str(door_number)
                mqtt.publish('receive',reply, 1)

                time = datetime.now()

                log = Log(time=time, ownership_id = owner.id, door=door_number)
                db.session.add(log)
                db.session.commit()
                return 1
            return 0

        else: return 0
    else: return 0

def check_passcode(phone, passcode, door_number):
    owner = Owner.query.filter_by(phone = phone).first()

    if owner is not None:
        if owner.verify_passcode(passcode):# owner.passcode_hash==hashlib.md5(str(passcode).encode('utf-8')).hexdigest():
            ownership = Ownership.query.filter_by(owner_id=owner.id).first()
            if ownership is not None:
                if ownership.end_date is None:
                    if (ownership.doors)>>(door_number-1) & 1:
                        reply = '1#'+str(door_number)
                        mqtt.publish('receive', reply, 1)
                        time = datetime.now()
                        log = Log(time = time, ownership_id = ownership.ownership_id, door=door_number)

                        db.session.add(log)
                        db.session.commit()

                        return 1
                    return 0
                return 0

            elif ownership.end_data>datetime.now():
                if (ownership.doors)>>(door_number-1) & 1:
                    reply = '1#'+str(door_number)
                    mqtt.publish('receive',reply, 1)

                    time = datetime.now()

                    log = Log(time=time, ownership_id = ownership.ownership_id, door=door_number)
                    db.session.add(log)
                    db.session.commit()
                    return 1
                return 0

            else: return 0
        else: return 0
    else: return 0

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode(),
        qos=message.qos,
    )

    arr = list(data['payload'].split('#'))

    from run import app

    with app.app_context():
        flag = 0
        if len(arr)==2:
            flag = check_rfidtag(arr[0], int(arr[1]))
        elif len(arr)==3:
            flag = check_passcode(arr[0], arr[1], int(arr[2]))

        if flag==0: mqtt.publish('receive', '0#'+str(arr[-1]))
    
        print('HAPA',userdata, data)

    