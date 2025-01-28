#--------------------------------Importing Libraries--------------------------------
import math
from flask import Flask, request, jsonify, render_template
import sys
import os
from fetching.yahoo_prices import fetch_prices, fetch_price_and_date
sys.path.append(os.path.join(os.path.dirname(__file__), 'fetching'))
from metrics import fetch_user_data, map_instrument_ids, map_instrument_ids_test, fetch_ticker_posts
import json
import requests
import numpy as np
import logging
from datetime import datetime, timedelta
# Add the fetching directory to the Python path
#--------------------------------Importing Libraries--------------------------------
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)
#--------------------------------Creating Flask App--------------------------------
app = Flask(__name__)
#--------------------------------Creating Flask App--------------------------------


#--------------------------------Helper Functions--------------------------------
def save_user_data(username, data):
    """Save user data to a specific file for that user."""
    user_data_dir = os.path.join(os.path.dirname(__file__), 'user_data')
    os.makedirs(user_data_dir, exist_ok=True)
    user_data_file = os.path.join(user_data_dir, f'{username}.json')
    with open(user_data_file, 'w') as f:
        json.dump(data, f, indent=4)
#--------------------------------Helper Functions--------------------------------


#--------------------------------Home Routes--------------------------------
@app.route('/home')
def home():
    prices = fetch_prices() #Call python script for yahoo finance prices
    return render_template('home.html', prices=prices)

