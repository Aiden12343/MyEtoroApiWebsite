from flask import Flask, request, jsonify, render_template
import sys
import os
from fetching.yahoo_prices import fetch_prices

# Add the fetching directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'fetching'))

from metrics import fetch_user_data

app = Flask(__name__)

@app.route('/home')
def home():
    prices = fetch_prices()
    return render_template('home.html', prices=prices)

@app.route('/api/fetch_user_data', methods=['GET'])
def api_fetch_user_data():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400
    try:
        data = fetch_user_data(username)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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
                "instrumentId": item['instrumentId']
            }
            for item in data["Risk Score Contribution Data"]
            if 'investmentPct' in item and 'instrumentId' in item
        ]
        return jsonify({"Exposure": investments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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