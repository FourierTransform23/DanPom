import requests
import pandas as pd
from datetime import datetime
import json
import os


class ActionNetworkClient:
    """Client for accessing Action Network API with authentication."""

    TOKEN_CACHE_FILE = "action_network_token.txt"

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://www.actionnetwork.com',
            'Referer': 'https://www.actionnetwork.com/'
        })
        self.token = None

    def _load_cached_token(self):
        """Load token from cache file if it exists and is valid."""
        if os.path.exists(self.TOKEN_CACHE_FILE):
            try:
                with open(self.TOKEN_CACHE_FILE, 'r') as f:
                    self.token = f.read().strip()
                return True
            except:
                return False
        return False

    def _save_token(self):
        """Save token to cache file."""
        try:
            with open(self.TOKEN_CACHE_FILE, 'w') as f:
                f.write(self.token)
        except:
            pass

    def login(self):
        """Login to Action Network and obtain JWT token."""
        login_url = "https://api.actionnetwork.com/web/v1/user/loginnew"

        # Note: The captcha_token in the HAR file suggests they use captcha
        # We'll try without it first - if it fails, we'll need a different approach
        payload = {
            "email": self.email,
            "password": self.password
        }

        try:
            response = self.session.post(login_url, json=payload)
            response.raise_for_status()

            data = response.json()

            if 'token' in data:
                self.token = data['token']
                self._save_token()
                print("✓ Successfully logged in to Action Network")
                return True
            else:
                print("Login response:", json.dumps(data, indent=2)[:500])
                return False

        except requests.exceptions.HTTPError as e:
            print(f"Login failed with HTTP error: {e}")
            if e.response.status_code == 400:
                print("Note: Action Network may require captcha. Trying cached token...")
                return self._load_cached_token()
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def get_sharp_report(self, date_str=None):
        """Fetch sharp money report for NCAAB games."""
        # Try cached token first
        if not self.token:
            if not self._load_cached_token():
                if not self.login():
                    raise Exception("Failed to authenticate with Action Network")

        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        url = "https://api.actionnetwork.com/web/v2/scoreboard/proreport/ncaab"

        params = {
            'bookIds': '15,30,1006,1548,974,939,1005,972,1902,1903,2194',
            'date': date_str,
            'division': 'D1',
            'periods': 'event',
            'tournament': '0'
        }

        # The token might be used in localStorage by the web app
        # Try the request without explicit auth first (browser session might handle it)
        response = self.session.get(url, params=params)

        if response.status_code == 401:
            # If unauthorized, try with Authorization header
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            response = self.session.get(url, params=params)

        response.raise_for_status()
        return response.json()

    @staticmethod
    def _parse_market_percentages(markets, book_id='15'):
        """
        Extract spread and total ticket/money percentages from the markets field.
        Uses book_id 15 (DraftKings) as the consensus source. Falls back to the
        first available book if 15 is not present.
        """
        result = {
            'Spread_Tickets_Away': None, 'Spread_Money_Away': None,
            'Spread_Tickets_Home': None, 'Spread_Money_Home': None,
            'Total_Tickets_Over': None, 'Total_Money_Over': None,
            'Total_Tickets_Under': None, 'Total_Money_Under': None,
            'Total_Line': None,
        }

        book_data = markets.get(book_id) or next(iter(markets.values()), {})
        bets = book_data.get('event', {})

        for bet_type, entries in bets.items():
            for e in entries:
                side = e.get('side')
                tickets_pct = e.get('bet_info', {}).get('tickets', {}).get('percent')
                money_pct = e.get('bet_info', {}).get('money', {}).get('percent')

                if 'spread' in bet_type:
                    if side == 'away':
                        result['Spread_Tickets_Away'] = tickets_pct
                        result['Spread_Money_Away'] = money_pct
                    elif side == 'home':
                        result['Spread_Tickets_Home'] = tickets_pct
                        result['Spread_Money_Home'] = money_pct

                elif 'team_score' in bet_type or 'total' in bet_type:
                    if side == 'over':
                        result['Total_Tickets_Over'] = tickets_pct
                        result['Total_Money_Over'] = money_pct
                        result['Total_Line'] = e.get('value')
                    elif side == 'under':
                        result['Total_Tickets_Under'] = tickets_pct
                        result['Total_Money_Under'] = money_pct

        return result

    def parse_sharp_report_to_df(self, data):
        """Parse sharp report JSON to DataFrame."""
        games_data = []

        for game in data.get('games', []):
            away_team = game['teams'][0]['display_name']
            home_team = game['teams'][1]['display_name']

            pro_report = game.get('pro_report', {})

            # --- PRO REPORT SIGNALS (flagged by Action Network) ---
            spread_data = pro_report.get('spread', {})
            total_data = pro_report.get('total', {})

            sharp_on_away = False
            sharp_on_home = False
            steam_moves_away = 0
            steam_moves_home = 0
            big_bets_flagged_away = False
            big_bets_flagged_home = False
            power_edge_away = 0.0
            power_edge_home = 0.0
            sharp_on_over = False
            sharp_on_under = False
            steam_moves_over = 0
            steam_moves_under = 0

            for signal in spread_data.get('away', []):
                t = signal.get('signal_type')
                if t == 'sharp_money':
                    sharp_on_away = True
                    steam_moves_away = signal.get('meta', {}).get('steam_moves', 0)
                elif t == 'big_bets':
                    big_bets_flagged_away = True
                elif t == 'power_rating_edge':
                    power_edge_away = signal.get('meta', {}).get('edge', 0.0)

            for signal in spread_data.get('home', []):
                t = signal.get('signal_type')
                if t == 'sharp_money':
                    sharp_on_home = True
                    steam_moves_home = signal.get('meta', {}).get('steam_moves', 0)
                elif t == 'big_bets':
                    big_bets_flagged_home = True
                elif t == 'power_rating_edge':
                    power_edge_home = signal.get('meta', {}).get('edge', 0.0)

            for signal in total_data.get('over', []):
                if signal.get('signal_type') == 'sharp_money':
                    sharp_on_over = True
                    steam_moves_over = signal.get('meta', {}).get('steam_moves', 0)

            for signal in total_data.get('under', []):
                if signal.get('signal_type') == 'sharp_money':
                    sharp_on_under = True
                    steam_moves_under = signal.get('meta', {}).get('steam_moves', 0)

            # --- RAW BET/MONEY PERCENTAGES from markets (all games, not just flagged) ---
            market_pcts = self._parse_market_percentages(game.get('markets', {}))

            # Money differential: positive = more money than tickets (sharp indicator)
            spread_money_diff_away = (
                (market_pcts['Spread_Money_Away'] or 0) - (market_pcts['Spread_Tickets_Away'] or 0)
            )
            spread_money_diff_home = (
                (market_pcts['Spread_Money_Home'] or 0) - (market_pcts['Spread_Tickets_Home'] or 0)
            )

            total_money_diff_over = (
                (market_pcts['Total_Money_Over'] or 0) - (market_pcts['Total_Tickets_Over'] or 0)
            )

            game_info = {
                'Away Team': away_team,
                'Home Team': home_team,
                # Raw spread percentages (every game)
                'Spread_Tickets_Away': market_pcts['Spread_Tickets_Away'],
                'Spread_Money_Away': market_pcts['Spread_Money_Away'],
                'Spread_Tickets_Home': market_pcts['Spread_Tickets_Home'],
                'Spread_Money_Home': market_pcts['Spread_Money_Home'],
                # Money vs tickets differential for spread (key sharp indicator)
                'Money_Diff_Away': spread_money_diff_away,
                'Money_Diff_Home': spread_money_diff_home,
                # Raw total percentages (every game)
                'Total_Line': market_pcts['Total_Line'],
                'Total_Tickets_Over': market_pcts['Total_Tickets_Over'],
                'Total_Money_Over': market_pcts['Total_Money_Over'],
                'Total_Tickets_Under': market_pcts['Total_Tickets_Under'],
                'Total_Money_Under': market_pcts['Total_Money_Under'],
                # Money vs tickets differential for totals
                'Total_Money_Diff_Over': total_money_diff_over,
                # PRO flagged signals
                'Sharp_on_Away': sharp_on_away,
                'Steam_Moves_Away': steam_moves_away,
                'Sharp_on_Home': sharp_on_home,
                'Steam_Moves_Home': steam_moves_home,
                'Big_Bets_Flagged_Away': big_bets_flagged_away,
                'Big_Bets_Flagged_Home': big_bets_flagged_home,
                'Power_Edge_Away': power_edge_away,
                'Power_Edge_Home': power_edge_home,
                'Sharp_on_Over': sharp_on_over,
                'Steam_Moves_Over': steam_moves_over,
                'Sharp_on_Under': sharp_on_under,
                'Steam_Moves_Under': steam_moves_under,
                'Start_Time': game['start_time']
            }

            games_data.append(game_info)

        return pd.DataFrame(games_data)


