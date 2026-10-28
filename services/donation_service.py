from datetime import datetime, timezone
from database import get_db, to_object_id
from services.notification_service import create_notification

def auto_expire_donations():
    """Checks for donations where available_until has passed and updates status to Expired."""
    db = get_db()
    now = datetime.now(timezone.utc)
    expired_cursor = db.donations.find({
        'status': {'$in': ['Available', 'Partially Reserved']},
        'available_until': {'$lt': now}
    })
    count = 0
    for donation in expired_cursor:
        db.donations.update_one(
            {'_id': donation['_id']},
            {'$set': {'status': 'Expired', 'updated_at': now}}
        )
        count += 1
        # Notify donor
        create_notification(
            user_id=donation['donor_id'],
            title='Donation Expired',
            message=f"Your donation '{donation.get('title')}' reached its pickup deadline and has expired.",
            link=f"/donations/{donation['_id']}",
            notif_type='warning'
        )
    return count

def create_donation(donor_id, data):
    db = get_db()
    did = to_object_id(donor_id)
    if not did:
        return None, "Invalid donor identifier."

    donor = db.users.find_one({'_id': did, 'role': 'donor'})
    if not donor:
        return None, "Donor account not found."

    qty = float(data.get('quantity', 0))
    if qty <= 0:
        return None, "Quantity must be greater than zero."

    now = datetime.now(timezone.utc)
    
    # Parse dates
    available_until = data.get('available_until')
    if isinstance(available_until, str):
        try:
            available_until = datetime.fromisoformat(available_until.replace('Z', '+00:00'))
        except Exception:
            available_until = now

    available_from = data.get('available_from', now)
    if isinstance(available_from, str):
        try:
            available_from = datetime.fromisoformat(available_from.replace('Z', '+00:00'))
        except Exception:
            available_from = now

    donation_doc = {
        'donor_id': did,
        'donor_name': donor.get('org_name') or donor.get('contact_name') or 'Verified Donor',
        'donor_contact': donor.get('phone', ''),
        'title': (data.get('title') or '').strip(),
        'category': data.get('category') or 'Prepared Meals',
        'description': (data.get('description') or '').strip(),
        'quantity': qty,
        'unit': data.get('unit') or 'kg',
        'remaining_quantity': qty,
        'food_classification': data.get('food_classification') or 'Vegetarian',
        'allergens': (data.get('allergens') or '').strip(),
        'storage_instructions': (data.get('storage_instructions') or '').strip(),
        'packaging_details': (data.get('packaging_details') or '').strip(),
        'preparation_time': data.get('preparation_time') or '',
        'available_from': available_from,
        'available_until': available_until,
        'pickup_start': data.get('pickup_start') or '10:00 AM',
        'pickup_end': data.get('pickup_end') or '06:00 PM',
        'pickup_address': (data.get('pickup_address') or donor.get('address') or '').strip(),
        'contact_instructions': (data.get('contact_instructions') or '').strip(),
        'accuracy_confirmed': bool(data.get('accuracy_confirmed', True)),
        'image_path': data.get('image_path') or '/static/images/prepared-meals.jpg',
        'status': data.get('status') or 'Available',  # Available, Draft
        'created_at': now,
        'updated_at': now
    }

    result = db.donations.insert_one(donation_doc)
    
    # Audit log
    db.audit_logs.insert_one({
        'action': 'CREATE_DONATION',
        'entity_type': 'donation',
        'entity_id': result.inserted_id,
        'user_id': did,
        'details': f"Created donation '{donation_doc['title']}' of {qty} {donation_doc['unit']}",
        'created_at': now
    })

    return str(result.inserted_id), None

def get_donation_by_id(donation_id):
    db = get_db()
    did = to_object_id(donation_id)
    if not did:
        return None
    auto_expire_donations()
    donation = db.donations.find_one({'_id': did})
    if donation:
        donor = db.users.find_one({'_id': donation.get('donor_id')})
        if donor:
            donation['donor'] = {
                'name': donor.get('org_name') or donor.get('contact_name'),
                'email': donor.get('email'),
                'phone': donor.get('phone'),
                'donor_type': donor.get('donor_type', 'Food Donor'),
                'address': donor.get('address')
            }
    return donation

def update_donation(donation_id, donor_id, update_data):
    db = get_db()
    did = to_object_id(donation_id)
    uid = to_object_id(donor_id)
    if not did or not uid:
        return False, "Invalid identifiers."

    existing = db.donations.find_one({'_id': did, 'donor_id': uid})
    if not existing:
        return False, "Donation not found or access denied."

    if existing['status'] in ['Collected', 'Completed']:
        return False, "Cannot modify a donation that has already been collected or completed."

    now = datetime.now(timezone.utc)
    fields_to_update = {
        'title': update_data.get('title', existing['title']),
        'category': update_data.get('category', existing['category']),
        'description': update_data.get('description', existing['description']),
        'food_classification': update_data.get('food_classification', existing.get('food_classification')),
        'allergens': update_data.get('allergens', existing.get('allergens')),
        'storage_instructions': update_data.get('storage_instructions', existing.get('storage_instructions')),
        'packaging_details': update_data.get('packaging_details', existing.get('packaging_details')),
        'pickup_start': update_data.get('pickup_start', existing.get('pickup_start')),
        'pickup_end': update_data.get('pickup_end', existing.get('pickup_end')),
        'pickup_address': update_data.get('pickup_address', existing.get('pickup_address')),
        'contact_instructions': update_data.get('contact_instructions', existing.get('contact_instructions')),
        'updated_at': now
    }
    if 'image_path' in update_data and update_data['image_path']:
        fields_to_update['image_path'] = update_data['image_path']

    # Update deadline if provided
    if 'available_until' in update_data and update_data['available_until']:
        try:
            fields_to_update['available_until'] = datetime.fromisoformat(update_data['available_until'].replace('Z', '+00:00'))
        except Exception:
            pass

    db.donations.update_one({'_id': did}, {'$set': fields_to_update})
    return True, None

