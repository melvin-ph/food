from datetime import datetime, timezone
from database import get_db, to_object_id
from services.notification_service import create_notification

def submit_request(recipient_id, data):
    db = get_db()
    rid = to_object_id(recipient_id)
    did = to_object_id(data.get('donation_id'))

    if not rid or not did:
        return None, "Invalid user or donation identifier."

    recipient = db.users.find_one({'_id': rid})
    if not recipient or recipient.get('role') not in ['ngo', 'recipient']:
        return None, "Only registered NGOs or individual recipients can request food."

    donation = db.donations.find_one({'_id': did})
    if not donation:
        return None, "Donation listing not found."

    if donation.get('status') not in ['Available', 'Partially Reserved']:
        return None, f"This donation is currently {donation.get('status')} and not accepting requests."

    now = datetime.now(timezone.utc)
    avail_until = donation.get('available_until')
    if avail_until:
        if avail_until.tzinfo is None:
            avail_until = avail_until.replace(tzinfo=timezone.utc)
        if avail_until < now:
            db.donations.update_one({'_id': did}, {'$set': {'status': 'Expired', 'updated_at': now}})
            return None, "This donation has reached its deadline and has expired."

    try:
        req_qty = float(data.get('requested_quantity', 0))
    except (ValueError, TypeError):
        return None, "Invalid requested quantity."

    if req_qty <= 0:
        return None, "Requested quantity must be greater than zero."

    remaining = float(donation.get('remaining_quantity', 0))
    if req_qty > remaining:
        return None, f"Requested quantity ({req_qty} {donation.get('unit')}) exceeds remaining availability ({remaining} {donation.get('unit')})."

    # Enforce reasonable limit for individual recipients to prevent abuse
    if recipient.get('role') == 'recipient' and req_qty > 10:
        return None, "Individual recipient requests are limited to a maximum of 10 units per request to ensure fair distribution."

    # Prevent duplicate pending request by the same recipient on the same donation
    existing_pending = db.donation_requests.find_one({
        'donation_id': did,
        'recipient_id': rid,
        'status': 'Pending'
    })
    if existing_pending:
        return None, "You already have a pending request for this donation. Please wait for the donor to review it."

    req_doc = {
        'donation_id': did,
        'donation_title': donation.get('title'),
        'donor_id': donation.get('donor_id'),
        'donor_name': donation.get('donor_name'),
        'recipient_id': rid,
        'recipient_name': recipient.get('org_name') or recipient.get('name') or recipient.get('contact_name'),
        'recipient_role': recipient.get('role'),
        'recipient_phone': recipient.get('phone', ''),
        'recipient_email': recipient.get('email', ''),
        'requested_quantity': req_qty,
        'unit': donation.get('unit', 'kg'),
        'approved_quantity': 0,
        'intended_pickup_time': (data.get('intended_pickup_time') or '').strip(),
        'pickup_window': f"{donation.get('pickup_start')} - {donation.get('pickup_end')}",
        'pickup_address': donation.get('pickup_address', ''),
        'notes': (data.get('notes') or '').strip(),
        'donor_notes': '',
        'status': 'Pending',  # Pending, Approved, Rejected, Cancelled, Collected, Completed
        'created_at': now,
        'updated_at': now,
        'collected_at': None,
        'completed_at': None
    }

    result = db.donation_requests.insert_one(req_doc)

    # Notify donor
    create_notification(
        user_id=donation['donor_id'],
        title='New Food Request',
        message=f"{req_doc['recipient_name']} requested {req_qty} {req_doc['unit']} of '{donation['title']}'.",
        link=f"/donor/requests",
        notif_type='info'
    )

    # Audit log
    db.audit_logs.insert_one({
        'action': 'SUBMIT_REQUEST',
        'entity_type': 'donation_request',
        'entity_id': result.inserted_id,
        'user_id': rid,
        'details': f"Requested {req_qty} {req_doc['unit']} for donation '{donation['title']}'",
        'created_at': now
    })

    return str(result.inserted_id), None

