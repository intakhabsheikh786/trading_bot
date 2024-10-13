import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_name='trading_bot.db'):
        self.db_name = db_name
        self.init_db()

    # Initialize the SQLite database and create necessary tables
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            trade_date TEXT NOT NULL
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL,
            average_price REAL NOT NULL,
            status TEXT NOT NULL
        )
        ''')

        # Create funds table to store balance
        c.execute('''
        CREATE TABLE IF NOT EXISTS funds (
            fund_id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance REAL NOT NULL
        )
        ''')

        # Create trade_threshold table to store per-trade risk threshold
        c.execute('''
        CREATE TABLE IF NOT EXISTS trade_threshold (
            threshold_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL UNIQUE,
            threshold REAL NOT NULL  -- Threshold per trade
        )
        ''')

        conn.commit()
        conn.close()

        # Function to add funds to a user account
    def fund_account(self, user_id, amount):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        # Insert user if not exists
        c.execute(
            'INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))

        # Update user balance
        c.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))

        conn.commit()
        conn.close()

        # Function to add funds to the balance
    def add_funds(cursor, amount):
        # Check if balance exists
        cursor.execute('SELECT balance FROM funds WHERE fund_id = 1;')
        result = cursor.fetchone()

        if result:
            current_balance = result[0]
            new_balance = current_balance + amount
            cursor.execute(
                'UPDATE funds SET balance = ? WHERE fund_id = 1;', (new_balance,))
        else:
            cursor.execute(
                'INSERT INTO funds (balance) VALUES (?);', (amount,))

        print(
            f"Funds added: {amount}. Current balance: {new_balance if result else amount}.")

    def set_trade_threshold(cursor, risk_amount):
        cursor.execute(
            'SELECT threshold FROM trade_threshold WHERE threshold_id = 1;')
        result = cursor.fetchone()

        if result:
            cursor.execute(
                'UPDATE trade_threshold SET threshold = ? WHERE threshold_id = 1;', (risk_amount,))
        else:
            cursor.execute(
                'INSERT INTO trade_threshold (threshold) VALUES (?);', (risk_amount,))

        print(f"Trade threshold set to {risk_amount} per trade.")

    # Function to fetch account balance

    def get_balance(self, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()

        conn.close()

        # If the user doesn't exist, return 0 balance
        return result[0] if result else 0

    def get_position(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM holdings where status = "open"')
        holdings = c.fetchall()

        json_data = [dict(holding) for holding in holdings]

        conn.close()
        # If the user doesn't exist, return 0 balance
        return json_data

    def insert_trade_if_valid(self, symbol, price):
        print(symbol, price)

        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        c.execute('''
        SELECT average_price FROM holdings
        WHERE symbol = ? and status = "open";
        ''', (symbol,))

        average_price = c.fetchone()

        c.execute('SELECT balance FROM funds WHERE fund_id = 1;')
        balance_result = c.fetchone()

        # Get the risk threshold
        c.execute('SELECT threshold FROM trade_threshold WHERE type = "Buy"')
        risk_threshold = c.fetchone()[0]

        if not balance_result or balance_result[0] < risk_threshold:
            print(f"Trade for {symbol} not executed. Insufficient funds.")
            return False

        quantity = int(risk_threshold / price)
        trade_cost = quantity * price

        # If the holding exists, compare the CMP
        if average_price:
            average_price = average_price[0]
            if price < average_price * 0.975:  # Check if CMP is 2.5% less than average price
                self.insert_trade(c, symbol, quantity, price)
                print(
                    f"Trade inserted for {symbol}: {quantity} shares at {price}.")
            else:
                print(
                    f"Trade for {symbol} not inserted. CMP is not 2.5% lower than average.")
                conn.close()
                return False
        else:
            # If the holding does not exist, insert the trade directly
            self.insert_trade(c, symbol, quantity, price)
            print(
                f"Trade inserted for {symbol}: {quantity} shares at {price} (no holding found).")

        # Deduct the trade cost from the balance
        new_balance = balance_result[0] - trade_cost
        c.execute('UPDATE funds SET balance = ? WHERE fund_id = 1;',
                  (new_balance,))
        print(f"Buy trade cost deducted. New balance: {new_balance}.")

        conn.commit()
        conn.close()
        return True

    def insert_trade(self, cursor, symbol, quantity, price):
        # Insert the trade
        cursor.execute('''
        INSERT INTO trades (symbol, quantity, price, type, status, trade_date)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, quantity, price, "buy", "open", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        # Update the average price in holdings
        self.update_average_price(cursor, symbol)

    def update_average_price(self, cursor, symbol):
        # Calculate the total cost and total quantity for the symbol
        cursor.execute('''
        SELECT SUM(price * quantity) AS total_cost, SUM(quantity) AS total_quantity
        FROM trades
        WHERE symbol = ? and type = ? and status = ?;
        ''', (symbol, "buy", "open", ))

        result = cursor.fetchone()
        total_cost = result[0] if result[0] is not None else 0
        total_quantity = result[1] if result[1] is not None else 0

        # Calculate average price
        average_price = total_cost / total_quantity if total_quantity > 0 else 0

        # Update or insert into holdings table
    # Update or insert into holdings table
        cursor.execute('''
            INSERT INTO holdings (symbol, quantity, average_price, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
            quantity = excluded.quantity,
            average_price = excluded.average_price;
            ''', (symbol, total_quantity, average_price, "open"))

    def exit_trade(self, symbol):
        # Exit the trade
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        ticker = symbol["symbol"]
        quantity = symbol["quantity"]
        cmp = symbol["cmp"]

        c.execute(
            'UPDATE trades SET status = "close" where symbol = ?;', (ticker, ))

        c.execute('''
            INSERT INTO trades (symbol, quantity, price, type, status, trade_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (ticker, quantity, cmp, "sell", "close", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # Update the average price in holdings

        c.execute(
            'DELETE FROM holdings WHERE symbol = ?;', (ticker, ))

        conn.commit()
        conn.close()

        return True

    def test(self, ticker, price):
        print(ticker, price)
        return True