def get_action_network_sharp_report(email, password, date_str=None):
    """
    Convenience function to get Action Network sharp money data.

    Parameters:
        email (str): Action Network account email
        password (str): Action Network account password
        date_str (str): Date in YYYYMMDD format. If None, uses today.

    Returns:
        pd.DataFrame: DataFrame with game info and sharp money signals
        Returns None if authentication fails
    """
    try:
        client = ActionNetworkClient(email, password)
        data = client.get_sharp_report(date_str)
        return client.parse_sharp_report_to_df(data)
    except Exception as e:
        print(f"Error fetching Action Network data: {e}")
        return None


if __name__ == "__main__":
    import pandas as pd
    import config
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)

    df = get_action_network_sharp_report(config.ACTION_NETWORK_EMAIL, config.ACTION_NETWORK_PASSWORD)

    if df is not None:
        print(f"Total games: {len(df)}\n")

        print("=== SPREAD BET/MONEY PERCENTAGES (all games) ===")
        print(df[['Away Team', 'Home Team',
                   'Spread_Tickets_Away', 'Spread_Money_Away', 'Money_Diff_Away',
                   'Spread_Tickets_Home', 'Spread_Money_Home', 'Money_Diff_Home']].to_string())

        print("\n=== TOTALS BET/MONEY PERCENTAGES (all games) ===")
        print(df[['Away Team', 'Home Team',
                   'Total_Line',
                   'Total_Tickets_Over', 'Total_Money_Over',
                   'Total_Tickets_Under', 'Total_Money_Under',
                   'Total_Money_Diff_Over']].to_string())

        print("\n=== PRO FLAGGED SIGNALS ===")
        flagged = df[
            df['Sharp_on_Away'] | df['Sharp_on_Home'] |
            df['Big_Bets_Flagged_Away'] | df['Big_Bets_Flagged_Home'] |
            (df['Power_Edge_Away'] > 0) | (df['Power_Edge_Home'] > 0)
        ]
        if len(flagged) > 0:
            print(flagged[['Away Team', 'Home Team',
                            'Sharp_on_Away', 'Steam_Moves_Away',
                            'Sharp_on_Home', 'Steam_Moves_Home',
                            'Big_Bets_Flagged_Away', 'Big_Bets_Flagged_Home',
                            'Power_Edge_Away', 'Power_Edge_Home']].to_string())
        else:
            print("No flagged signals today")
    else:
        print("\nFailed to fetch data from Action Network")