def review_request(request_id, donor_id, action, donor_notes=""):
    """Action: 'approve' or 'reject'"""
    db = get_db()
    rid = to_object_id(request_id)
    did = to_object_id(donor_id)
    if not rid or not did:
        return False, "Invalid identifiers."

    request_item = db.donation_requests.find_one({'_id': rid})
    if not request_item:
        return False, "Request not found."

    donor = db.users.find_one({'_id': did})
    if request_item['donor_id'] != did and (not donor or donor.get('role') != 'admin'):
        return False, "You are not authorized to review this request."

    if request_item['status'] != 'Pending':
        return False, f"This request is already {request_item['status']}."

    donation = db.donations.find_one({'_id': request_item['donation_id']})
    if not donation:
        return False, "Associated donation no longer exists."

    now = datetime.now(timezone.utc)
    req_qty = float(request_item['requested_quantity'])

    if action == 'approve':
        remaining = float(donation.get('remaining_quantity', 0))
        if req_qty > remaining:
            return False, f"Cannot approve: requested quantity ({req_qty}) exceeds current remaining quantity ({remaining})."

        new_remaining = remaining - req_qty
        new_status = 'Fully Reserved' if new_remaining <= 0 else 'Partially Reserved'

        # Update donation atomically
        db.donations.update_one(
            {'_id': donation['_id']},
            {'$set': {'remaining_quantity': new_remaining, 'status': new_status, 'updated_at': now}}
        )

        # Update request
        db.donation_requests.update_one(
            {'_id': rid},
            {'$set': {
                'status': 'Approved',
                'approved_quantity': req_qty,
                'donor_notes': donor_notes.strip(),
                'updated_at': now
            }}
        )

        # Notify recipient
        create_notification(
            user_id=request_item['recipient_id'],
            title='Request Approved!',
            message=f"Your request for {req_qty} {request_item['unit']} of '{donation['title']}' was approved! Check pickup instructions.",
            link=f"/requests/my-requests",
            notif_type='success'
        )

        # Audit log
        db.audit_logs.insert_one({
            'action': 'APPROVE_REQUEST',
            'entity_type': 'donation_request',
            'entity_id': rid,
            'user_id': did,
            'details': f"Approved {req_qty} units. Remaining: {new_remaining}",
            'created_at': now
        })
        return True, "Request successfully approved."

    elif action == 'reject':
        db.donation_requests.update_one(
            {'_id': rid},
            {'$set': {
                'status': 'Rejected',
                'donor_notes': donor_notes.strip(),
                'updated_at': now
            }}
        )

        # Notify recipient
        create_notification(
            user_id=request_item['recipient_id'],
            title='Request Declined',
            message=f"Your request for '{donation['title']}' was declined. Note: {donor_notes or 'Quantity unavailable'}",
            link=f"/requests/my-requests",
            notif_type='warning'
        )

        # Audit log
        db.audit_logs.insert_one({
            'action': 'REJECT_REQUEST',
            'entity_type': 'donation_request',
            'entity_id': rid,
            'user_id': did,
            'details': f"Rejected request with reason: {donor_notes}",
            'created_at': now
        })
        return True, "Request rejected."

    return False, "Unknown action."

def confirm_collection(request_id, user_id):
    db = get_db()
    rid = to_object_id(request_id)
    uid = to_object_id(user_id)
    if not rid or not uid:
        return False, "Invalid identifiers."

    request_item = db.donation_requests.find_one({'_id': rid})
    if not request_item:
        return False, "Request not found."

    user = db.users.find_one({'_id': uid})
    is_donor = request_item['donor_id'] == uid
    is_recipient = request_item['recipient_id'] == uid
    is_admin = user and user.get('role') == 'admin'

    if not (is_donor or is_recipient or is_admin):
        return False, "Access denied."

    if request_item['status'] != 'Approved':
        return False, f"Only approved requests can be confirmed as collected. Current status: {request_item['status']}."

    now = datetime.now(timezone.utc)
    db.donation_requests.update_one(
        {'_id': rid},
        {'$set': {'status': 'Collected', 'collected_at': now, 'updated_at': now}}
    )

    donation_id = request_item['donation_id']
    donation = db.donations.find_one({'_id': donation_id})

    # Check if all requests for this donation are collected/completed and remaining is 0
    if donation:
        active_uncollected = db.donation_requests.count_documents({
            'donation_id': donation_id,
            'status': {'$in': ['Pending', 'Approved']}
        })
        if active_uncollected == 0 and donation.get('remaining_quantity', 0) <= 0:
            db.donations.update_one(
                {'_id': donation_id},
                {'$set': {'status': 'Collected', 'updated_at': now}}
            )

    # Notify parties
    target_user = request_item['recipient_id'] if is_donor else request_item['donor_id']
    create_notification(
        user_id=target_user,
        title='Food Collection Confirmed',
        message=f"Collection for '{request_item['donation_title']}' ({request_item['requested_quantity']} {request_item['unit']}) has been confirmed.",
        link=f"/requests/my-requests",
        notif_type='success'
    )

    return True, "Collection confirmed successfully."

