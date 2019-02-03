from Poloniex_API import Poloniex_API
import json
import datetime
import time
import sys, getopt
import os

s=""
k=""
poloAPI = Poloniex_API(s, k)


def fib(candles):
	high = sorted([x["high"] for x in candles["candleStick"]])[-1]
	low = sorted([x["low"] for x in candles["candleStick"]])[0]
	float = high-low
	return (high, 0.628*float+low, 0.5*float+low, 0.382*float+low, 0.236*float+low, low)
	

def macd(candles, length, interval_length):
	ema12, ema12_line = exponential_moving_average(12, candles, length, interval_length,[])
	ema26, ema26_line = exponential_moving_average(26, candles, length, interval_length,[])
	macd_line = [ema12_line[-(i+1)] - ema26_line[-(i+1)] for i in range(len(ema26_line))]
	
	print macd_line
	# print "ema26\n"
	# print ema26
	# print ema26_line
	# print len(ema26_line)
	# print "ema12\n"
	# print ema12
	# print ema12_line
	# print len(ema12_line)
	print "Not implemented"
	return 0 

def average_gain_loss(number_of_intervals, candles, length, interval_length, gains=[], losses=[]):
	if length*60/interval_length > number_of_intervals:
		if len(candles["candleStick"]) == number_of_intervals:
		#if len(candles) == number_of_intervals:	
			# get open prices
			opens = [x["open"] for x in candles["candleStick"]]
			# get close prices
			close = [x["close"] for x in candles["candleStick"]]
			#calculate gains and losses
			gains_losses = [close[-(i+1)]-close[-(i+2)] for i in range(len(opens)-1)]
			# separate gains and losses
			all_gains = [x for x in gains_losses if x > 0]
			all_losses = [x for x in gains_losses if x < 0 ]
			# calculate simple ave gain and ave loss
			ave_gain = abs(sum(all_gains))/number_of_intervals
			ave_loss = abs(sum(all_losses))/number_of_intervals
		else:
			previous_candles = {"candleStick": candles["candleStick"][:-1]}
			current_gain_loss = candles["candleStick"][-1]["close"]-candles["candleStick"][-2]["close"]
			# previous_candles = candles[:-1]
			# current_gain_loss = candles[-1]-candles[-2]
			if current_gain_loss > 0:
				current_gain = abs(current_gain_loss)
				current_loss = 0
			elif current_gain_loss < 0:
				current_loss = abs(current_gain_loss)
				current_gain = 0
			else:
				current_gain = 0
				current_loss = 0
			all_ave_gains, all_ave_losses = average_gain_loss(number_of_intervals, previous_candles, length, interval_length, gains, losses)
			ave_gain = (all_ave_gains[-1]*(number_of_intervals-1) + current_gain)/number_of_intervals
			ave_loss = (all_ave_losses[-1]*(number_of_intervals-1) + current_loss)/number_of_intervals
		gains.append(ave_gain)
		losses.append(ave_loss)
	return gains, losses

def RSI(number_of_intervals, candles, length, interval_length):
	rsi = []
	average_gains, average_losses = average_gain_loss(number_of_intervals, candles, length, interval_length)
	# print average_losses
	# print "\n"
	# print average_gains
	for i in range(len(average_losses)):
		rsi.append(100-100/(1+average_gains[i]/average_losses[i]))
	return rsi


def simple_moving_average(candles, number_of_intervals):
	# Total number periods minus number periods for SMA
	starting_point = len(candles["candleStick"])-number_of_intervals
	# all closing prices
	closes = [x["close"] for x in candles["candleStick"]]
	# sum of previous number_of_intervals closes
	closes_sum = sum(closes, starting_point)
	# sma 
	sma = closes_sum/number_of_intervals
	return sma
	

def exponential_moving_average(number_of_intervals, candles, length, interval_length, emas=[]):
	if length*60/interval_length > number_of_intervals:
		if len(candles["candleStick"]) == number_of_intervals:
			ema = simple_moving_average(candles, number_of_intervals)
		else:
			multiplier = 2.0/(number_of_intervals+1)
			close = candles["candleStick"][-1]["close"]
			previous_candles = {"candleStick": candles["candleStick"][:-1]}
			previous_ema, emas= exponential_moving_average(number_of_intervals, previous_candles, length, interval_length, emas)
			ema = (close - previous_ema) * multiplier + previous_ema
	else:
		print "Time period too short"
	#figure out how to save all intermediate emas 	
	emas.append(ema)
	return ema, emas


def average_volume(candles, number_of_intervals):
	# Total number periods minus number periods for SMA
	starting_point = len(candles["candleStick"])-number_of_intervals
	# all closing prices
	volumes = [x["volume"] for x in candles["candleStick"]]
	# sum of previous number_of_intervals closes
	sum_volumes = sum(volumes, starting_point)
	# sma 
	ave_volume = sum_volumes/number_of_intervals
	return ave_volume
	
	
## Setup Poloniex API Trading connection
def trade():
	# Checking available Margin NetValue
	balances = poloAPI.returnMarginAccountSummary()
	MarginValue = float(balances["netValue"])

	# length_of_intervals is in min
	# length_of_time is in hours
	#candles = poloAPI.returnChartData("BTC_BTS", length_of_intervals*60, (time.time() - length_of_time*3600), time.time())


	#Setting up Buy parameters
	if(1):
		rate = 0.00002
		amount = MarginValue*2/0.00002
		lendingRate = 0.0001
		currencyPair = "BTC_BTS"


	# execute Margin Buy
		#ret = poloAPI.getMarginPosition("BTC_STR")
		ret = poloAPI.marginBuy(currencyPair, rate, 100, lendingRate)
		#ret  = poloAPI.closeMarginPosition(currencyPair)
		ret2 = poloAPI.cancel(currencyPair, ret["orderNumber"])

		print json.dumps(ret, sort_keys = True, indent =4, separators=(',', ':'))
		print json.dumps(ret2, sort_keys = True, indent =4, separators=(',', ':'))


# if __name__ == "__main__":
	
	# try:
		# opts, args = getopt.getopt(argv, "", [])
	# except getopt.GetoptError:
		# print "Error"

		
#fix for recursion overflow
length_of_intervals = 30 # in mins
length_of_time = 1*24 # in hours
candles = poloAPI.returnChartData("BTC_BTS", length_of_intervals*60, (time.time() - length_of_time*3600), time.time())
#print json.dumps(candles, sort_keys = True, indent =4, separators=(',', ':'))
macd(candles, length_of_time, length_of_intervals)
# ema30, intermediate_emas = exponential_moving_average(30, candles, length_of_time, length_of_intervals,[])
# print ema30
# print intermediate_emas
# ema26, intermediate_emas2 = exponential_moving_average(26, candles, length_of_time, length_of_intervals,[])
# ema12, intermediate_emas1 = exponential_moving_average(12, candles, length_of_time, length_of_intervals,[])
# print "ema26\n"
# print ema26
# print intermediate_emas2
# print "ema12\n"
# print ema12
# print intermediate_emas1
#print RSI(14, candles, length_of_time, length_of_intervals)
#trade()
