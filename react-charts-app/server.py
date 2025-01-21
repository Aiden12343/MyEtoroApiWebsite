#--------------------------------Importing Libraries--------------------------------
import math
from flask import Flask, request, jsonify, render_template
import sys
import os
from fetching.yahoo_prices import fetch_prices
sys.path.append(os.path.join(os.path.dirname(__file__), 'fetching'))
from metrics import fetch_user_data, map_instrument_ids, map_instrument_ids_test
import json
import requests
import numpy as np
import logging
# Add the fetching directory to the Python path
#--------------------------------Importing Libraries--------------------------------


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
# Configure logging
logging.basicConfig(level=logging.DEBUG)

##Function to convert a string ticker into an integer (used for converting the param url of ticker into the instrument id)
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
    
@app.route('/tickers')
def tickers():
    ticker_name = request.args.get('ticker')
    size = request.args.get('size', type=int, default=12)  # Default size is 12 if not provided

    if not ticker_name:
        logging.error("Ticker name is required")
        return render_template('error.html', message="Ticker name is required")
    
    # Convert ticker name to InstrumentID
    instrument_id = map_ticker_to_instrument_id(ticker_name, "C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/instrument_mapping.json")
    if not instrument_id:
        logging.error(f"InstrumentID not found for ticker {ticker_name}")
        return render_template('error.html', message=f"InstrumentID not found for ticker {ticker_name}")

    user_data_dir = r'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/user_data'
    users_with_ticker = []
    country_count = {}
    copier_count = {}

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

    logging.info(f"Copier percentage: {copier_percentage}")
    return render_template('tickers.html', ticker_name=ticker_name, users_with_ticker=users_with_ticker, country_percentage=country_percentage, copier_percentage=copier_percentage)

if __name__ == "__main__":
    app.run(debug=True)
