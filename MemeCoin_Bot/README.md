# Solana Trading Bot

This Python-based bot interacts with the Solana blockchain to automate trading on Serum, a decentralized exchange. It uses social media signals (from Twitter) to analyze potential trading opportunities and places buy/sell orders accordingly. It integrates several APIs to fetch contract scores, analyze Twitter profiles, and manage trades.

## Features

- **Twitter-based Signals**: The bot monitors predefined Twitter accounts for contract addresses mentioned in their tweets (Solana and Ethereum contracts).
- **Contract Scoring**: Contracts are assessed using the SolSniffer API, and only those with scores above a threshold are considered.
- **Serum Trading**: The bot places buy and sell orders on Serum with a slippage factor, aiming for a 10x profit multiplier.
- **Moonbag Strategy**: A moonbag of 15% is retained after selling for profit.
- **Twitter Profile Analysis**: Each contract is analyzed for Twitter engagement and trust level using the TweetScout API.

## Requirements

- **Python 3.12 or higher** (for the latest dependencies)
- **Python Packages**:
  - `solana`
  - `pyserum`
  - `tweepy`
  - `requests`
  - `solders`
  
  Install the dependencies using the following command:

  ```bash
  pip install solana pyserum tweepy requests solders
