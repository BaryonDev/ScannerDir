import requests
import time
from bs4 import BeautifulSoup
import difflib
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UserEnumerator:
    def __init__(self, url, username_file):
        self.url = url
        self.username_file = username_file
        self.session = requests.Session()
        self.baseline_response = None

    def get_baseline(self):
        print("Obtaining baseline response...")
        self.baseline_response = self.send_request("nonexistent_user_12345")
        return self.baseline_response

    def send_request(self, username):
        data = {
            "username": username,
            "password": "invalid_password_54321"
        }
        try:
            response = self.session.post(self.url, data=data, verify=False, allow_redirects=True)
            return response
        except requests.RequestException as e:
            print(f"Error sending request: {e}")
            return None

    def analyze_response(self, response, username):
        if not response:
            return False

        if not self.baseline_response:
            self.get_baseline()

        diff = difflib.SequenceMatcher(None, self.baseline_response.text, response.text).ratio()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        error_messages = soup.find_all(class_='error-message')
        
        if diff < 0.95 or any("Invalid username" not in msg.text for msg in error_messages):
            print(f"Potential valid username found: {username}")
            print(f"Difference ratio: {diff}")
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(response.content)}")
            if error_messages:
                print("Error messages:")
                for msg in error_messages:
                    print(f"- {msg.text.strip()}")
            print("\n")
            return True
        return False

    def enumerate_usernames(self):
        valid_usernames = []
        with open(self.username_file, 'r') as file:
            usernames = file.read().splitlines()

        total = len(usernames)
        for i, username in enumerate(usernames, 1):
            print(f"Testing username {i}/{total}: {username}")
            response = self.send_request(username)
            if self.analyze_response(response, username):
                valid_usernames.append(username)
            time.sleep(1)

        return valid_usernames

def main():
    url = input("Enter the target URL: ")
    username_file = input("Enter the path to the username file: ")

    enumerator = UserEnumerator(url, username_file)
    valid_usernames = enumerator.enumerate_usernames()

    print("\nEnumeration complete. Potentially valid usernames:")
    for username in valid_usernames:
        print(username)

if __name__ == "__main__":
    main()