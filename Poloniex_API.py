import urllib
import urllib2
import json
import time
import hmac, hashlib


######################################################################################################
##                                                                                                  ##
##  	The following code was written by postbin user oipminer and can be found at 				##
##		https://pastebin.com/fbkheaRb																##
##																									##
##		I have added many of the Trading API calls to oipminer's code								##
##																									##
######################################################################################################

def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))


class Poloniex_API:
    def __init__(self, APIKey, Secret):
        self.APIKey = APIKey
        self.Secret = Secret

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if ('return' in after):
            if (isinstance(after['return'], list)):
                for x in xrange(0, len(after['return'])):
                    if (isinstance(after['return'][x], dict)):
                        if ('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))

        return after

    def api_query(self, command, req={}):

        if command == "returnTicker" or command == "return24Volume":
            ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/public?command=' + command))
            return json.loads(ret.read())
        elif (command == "returnOrderBook"):
            ret = urllib2.urlopen(urllib2.Request(
                'https://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])))
            return json.loads(ret.read())
        elif (command == "returnTradeHistory"):
            ret = urllib2.urlopen(urllib2.Request(
                'https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(
                    req['currencyPair'])))
            return json.loads(ret.read())
        else:
            if (command == "returnMyTradeHistory"):
                command = "returnTradeHistory"
            req['command'] = command
            req['nonce'] = int(time.time() * 1000)
            post_data = urllib.urlencode(req)

            print post_data

            sign = hmac.new(self.Secret, post_data, hashlib.sha512).hexdigest()
            print sign
            headers = {
                'Sign': sign,
                'Key': self.APIKey
            }

            urlReq = urllib2.Request('https://poloniex.com/tradingApi', post_data, headers)

            ret = urllib2.urlopen(urlReq)
            jsonRet = json.loads(ret.read())
        return self.post_process(jsonRet)

    def returnTicker(self):
        return self.api_query("returnTicker")

    def return24Volume(self):
        return self.api_query("return24Volume")

    def returnOrderBook(self, currencyPair):
        return self.api_query("returnOrderBook", {'currencyPair': currencyPair})

    def returnTradeHistory(self, currencyPair):
        return self.api_query("returnTradeHistory", {'currencyPair': currencyPair})

    # Returns candlestick chart data.
    # Call 			https://poloniex.com/public?command=returnChartData&currencyPair=BTC_XMR&start=1405699200&end=9999999999&period=14400
    # Inputs:
    # currencyPair	The currency pair e.g.  "BTC_BTS"
    # period		Time interval per candle in seconds; valid values are 300, 900, 1800, 7200, 14400, and 86400
    # start			start date range in UNIX timestamp
    # end			end date range in UNIX timestamp
    # Outputs:
    # date			UNIX timestamp
    def returnChartData(self, currencyPair, period, start, end):
        return self.api_query("returnChartData",
                              {'currencyPair': currencyPair, 'period': period, 'start': start, 'end': end})

    # print "Not Implemented"
    # return 0

    # Returns information about currencies
    def returnCurrencies(self):
        return self.api_query("returnCurrencies")

    # print "Not Implemented"
    # return 0

    ######################################################################################################
    ##                                                                                                  ##
    ##                                                                                                  ##
    ##							Start Trading (Account Specific) API Methods							##
    ##																									##
    ##																									##
    ######################################################################################################

    # Returns all of your balances.
    # Outputs:
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def returnBalances(self):
        return self.api_query('returnBalances')

    def returnCompleteBalances(self):
        return self.api_query('returnCompleteBalances')

    # print "Not Implemented"
    # return 0

    def returnDepositAddresses(self):
        return self.api_query('returnDepositAddresses')

    # print "Not Implemented"
    # return 0

    # Generates a new deposit address for the currency specified by the "currency" POST parameter.
    def generateNewAddress(self, currencyPair):
        # return self.api_query('generateNewAddress', {'currencyPair': currencyPair})
        print "Not Implemented"
        return 0

    def returnDepositsWithdrawals(self, start, end):
        return self.api_query('returnDepositsWithdrawals', {'start': start, 'end': end})

    # print "Not Implemented"
    # return 0

    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def returnOpenOrders(self, currencyPair):
        return self.api_query('returnOpenOrders', {"currencyPair": currencyPair})

    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def returnMyTradeHistory(self, currencyPair):
        return self.api_query('returnMyTradeHistory', {"currencyPair": currencyPair})

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs:
    # orderNumber   The order number
    def buy(self, currencyPair, rate, amount):
        return self.api_query('buy', {"currencyPair": currencyPair, "rate": rate, "amount": amount})

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs:
    # orderNumber   The order number
    def sell(self, currencyPair, rate, amount):
        return self.api_query('sell', {"currencyPair": currencyPair, "rate": rate, "amount": amount})

    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs:
    # succes        1 or 0
    def cancel(self, currencyPair, orderNumber):
        return self.api_query('cancelOrder', {"currencyPair": currencyPair, "orderNumber": orderNumber})

    # Cancels an order and places a new one of the same type in an atomic transaction
    def moveOrder(self, orderNumber, rate, amount, fillOrKill=0, immediateOrCancel=0, postOnly=0):
        return self.api_query('moveOrder',
                              {"orderNumber": orderNumber, "rate": rate, "amount": amount, "fillOrKill": fillOrKill,
                               "immediateOrCancel": immediateOrCancel, "postOnly": postOnly})

    # print "Not Implemented"
    # return 0

    # Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method, the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs:
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw', {"currency": currency, "amount": amount, "address": address})

    ######################################################################################################
    ##                                                                                                  ##
    ##                                                                                                  ##
    ##						Start Margin Trading (Account Specific) API Methods							##
    ##																									##
    ##																									##
    ######################################################################################################

    # Transfers funds from one account to another.
    def transferBalance(self, currency, amount, fromAccount, toAccount):
        return self.api_query('transferBalance', {"currency": currency, "amount": amount, "fromAccount": fromAccount,
                                                  "toAccount": toAccount})

    # print "Not Implemented"
    # return 0

    # Returns a summary of your entire margin account. This is the same information you will find in the Margin Account section of the Margin Trading page, under the Markets list. Sample output:
    def returnMarginAccountSummary(self):
        return self.api_query('returnMarginAccountSummary')

    # print "Not Implemented"
    # return 0

    # Places a margin buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". You may optionally specify a maximum lending rate using the "lendingRate" parameter.
    # Inputs:
    # currencyPair	currencyPair market to palce margin buy position in
    # rate 			price to buy at
    # amount 		number of coins to buy
    # lendingRate	percent rate of maximum interest rate on borrowed funds
    def marginBuy(self, currencyPair, rate, amount, lendingRate):
        return self.api_query('marginBuy', {"currencyPair": currencyPair, "rate": rate, "amount": amount,
                                            "lendingRate": lendingRate})

    # print "Not Implemented"
    # return 0

    # Places a margin sell order in a given market. Parameters and output are the same as for the marginBuy method.
    # Inputs:
    # currencyPair	currencyPair market to palce margin sell position in
    # rate 			price to sell at
    # amount 		number of coins to sell
    # lendingRate	percent rate of maximum interest rate on borrowed funds
    # Outputs:
    #
    def marginSell(self, currencyPair, rate, amount, lendingRate):
        return self.api_query('marginSell', {"currencyPair": currencyPair, "rate": rate, "amount": amount,
                                             "lendingRate": lendingRate})

    # print "Not Implemented"
    # return 0

    # Returns information about your margin position in a given market, specified by the "currencyPair" POST parameter (can be "all").
    # Inputs:
    # currencyPair	currencyPair market to get margin position information from
    # Outputs:
    #
    def getMarginPosition(self, currencyPair):
        return self.api_query('getMarginPosition', {"currencyPair": currencyPair})

    # print "Not Implemented"
    # return 0

    # Closes current Margin position in specified market
    # Inputs:
    # currencyPair	currencyPair market to close position in
    # Outputs:
    #
    def closeMarginPosition(self, currencyPair):
        return self.api_query('closeMarginPosition', {"currencyPair": currencyPair})
    # print "Not Implemented"
    # return 0
