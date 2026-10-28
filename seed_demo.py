import sys
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash
from database import get_db, init_db_indexes

def seed():
    print("Initializing FoodShare database & seeding demonstration records...")
    db = get_db()
    init_db_indexes(db)
    now = datetime.now(timezone.utc)

    # 1. Seed Categories
    categories = [
        {'name': 'Prepared Meals', 'icon': 'bi-cup-hot'},
        {'name': 'Fresh Produce', 'icon': 'bi-basket'},
        {'name': 'Bakery & Bread', 'icon': 'bi-cookie'},
        {'name': 'Dairy Products', 'icon': 'bi-egg'},
        {'name': 'Packaged Foods', 'icon': 'bi-box-seam'},
        {'name': 'Beverages', 'icon': 'bi-cup-straw'}
    ]
    for cat in categories:
        if not db.categories.find_one({'name': cat['name']}):
            cat['created_at'] = now
            db.categories.insert_one(cat)
    print(f"Verified {len(categories)} food categories.")

    # 2. Seed Demo Accounts
    demo_users = [
        {
            'email': 'donor@foodshare.com',
            'password_hash': generate_password_hash('Donor123!', method='pbkdf2:sha256'),
            'role': 'donor',
            'org_name': 'Hotel Grand Plaza',
            'contact_name': 'Chef Rajesh Kumar',
            'donor_type': 'Hotel / Restaurant',
            'phone': '+91 98765 43210',
            'address': '45 Heritage Boulevard, MG Road Metro District',
            'verified': True,
            'status': 'active'
        },
        {
            'email': 'ngo@foodshare.com',
            'password_hash': generate_password_hash('Ngo123!', method='pbkdf2:sha256'),
            'role': 'ngo',
            'org_name': 'Helping Hands NGO',
            'contact_name': 'Ananya Roy',
            'reg_number': 'NGO-IND-2021-8842',
            'service_area': 'Central & East Metro Zones',
            'description': 'Dedicated to hunger eradication, daily community kitchens, and immediate surplus food recovery.',
            'phone': '+91 98123 45678',
            'address': '12 Community Centre Way, East District',
            'verified': True,
            'status': 'active'
        },
        {
            'email': 'user@foodshare.com',
            'password_hash': generate_password_hash('User123!', method='pbkdf2:sha256'),
            'role': 'recipient',
            'name': 'Priya Sharma',
            'phone': '+91 99887 76655',
            'service_area': 'East District Neighborhood',
            'address': 'Flat 302, Greenview Apartments, Lake Road',
            'verified': True,
            'status': 'active'
        },
        {
            'email': 'admin@foodshare.com',
            'password_hash': generate_password_hash('Admin123!', method='pbkdf2:sha256'),
            'role': 'admin',
            'name': 'Platform Administrator',
            'phone': '+91 90000 00000',
            'address': 'FoodShare Operations HQ',
            'verified': True,
            'status': 'active'
        }
    ]

    user_ids = {}
    for user_info in demo_users:
        existing = db.users.find_one({'email': user_info['email']})
        if not existing:
            user_info['created_at'] = now
            user_info['updated_at'] = now
            res = db.users.insert_one(user_info)
            user_ids[user_info['role']] = res.inserted_id
            print(f"Created demo account: {user_info['email']} ({user_info['role']})")
        else:
            user_ids[user_info['role']] = existing['_id']
            print(f"Found existing demo account: {user_info['email']}")

    # 3. Seed Realistic Food Donations
    donor_id = user_ids.get('donor')
    ngo_id = user_ids.get('ngo')
    user_id = user_ids.get('recipient')

    sample_donations = [
        {
            'donor_id': donor_id,
            'donor_name': 'Hotel Grand Plaza',
            'donor_contact': '+91 98765 43210',
            'title': 'Veg Dum Biryani & Raita',
            'category': 'Prepared Meals',
            'description': 'Aromatic long grain basmati rice with mixed vegetables and Indian spices, freshly prepared for afternoon banquet. Kept at safe warm temperature.',
            'quantity': 25.0,
            'unit': 'kg',
            'remaining_quantity': 15.0,
            'food_classification': 'Vegetarian',
            'allergens': 'Dairy (ghee/raita), Nuts (cashews)',
            'storage_instructions': 'Hot holding above 65°C or consume within 4 hours',
            'packaging_details': 'Food-grade stainless steel pots & insulated meal containers',
            'preparation_time': 'Today, 11:30 AM',
            'available_from': now,
            'available_until': now + timedelta(days=1),
            'pickup_start': '02:00 PM',
            'pickup_end': '06:00 PM',
            'pickup_address': 'Hotel Grand Plaza Kitchen Gate 3, MG Road',
            'contact_instructions': 'Ask for Chef Rajesh at the service entry',
            'accuracy_confirmed': True,
            'image_path': '/static/images/veg-biryani.jpg',
            'status': 'Partially Reserved',
            'created_at': now - timedelta(hours=3),
            'updated_at': now
        },
        {
            'donor_id': donor_id,
            'donor_name': 'Hotel Grand Plaza',
            'donor_contact': '+91 98765 43210',
            'title': 'Vegetable Fried Rice & Manchurian',
            'category': 'Prepared Meals',
            'description': 'Freshly cooked vegetable fried rice with crispy vegetable manchurian gravy in sealed food trays.',
            'quantity': 15.0,
            'unit': 'kg',
            'remaining_quantity': 15.0,
            'food_classification': 'Vegetarian',
            'allergens': 'Soy, Gluten',
            'storage_instructions': 'Keep warm or refrigerate immediately below 4°C',
            'packaging_details': 'Sealed heavy-duty food foil trays',
            'preparation_time': 'Today, 12:00 PM',
            'available_from': now,
            'available_until': now + timedelta(days=2),
            'pickup_start': '03:00 PM',
            'pickup_end': '07:00 PM',
            'pickup_address': 'Hotel Grand Plaza Banquet Back Loading Dock',
            'contact_instructions': 'Call donor upon arrival at Gate 2',
            'accuracy_confirmed': True,
            'image_path': '/static/images/fried-rice.jpg',
            'status': 'Available',
            'created_at': now - timedelta(hours=2),
            'updated_at': now
        },
        {
            'donor_id': donor_id,
            'donor_name': 'Hotel Grand Plaza',
            'donor_contact': '+91 98765 43210',
            'title': 'Fresh Organic Fruits Assortment',
            'category': 'Fresh Produce',
            'description': 'Wholesome crate of apples, bananas, sweet oranges, and seasonal melons, ripe and ready for consumption.',
            'quantity': 20.0,
            'unit': 'kg',
            'remaining_quantity': 20.0,
            'food_classification': 'Vegetarian',
            'allergens': 'None',
            'storage_instructions': 'Keep in cool, dry ventilated area',
            'packaging_details': 'Ventilated wooden fruit crates',
            'preparation_time': 'Freshly sorted morning harvest',
            'available_from': now,
            'available_until': now + timedelta(days=3),
            'pickup_start': '10:00 AM',
            'pickup_end': '08:00 PM',
            'pickup_address': 'Hotel Grand Plaza Green Pantry Room',
            'contact_instructions': 'Ring doorbell at pantry reception',
            'accuracy_confirmed': True,
            'image_path': '/static/images/fresh-produce.jpg',
            'status': 'Available',
            'created_at': now - timedelta(hours=5),
            'updated_at': now
        },
        {
            'donor_id': donor_id,
            'donor_name': 'Hotel Grand Plaza',
            'donor_contact': '+91 98765 43210',
            'title': 'Handcrafted Whole Wheat Rotis & Dal Tadka',
            'category': 'Prepared Meals',
            'description': 'Soft handmade rotis paired with nutritious yellow lentil dal prepared with minimal oil.',
            'quantity': 30.0,
            'unit': 'servings',
            'remaining_quantity': 0.0,
            'food_classification': 'Vegetarian',
            'allergens': 'Gluten (wheat)',
            'storage_instructions': 'Ready to eat immediately',
            'packaging_details': 'Clean insulated casserole packs',
            'preparation_time': 'Yesterday evening',
            'available_from': now - timedelta(days=1),
            'available_until': now + timedelta(hours=12),
            'pickup_start': '08:00 AM',
            'pickup_end': '12:00 PM',
            'pickup_address': 'Hotel Grand Plaza Staff Dining Entrance',
            'contact_instructions': 'Security office check-in',
            'accuracy_confirmed': True,
            'image_path': '/static/images/chapati-sabzi.jpg',
            'status': 'Collected',
            'created_at': now - timedelta(days=1),
            'updated_at': now
        }
    ]

    created_donations = []
    for d in sample_donations:
        existing_donation = db.donations.find_one({'title': d['title'], 'donor_id': donor_id})
        if not existing_donation:
            res = db.donations.insert_one(d)
            created_donations.append(res.inserted_id)
        else:
            created_donations.append(existing_donation['_id'])
    print(f"Verified {len(sample_donations)} sample food donations.")

    # 4. Seed Requests and Collections
    if created_donations and ngo_id:
        biryani_id = created_donations[0]
        roti_id = created_donations[3]

        # Request 1: Approved request by NGO for Veg Biryani (10 kg)
        if not db.donation_requests.find_one({'donation_id': biryani_id, 'recipient_id': ngo_id}):
            db.donation_requests.insert_one({
                'donation_id': biryani_id,
                'donation_title': 'Veg Dum Biryani & Raita',
                'donor_id': donor_id,
                'donor_name': 'Hotel Grand Plaza',
                'recipient_id': ngo_id,
                'recipient_name': 'Helping Hands NGO',
                'recipient_role': 'ngo',
                'recipient_phone': '+91 98123 45678',
                'recipient_email': 'ngo@foodshare.com',
                'requested_quantity': 10.0,
                'unit': 'kg',
                'approved_quantity': 10.0,
                'intended_pickup_time': 'Today at 03:30 PM',
                'pickup_window': '02:00 PM - 06:00 PM',
                'pickup_address': 'Hotel Grand Plaza Kitchen Gate 3, MG Road',
                'notes': 'Will be distributed immediately at the City Shelter Ward 4.',
                'donor_notes': 'Please bring clean insulated boxes. Gate entry cleared.',
                'status': 'Approved',
                'created_at': now - timedelta(hours=2),
                'updated_at': now - timedelta(hours=1),
                'collected_at': None,
                'completed_at': None
            })

        # Request 2: Completed / Collected request for Whole Wheat Rotis
        if not db.donation_requests.find_one({'donation_id': roti_id, 'recipient_id': ngo_id}):
            db.donation_requests.insert_one({
                'donation_id': roti_id,
                'donation_title': 'Handcrafted Whole Wheat Rotis & Dal Tadka',
                'donor_id': donor_id,
                'donor_name': 'Hotel Grand Plaza',
                'recipient_id': ngo_id,
                'recipient_name': 'Helping Hands NGO',
                'recipient_role': 'ngo',
                'recipient_phone': '+91 98123 45678',
                'recipient_email': 'ngo@foodshare.com',
                'requested_quantity': 30.0,
                'unit': 'servings',
                'approved_quantity': 30.0,
                'intended_pickup_time': 'Yesterday at 09:30 AM',
                'pickup_window': '08:00 AM - 12:00 PM',
                'pickup_address': 'Hotel Grand Plaza Staff Dining Entrance',
                'notes': 'Distributed to 60 seniors at the community home.',
                'donor_notes': 'Collected on time. Great coordination!',
                'status': 'Collected',
                'created_at': now - timedelta(days=1, hours=2),
                'updated_at': now - timedelta(days=1),
                'collected_at': now - timedelta(days=1),
                'completed_at': now - timedelta(days=1)
            })

        # Request 3: Pending request by Individual recipient for Veg Fried Rice
        if user_id and len(created_donations) > 1:
            rice_id = created_donations[1]
            if not db.donation_requests.find_one({'donation_id': rice_id, 'recipient_id': user_id}):
                db.donation_requests.insert_one({
                    'donation_id': rice_id,
                    'donation_title': 'Vegetable Fried Rice & Manchurian',
                    'donor_id': donor_id,
                    'donor_name': 'Hotel Grand Plaza',
                    'recipient_id': user_id,
                    'recipient_name': 'Priya Sharma',
                    'recipient_role': 'recipient',
                    'recipient_phone': '+91 99887 76655',
                    'recipient_email': 'user@foodshare.com',
                    'requested_quantity': 3.0,
                    'unit': 'kg',
                    'approved_quantity': 0,
                    'intended_pickup_time': 'Today at 04:30 PM',
                    'pickup_window': '03:00 PM - 07:00 PM',
                    'pickup_address': 'Hotel Grand Plaza Banquet Back Loading Dock',
                    'notes': 'For my family and elderly neighbors.',
                    'donor_notes': '',
                    'status': 'Pending',
                    'created_at': now - timedelta(minutes=45),
                    'updated_at': now - timedelta(minutes=45),
                    'collected_at': None,
                    'completed_at': None
                })

    # 5. Seed Notifications
    if donor_id:
        db.notifications.insert_one({
            'user_id': donor_id,
            'title': 'New Request Pending Review',
            'message': 'Priya Sharma requested 3.0 kg of Vegetable Fried Rice & Manchurian.',
            'link': '/donor/requests',
            'type': 'info',
            'is_read': False,
            'created_at': now - timedelta(minutes=45)
        })

    if ngo_id:
        db.notifications.insert_one({
            'user_id': ngo_id,
            'title': 'Request Approved!',
            'message': "Your request for 10.0 kg of 'Veg Dum Biryani & Raita' has been approved! Pickup window: 02:00 PM - 06:00 PM.",
            'link': '/ngo/requests',
            'type': 'success',
            'is_read': False,
            'created_at': now - timedelta(hours=1)
        })

    # 6. Global Platform Settings
    db.platform_settings.update_one(
        {'type': 'global'},
        {'$set': {
            'type': 'global',
            'platform_name': 'FoodShare',
            'tagline': 'Good Food. Brighter Tomorrows.',
            'support_email': 'support@foodshare.com',
            'disclaimer': 'FoodShare is a technological redistribution facilitator. Donors are legally responsible for food hygiene, freshness, and allergen accuracy under local safety regulations.',
            'individual_max_units': 10,
            'updated_at': now
        }},
        upsert=True
    )

    print("\nFoodShare database seeded successfully!")
    print("--------------------------------------------------")
    print("Demo Accounts:")
    print("  Donor:       donor@foodshare.com   /  Donor123!")
    print("  NGO:         ngo@foodshare.com     /  Ngo123!")
    print("  Recipient:   user@foodshare.com    /  User123!")
    print("  Admin:       admin@foodshare.com   /  Admin123!")
    print("--------------------------------------------------")

if __name__ == '__main__':
    seed()
