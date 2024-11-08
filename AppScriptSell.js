const exit_trade_prod_url = "https://trading-bot-7d9t.onrender.com/exit_trade";
const get_position_prod_url = "https://trading-bot-7d9t.onrender.com/get_position";

const exit_trade_test_url = " https://e16a-183-87-168-248.ngrok-free.app/exit_trade";
const get_position_test_url = "https://e16a-183-87-168-248.ngrok-free.app/get_position";


const sell_sheet_url = "https://docs.google.com/spreadsheets/d/1Drp0pgi4QOw7amOowJNiRrjNdKwCW-JWiJ5MId1DfVw/edit?gid=0#gid=0";

function createTimeTriggerAt() {
  Logger.log("Creating Trigger...");
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if(triggers[i].getHandlerFunction() === "scheduleTriggerTradingHours"){
      Logger.log("Deleting trigger: " + triggers[i].getHandlerFunction());
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }

   ScriptApp.newTrigger('scheduleTriggerTradingHours')
    .timeBased()
    .everyMinutes(15)
    .create();
  Logger.log("Trigger Created...");

}

function scheduleTriggerTradingHours() {
  var now = new Date();
  var startTime = new Date(now);
  var endTime = new Date(now);

  startTime.setHours(9);
  startTime.setMinutes(15);
  startTime.setSeconds(0);
  
  endTime.setHours(15);
  endTime.setMinutes(15);
  endTime.setSeconds(0);
  if (now >= startTime && now <= endTime) {
    getAndComparePosition();
  }
}


function getAndComparePosition() {

  var sheet = SpreadsheetApp.openByUrl(sell_sheet_url);
  const profitPer = 6;

  const holdings = getPositionFromBot();
  const positions = JSON.parse(holdings); 

  positions.forEach(function(position) {
    const tickerRange = sheet.getRange('A3:A98').getValues();
    for (let i = 0; i < tickerRange.length; i++) {
      if (tickerRange[i][0] == position.symbol) {
        const row = i + 3;  
        const cmp = sheet.getRange('C' + row).getValue();
        const avg = position.average_price;
        const diff = cmp - avg;
        const per = (diff/avg) * 100;
        if (per >= profitPer) {
          exit_trade({...position, cmp});
          Logger.log(`Going to exit for Ttcker: "${position.symbol}" | CMP: "${cmp}" | AVG: "${position.average_price}" at P/L: "${per}"`);
          break;
        }
        Logger.log(`Ticker: "${position.symbol}" | CMP: "${cmp}" | AVG: "${position.average_price}" at P/L: "${per}"`);
        break;
      }
    }
  });

}

function exit_trade(symbol) {
  var telegramApiUrl = exit_trade_prod_url
  var chatId = "1316144383";  // Replace with your chat ID
  var payload = {
    "message": {
      "chat" : {
        "id" : chatId
      }
    },
    "symbol": symbol
  };

  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload)
  };
  UrlFetchApp.fetch(telegramApiUrl, options);
}



function getPositionFromBot() {
  var telegramApiUrl = get_position_prod_url
  var options = {
    "method": "post",
    "contentType": "application/json",
  };

  return UrlFetchApp.fetch(telegramApiUrl, options);
}