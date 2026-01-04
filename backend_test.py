import requests
import sys
import json
from datetime import datetime

class RiddleGameAPITester:
    def __init__(self, base_url="https://wordpuzzle-3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        username = f"testuser_{timestamp}"
        password = "TestPass123!"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_data = response['user']
            return True, username, password
        return False, None, None

    def test_user_login(self, username, password):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_data = response['user']
            return True
        return False

    def test_get_user_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_riddle_generation(self, difficulty="easy"):
        """Test riddle generation"""
        success, response = self.run_test(
            f"Generate {difficulty.title()} Riddle",
            "POST",
            "riddle/generate",
            200,
            data={"difficulty": difficulty}
        )
        
        if success and 'riddle_id' in response:
            return True, response
        return False, None

    def test_riddle_guess(self, riddle_data, guess="KEYBOARD"):
        """Test riddle guess submission"""
        success, response = self.run_test(
            "Submit Riddle Guess",
            "POST",
            "riddle/guess",
            200,
            data={
                "riddle_id": riddle_data['riddle_id'],
                "guess": guess,
                "time_remaining": 100,
                "guesses_used": 1
            }
        )
        return success, response

    def test_premium_unlock(self):
        """Test premium unlock (mocked)"""
        success, response = self.run_test(
            "Premium Unlock (Mock)",
            "POST",
            "premium/unlock",
            200
        )
        return success

    def test_premium_riddle_access(self):
        """Test access to premium riddles after unlock"""
        success, response = self.run_test(
            "Generate Very Hard Riddle (Premium)",
            "POST",
            "riddle/generate",
            200,
            data={"difficulty": "very_hard"}
        )
        return success

    def test_global_leaderboard(self):
        """Test global leaderboard"""
        success, response = self.run_test(
            "Global Leaderboard",
            "GET",
            "leaderboard/global",
            200
        )
        return success

    def test_friends_leaderboard(self):
        """Test friends leaderboard"""
        success, response = self.run_test(
            "Friends Leaderboard",
            "GET",
            "leaderboard/friends",
            200
        )
        return success

    def test_add_friend(self, friend_username="nonexistent_user"):
        """Test adding a friend"""
        success, response = self.run_test(
            "Add Friend",
            "POST",
            "friends/add",
            404,  # Expecting 404 for non-existent user
            data={"friend_username": friend_username}
        )
        return success

    def test_user_stats(self):
        """Test user statistics"""
        success, response = self.run_test(
            "User Statistics",
            "GET",
            "user/stats",
            200
        )
        return success

    def test_invalid_token_access(self):
        """Test access with invalid token"""
        old_token = self.token
        self.token = "invalid_token_123"
        
        success, response = self.run_test(
            "Invalid Token Access",
            "GET",
            "auth/me",
            401  # Expecting unauthorized
        )
        
        self.token = old_token  # Restore valid token
        return success

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Riddle Game API Tests")
        print("=" * 50)
        
        # Test user registration and authentication
        reg_success, username, password = self.test_user_registration()
        if not reg_success:
            print("❌ Registration failed, stopping tests")
            return False
        
        # Test login
        if not self.test_user_login(username, password):
            print("❌ Login failed, stopping tests")
            return False
        
        # Test user profile
        self.test_get_user_profile()
        
        # Test riddle generation for free difficulties
        easy_riddle = None
        for difficulty in ["easy", "medium", "hard"]:
            success, riddle_data = self.test_riddle_generation(difficulty)
            if success and difficulty == "easy":
                easy_riddle = riddle_data
        
        # Test riddle guess if we have a riddle
        if easy_riddle:
            self.test_riddle_guess(easy_riddle, "KEYBOARD")
        
        # Test premium functionality
        self.test_premium_unlock()
        self.test_premium_riddle_access()
        
        # Test leaderboards
        self.test_global_leaderboard()
        self.test_friends_leaderboard()
        
        # Test friend functionality
        self.test_add_friend()
        
        # Test user stats
        self.test_user_stats()
        
        # Test security
        self.test_invalid_token_access()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = RiddleGameAPITester()
    success = tester.run_comprehensive_test()
    
    # Save detailed results
    with open('/app/test_reports/backend_api_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': f"{(tester.tests_passed/tester.tests_run)*100:.1f}%" if tester.tests_run > 0 else "0%",
            'test_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())