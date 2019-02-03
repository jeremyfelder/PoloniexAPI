from Poloniex_API import Poloniex_API
import json
import datetime
import time
import sys, getopt
import os
import urllib2 



############ For testing purposes #####################
# if os.path.exists("FilledTrades.txt"):
#     os.remove("FilledTrades.txt")
FilledTrades = open("FilledTrades.txt", "a")
# if os.path.exists("ErrorFile.txt"):
#     os.remove("ErrorFile.txt")
ErrorFile = open("ErrorFile.txt", "a")


def errorFileWrite(error, area, start_time):
	ErrorFile.write("Current time:" + time.ctime(time.time()) + "\n")
	mins, secs = divmod(int(time.time()) - start_time, 60)
	hours, minutes = divmod(mins, 60)
	ErrorFile.write("Time from start: " + str(hours) + ":" + str(minutes) + ":" + str(secs) + "\n")
	ErrorFile.write("Error: " + str(error) + "\n")
	ErrorFile.write("From: " + area + "\n")
	ErrorFile.flush()
	return 0


def margin_amount(margin_percentage, margin_balances):
	totalBorrowedValue = float(margin_balances["totalBorrowedValue"])
	netValue = float(margin_balances["netValue"])
	amount_to_use = (netValue/(margin_percentage*0.01))-totalBorrowedValue
	return amount_to_use



#100-((totalBorrowedValue-netValue)/netValue) = 66
#100-((totalBorrowedValue+extra-netValue)/netValue) = 55

#####################    Need to add in open order timeout capability       ##########################
#####################    Need to add try execpt blocks for error handling   ##########################
def open_pos(polo, long_or_short, rate, amount, currency_pair, cancel_unfilled, timeout, start_time):
	no_open_positions = True
	canceled = False
	pos_amount = 0
	ret = None
	open_pos_ret = None
	timeout_not_reached = True

	# Execute Margin Trade
	if long_or_short == "long":
		try:
			ret = polo.marginBuy(currency_pair, rate, amount, 0.001)
		except Exception as e:
			errorFileWrite(e, "marginBuy in open_pos", start_time)
	else:
		try:
			ret = polo.marginSell(currency_pair, rate, amount, 0.001)
		except Exception as e:
			errorFileWrite(e, "marginSell in open_pos", start_time)

	try:	
		# Check for successful open order
		if ret["message"] == "Margin order placed.":
			# Continuously check for filled order
			while(no_open_positions and timeout_not_reached):
				time.sleep(0.3)
				try:
					open_pos_ret = polo.getMarginPosition(currency_pair)
				except Exception as e:
					errorFileWrite(e, "getMarginPosition in open_pos", start_time)
				# Check for timeout reached
				if time.time()-start_time > timeout:
					timeout_not_reached = False
					break
				if open_pos_ret["type"] is not "none":
					FilledTrades.write("Trade filled at: " + time.ctime(time.time()) + "\n")
					FilledTrades.write(str(open_pos_ret)+"\n")
					# Once filled, set variables for close_long
					no_open_positions = False
					pos_amount = float(open_pos_ret["amount"])
					# Allows for user to specify fill on the first time or cancel the remainder
					if pos_amount <> amount and cancel_unfilled:
						try:
							cancel_remainder = polo.cancel(currency_pair, int(ret["orderNumber"]))
						except Exception as e:
							errorFileWrite(e, "cancel Unfilled in open_pos", start_time)
						if cancel_remainder["success"]:
							canceled = True
			if not timeout_not_reached:
				try:
					cancel_remainder = polo.cancel(currency_pair, int(ret["orderNumber"]))
				except Exception as e:
					errorFileWrite(e, "cancel Timeout in open_pos", start_time)
				if cancel_remainder["success"]:
					timeout_canceled = True
		#fix this elif statement!!!!!
		elif ret["success"] == 0:
			print ret
			trade_made = False
			sys.exit(2)
		else:
			print "Error. Exiting."
			sys.exit(2)
	except KeyError as k:
		print ret
		sys.exit(2)
	return open_pos_ret, canceled, timeout_canceled


###########################   Add capability to specify Market or Limit to close   ##########################
def close_position(polo, close_rate, amount, currency_pair, profit_target,
 allowable_loss, canceled, start_time):
	closed = False
	# Get current position amount to double check total amount
	try:
		open_position = polo.getMarginPosition(currency_pair)
	except Exception as e:
		errorFileWrite(e, "getMarginPosition in closed_position", start_time)
	pos_type = open_position["type"]
# If statement not necessary for now since if the rest of the open order filled 
# we still want to close the position with the parameters set
#if open_position["amount"] == amount or canceled:
	while(not closed):
		time.sleep(0.3)
		try:
			rate = float((polo.returnTradeHistory(currency_pair))[0]["rate"])
		except Exception as e:
			errorFileWrite(e, "returnTradeHistory in closed_position", start_time)

		profit_loss = float(open_position["pl"])
		# The following if statement is necessary because of the mutual exclusiveness of profit_target and close_long_rate
		if ((profit_loss > profit_target and profit_target is not None) or 
			(profit_loss < allowable_loss and allowable_loss is not None) or 
			(rate > close_rate and close_rate is not None and pos_type == "long") or 
			(rate < close_rate and close_rate is not None and pos_type == "short")):
			try:
				closed_position = polo.closeMarginPosition(currency_pair)
			except Exception as e:
				errorFileWrite(e, "closeMarginPosition in closed_position", start_time)
			if closed_position["resultingTrades"]:
				closed = True