def complete_request(request_id, user_id):
    db = get_db()
    rid = to_object_id(request_id)
    uid = to_object_id(user_id)
    if not rid or not uid:
        return False, "Invalid identifiers."

    request_item = db.donation_requests.find_one({'_id': rid})
    if not request_item:
        return False, "Request not found."

    now = datetime.now(timezone.utc)
    db.donation_requests.update_one(
        {'_id': rid},
        {'$set': {'status': 'Completed', 'completed_at': now, 'updated_at': now}}
    )

    # Also update donation status if all items completed
    donation_id = request_item['donation_id']
    pending_items = db.donation_requests.count_documents({
        'donation_id': donation_id,
        'status': {'$in': ['Pending', 'Approved']}
    })
    if pending_items == 0:
        db.donations.update_one({'_id': donation_id}, {'$set': {'status': 'Completed', 'updated_at': now}})

    return True, "Completed."

def cancel_request(request_id, user_id, reason="Cancelled by user"):
    db = get_db()
    rid = to_object_id(request_id)
    uid = to_object_id(user_id)
    if not rid or not uid:
        return False, "Invalid identifiers."

    request_item = db.donation_requests.find_one({'_id': rid})
    if not request_item:
        return False, "Request not found."

    user = db.users.find_one({'_id': uid})
    if request_item['recipient_id'] != uid and (not user or user.get('role') != 'admin'):
        return False, "Access denied."

    if request_item['status'] in ['Collected', 'Completed', 'Cancelled', 'Rejected']:
        return False, f"Cannot cancel a request that is {request_item['status']}."

    now = datetime.now(timezone.utc)
    was_approved = request_item['status'] == 'Approved'
    req_qty = float(request_item['requested_quantity'])

    # If was approved, restore quantity to donation
    if was_approved:
        donation = db.donations.find_one({'_id': request_item['donation_id']})
        if donation:
            new_remaining = float(donation.get('remaining_quantity', 0)) + req_qty
            new_status = 'Available' if new_remaining >= float(donation.get('quantity', 0)) else 'Partially Reserved'
            db.donations.update_one(
                {'_id': donation['_id']},
                {'$set': {'remaining_quantity': new_remaining, 'status': new_status, 'updated_at': now}}
            )

    db.donation_requests.update_one(
        {'_id': rid},
        {'$set': {'status': 'Cancelled', 'donor_notes': reason, 'updated_at': now}}
    )

    # Notify donor
    create_notification(
        user_id=request_item['donor_id'],
        title='Request Cancelled',
        message=f"{request_item['recipient_name']} cancelled their request for '{request_item['donation_title']}'.",
        link=f"/donor/requests",
        notif_type='warning'
    )

    return True, "Request cancelled."

def get_requests_for_donor(donor_id, status=None):
    db = get_db()
    did = to_object_id(donor_id)
    if not did:
        return []
    query = {'donor_id': did}
    if status:
        query['status'] = status
    return list(db.donation_requests.find(query).sort('created_at', -1))

def get_requests_for_recipient(recipient_id, status=None):
    db = get_db()
    rid = to_object_id(recipient_id)
    if not rid:
        return []
    query = {'recipient_id': rid}
    if status:
        query['status'] = status
    return list(db.donation_requests.find(query).sort('created_at', -1))
