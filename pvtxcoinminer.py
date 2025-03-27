import os
import configparser
import requests
import time
from getpass import getpass

SERVER_URL = "https://pvtxpage-production.up.railway.app/"
CONFIG_FILE = "pvtxc_config.ini"

class PVTXCClient:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.session = requests.Session()
        self.user_id = None
        self.username = None
        self.password = None
        
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
            if 'auth' in self.config:
                self.user_id = self.config['auth'].get('user_id')
                self.username = self.config['auth'].get('username')

    def save_config(self):
        if not self.config.has_section('auth'):
            self.config.add_section('auth')
        self.config.set('auth', 'user_id', str(self.user_id))
        self.config.set('auth', 'username', str(self.username))
        with open(CONFIG_FILE, 'w') as f:
            self.config.write(f)

    def login(self):
        if self.user_id:
            print(f"Found saved credentials for {self.username}")
            password = getpass("Enter password: ")
            resp = self.session.post(
                f"{SERVER_URL}/login",
                json={"username": self.username, "password": password}
            )
            if resp.status_code == 200:
                self.password = password
                return True

        while True:
            self.username = input("Username: ").strip()
            password = getpass("Password: ")
            
            resp = self.session.post(
                f"{SERVER_URL}/login",
                json={"username": self.username, "password": password}
            )
            
            if resp.status_code == 200:
                self.user_id = resp.json()['user_id']
                self.password = password
                self.save_config()
                return True
            else:
                print("Login failed. Register? (y/n)")
                if input().lower() == 'y':
                    if self.register(password):
                        return True
                else:
                    continue

    def register(self, password):
        resp = self.session.post(
            f"{SERVER_URL}/register",
            json={"username": self.username, "password": password}
        )
        if resp.status_code == 201:
            self.user_id = resp.json()['user_id']
            self.password = password
            self.save_config()
            return True
        print(f"Registration failed: {resp.text}")
        return False

    def get_balance(self):
        resp = self.session.post(
            f"{SERVER_URL}/login",
            json={"username": self.username, "password": self.password}
        )
        if resp.status_code == 200:
            return resp.json().get('balance')
        return None

    def mining_loop(self):
        while True:
            try:
                # Get problem
                resp = self.session.post(
                    f"{SERVER_URL}/problem",
                    json={"user_id": self.user_id, "password": self.password}
                )
                if resp.status_code != 200:
                    time.sleep(1)
                    continue
                
                problem_data = resp.json()
                problem_id = problem_data['problem_id']
                problem = problem_data['problem']
                
                # Solve problem
                answer = eval(problem.replace('÷', '/'))
                
                # Submit solution
                mine_resp = self.session.post(
                    f"{SERVER_URL}/mine",
                    json={
                        "user_id": self.user_id,
                        "password": self.password,
                        "problem_id": problem_id,
                        "answer": answer
                    }
                )
                
                if mine_resp.status_code == 200:
                    result = mine_resp.json()
                    print(f"Mined {result['reward']} PVTXC | Balance: {result['balance']}")
                elif mine_resp.status_code == 429:
                    print("Too fast, waiting...")
                    time.sleep(1)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error: {str(e)}")
                time.sleep(1)

    def transfer(self):
        receiver = input("Receiver username: ").strip()
        amount = input("Amount to transfer: ").strip()
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except:
            print("Invalid amount")
            return
        
        resp = self.session.post(
            f"{SERVER_URL}/transfer",
            json={
                "user_id": self.user_id,
                "password": self.password,
                "receiver": receiver,
                "amount": amount
            }
        )
        
        if resp.status_code == 200:
            print("Transfer successful!")
        else:
            print(f"Error: {resp.json().get('error', 'Unknown error')}")

    def show_transactions(self):
        resp = self.session.post(
            f"{SERVER_URL}/transactions",
            json={"user_id": self.user_id, "password": self.password}
        )
        
        if resp.status_code == 200:
            print("\nTransaction History:")
            for txn in resp.json():
                print(f"{txn['timestamp']} - {txn['type'].upper()} {txn['amount']} ", end='')
                if txn['target_id']:
                    if txn['amount'] > 0:
                        print(f"from {txn['target_id']}")
                    else:
                        print(f"to {txn['target_id']}")
                else:
                    print()
        else:
            print("Failed to retrieve transactions")

if __name__ == "__main__":
    client = PVTXCClient()
    
    if not client.login():
        print("Exiting...")
        exit()

    while True:
        print("\nPVTXC Miner")
        print("1. Start mining")
        print("2. Check balance")
        print("3. Transfer coins")
        print("4. View transactions")
        print("5. Exit")
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            try:
                print("Starting miner (Ctrl+C to stop)...")
                client.mining_loop()
            except KeyboardInterrupt:
                print("\nMining stopped")
        elif choice == '2':
            balance = client.get_balance()
            if balance is not None:
                print(f"Current balance: {balance:.4f} PVTXC")
        elif choice == '3':
            client.transfer()
        elif choice == '4':
            client.show_transactions()
        elif choice == '5':
            break
        else:
            print("Invalid choice")