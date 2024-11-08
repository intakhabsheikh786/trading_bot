var prod_url = "https://trading-bot-7d9t.onrender.com/trade";
var test_url = "https://e16a-183-87-168-248.ngrok-free.app/trade";
var sheet_url = "https://docs.google.com/spreadsheets/d/1Drp0pgi4QOw7amOowJNiRrjNdKwCW-JWiJ5MId1DfVw/edit?gid=0#gid=0"

function createTimeTriggerAt() {

  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if(triggers[i].getHandlerFunction() === "sendTickerInfo"){
      Logger.log("Deleting trigger: " + triggers[i].getHandlerFunction());
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  ScriptApp.newTrigger('sendTickerInfo')
    .timeBased()
    .atHour(15)           
    .nearMinute(1)        
    .everyDays(1)
    .inTimezone(Session.getScriptTimeZone())  
    .create();
  
  Logger.log("Time-based trigger created.");
}

function sendTickerInfo() {

  var today = new Date();
  var day = today.getDay(); 
  if (day >= 1 && day <= 5) {
    Logger.log("Running at 3 PM on a weekday.");
    const tickers = getCMPforTickers();
    sendTrade(tickers);
  }

}


function getCMPforTickers() {
  var tickers_for_send = [];
  var sheet = SpreadsheetApp.openByUrl(sheet_url);
  var worksheet = sheet.getSheetByName("ETF_SHOP"); 
  var tickers = [worksheet.getRange('I4').getValue(), 
                 worksheet.getRange('I5').getValue(), 
                 worksheet.getRange('I6').getValue()];
  tickers.forEach(function(ticker) {
    var tickerRange = sheet.getRange('A3:A98').getValues();
    for (var i = 0; i < tickerRange.length; i++) {
      if (tickerRange[i][0] == ticker) { 
        var row = i + 3;  
        var cmp = sheet.getRange('C' + row).getValue();  
        Logger.log("Ticker: " + ticker + " | CMP: " + cmp);
        tickers_for_send.push({
          ticker, cmp
        })
        break;  
      }
    }
  });
  return tickers_for_send;
}




function sendTrade(message) {
  var telegramApiUrl = prod_url;
  var chatId = "1316144383";
  var payload = {
    "message": {
      "chat" : {
        "id" : chatId
      }
    },
    "text": message
  };

  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload)
  };

  UrlFetchApp.fetch(telegramApiUrl, options);
}