#--------------------------------API Routes--------------------------------
@app.route('/api/fetch_user_data', methods=['GET'])#All API data
def api_fetch_user_data():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        save_user_data(username, data)  # Save user data to a file
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#--------------------------------Exposure API--------------------------------
@app.route('/api/exposure', methods=['GET'])
def api_investment_data():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        save_user_data(username, data)  # Save user data to a file
        
        investments = []
        for item in data["Risk Score Contribution Data"]:
            if 'investmentPct' in item and 'instrumentId' in item:
                raw_instrument_id = item['instrumentId']
                instrument_id = map_instrument_ids_test(
                    str(raw_instrument_id),
                    "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/instrument_mapping.json"
                )
                if instrument_id:
                    investments.append({
                        "investmentPct": item['investmentPct'],
                        "instrumentId": instrument_id
                    })
        
        return jsonify({"Exposure": investments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#--------------------------------Portfolio Returns API--------------------------------
@app.route('/api/portfolio_returns', methods=['GET'])
def api_portfolio_returns():
    username = request.args.get('username')
    timeframe = request.args.get('timeframe', 'monthly').lower()
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if timeframe not in ['monthly', 'yearly']:
        return jsonify({"error": "Invalid timeframe. Options are 'monthly' or 'yearly'"}), 400
    
    try:
        data = fetch_user_data(username)
        save_user_data(username, data)  # Save user data to a file
        
        returns = [
            {
                "start": item['start'],
                "gain": item['gain']
            }
            for item in data["Returns Data"].get(timeframe, [])
            if 'gain' in item and 'start' in item
        ]
        return jsonify({"returns": returns})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#--------------------------------Risk Score API--------------------------------
@app.route('/api/risk_score', methods=['GET'])
def api_risk_score():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        save_user_data(username, data)  # Save user data to a file
        risk_score = data.get("Risk Score")
        return jsonify({"Risk Score": risk_score})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------Risk Score API--------------------------------

#--------------------------------Copier Numbers API--------------------------------
@app.route('/api/copier_numbers', methods=['GET'])
def api_copier_numbers():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        save_user_data(username, data)  # Save user data to a file
        copier_numbers = data.get("Historical Copier Numbers", {}).get("dailyCopiers", [])
        return jsonify({"copier_numbers": copier_numbers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------Copier Numbers API--------------------------------


#--------------------------------Username Route--------------------------------
@app.route('/username')
def username_page():
    username = request.args.get('username')
    if not username:
        return render_template('error.html', message="Username is required")
    try:
        data = fetch_user_data(username)
        save_user_data(username, data)  # Save user data to a file
        #Fetch Investment %'s
        investment_pcts = [item['investmentPct'] for item in data["Risk Score Contribution Data"] if 'investmentPct' in item]
        asset_names     = [item['instrumentId']  for item in data["Risk Score Contribution Data"] if 'instrumentId' in item]
        #Fetch Avatar URL and Bio
        avatar_url = data["User Data"].get("Avatar URL", "")
        bio        = data["User Data"].get("About Me", "")
        #Fetch Closed Trade Metrics
        closed_trade_metrics          = data.get("Closed Trade Metrics", {})
        TotaClosedManualPostions      = closed_trade_metrics.get("TotalClosedManualPositions"  , 0)
        TotalClosedMirrorPositions    = closed_trade_metrics.get("TotalClosedMirrorPositions"  , 0)
        TotalClosedTrades             = closed_trade_metrics.get("TotalClosedTrades"           , 0)
        TotalNetProfitPercentage      = closed_trade_metrics.get("TotalNetProfitPercentage"    , 0.0)
        TotalProfitabilityPercentage  = closed_trade_metrics.get("TotalProfitabilityPercentage", 0.0)
        #Fetch Number of Copiers
        Copiers              = data["Risk Score and Rankings"].get("Copiers"             , 0)
        ThisWeekGain         = data["Risk Score and Rankings"].get("ThisWeekGain"        , 0)
        RiskScore            = data["Risk Score and Rankings"].get("RiskScore"           , 0)
        MaxDailyRiskScore    = data["Risk Score and Rankings"].get("MaxDailyRiskScore"   , 0)
        MaxMonthlyRiskScore  = data["Risk Score and Rankings"].get("MaxMonthlyRiskScore" , 0)
        WinRatio             = data["Risk Score and Rankings"].get("WinRatio"            , 0)
        MediumLeveragePct    = data["Risk Score and Rankings"].get("MediumLeveragePct"   , 0)
        HighLeveragePct      = data["Risk Score and Rankings"].get("HighLeveragePct"     , 0)
        CopyBlock            = data["Risk Score and Rankings"].get("CopyBlock"           , 0)
        # Fetch Historical Copier Numbers
        historical_copier_numbers = data.get("Historical Copier Numbers", {}).get("dailyCopiers", [])
        copier_numbers            = [item['copiers']   for item in historical_copier_numbers if 'copiers'   in item]
        timestamp                 = [item['timestamp'] for item in historical_copier_numbers if 'timestamp' in item]
        # Calculating standard deviation between benchmark and equity
        with open("react-charts-app/fetching/benchmark_changes.json", 'r') as file:
            benchmark_data = json.load(file)
        
        # Skip the first entry and filter out records where EquityPercentChange is null
        filtered_data = [
            (entry['EquityPercentChange'], entry['PercentChange'])
            for entry in benchmark_data[1:]  # Skip the first entry
            if entry['EquityPercentChange'] is not None and entry['PercentChange'] is not None
        ]

        # Extract values for calculation
        differences = [e - p for e, p in filtered_data]

        # Calculate the mean of differences
        mean_diff = sum(differences) / len(differences)

        # Calculate the variance
        variance = sum((diff - mean_diff) ** 2 for diff in differences) / len(differences)

        # Standard deviation is the square root of variance
        std_deviation = math.sqrt(variance)
        print("DEBUG DEBUG DEBUG", std_deviation)

        # Fetch Open Positions Data
        print("Fetching open positions data")
        open_positions_data = data.get("Open Positions Data", [])
        
        open_positions = [
            {
            "TickerName": item['TickerName'],
            "AverageOpen": item['AverageOpen'],
            "InvestedAmount": item['InvestedAmount'],
            "UnrealisedValue": item['UnrealisedValue'],
            "Leverage": item['Leverage'],
            "CurrentRate": item['CurrentRate']
            }
            for item in open_positions_data
        ]
        
        return render_template(
            'username.html', 
            username                       = username, 
            investment_pcts                = investment_pcts, 
            asset_names                    = asset_names, 
            avatar_url                     = avatar_url, 
            bio                            = bio, 
            TotalClosedManualPositions     = TotaClosedManualPostions,
            TotalClosedMirrorPositions     = TotalClosedMirrorPositions,
            TotalClosedTrades              = TotalClosedTrades,
            TotalNetProfitPercentage       = TotalNetProfitPercentage,
            TotalProfitabilityPercentage   = TotalProfitabilityPercentage,
            Copiers                        = Copiers,
            ThisWeekGain                   = ThisWeekGain,
            RiskScore                      = RiskScore,
            MaxDailyRiskScore              = MaxDailyRiskScore,
            MaxMonthlyRiskScore            = MaxMonthlyRiskScore,
            WinRatio                       = WinRatio,
            MediumLeveragePct              = MediumLeveragePct,
            HighLeveragePct                = HighLeveragePct,
            CopyBlock                      = CopyBlock,
            copier_numbers                 = copier_numbers,
            timestamp                      = timestamp,
            open_positions                 = open_positions,
            std_deviation                  = std_deviation
        )
    except Exception as e:
        return render_template('error.html', message=str(e))
#--------------------------------Username Route--------------------------------


#--------------------------------Hot Stocks Route--------------------------------
@app.route('/hotstocks')
def hot_stocks():
    user_data_dir       = os.path.join(os.path.dirname(__file__), 'user_data')
    aggregated_data_dir = os.path.join(os.path.dirname(__file__), 'aggregated_user_data')
    os.makedirs(aggregated_data_dir, exist_ok=True)
    user_count          = 0
    instrument_data     = {}
    for filename in os.listdir(user_data_dir):
        if filename.endswith('.json'):
            user_count += 1
            with open(os.path.join(user_data_dir, filename), 'r') as f:
                data           = json.load(f)
                portfolio_data = data.get("Portfolio Data", [])
                for item in portfolio_data:
                    raw_instrument_id = item.get("InstrumentID")
                    if raw_instrument_id is not None:
                        instrument_id = map_instrument_ids_test(
                            str(raw_instrument_id),
                            "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/instrument_mapping.json"
                        )
                        if instrument_id:
                            if instrument_id not in instrument_data:
                                instrument_data[instrument_id] = {
                                    "buy_count"        : 0,
                                    "sell_count"       : 0,
                                    "total_invested"   : 0,
                                    "total_net_profit" : 0,
                                    "total_value"      : 0,
                                    "user_count"       : 0
                                }
                            if item.get("Direction") == "Buy":
                                instrument_data[instrument_id]["buy_count"] += 1
                            elif item.get("Direction") == "Sell":
                                instrument_data[instrument_id]["sell_count"] += 1
                            instrument_data[instrument_id]["total_invested"]   += item.get("InvestedAmount", 0)
                            instrument_data[instrument_id]["total_net_profit"]  = round(instrument_data[instrument_id]["total_net_profit"] + item.get("NetProfit", 0), 2)
                            instrument_data[instrument_id]["total_value"]      += round(item.get("Value", 0), 2)
                            instrument_data[instrument_id]["user_count"]       += 1

    if user_count == 0:
        return render_template('error.html', message="No user data found")

    most_popular_bought = max(instrument_data, key=lambda x: instrument_data[x]["buy_count"], default=None)
    most_shorted        = max(instrument_data, key=lambda x: instrument_data[x]["sell_count"], default=None)

    for instrument_id, data in instrument_data.items():
        if data["user_count"] > 0:
            data["average_invested"]   = round(data["total_invested"] / data["user_count"], 2)
            data["average_net_profit"] = round(data["total_net_profit"] / data["user_count"], 2)
            data["average_value"]      = round(data["total_value"] / data["user_count"], 2)
        else:
            data["average_invested"]   = 0
            data["average_net_profit"] = 0
            data["average_value"]      = 0

    ordered_instrument_data = dict(sorted(instrument_data.items(), key=lambda item: item[1]["user_count"], reverse=True))

    hot_stocks_data = {
        "total_instruments"  : len(ordered_instrument_data),
        "most_popular_bought": most_popular_bought,
        "most_shorted"       : most_shorted,
        "user_count"         : user_count,
        "instrument_data"    : ordered_instrument_data
    }

    hot_stocks_file = os.path.join(aggregated_data_dir, 'hot_stocks_data.json')
    with open(hot_stocks_file, 'w') as f:
        json.dump(hot_stocks_data, f, indent=4)
    
    top_10_assets = dict(list(ordered_instrument_data.items())[:10])

    top_10_assets_file = os.path.join(aggregated_data_dir, 'top_10_assets.json')
    with open(top_10_assets_file, 'w') as f:
        json.dump(top_10_assets, f, indent=4)

    top_10_shorted_assets = dict(
        list(
            sorted(
                {k: v for k, v in ordered_instrument_data.items() if v["sell_count"] > 0}.items(),
                key=lambda item: item[1]["sell_count"],
                reverse=True
            )[:10]
        )
    )

    top_10_shorted_assets_file = os.path.join(aggregated_data_dir, 'top_10_shorted_assets.json')
    with open(top_10_shorted_assets_file, 'w') as f:
        json.dump(top_10_shorted_assets, f, indent=4)

    top_10_net_profit_assets = dict(
        list(
            sorted(
                ordered_instrument_data.items(),
                key=lambda item: item[1]["total_net_profit"],
                reverse=True
            )[:10]
        )
    )

    top_10_net_profit_assets_file = os.path.join(aggregated_data_dir, 'top_10_net_profit_assets.json')
    with open(top_10_net_profit_assets_file, 'w') as f:
        json.dump(top_10_net_profit_assets, f, indent=4, sort_keys=False)

    return render_template('hotstocks.html', hot_stocks_data=hot_stocks_data, top_10_assets=top_10_assets, top_10_shorted_assets=top_10_shorted_assets, top_10_net_profit_assets=top_10_net_profit_assets)

#--------------------------------Tickers Route--------------------------------
#Reverse mapping to find instrument_id from tickername **Neccessary since we are using a ticker name in the tickers route url and need to map to integer ID**
def map_ticker_to_instrument_id(ticker_name, mapping_file):
    """Map a ticker name to an InstrumentID using the provided mapping file."""
    try:
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        # Reverse the mapping to get ticker name to InstrumentID
        reversed_mapping = {v: k for k, v in mapping.items()}
        return reversed_mapping.get(ticker_name)
    except Exception as e:
        logging.error(f"Error reading mapping file: {e}")
        return None
    
#Reading date time strings
def parse_date(date_str):
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
    return None

#Counting open positions within a year
def count_positions_within_year(file_path, ticker_name):
    count_by_date = {}
    one_year_ago = datetime.now() - timedelta(days=365)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        for position in data:
            if position.get("TickerName") == ticker_name:
                open_dates = position.get("OpenDates", [])
                for open_date_str in open_dates:
                    open_date = parse_date(open_date_str)
                    if open_date and open_date >= one_year_ago:
                        current_date = one_year_ago
                        while current_date <= datetime.now():
                            if open_date <= current_date:
                                count_by_date[current_date.strftime("%Y-%m-%d")] = count_by_date.get(current_date.strftime("%Y-%m-%d"), 0) + 1
                            current_date += timedelta(days=1)
    return count_by_date

#Aggregating data 
def aggregate_counts(counts_list):
    aggregated_counts = {}
    for counts in counts_list:
        for date, count in counts.items():
            aggregated_counts[date] = aggregated_counts.get(date, 0) + count
    return aggregated_counts

#Counting number of closed positions within a year
def count_closed_positions_within_year(file_path, ticker_name):
    count_by_date = {}
    one_year_ago = datetime.now() - timedelta(days=365)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        for position in data:
            if position.get("TickerName") == ticker_name:
                open_dates = position.get("OpenDates", [])
                close_dates = position.get("CloseDates", [])
                for open_date_str, close_date_str in zip(open_dates, close_dates):
                    open_date = parse_date(open_date_str)
                    close_date = parse_date(close_date_str)
                    if open_date and close_date and open_date >= one_year_ago:
                        current_date = one_year_ago
                        while current_date <= datetime.now():
                            if open_date <= current_date <= close_date:
                                count_by_date[current_date.strftime("%Y-%m-%d")] = count_by_date.get(current_date.strftime("%Y-%m-%d"), 0) + 1
                            current_date += timedelta(days=1)
    return count_by_date

#Calculating average invested amount **Based on open positions**
def calculate_average_invested_amount(folder_path, ticker_name):
    total_invested_amount_by_date = {}
    investor_count_by_date = {}

    one_year_ago = datetime.now() - timedelta(days=365)

    for filename in os.listdir(folder_path):
        if filename.endswith('_positions.json') and not filename.endswith('_closed_positions.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from file {filename}: {e}")
                    continue

                for item in data:
                    if item.get("TickerName") == ticker_name:
                        open_dates = item.get("OpenDates", [])
                        for open_date_str in open_dates:
                            open_date = parse_date(open_date_str)
                            if open_date and open_date >= one_year_ago:
                                current_date = one_year_ago
                                while current_date <= datetime.now():
                                    if open_date <= current_date:
                                        date_str = current_date.strftime("%Y-%m-%d")
                                        invested_amount = item.get("InvestedAmount", 0)
                                        total_invested_amount_by_date[date_str] = total_invested_amount_by_date.get(date_str, 0) + invested_amount
                                        investor_count_by_date[date_str] = investor_count_by_date.get(date_str, 0) + 1
                                    current_date += timedelta(days=1)

    average_invested_amount_by_date = {}
    for date_str in total_invested_amount_by_date:
        total_invested_amount = total_invested_amount_by_date[date_str]
        investor_count = investor_count_by_date[date_str]
        average_invested_amount_by_date[date_str] = round(total_invested_amount / investor_count, 2)

    avg_invested_ticker_file = "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/ticker_data/avg_invested_ticker.json"
    ordered_average_invested_amount_by_date = dict(sorted(average_invested_amount_by_date.items(), key=lambda item: item[0], reverse=True))
    with open(avg_invested_ticker_file, 'w') as f:
        json.dump(ordered_average_invested_amount_by_date, f, indent=4)

    return average_invested_amount_by_date

@app.route('/tickers')
def tickers():
    ticker_name = request.args.get('ticker')
    size = request.args.get('size', type=int, default=12)  # Default size is 12 if not provided
    lookback = request.args.get('lookback', type=int, default=size)  # Default lookback is 365 days if not provided
    filter_term = request.args.get('filter', default=None)

    if not ticker_name:
        return render_template('tickers.html', ticker_name=ticker_name)

    # Ensure ticker_name is capitalized and filter_term is lower case
    ticker_name = ticker_name.upper()
    if filter_term:
        filter_term = filter_term.lower()

    # Convert ticker name to InstrumentID
    instrument_id = map_ticker_to_instrument_id(ticker_name, "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/instrument_mapping.json")
    if not instrument_id:
        logging.error(f"InstrumentID not found for ticker {ticker_name}")
        return render_template('error.html', message=f"InstrumentID not found for ticker {ticker_name}")

    user_data_dir = r'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/user_data'
    users_with_ticker = []
    country_count = {}
    copier_count = {}
    total_copiers = sum(user_info["Copiers"] for user_info in users_with_ticker)

    for filename in os.listdir(user_data_dir):
        if filename.endswith('.json'):
            with open(os.path.join(user_data_dir, filename), 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from file {filename}: {e}")
                    continue

                portfolio_data = data.get("Portfolio Data", [])
                if not portfolio_data:
                    continue

                for item in portfolio_data:
                    if str(item.get("InstrumentID")) == instrument_id:
                        user_info = {
                            "username": filename.replace('.json', ''),
                            "avatar_url": data["User Data"].get("Avatar URL", ""),
                            "TotalClosedManualPositions": data.get("Closed Trade Metrics", {}).get("TotalClosedManualPositions", 0),
                            "TotalClosedMirrorPositions": data.get("Closed Trade Metrics", {}).get("TotalClosedMirrorPositions", 0),
                            "TotalNetProfitPercentage": data.get("Closed Trade Metrics", {}).get("TotalNetProfitPercentage", 0.0),
                            "TotalProfitabilityPercentage": data.get("Closed Trade Metrics", {}).get("TotalProfitabilityPercentage", 0.0),
                            "RiskScore": data["Risk Score and Rankings"].get("RiskScore", 0),
                            "Country": data["Risk Score and Rankings"].get("Country", "Unknown")
                        }
                        copiers = data["Risk Score and Rankings"].get("Copiers", 0)
                        user_info["Copiers"] = copiers
                        if copiers <= 100:
                            copier_category = "0-100"
                        elif copiers <= 300:
                            copier_category = "101-300"
                        elif copiers <= 600:
                            copier_category = "301-600"
                        elif copiers <= 1000:
                            copier_category = "601-1000"
                        elif copiers <= 2000:
                            copier_category = "1001-2000"
                        else:
                            copier_category = "2001+"
                        copier_count[copier_category] = copier_count.get(copier_category, 0) + 1

                        users_with_ticker.append(user_info)
                        country = user_info["Country"]
                        country_count[country] = country_count.get(country, 0) + 1

                        break

    if not users_with_ticker:
        logging.info(f"No users found with ticker {ticker_name}")
        return render_template('error.html', message=f"No users found with ticker {ticker_name}")

    # Limit the number of users returned based on the size parameter
    users_with_ticker = users_with_ticker[:size]

    # Calculate the percentage of users belonging to each country
    country_percentage = {country: (count / sum(country_count.values())) * 100 for country, count in country_count.items()}

    copier_percentage = {category: round((count / sum(copier_count.values())) * 100, 2) for category, count in copier_count.items()}

    # Calculate the number of owners of the ticker for every day since 1 year ago
    portfolio_data_dir = r'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/portfolio_data'
    aggregated_data_dir = os.path.join(os.path.dirname(__file__), 'aggregated_user_data')
    os.makedirs(aggregated_data_dir, exist_ok=True)

    all_counts = []
    closed_counts = []

    for filename in os.listdir(portfolio_data_dir):
        if filename.endswith('_positions.json') and not filename.endswith('_closed_positions.json'):
            user_counts = count_positions_within_year(os.path.join(portfolio_data_dir, filename), ticker_name)
            all_counts.append(user_counts)
            print(f"Open positions for {filename}: {user_counts}")
        elif filename.endswith('_closed_positions.json'):
            closed_user_counts = count_closed_positions_within_year(os.path.join(portfolio_data_dir, filename), ticker_name)
            closed_counts.append(closed_user_counts)
            print(f"Closed positions for {filename}: {closed_user_counts}")

    aggregated_counts = aggregate_counts(all_counts)
    aggregated_closed_counts = aggregate_counts(closed_counts)

    # Save the aggregated counts to a file
    aggregated_counts_file = "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/ticker_data/ticker_interest.json"
    aggregated_closed_counts_file = "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/ticker_data/ticker_interest_closed.json"

    # Order the aggregated counts by date, with most recent date first
    ordered_aggregated_counts = dict(sorted(aggregated_counts.items(), key=lambda item: item[0], reverse=True))
    ordered_aggregated_closed_counts = dict(sorted(aggregated_closed_counts.items(), key=lambda item: item[0], reverse=True))

    with open(aggregated_counts_file, 'w') as f:
        json.dump(ordered_aggregated_counts, f, indent=4)

    with open(aggregated_closed_counts_file, 'w') as f:
        json.dump(ordered_aggregated_closed_counts, f, indent=4)

    average_invested_amount = calculate_average_invested_amount(portfolio_data_dir, ticker_name)

    # Fetch price and date data for the ticker from the oldest date in aggregated_closed_counts_file to the current date
    try:
        if ordered_aggregated_closed_counts:
            oldest_date_str = min(ordered_aggregated_closed_counts.keys())
            oldest_date = datetime.strptime(oldest_date_str, "%Y-%m-%d")
        else:
            oldest_date = datetime.now() - timedelta(days=365)  # Default to one year ago if no data

        current_date = datetime.now()
        price_data = fetch_price_and_date(ticker_name, oldest_date, current_date)
        ticker_prices_file = "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/ticker_data/ticker_prices.json"
        with open(ticker_prices_file, 'w') as f:
            json.dump(price_data, f, indent=4)
    except Exception as e:
        logging.error(f"Error fetching price and date data for ticker {ticker_name}: {e}")

    ##Fetch average invested amount
    average_invested_amount = calculate_average_invested_amount(portfolio_data_dir, ticker_name)
    print("debug debug debug avg", average_invested_amount)
    total_users_invested = len([filename for filename in os.listdir(user_data_dir) if filename.endswith('.json') and any(
        str(item.get("InstrumentID")) == instrument_id for item in json.load(open(os.path.join(user_data_dir, filename), 'r')).get("Portfolio Data", [])
    )])
    print("debug debug debug totalusrs", total_users_invested)

    logging.info(f"Copier percentage: {copier_percentage}")
    # Fetch ticker information from the instrument_info folder
    instrument_info_dir = r'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/instrument_info'
    ticker_info_file = os.path.join(instrument_info_dir, f'{ticker_name}_stock_info.json')
    
    try:
        with open(ticker_info_file, 'r') as f:
            ticker_info = json.load(f)
    except FileNotFoundError:
        logging.error(f"Ticker info file not found for {ticker_name}")
        ticker_info = {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from ticker info file for {ticker_name}: {e}")
        ticker_info = {}

   # Extract values from ticker_info with more understandable names
    instrument_information = {
        "Instrument Name": ticker_info.get("internalInstrumentDisplayName", ""),
        "Symbol": ticker_info.get("internalSymbolFull", ""),
        "Instrument ID": ticker_info.get("internalInstrumentId", ""),
        "Exchange Name": ticker_info.get("internalExchangeName", ""),
        "Stock Industry Name": ticker_info.get("internalStockIndustryName", ""),
        "Asset Class Name": ticker_info.get("internalAssetClassName", ""),
        "Ticker Photo": ticker_info.get("logo50x50", "")
    }

    price_information = {
        "Current Rate": round(ticker_info.get("currentRate", 0.0), 2),
        "Closing Price": round(ticker_info.get("internalClosingPrice", 0.0), 2),
        "Daily Price Change": round(ticker_info.get("dailyPriceChange", 0.0), 2),
        "Weekly Price Change": round(ticker_info.get("weeklyPriceChange", 0.0), 2),
        "Monthly Price Change": round(ticker_info.get("monthlyPriceChange", 0.0), 2),
        "Three Month Price Change": round(ticker_info.get("threeMonthPriceChange", 0.0), 2),
        "Six Month Price Change": round(ticker_info.get("sixMonthPriceChange", 0.0), 2),
        "Year-to-Date Price Change": round(ticker_info.get("currYearPriceChange", 0.0), 2),
        "High Price Last 9 Months": round(ticker_info.get("highPriceLast9Months-TTM", 0.0), 2),
        "Low Price Last 13 Weeks": round(ticker_info.get("lowPriceLast13Weeks-TTM", 0.0), 2),
        "High Price Last 13 Weeks": round(ticker_info.get("highPriceLast13Weeks-TTM", 0.0), 2),
        "One Month Ago Price Change": round(ticker_info.get("oneMonthAgoPriceChange", 0.0), 2),
        "Two Months Ago Price Change": round(ticker_info.get("twoMonthsAgoPriceChange", 0.0), 2),
        "Three Months Ago Price Change": round(ticker_info.get("threeMonthsAgoPriceChange", 0.0), 2),
        "Six Months Ago Price Change": round(ticker_info.get("sixMonthsAgoPriceChange", 0.0), 2)
    }

    volume_and_popularity = {
        "Average Daily Volume (52 Weeks)": round(ticker_info.get("averageDailyVolumeLast52Weeks-Annual", 0), 2),
        "Popularity (7 Days)": round(ticker_info.get("popularityUniques7Day", 0), 2),
        "Popularity (14 Days)": round(ticker_info.get("popularityUniques14Day", 0), 2),
        "Popularity (30 Days)": round(ticker_info.get("popularityUniques30Day", 0), 2),
        "Traders 7 Day Change": round(ticker_info.get("traders7DayChange", 0), 2),
        "Traders 14 Day Change": round(ticker_info.get("traders14DayChange", 0), 2),
        "Traders 30 Day Change": round(ticker_info.get("traders30DayChange", 0), 2)
    }

    financial_metrics = {
        "Operating Income (TTM)": round(ticker_info.get("operatingIncomeAfterUnusualItems-TTM", 0.0), 2),
        "3-Year Annual Income Growth Rate": round(ticker_info.get("3YearAnnualIncomeGrowthRate-TTM", 0.0), 2),
        "Short Term Debt (TTM)": round(ticker_info.get("shortTermDebt-TTM", 0.0), 2),
        "Deferred Taxes": round(ticker_info.get("deferredTaxes-Annual", 0.0), 2),
        "Investment in Unconsolidated Affiliates": round(ticker_info.get("investmentInUnconsolidatedAffiliates-Annual", 0.0), 2),
        "5-Year Average Total Debt/Equity Ratio": round(ticker_info.get("5YearAverageTotalDebtEquityRatio-TTM", 0.0), 2),
        "Percent Price Change 26 Weeks (TTM)": round(ticker_info.get("percentPriceChange26Weeks-TTM", 0.0), 2),
        "High Price Last 9 Months (TTM)": round(ticker_info.get("highPriceLast9Months-TTM", 0.0), 2),
        "Low Price Last 13 Weeks (TTM)": round(ticker_info.get("lowPriceLast13Weeks-TTM", 0.0), 2),
        "High Price Last 13 Weeks (TTM)": round(ticker_info.get("highPriceLast13Weeks-TTM", 0.0), 2),
        "Investment in Unconsolidated Affiliates (Annual)": round(ticker_info.get("investmentInUnconsolidatedAffiliates-Annual", 0.0), 2),
        "Deferred Taxes (Annual)": round(ticker_info.get("deferredTaxes-Annual", 0.0), 2),
        "5-Year Average Total Debt/Equity Ratio (TTM)": round(ticker_info.get("5YearAverageTotalDebtEquityRatio-TTM", 0.0), 2)
    }

    market_sentiment = {
        "Currently Tradable": ticker_info.get("isCurrentlyTradable", False),
        "Exchange Open": ticker_info.get("isExchangeOpen", False),
        "Buy Enabled": ticker_info.get("isBuyEnabled", False),
        "Is Delisted": ticker_info.get("isDelisted", False),
        "Is Active In Platform": ticker_info.get("isActiveInPlatform", False)
    }

    business_description = {
        "Business Description": ticker_info.get("shortBio-en-gb" , ""),
    }

    urls = {
        "Investor Relations" : ticker_info.get("investorRelationsUrl", ""),
        "Company Website"     : ticker_info.get("website-Annual", ""),
        "Upcoming Earnings Call"    : ticker_info.get("conferenceCallBroadcastURL", ""),
        "Analyst Article" : ticker_info.get("tipRanksFourStarsRecommendationArticleUrl", ""),
    }

   # Extract the username and net profit for each user on their ticker position
    def fetch_unrealised_values(users_with_ticker, ticker_name, user_data_dir):
        for username in users_with_ticker:
            user_data_file = os.path.join(user_data_dir, f"{username['username'].lower()}.json")
            if not os.path.exists(user_data_file):
                user_data_file = os.path.join(user_data_dir, f"{username['username'].upper()}.json")
            with open(user_data_file, 'r') as f:
                data = json.load(f)
            open_positions_data = data.get("Open Positions Data", [])
            for item in open_positions_data:
                if item.get("TickerName") == ticker_name:
                    username["UnrealisedValue"] = item.get("UnrealisedValue", 0)
                    break
            else:
                username["UnrealisedValue"] = 0

    fetch_unrealised_values(users_with_ticker, ticker_name, user_data_dir)
    post_tickers = [ticker_name]
    fetch_ticker_posts("C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/instrument_mapping.json", post_tickers, lookback, filter_term)

    # Load ticker posts count from the related _post_counts.json file
    post_counts_file = os.path.join("C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/post_data", f"{ticker_name}_post_counts.json")
    try:
        with open(post_counts_file, 'r') as f:
            ticker_posts = json.load(f)
    except FileNotFoundError:
        ticker_posts = {}

    temp_stock_data = {
        "ticker_name": ticker_name,
        "users_with_ticker": users_with_ticker,
        "country_percentage": country_percentage,
        "copier_percentage": copier_percentage,
        "ordered_aggregated_counts": ordered_aggregated_counts,
        "ordered_aggregated_closed_counts": ordered_aggregated_closed_counts,
        "size": size,
        "price_data": price_data,
        "average_invested_amount": average_invested_amount,
        "total_users_invested": total_users_invested,
        "total_copiers": total_copiers,
        "instrument_information": instrument_information,
        "price_information": price_information,
        "volume_and_popularity": volume_and_popularity,
        "financial_metrics": financial_metrics,
        "market_sentiment": market_sentiment,
        "business_description": business_description,
        "users_percentage_profit_loss": users_with_ticker,
        "urls": urls,
        "ticker_posts": ticker_posts
    }

    # Debugging statements
    for user in temp_stock_data["users_percentage_profit_loss"]:
        print(f"Username: {user['username']}, Posiion P/L: {user['UnrealisedValue']}")
    
    print("Ticker Post DEBUG DEBUG DEBUG", ticker_posts)
    # Save the temp_stock_data to a file for further inspection
    temp_stock_data_file = "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/ticker_data/temp_stock_data.json"
    with open(temp_stock_data_file, 'w') as f:
        json.dump(temp_stock_data, f, indent=4)
    return render_template('tickers.html', ticker_name=ticker_name, users_with_ticker=users_with_ticker, country_percentage=country_percentage, copier_percentage=copier_percentage, ordered_aggregated_counts=ordered_aggregated_counts, ordered_aggregated_closed_counts = ordered_aggregated_closed_counts, size = size, price_data = price_data, average_invested_amount = average_invested_amount, total_users_invested=total_users_invested, total_copiers = total_copiers, instrument_information=instrument_information, price_information=price_information, volume_and_popularity=volume_and_popularity, financial_metrics=financial_metrics, market_sentiment=market_sentiment, business_description=business_description, urls = urls, ticker_posts = ticker_posts)

#--------------------------------Screener Route--------------------------------
@app.route('/screener')
def screener():
    try:
        # Load user data
        user_data_dir = os.path.join(os.path.dirname(__file__), 'user_data')
        users_data = []
        for filename in os.listdir(user_data_dir):
            if filename.endswith('.json'):
                with open(os.path.join(user_data_dir, filename), 'r') as f:
                    data = json.load(f)
                    users_data.append(data)

        # Load stock data
        aggregated_data_dir = os.path.join(os.path.dirname(__file__), 'aggregated_user_data')
        hot_stocks_file = os.path.join(aggregated_data_dir, 'hot_stocks_data.json')
        with open(hot_stocks_file, 'r') as f:
            hot_stocks_data = json.load(f)

        # Load top 10 assets data
        top_10_assets_file = os.path.join(aggregated_data_dir, 'top_10_assets.json')
        with open(top_10_assets_file, 'r') as f:
            top_10_assets = json.load(f)

        # Load top 10 shorted assets data
        top_10_shorted_assets_file = os.path.join(aggregated_data_dir, 'top_10_shorted_assets.json')
        with open(top_10_shorted_assets_file, 'r') as f:
            top_10_shorted_assets = json.load(f)

        # Load top 10 net profit assets data
        top_10_net_profit_assets_file = os.path.join(aggregated_data_dir, 'top_10_net_profit_assets.json')
        with open(top_10_net_profit_assets_file, 'r') as f:
            top_10_net_profit_assets = json.load(f)

        return render_template(
            'screener.html',
            users_data=users_data,
            hot_stocks_data=hot_stocks_data,
            top_10_assets=top_10_assets,
            top_10_shorted_assets=top_10_shorted_assets,
            top_10_net_profit_assets=top_10_net_profit_assets
        )
    except Exception as e:
        return render_template('error.html', message=str(e))
#--------------------------------Screener Route--------------------------------

if __name__ == "__main__":
    app.run(debug=True)