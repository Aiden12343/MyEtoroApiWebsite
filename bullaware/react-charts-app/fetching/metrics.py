import json
import requests

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

def fetch_user_data(username):
    headers      = get_headers() 
    proxies      = get_proxies()
    instrument_map = load_instrument_map('react-charts-app/fetching/instrument_mapping.json')

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

    #<---------------------------------------------------------- Fetching Open Positions Data ---------------------------------------------------------->#
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
            #<---------------------------------------------------------- Fetching Open Position Data (Dollarised) ---------------------------------------------------------->#
            position_url = f"https://www.etoro.com/sapi/trade-data-real/live/public/positions?cid={cid_data['realCID']}&InstrumentID={instrument_id}"
            response     = requests.get(position_url, headers=headers, proxies=proxies)
            response.raise_for_status()
            position_data = response.json()
            
            average_open    = position_data.get('AverageOpen', 0)
            leverage        = position_data['PublicPositions'][0].get('Leverage', 1)
            invested_amount = average_open / leverage
            total_open_dollar_invested += invested_amount
            
            net_profit       = position_data.get('NetProfit', 0)
            unrealised_value = invested_amount * (1 + net_profit / 100)
            total_unrealised_value += unrealised_value
            
            ticker_name_open_position = instrument_map.get(str(instrument_id).lower(), 'Unknown')
            
            positions_data.append({
                'TickerName'       : ticker_name_open_position,
                'AverageOpen'      : round(average_open, 2),
                'InvestedAmount'   : round(invested_amount, 2),
                'UnrealisedValue'  : round(unrealised_value, 2),
                'Leverage'         : leverage
            })
    
    print(f"Cumulative Invested Amount: {total_open_dollar_invested}, Cumulative Unrealised Value: {total_unrealised_value}")

    with open('react-charts-app/fetching/open_positions_equity.json', 'w') as f:
        json.dump(positions_data, f, indent=4)

    #<---------------------------------------------------------- Fetching Risk Score Contribution Data ---------------------------------------------------------->#
    print(f"Fetching risk score contribution data for https://www.etoro.com/sapi/userstats/risk/UserName/{username}/Contribution")
    risk_exposure_url = f"https://www.etoro.com/sapi/userstats/risk/UserName/{username}/Contribution"
    response          = requests.get(risk_exposure_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    risk_exposure_data = response.json()

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

    with open('react-charts-app/fetching/temp_equity.json', 'w') as f:
        json.dump(trade_data, f, indent=4)

    #<---------------------------------------------------------- Fetching Aggregated Closed Trade Data (Total Closed Trades, Total Closed Manual Trades, Net % Closed Realised) ---------------------------------------------------------->#
    print(f"Fetching aggregated closed trade data for https://www.etoro.com/sapi/trade-data-real/history/public/credit/flat/aggregated?StartTime=2024-01-13T00:00:00.000Z&CID={cid_data['realCID']}")
    aggregated_closed_trade_url = f"https://www.etoro.com/sapi/trade-data-real/history/public/credit/flat/aggregated?StartTime=2024-01-13T00:00:00.000Z&CID={cid_data['realCID']}"
    response                    = requests.get(aggregated_closed_trade_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    aggregated_closed_trade_data = response.json()

    TotalClosedTrades           = aggregated_closed_trade_data.get('TotalClosedTrades')
    TotalClosedManualPositions  = aggregated_closed_trade_data.get('TotalClosedManualPositions')
    TotalClosedMirrorPositions  = aggregated_closed_trade_data.get('TotalClosedMirrorPositions')
    TotalProfitabilityPercentage = aggregated_closed_trade_data.get('TotalProfitabilityPercentage')
    TotalNetProfitPercentage    = aggregated_closed_trade_data.get('TotalNetProfitPercentage')

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
    }
    
    # Save the result to a JSON file
    with open('react-charts-app/fetching/user_data.json', 'w') as f:
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