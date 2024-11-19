from solders.pubkey import Pubkey as PublicKey
from solders.keypair import Keypair
from solana.transaction import Transaction
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
import solders.system_program as sp
from pyserum.market import Market
from pyserum.connection import get_live_markets
import tweepy
import requests
import re

# Configuration
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
client = Client(SOLANA_RPC_URL)
wallet = Keypair()

# Constants
SLIPPAGE = 0.15
BUY_AMOUNT = 1  # 1 SOL
TAKE_PROFIT_MULTIPLIER = 3  # 3x profit
MOONBAG = 0.15  # 15% as moonbag
MIN_SCORE = 85  # Minimum score threshold
TWITTER_ACCOUNTS = []
TWEETS_COUNT = 10

# API Keys
TWITTER_API = {
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN",
    "access_secret": "YOUR_ACCESS_SECRET",
}
SOLSNIFFER_API_KEY = "YOUR_SOL_SNIFFER_API_KEY"
TWEETSCOUT_API_KEY = "YOUR_TWEETSCOUT_API_KEY"

# Market Address
MARKET_ADDRESS = "MARKET_ADDRESS_HERE"  # Replace with actual market address
market = None


# Initialize Serum market
def initialize_market():
    """Load and initialize the Serum market."""
    global market
    try:
        market_address = PublicKey(MARKET_ADDRESS)
        market = Market.load(client, market_address, payer=wallet)
        print(f"Market initialized for address: {MARKET_ADDRESS}")
    except Exception as e:
        print(f"Error initializing market: {e}")


# Extract Ethereum and Solana contract addresses from tweets
def extract_contracts(tweet):
    """Extract Ethereum and Solana contract addresses from tweet text."""
    eth_contracts = re.findall(r"0x[a-fA-F0-9]{40}", tweet)
    sol_contracts = re.findall(r"[a-zA-Z0-9]{43,44}", tweet)
    return eth_contracts + sol_contracts


# Check contract score via SolSniffer
def get_contract_score(contract):
    """Fetch the contract's score using the SolSniffer API."""
    try:
        url = f"https://solsniffer.com/api/contract/{contract}"
        response = requests.get(url, headers={"Authorization": f"Bearer {SOLSNIFFER_API_KEY}"})
        if response.status_code == 200:
            return response.json().get("score", 0)
    except Exception as e:
        print(f"Error fetching contract score for {contract}: {e}")
    return 0


# Analyze Twitter handle using TweetScout
def analyze_twitter_page(handle):
    """Analyze a Twitter page using the TweetScout API."""
    try:
        url = f"https://app.tweetscout.io/api/{handle}"
        headers = {"Authorization": f"Bearer {TWEETSCOUT_API_KEY}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error analyzing Twitter handle {handle}: {e}")
    return {}


# Fetch recent tweets from a given Twitter account
def fetch_tweets(account):
    """Fetch recent tweets from a Twitter account."""
    try:
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API["api_key"],
            TWITTER_API["api_secret"],
            TWITTER_API["access_token"],
            TWITTER_API["access_secret"],
        )
        api = tweepy.API(auth)
        return api.user_timeline(screen_name=account, count=TWEETS_COUNT)
    except Exception as e:
        print(f"Error fetching tweets for {account}: {e}")
        return []


# Place a buy order on Serum
def place_buy_order(amount, price):
    """Place a buy order on Serum."""
    try:
        slippage_amount = amount * SLIPPAGE
        transaction = Transaction()
        transaction.add(
            market.make_place_order_instruction(
                owner=wallet.public_key,
                payer=wallet.public_key,
                side="buy",
                price=price + slippage_amount,
                size=amount,
                order_type="limit",
            )
        )
        signature = client.send_transaction(transaction, wallet, opts=TxOpts(skip_preflight=True))
        print(f"Buy order placed. Signature: {signature}")
    except Exception as e:
        print(f"Error placing buy order: {e}")


# Place a sell order with take profit and moonbag
def place_sell_order(amount, target_price):
    """Place a sell order on Serum."""
    try:
        transaction = Transaction()
        transaction.add(
            market.make_place_order_instruction(
                owner=wallet.public_key,
                payer=wallet.public_key,
                side="sell",
                price=target_price,
                size=amount,
                order_type="limit",
            )
        )
        signature = client.send_transaction(transaction, wallet, opts=TxOpts(skip_preflight=True))
        print(f"Sell order placed. Signature: {signature}")
    except Exception as e:
        print(f"Error placing sell order: {e}")


# Main process
def process_twitter_handles():
    """Process tweets from configured Twitter handles."""
    for account in TWITTER_ACCOUNTS:
        tweets = fetch_tweets(account)
        for tweet in tweets:
            contracts = extract_contracts(tweet.text)
            for contract in contracts:
                score = get_contract_score(contract)
                if score < MIN_SCORE:
                    print(f"Skipping contract {contract} with score {score}")
                    continue

                print(f"Contract {contract} passed with score {score}")
                twitter_data = analyze_twitter_page(contract)
                overall_score = twitter_data.get("overallScore", "N/A")
                known_followers = twitter_data.get("knownFollowers", "N/A")
                trust_level = twitter_data.get("trustLevel", "N/A")
                print(f"Twitter Analysis: Score {overall_score}, Followers {known_followers}, Trust {trust_level}")

                # Get market price and place buy/sell orders
                price = market.get_price()
                amount_to_buy = BUY_AMOUNT / price
                place_buy_order(amount_to_buy, price)
                target_price = price * TAKE_PROFIT_MULTIPLIER
                sell_amount = (1 - MOONBAG) * amount_to_buy
                place_sell_order(sell_amount, target_price)


# Execute the bot
if __name__ == "__main__":
    try:
        initialize_market()
        process_twitter_handles()
    except Exception as e:
        print(f"Error in main process: {e}")
