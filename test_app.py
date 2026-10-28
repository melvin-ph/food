import unittest
import json
from datetime import datetime, timezone, timedelta
from app import create_app
from database import get_db, to_object_id

class FoodShareEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF in tests for direct post convenience
        cls.client = cls.app.test_client()

    def test_01_public_endpoints(self):
        """Test public pages load successfully with 200 OK."""
        routes = ['/', '/how-it-works', '/impact', '/about', '/food-safety', '/contact', '/login', '/register']
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed to load.")
            self.assertIn(b'FoodShare', res.data)

    def test_02_demo_login_all_roles(self):
        """Test logging into all 4 demo accounts created by seed."""
        accounts = [
            ('donor@foodshare.com', 'Donor123!', '/donor/dashboard'),
            ('ngo@foodshare.com', 'Ngo123!', '/ngo/dashboard'),
            ('user@foodshare.com', 'User123!', '/recipient/dashboard'),
            ('admin@foodshare.com', 'Admin123!', '/admin/dashboard'),
        ]
        for email, password, expected_dashboard in accounts:
            with self.client as c:
                res = c.post('/login', data={'email': email, 'password': password}, follow_redirects=True)
                self.assertEqual(res.status_code, 200)
                self.assertIn(expected_dashboard.split('/')[-1].encode(), res.data)

    def test_03_role_based_access_security(self):
        """Verify that an individual recipient cannot access admin or donor portals."""
        with self.client as c:
            # Login as recipient
            c.post('/login', data={'email': 'user@foodshare.com', 'password': 'User123!'})
            
            # Attempt to access donor dashboard -> should redirect or deny
            res = c.get('/donor/dashboard', follow_redirects=True)
            self.assertIn(b'authorized', res.data.lower())

            # Attempt to access admin dashboard -> should redirect or deny
            res = c.get('/admin/dashboard', follow_redirects=True)
            self.assertIn(b'authorized', res.data.lower())

    def test_04_donation_and_request_workflow(self):
        """Test full donation lifecycle: create donation, request by NGO, approve by Donor, verify atomic deduction."""
        db = get_db()
        donor = db.users.find_one({'email': 'donor@foodshare.com'})
        ngo = db.users.find_one({'email': 'ngo@foodshare.com'})

        # 1. Login as Donor and create donation
        test_title = f"Automated Test Dal Makhani {int(datetime.now().timestamp())}"
        with self.client as c:
            c.post('/login', data={'email': 'donor@foodshare.com', 'password': 'Donor123!'})
            res = c.post('/donor/donations/create', data={
                'title': test_title,
                'category': 'Prepared Meals',
                'description': 'Rich slow-cooked lentils with fresh cream.',
                'quantity': '20',
                'unit': 'kg',
                'food_classification': 'Vegetarian',
                'allergens': 'Dairy',
                'storage_instructions': 'Hot hold above 65°C',
                'packaging_details': 'Sealed insulated tubs',
                'available_until': (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                'pickup_start': '01:00 PM',
                'pickup_end': '05:00 PM',
                'pickup_address': 'Hotel Kitchen Test Gate',
                'accuracy_confirmed': '1'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

        # Verify donation exists in DB
        created_donation = db.donations.find_one({'title': test_title})
        self.assertIsNotNone(created_donation)
        donation_id = created_donation['_id']
        self.assertEqual(created_donation['remaining_quantity'], 20.0)

        # 2. Login as NGO and request 8 kg
        with self.client as c:
            c.post('/login', data={'email': 'ngo@foodshare.com', 'password': 'Ngo123!'})
            res = c.post('/ngo/requests/submit', data={
                'donation_id': str(donation_id),
                'requested_quantity': '8',
                'intended_pickup_time': 'Today at 02:30 PM',
                'notes': 'For shelter dinner'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

        # Verify request created with status Pending
        req = db.donation_requests.find_one({'donation_id': donation_id, 'recipient_id': ngo['_id']})
        self.assertIsNotNone(req)
        self.assertEqual(req['status'], 'Pending')
        req_id = req['_id']

        # 3. Login as Donor and Approve the request
        with self.client as c:
            c.post('/login', data={'email': 'donor@foodshare.com', 'password': 'Donor123!'})
            res = c.post(f'/donor/requests/{req_id}/review', data={
                'action': 'approve',
                'notes': 'Approved, gate security notified.'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

        # 4. Verify atomic quantity deduction
        updated_donation = db.donations.find_one({'_id': donation_id})
        self.assertEqual(updated_donation['remaining_quantity'], 12.0)
        self.assertEqual(updated_donation['status'], 'Partially Reserved')

        # 5. Confirm handover
        with self.client as c:
            c.post('/login', data={'email': 'donor@foodshare.com', 'password': 'Donor123!'})
            res = c.post(f'/donor/requests/{req_id}/collect', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

        updated_req = db.donation_requests.find_one({'_id': req_id})
        self.assertEqual(updated_req['status'], 'Collected')
        print("\nEnd-to-end donation and request test PASSED successfully!")

if __name__ == '__main__':
    unittest.main()
