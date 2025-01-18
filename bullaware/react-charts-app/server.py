#--------------------------------Importing Libraries--------------------------------
from flask import Flask, request, jsonify, render_template
import sys
import os
from fetching.yahoo_prices import fetch_prices
sys.path.append(os.path.join(os.path.dirname(__file__), 'fetching'))
from metrics import fetch_user_data
import json
# Add the fetching directory to the Python path
#--------------------------------Importing Libraries--------------------------------


#--------------------------------Creating Flask App--------------------------------
app = Flask(__name__)
#--------------------------------Creating Flask App--------------------------------


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
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#Map instrumentIDs to their names
with open('react-charts-app/fetching/instrument_mapping.json') as f:
    instrument_mapping = json.load(f)
#--------------------------------API Routes--------------------------------

#--------------------------------Exposure API--------------------------------
@app.route('/api/exposure', methods=['GET'])
def api_investment_data():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        
        investments = [
            {
                "investmentPct": item['investmentPct'],
                "instrumentId": instrument_mapping.get(str(item['instrumentId']), item['instrumentId'])
            }
            for item in data["Risk Score Contribution Data"]
            if 'investmentPct' in item and 'instrumentId' in item
        ]
        return jsonify({"Exposure": investments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------Exposure API--------------------------------

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
#--------------------------------Portfolio Returns API--------------------------------

#--------------------------------Risk Score API--------------------------------
@app.route('/api/risk_score', methods=['GET'])
def api_risk_score():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        risk_score = data.get("Risk Score")
        return jsonify({"Risk Score": risk_score})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------Risk Score API--------------------------------

@app.route('/username')
def username_page():
    username = request.args.get('username')
    if not username:
        return render_template('error.html', message="Username is required")
    try:
        data = fetch_user_data(username)
        investment_pcts = [item['investmentPct'] for item in data["Risk Score Contribution Data"] if 'investmentPct' in item]
        asset_names     = [item['instrumentId']  for item in data["Risk Score Contribution Data"] if 'instrumentId' in item]
        print("DEBUG DEBUG", investment_pcts)
        return render_template('username.html', username=username, investment_pcts=investment_pcts, asset_names = asset_names)
    except Exception as e:
        return render_template('error.html', message=str(e))

if __name__ == '__main__':
    app.run(debug=True)