#else:
#	print "Rest of long must have filled"
	return closed


def check_params(long_rate, buy_rate, close_long_rate, short_rate, sell_rate, 
	close_short_rate, margin_percent, currency_pair, cancel, allowable_loss, profit_target, cancel_unfilled, secret, key, timeout):
	
	secret = "60BCO1HN-ELKXNDM1-XG4NDV03-UUH8D5SA"
	key = "aef835063d5caa603b0c329aef3e30332b962136c87711d8ce12a591d5d9848eb60f63b09598179f698185354147951cfabd737e6d09272d419ee04f768f29ae"

	looking_message = [" -- Checking rate", " /  Checking rate", " |  Checking rate", " \  Checking rate"]
	i = 0
	# Set loop params
	order_filled_and_closed = False
	closed_position = False
	current_rate = None
	start_time = time.time()
	# Initialize Trading API connection
	poloAPI = Poloniex_API(secret, key)

	# Set order params
	try:
		balances = poloAPI.returnMarginAccountSummary()
	except Exception as e:
		errorFileWrite(e, "returnMarginAccountSummary in check_params", start_time)
	# Start checking rate and trading
	while(not order_filled_and_closed):
		# Prints Checking Rate message
		print "\r" + looking_message[i],
		i += 1
		if i == 4:
			i = 0
		# Prevents IP ban for more than 6 API calls within 1 sec
		time.sleep(0.3)
		print time.ctime(time.time()) + "      ",
		# Check the current rate for the given currency_pair
		# Should probably be using the subscription to the websocket
		try:
			current_rate = float((poloAPI.returnTradeHistory(currency_pair))[0]["rate"])
		except Exception as e:
			errorFileWrite(e, "returnTradeHistory in check_params\n" + str(current_rate), start_time)
		
		# Check for long trade		
		if current_rate < long_rate and long_rate is not None and current_rate is not None:
			# Set the amount to be bought
			amount = margin_amount(margin_percent, balances)/buy_rate
			# Maybe add another function that has all of this duplicate code for long and short??
			open_position_info, canceled, timeout_canceled = open_pos(poloAPI, "long", buy_rate, amount, currency_pair, cancel_unfilled, timeout, start_time)
			print json.dumps(open_position_info, sort_keys = True, indent =4, separators=(',', ':'))
################# add conditions to allow for opening positions and not closing them ###################
################# this allows for staggered entries to a position  					 ###################
			if open_position_info and (close_long_rate is not None or profit_target is not None):
				closed_position = close_position(poloAPI, close_long_rate, open_position_info["amount"], currency_pair, profit_target, allowable_loss, canceled, start_time)
		# Check for short trade
		elif current_rate > short_rate and short_rate is not None and current_rate is not None:
			amount = margin_amount(margin_percent, balances)/sell_rate
			open_position_info, canceled, timeout_canceled = open_pos(poloAPI, "short", sell_rate, amount, currency_pair, cancel_unfilled, timeout, start_time)
			print json.dumps(open_position_info, sort_keys = True, indent =4, separators=(',', ':'))
			if open_position_info:
				closed_position = close_position(poloAPI, close_short_rate, open_position_info["amount"], currency_pair, profit_target, allowable_loss, canceled, start_time)
		
		if closed_position:
			order_filled_and_closed = True
			
