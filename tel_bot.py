#!/usr/bin/env python3
"""Telegram bot for sending notifications about AWL garbage pickup."""

import requests


def send_telegram_notification(bot_token, chat_id, message):
    """
    Send a notification to the Telegram bot.

    Parameters:
        bot_token (str): The token of the Telegram bot.
        chat_id (str): The chat ID to send the message to.
        message (str): The message to send.

    Returns:
        dict: The response from the Telegram API.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response.json()


# Example usage
if __name__ == "__main__":
    # the bot token can be checked via
    #  https://api.telegram.org/bot<BOT_TOKEN>/getMe
    BOT_TOKEN = "7109240230:AAEAP0p71nPZ1EFzi8ezbhXgc1upwBpNcQM"
    CHAT_ID = "823682731"      # Replace with your chat ID
    MESSAGE = "This is a test notification from awlSchedule."

    result = send_telegram_notification(BOT_TOKEN, CHAT_ID, MESSAGE)
    print(result)