def cancel_donation(donation_id, donor_id, reason="Donor cancelled listing"):
    db = get_db()
    did = to_object_id(donation_id)
    uid = to_object_id(donor_id)
    if not did or not uid:
        return False, "Invalid identifiers."

    donation = db.donations.find_one({'_id': did})
    if not donation:
        return False, "Donation not found."

    # Allow donor or admin to cancel
    user = db.users.find_one({'_id': uid})
    if donation['donor_id'] != uid and (not user or user.get('role') != 'admin'):
        return False, "Access denied."

    if donation['status'] in ['Collected', 'Completed']:
        return False, "Cannot cancel a completed or collected donation."

    now = datetime.now(timezone.utc)
    db.donations.update_one({'_id': did}, {'$set': {'status': 'Cancelled', 'cancellation_reason': reason, 'updated_at': now}})

    # Cancel any pending requests on this donation
    pending_requests = list(db.donation_requests.find({'donation_id': did, 'status': 'Pending'}))
    for req in pending_requests:
        db.donation_requests.update_one(
            {'_id': req['_id']},
            {'$set': {'status': 'Cancelled', 'donor_notes': 'Donation was cancelled by donor', 'updated_at': now}}
        )
        create_notification(
            user_id=req['recipient_id'],
            title='Request Cancelled',
            message=f"The listing for '{donation['title']}' was cancelled by the donor.",
            link=f"/requests/my-requests",
            notif_type='warning'
        )

    return True, None

def list_donations(filters=None, page=1, per_page=12):
    db = get_db()
    auto_expire_donations()
    query = {}
    filters = filters or {}

    # Status filter
    if 'status' in filters and filters['status']:
        if isinstance(filters['status'], list):
            query['status'] = {'$in': filters['status']}
        else:
            query['status'] = filters['status']
    else:
        # Default browse shows Available & Partially Reserved
        query['status'] = {'$in': ['Available', 'Partially Reserved']}

    # Category filter
    if filters.get('category') and filters['category'] != 'All':
        query['category'] = filters['category']

    # Veg / Non-veg
    if filters.get('food_classification') and filters['food_classification'] != 'All':
        query['food_classification'] = filters['food_classification']

    # Search keyword
    if filters.get('search'):
        search_term = filters['search'].strip()
        query['$or'] = [
            {'title': {'$regex': search_term, '$options': 'i'}},
            {'description': {'$regex': search_term, '$options': 'i'}},
            {'pickup_address': {'$regex': search_term, '$options': 'i'}},
            {'donor_name': {'$regex': search_term, '$options': 'i'}}
        ]

    # Donor ID
    if filters.get('donor_id'):
        query['donor_id'] = to_object_id(filters['donor_id'])

    # Min quantity
    if filters.get('min_qty'):
        try:
            query['remaining_quantity'] = {'$gte': float(filters['min_qty'])}
        except ValueError:
            pass

    skip = (page - 1) * per_page
    total = db.donations.count_documents(query)
    donations = list(db.donations.find(query).sort('created_at', -1).skip(skip).limit(per_page))

    # Add count of requests to each donation
    for d in donations:
        d['requests_count'] = db.donation_requests.count_documents({'donation_id': d['_id']})

    return donations, total

def get_donor_stats(donor_id):
    db = get_db()
    did = to_object_id(donor_id)
    if not did:
        return {}

    auto_expire_donations()
    total_donations = db.donations.count_documents({'donor_id': did})
    available_donations = db.donations.count_documents({'donor_id': did, 'status': {'$in': ['Available', 'Partially Reserved']}})
    collected_donations = db.donations.count_documents({'donor_id': did, 'status': 'Collected'})
    completed_donations = db.donations.count_documents({'donor_id': did, 'status': 'Completed'})
    cancelled_donations = db.donations.count_documents({'donor_id': did, 'status': 'Cancelled'})
    
    # Pending requests on this donor's donations
    pending_requests = db.donation_requests.count_documents({'donor_id': did, 'status': 'Pending'})

    # Calculate total food quantity redistributed (from completed/collected requests)
    pipeline = [
        {'$match': {'donor_id': did, 'status': {'$in': ['Approved', 'Collected', 'Completed']}}},
        {'$group': {'_id': None, 'total_qty': {'$sum': '$requested_quantity'}}}
    ]
    agg_result = list(db.donation_requests.aggregate(pipeline))
    redistributed_qty = agg_result[0]['total_qty'] if agg_result else 0

    return {
        'total_donations': total_donations,
        'available_donations': available_donations,
        'collected_donations': collected_donations + completed_donations,
        'pending_requests': pending_requests,
        'cancelled_donations': cancelled_donations,
        'completed_donations': completed_donations,
        'redistributed_qty': round(redistributed_qty, 1)
    }