###########################   CHANGE TO ALLOW FOR CLOSING AN ALREADY OPEN POSITION   ##########################
# Command line options and Usage			
def main(argv):
	# Give default values for all variables
	long_rate=short_rate=buy_rate=sell_rate=close_short_rate=close_long_rate=None
	margin_percent=currency_pair=profit_target=allowable_loss=secret=key=timeout=None
	cancel_unfilled = cancel = help_chosen = False

	# Parse command line variables
	try:
		opts, args = getopt.getopt(argv,"hl:b:L:s:z:S:p:c:g:r:Cut:",["help","long_rate=","buy_rate=","close_long_rate=", "short_rate=","sell_rate=","close_short_rate=","margin_percent=","currency_pair=", "cancel", "profit=","loss=","cancel_unfilled", "secret=", "key=", "timeout="])
	except getopt.GetoptError:
		print 'Invalid Option. Use -h or --help for command line syntax'
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ('-h', "--help"):
			help_chosen = True
			print '\n\nSYNTAX\n\nShabbatTradeTest.py -l <long_rate> -b <buy_rate> -L <close_long_rate> -s <short_rate> -z <sell_rate> -S <close_short_rate> -p <percent_margin> -c <currency_pair>\n'
			print 'OPTIONS\n\n-l --long_rate\t\t\t This is the rate that triggers a buy order to be placed at the buy_rate.\n'
			print '-b --buy_rate\t\t\t This is the rate at which a buy order will be placed.\n'
			print "-L --close_long_rate\t\t This is the rate that a sell order will be placed to close a long position.\n\t \
			This parameter is mutually exclusive with profit.\n\t \
			If close_short_rate and profit are specified, the program will exit with an error.\n"
			print "-s --short_rate\t\t\t This is the rate that triggers a sell order to be placed at the sell_rate.\n"
			print "-z --sell_rate\t\t\t This is the rate at which a sell order will be placed.\n"
			print "-S --close_short_rate\t\t This is the rate that a buy order will be placed to close a short position.\n\t \
			This parameter is mutually exclusive with profit.\n\t \
			If close_short_rate and profit are specified, the program will exit with an error.\n"
			print "-p --margin_percent\t\t This is the percent of total MarginValue to be used in an order.\n\t\t\t\t i.e. If MarginValue = .1BTC, TotalMarginValue = .25BTC, and percent_margin = .5,\n\t\t\t\t then the total amount spent at any given rate will be .125 BTC\n"
			print "-c --currency_pair\t\t This is the currency pair that trades will execute on.\n"
			print "-g --profit\t\t\t The profit target on a position, at which amount the position will be closed.\n\t \
			This parameter is mutually exclusive with close_short_rate and close_long_rate.\n\t \
			If profit and either of close_long_rate or close_short_rate are specified, the program will exit with an error\n"
			print "-r --loss\t\t\t The allowable loss on a position until it should be closed. This must be a negative number.\n"
			print "-C --cancel\t\t\t If a long or short trade has been executed and both long and short rates were specified\n\t\t\t\t initially, the trade that did not execute will be canceled.\n"
			print "-u --cancel_unfilled\t\t Cancels any unfilled long or short portion of an open order.\n"
			print "--secret\t\t\t This is the Secret of the API Pair"
			print "--key\t\t\t This is the Key of the API Pair"
			print "-t --timeout\t\t\t The amount of time in hours before an open order is canceled"
			sys.exit()
		elif opt in ("-l", "--long_rate"):
			long_rate = float(arg)
		elif opt in ("-b", "--buy_rate"):
			buy_rate = float(arg)
		elif opt in ("-L", "--close_long_rate"):
			if profit_target is not None:
				print "Parameters close_long_rate and profit are mutually exclusive."
				sys.exit(2)
			else:
				close_long_rate = float(arg)
		elif opt in ("-s", "--short_rate"):
			short_rate = float(arg)
		elif opt in ("-z", "--sell_rate"):
			sell_rate = float(arg)
		elif opt in ("-S", "--close_short_rate"):
			if profit_target is not None:
				print "Parameters close_short_rate and profit are mutually exclusive."
				sys.exit(2)
			else:
				close_short_rate = float(arg)
		elif opt in ("-p", "--margin_percent"):
			margin_percent = int(arg)
		elif opt in ("-c", "--currency_pair"):
			currency_pair = arg
		elif opt in ("-g", "--profit"):
			if close_long_rate is not None or close_short_rate is not None:
				print "Parameters profit and close_short_rate/close_long_rate are mutually exclusive."
				sys.exit(2)
			else:
				profit_target = float(arg)
		elif opt in ("-r", "--loss"):
			if float(arg) >= 0 :
				print "Parameter loss must be a negative number."
				sys.exit(2)
			else:
				allowable_loss = float(arg)
		elif opt in ("-C", "--cancel"):
			cancel = True
		elif opt in ("-u", "--cancel_unfilled"):
			cancel_unfilled = True
		elif opt in ("--secret"):
			secret = arg
		elif opt in ("--key"):
			key = arg
		elif opt in ("-t", "--timeout"):
			timeout = int(arg)*3600

	print ("Long Rate: "+ str(long_rate) +"\n" + 
	"Buy Rate: "+ str(buy_rate) +"\n" + 
	"Close Long Rate: " + str(close_long_rate) + "\n" +
	"Short Rate: " + str(short_rate) + "\n" +
	"Sell Rate: " + str(sell_rate) + "\n" +
	"Close Short Rate: " + str(close_short_rate) + "\n" +
	"Margin Percent: " + str(margin_percent) + "\n" +
	"Currency Pair: " + str(currency_pair) + "\n" +
	"Cancel: " + str(cancel) + "\n" +
	"Allowable Loss: " + str(allowable_loss) + "\n" +
	"Profit Target: " + str(profit_target) + "\n" +
	"Cancel Unfilled: " + str(cancel_unfilled) + "\n" +
	"Secret: " + str(secret) + "\n" +
	"Key: " + str(key) + "\n" +
	"Timeout: " + str(timeout) + "\n")


	if not help_chosen:
		check_params(long_rate, buy_rate, close_long_rate, 
						short_rate, sell_rate, close_short_rate, 
						margin_percent, currency_pair, cancel, 
						allowable_loss, profit_target, cancel_unfilled,
						secret, key, timeout)

if __name__ == "__main__":
	main(sys.argv[1:])