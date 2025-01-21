import json
import requests
import sys

def get_proxies():
    return {}

def get_headers():
    return {
        'User-Agent'      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept'          : 'application/json, text/plain, */*',
        'Accept-Language' : 'en-US,en;q=0.9',
        'Referer'         : 'https://www.etoro.com/',
        'Origin'          : 'https://www.etoro.com',
        'Connection'      : 'keep-alive',
        'Sec-Fetch-Dest'  : 'empty',
        'Sec-Fetch-Mode'  : 'cors',
        'Sec-Fetch-Site'  : 'same-origin',
        'TE'              : 'trailers',
    }

import os
import time

def fetch_user_data(username):
    headers      = get_headers() 
    proxies      = get_proxies()
    instrument_map_path = 'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/instrument_mapping.json'
    if not os.path.exists(instrument_map_path):
        raise FileNotFoundError(f"Instrument mapping file not found: {instrument_map_path}")
    instrument_map = load_instrument_map(instrument_map_path)

    #<---------------------------------------------------------- Fetching CID Data ---------------------------------------------------------->#
    print(f"Fetching user data for: https://www.etoro.com/api/logininfo/v1.1/users/{username}")
    endpoint_url = f"https://www.etoro.com/api/logininfo/v1.1/users/{username}"
    response     = requests.get(endpoint_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    cid_data     = response.json() 
    avatar_url   = next((avatar['url'] for avatar in cid_data['avatars'] if avatar['type'] == 'Original'), None)
    about_me     = cid_data['aboutMeShort']

    #<---------------------------------------------------------- Fetching Portfolio Data (Risk scores, Returns, Copiers...) ---------------------------------------------------------->#
    print(f"Fetching risk score data and rankings for : https://www.etoro.com/sapi/rankings/cid/{cid_data['realCID']}/rankings/?Period=OneYearAgo")
    rankings_url = f"https://www.etoro.com/sapi/rankings/cid/{cid_data['realCID']}/rankings/?Period=OneYearAgo"
    response     = requests.get(rankings_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    rankings_data = response.json()

    copiers                 = rankings_data['Data']['Copiers']
    YGain                   = rankings_data['Data']['Gain']
    DailyGain               = rankings_data['Data']['DailyGain']
    WeekGain                = rankings_data['Data']['ThisWeekGain']
    riskscore               = rankings_data['Data']['RiskScore']
    MaxDailyRiskScore       = rankings_data['Data']['MaxDailyRiskScore']
    MaxMonthlyRiskScore     = rankings_data['Data']['MaxMonthlyRiskScore']
    WeeksSinceRegistration  = rankings_data['Data']['WeeksSinceRegistration']
    WinRatio                = rankings_data['Data']['WinRatio']
    ProfitableWeeksPct      = rankings_data['Data']['ProfitableWeeksPct']
    LongPosPct              = rankings_data['Data']['LongPosPct']
    TopTradedInstrumentId   = rankings_data['Data']['TopTradedInstrumentId']
    TotalTradedInstruments  = rankings_data['Data']['TotalTradedInstruments']
    AvgPosSize              = rankings_data['Data']['AvgPosSize']

    #<---------------------------------------------------------- Fetching Open Positions Data (Total Positions) ---------------------------------------------------------->#
    print(f"Fetching portfolio data for https://www.etoro.com/sapi/trade-data-real/live/public/portfolios?cid={cid_data['realCID']}")
    portfolio_url = f"https://www.etoro.com/sapi/trade-data-real/live/public/portfolios?cid={cid_data['realCID']}"
    response      = requests.get(portfolio_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    portfolio_data = response.json()

    positions_data             = []
    total_open_dollar_invested = 0
    total_unrealised_value     = 0
    for position in portfolio_data.get('AggregatedPositions', []):
        instrument_id   = position.get('InstrumentID')
        if instrument_id:
            #<---------------------------------------------------------- Fetching Open Position Data (Individual Positions incl duplicated)---------------------------------------------------------->#
            print(f"Fetching open position data for https://www.etoro.com/sapi/trade-data-real/live/public/positions?cid={cid_data['realCID']}&InstrumentID={instrument_id}")
            position_url = f"https://www.etoro.com/sapi/trade-data-real/live/public/positions?cid={cid_data['realCID']}&InstrumentID={instrument_id}"
            response     = requests.get(position_url, headers=headers, proxies=proxies)
            response.raise_for_status()
            position_data = response.json()
            
            average_open     = position_data.get('AverageOpen', 0)
            invested_amount  = position_data.get('Invested', 0)
            net_profit       = position_data.get('NetProfit', 0)
            current_rate     = position_data.get('CurrentRate', 0)
            current_rate = position_data['PublicPositions'][0]['CurrentRate'] if position_data['PublicPositions'] else 0
            IsBuy = position_data['PublicPositions'][0]['IsBuy']


            leverage = sum(pos.get('Leverage', 1) for pos in position_data['PublicPositions']) / len(position_data['PublicPositions'])
            if IsBuy:
                profit_loss_percentage = ((current_rate - average_open) / average_open) * 100 if average_open != 0 else 0
            else:
                profit_loss_percentage = ((average_open - current_rate) / average_open) * 100 if average_open != 0 else 0
            profit_loss_percentage *= leverage
            unrealised_value = invested_amount * (1 + net_profit / 100)
            total_unrealised_value += unrealised_value
            
            ticker_name_open_position = instrument_map.get(str(instrument_id).lower(), 'Unknown')
            
            positions_data.append({
                'TickerName'       : ticker_name_open_position,
                'AverageOpen'      : average_open,
                'InvestedAmount'   : invested_amount,
                'UnrealisedValue'  : profit_loss_percentage,
                'Leverage'         : leverage,
                'CurrentRate'      : current_rate,
            })
    
    print(f"Cumulative Invested Amount: {total_open_dollar_invested}, Cumulative Unrealised Value: {total_unrealised_value}")

    with open('C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/open_positions_equity.json', 'w') as f:
        json.dump(positions_data, f, indent=4)

    #<---------------------------------------------------------- Fetching Risk Score Contribution Data ---------------------------------------------------------->#
    print(f"Fetching risk score contribution data for https://www.etoro.com/sapi/userstats/risk/UserName/{username}/Contribution")
    risk_exposure_url = f"https://www.etoro.com/sapi/userstats/risk/UserName/{username}/Contribution"
    response          = requests.get(risk_exposure_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    risk_exposure_data = response.json()
    #<------------------------------------------------ Fetching Annual and Monthly Returns Data ------------------------------------------------>#
    print(f"Fetching annual and monthly returns data for www.etoro.com/sapi/userstats/gain/cid/{cid_data['realCID']}/history?IncludeSimulation=true")
    returns_url = f"https://www.etoro.com/sapi/userstats/gain/cid/{cid_data['realCID']}/history?IncludeSimulation=true"
    response    = requests.get(returns_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    returns_data = response.json()

    #<------------------------------------------------ Fetching Closed Trade Data (Dollarised) ------------------------------------------------>#
    print(f"Fetching Closed Trade Data for https://www.etoro.com/sapi/trade-data-real/history/public/credit/flat?StartTime=2024-01-12T00:00:00.000Z&PageNumber=1&ItemsPerPage=300000&PublicHistoryPortfolioFilter=&CID={cid_data['realCID']}")
    closed_trade_url = f"https://www.etoro.com/sapi/trade-data-real/history/public/credit/flat?StartTime=2024-01-12T00:00:00.000Z&PageNumber=1&ItemsPerPage=300000&PublicHistoryPortfolioFilter=&CID={cid_data['realCID']}"
    response         = requests.get(closed_trade_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    closed_trade_data = response.json()
    
    ClosedData          = closed_trade_data.get('PublicHistoryPositions', [])
    dollar_returns      = []
    total_dollar_return = 0
    trade_data          = []
    start_date          = None

    total_position_size = 0
    total_trades        = 0

    for trade in ClosedData:
        ClosedTradeInstrumentID = trade.get('InstrumentID')
        leverage                = trade.get('Leverage')
        OpenRate                = trade.get('OpenRate')
        ClosedRate              = trade.get('CloseRate')
        IsBuy                   = trade.get('IsBuy')
        CloseDateTime           = trade.get('CloseDateTime')
        if start_date is None or (CloseDateTime and CloseDateTime < start_date):
            start_date = CloseDateTime
        if ClosedTradeInstrumentID is not None and OpenRate is not None and ClosedRate is not None and IsBuy is not None:
            if IsBuy:
                dollar_return = (ClosedRate - OpenRate)
            else:
                dollar_return = (OpenRate - ClosedRate)
            invested_amount = OpenRate / leverage
            dollar_returns.append(dollar_return)
            total_dollar_return += dollar_return

            ticker_name = instrument_map.get(str(ClosedTradeInstrumentID).lower(), 'Unknown')

            trade_data.append({
                'TickerName'      : ticker_name,
                'OpenRate'        : OpenRate,
                'ClosedRate'      : ClosedRate,
                'IsBuy'           : IsBuy,
                'dollar_return'   : dollar_return,
                'invested_amount' : invested_amount,
                'leverage'        : leverage,
                'CloseDateTime'   : CloseDateTime
            })

            total_position_size += invested_amount
            total_trades        += 1
        else:
            print(f"Missing data in trade: {trade}")

    average_position_size = total_position_size / total_trades if total_trades > 0 else 0

    with open('C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/temp_equity.json', 'w') as f:
        json.dump(trade_data, f, indent=4)

    #<---------------------------------------------------------- Fetching Aggregated Closed Trade Data (Total Closed Trades, Total Closed Manual Trades, Net % Closed Realised) ---------------------------------------------------------->#
    print(f"Fetching aggregated closed trade data for https://www.etoro.com/sapi/trade-data-real/history/public/credit/flat/aggregated?StartTime=2024-01-13T00:00:00.000Z&CID={cid_data['realCID']}")
    aggregated_closed_trade_url = f"https://www.etoro.com/sapi/trade-data-real/history/public/credit/flat/aggregated?StartTime=2024-01-13T00:00:00.000Z&CID={cid_data['realCID']}"
    response                    = requests.get(aggregated_closed_trade_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    aggregated_closed_trade_data = response.json()

    AggregatedClosedTradeData = {
        "TotalClosedTrades": aggregated_closed_trade_data.get('TotalClosedTrades'),
        "TotalClosedManualPositions": aggregated_closed_trade_data.get('TotalClosedManualPositions'),
        "TotalClosedMirrorPositions": aggregated_closed_trade_data.get('TotalClosedMirrorPositions'),
        "TotalProfitabilityPercentage": aggregated_closed_trade_data.get('TotalProfitabilityPercentage'),
        "TotalNetProfitPercentage": aggregated_closed_trade_data.get('TotalNetProfitPercentage')
    }

    #<------------------------------------------------Fetching Historical Copier Numbers------------------------------------------------>#
    print(f"Fetching historical copier numbers for www.etoro.com/sapi/userstats/copiers/userName/{username}/history?mindate=2000-12-18T00:25:38.179Z")
    copier_url = f"https://www.etoro.com/sapi/userstats/copiers/userName/{username}/history?mindate=2000-12-18T00:25:38.179Z"
    response   = requests.get(copier_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    copier_data = response.json()

    #<---------------------------------------------------------- Benchmark Values------------------------------
    print(f"Fetching benchmark values for https://www.etoro.com/sapi/candles/candles/desc.json/OneDay/760/3000")
    benchmark_url = f"https://www.etoro.com/sapi/candles/candles/desc.json/OneDay/760/3000"
    response      = requests.get(benchmark_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    benchmark_data = response.json()

    # Fetch equity value from https://www.etoro.com/sapi/trade-data-real/chart/public/{username}/oneYearAgo/1
    equity_url = f"https://www.etoro.com/sapi/trade-data-real/chart/public/{username}/oneYearAgo/1"
    response = requests.get(equity_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    equity_data = response.json()

    benchmark_changes = []
    previous_equity = None

    open_values_count = 0
    for candle in benchmark_data.get('Candles', []):
        for daily_data in candle.get('Candles', []):
            if open_values_count >= 90:
                break
            open_value = daily_data.get('Open')
            close_value = daily_data.get('Close')
            if open_value and close_value:
                percent_change = ((close_value - open_value) / open_value) * 100

                equity = next((item['equity'] for item in equity_data['simulation']['oneYearAgo']['chart'] if item['timestamp'] == daily_data.get('FromDate')), None)
                equity_percent_change = None
                if previous_equity is not None and equity is not None:
                    equity_percent_change = ((equity - previous_equity) / previous_equity) * 100

                benchmark_changes.append({
                    'FromDate': daily_data.get('FromDate'),
                    'Open': open_value,
                    'Close': close_value,
                    'PercentChange': percent_change,
                    'Equity': equity,
                    'EquityPercentChange': equity_percent_change
                })
                open_values_count += 1

                previous_equity = equity
    with open('C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/fetching/benchmark_changes.json', 'w') as f:
        json.dump(benchmark_changes, f, indent=4)

    result = {
        "User Data": {
            "Avatar URL": avatar_url,
            "About Me": about_me
        },
        "Risk Score and Rankings": rankings_data['Data'],
        "Portfolio Data": portfolio_data['AggregatedPositions'],
        "Open Positions Data": positions_data,
        "Risk Score Contribution Data": risk_exposure_data,
        "Closed Trade Data": closed_trade_data.get('PublicHistoryPositions', []),
        "Aggregated Closed Trade Data": aggregated_closed_trade_data,
        "Returns Data": returns_data,
        "Closed Trade Metrics" : AggregatedClosedTradeData,
        "Historical Copier Numbers": copier_data,
    }
    # Save the result to a JSON file
    with open(f'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/user_data/{username}.json', 'w') as f:
        json.dump(result, f, indent=4)

    return result

def load_instrument_map(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
    
def map_instrument_ids(data, instrument_map):
    for item in data:
        instrument_id = None
        for key in item:
            if key.lower() == 'instrumentid':
                instrument_id = item.get(key)
                break
        if instrument_id is not None:
            instrument_id = str(instrument_id).lower()
            if instrument_id in instrument_map:
                item['TickerName'] = instrument_map[instrument_id]
            else:
                print(f"InstrumentID {instrument_id} not found in instrument_map.")
                item['TickerName'] = 'Unknown'
        else:
            item['TickerName'] = 'Unknown'
    return data

def map_instrument_ids_test(instrument_id, instrument_map_path):
    # Load the instrument mapping from the file
    with open(instrument_map_path, 'r') as f:
        instrument_map = json.load(f)
    
    if instrument_id is not None:
        instrument_id = str(instrument_id).lower()  # Ensure the ID is a lowercase string
        if instrument_id in instrument_map:
            return instrument_map[instrument_id]  # Return the mapped ticker name
        else:
            print(f"InstrumentID {instrument_id} not found in instrument_map.")
            return 'Unknown'  # Return 'Unknown' if not found
    else:
        return 'Unknown'  # Return 'Unknown' if instrument_id is None

def main(usernames_file):
    user_data_dir = 'C:/Users/aiden/OneDrive/Documents/Desktop/bullaware/react-charts-app/user_data'
    with open(usernames_file, 'r') as f:
        usernames = f.read().splitlines()
    
    for username in usernames:
        user_data_file = os.path.join(user_data_dir, f"{username}.json")
        if os.path.exists(user_data_file):
            print(f"User data for {username} already exists. Skipping...")
            print("------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            continue
        
        try:
            fetch_user_data(username)
            print(f"Successfully fetched data for {username}")
            print("------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            # Remove the username from the file after processing
            with open(usernames_file, 'w') as f:
                remaining_usernames = [u for u in usernames if u != username]
                f.write('\n'.join(remaining_usernames))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"Rate limit exceeded for {username}. Waiting for an additional minute before retrying...")
                time.sleep(60)
                continue
            else:
                print(f"Error fetching data for {username}: {e}")
        except Exception as e:
            print(f"Error fetching data for {username}: {e}")
        print("------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        print("Pausing for 20 seconds...")
        time.sleep(20)  # Pause for 20 seconds between each user request

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python metrics.py <usernames_file>")
    else:
        main(sys.argv[1])
