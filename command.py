class Command:
    def __init__(self, update, db):
        self.update = update
        self.db = db
        self.chat_id = self.update['message']['chat']['id']

    def execute(self):
        pass

    def _create_response(self, response, response_type):
        return {"response": response, "chat_id": self.chat_id, "type": response_type}


class StartCommand(Command):
    def execute(self):
        response = "Hello! How can I help you?"
        return self._create_response(response, "text")


class HelpCommand(Command):
    def execute(self):
        response = '''format for download chart is below\n\n/download\n31-12-2022\n1,2,3'''
        return self._create_response(response, "text")


class AddFundCommand(Command):
    def execute(self):
        try:
            amount = self.update['message']["text"].split("\n")[1]
            user_id = self.update['message']['from']['id']
            self.db.fund_account(user_id, amount)
            balance = self.db.get_balance(user_id)
            response = f"Your account has been funded with {amount}. Current balance: {balance}"
            return self._create_response(response, "text")
        except (IndexError, ValueError):
            response = f"Usage: /fund \n<amount>"
            return self._create_response(response, "text")


class GetFundCommand(Command):
    def execute(self):
        try:
            response = f"Your current balance is : {round(self.db.get_balance(1),2)}"
            return self._create_response(response, "text")
        except:
            response = f"Something wrong at server level"
            return self._create_response(response, "text")


class HoldingsCommand(Command):
    def execute(self):
        holdings = self.db.get_position()
        # response = "\n".join(
        #     [f"{h[1]} at {h[3]} for {h[2]}" for h in holdings])
        return self._create_response(holdings, "text")


class OrdersCommand(Command):
    def execute(self):
        holdings = self.db.get_orders()
        return self._create_response(holdings, "text")


class TradeExecutionCommand(Command):
    def execute(self):
        trade = {}
        try:
            for ticker in self.update["text"]:
                symbol = ticker["ticker"]
                cmp = ticker["cmp"]
                trade = self.db.insert_trade_if_valid(symbol, cmp)
                if trade["status"] == True:
                    response = f"Trade Executed of {symbol} at {cmp} for qauntity {trade['qauntity']}"
                    return self._create_response(response, "text")

            response = trade["message"]
            return self._create_response(response, "text")

        except (IndexError, ValueError):
            response = f"Trade failed At Server Level"
            return self._create_response(response, "text")


class ExitCommand(Command):
    def execute(self):
        try:
            symbol = self.update["symbol"]
            print("Going to exit :", symbol)
            status = self.db.exit_trade(symbol)
            if status:
                response = f"Trade exited ${symbol}."
                return self._create_response(response, "text")
            else:
                response = f"Trade failed to exit ${symbol}."
                return self._create_response(response, "text")

        except (IndexError, ValueError):
            response = f"Trade failed At Server Level"
            return self._create_response(response, "text")


class DefaultCommand(Command):
    def execute(self):
        message = self.update['message']['text']
        response = "Invalid command: " + message
        return self._create_response(response, "text")
