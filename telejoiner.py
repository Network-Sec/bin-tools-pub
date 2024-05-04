#!/usr/bin/env python3

# telejoiner 
# - join telegram groups by name or id
# - try to scrape while joining and output info
# - not fully finished

import sys
import csv
from telethon.sync import TelegramClient
from telethon.tl import functions
from telethon.tl.functions import *
from telethon.tl.functions.channels import *
from telethon.tl.types import *
from telethon.errors import *
from telethon.sync import TelegramClient
import sys
from colorama import init, Fore, Style
from tabulate import tabulate

# Initialize colorama
init(autoreset=True)

# Replace these values with your own API ID, API hash, and phone number
api_id = '...'
api_hash = '...'
phone_number = '+....'

def print_channel_info(client, entity):
    try:
        full_info = client(GetFullChannelRequest(entity))
        data = [
            ["Title", entity.title],
            ["ID", entity.id],
            ["Access Hash", entity.access_hash],
            ["Username", entity.username or "None"],
            ["Description", full_info.full_chat.about],
            ["Member Count", full_info.full_chat.participants_count],
            ["Admins Count", full_info.full_chat.admins_count],
            ["Banned Count", full_info.full_chat.banned_count],
            ["Kicked Count", full_info.full_chat.kicked_count],
        ]
        print(Fore.YELLOW + Style.BRIGHT + "\nChannel Details:\n" + Style.NORMAL + tabulate(data, headers=["Field", "Value"], tablefmt="grid"))
    except Exception as e:
        print(Fore.RED + f"Failed to retrieve full channel info: {str(e)}")

def list_channel_users(client, entity):
    try:
        print(Fore.CYAN + Style.BRIGHT + "\nListing members:")
        offset = 0
        limit = 100
        members = []
        while True:
            participants = client(GetParticipantsRequest(entity, ChannelParticipantsSearch(''), offset, limit, hash=0))
            if not participants.users:
                break
            members.extend(participants.users)
            offset += len(participants.users)
        data = [[user.id, user.first_name, user.last_name, user.username] for user in members]
        print(tabulate(data, headers=["ID", "First Name", "Last Name", "Username"], tablefmt="grid"))
    except Exception as e:
        print(Fore.RED + f"Failed to list channel members: {str(e)}")

def interact_with_entity(client, entity):
    try:
        result = client(JoinChannelRequest(entity))
        print(f"Joined channel/group: {result.chats[0].title}")
        #client(LeaveChannelRequest(entity))
        #print(f"Left the channel/group: {entity.title}")
    except ChannelPrivateError:
        print("The channel/group is private and cannot be joined.")
    except Exception as e:
        print(f"Failed to join or leave channel/group: {str(e)}")

    try:
        client.send_message(entity, '❤️')
        print("Message sent.")
    except UserPrivacyRestrictedError:
        print("Cannot send message due to user privacy settings.")
    except Exception as e:
        print(f"Failed to send message: {str(e)}")

def join_and_leave_group(client, entity):
    # Join and immediately leave the group to show capabilities
    try:
        result = client(JoinChannelRequest(entity))
        print(f"Joined channel/group: {result.chats[0].title}")
        client(LeaveChannelRequest(entity))
        print(f"Left the channel/group: {entity.title}")
    except Exception as e:
        print(f"Failed to join or leave channel/group: {str(e)}")

def send_message(client, entity):
    # Try sending a message
    try:
        client.send_message(entity, '❤️')
        print("Message sent.")
    except Exception as e:
        print(f"Failed to send message: {str(e)}")

def add_to_contacts(client, entity):
    # Try adding to contacts if it's a user
    if isinstance(entity, types.User):
        try:
            client(functions.contacts.AddContactRequest(id=entity.id, first_name=entity.first_name or 'No First Name', last_name=entity.last_name or '', phone='Unknown', add_phone_privacy_exception=True))
            print("Added to contacts.")
        except Exception as e:
            print(f"Failed to add to contacts: {str(e)}")

def get_detailed_info(client, entity):
    # Get detailed info for channels/groups
    if hasattr(entity, 'broadcast') or hasattr(entity, 'megagroup'):
        try:
            full_info = client(GetFullChannelRequest(channel=entity))
            print(f"Channel/Group info: {full_info.full_chat.about if full_info.full_chat.about else 'No additional info available'}")
        except Exception as e:
            print(f"Failed to get full info: {str(e)}")

def scrape_and_add(client):
    # Example scraping and adding process
    source_group = 'source_group_username'
    target_group = 'target_group_username'
    all_members = scrape_members(client, source_group)
    add_members_to_group(client, all_members, target_group)

def scrape_members(client, group_username):
    group_entity = client.get_entity(group_username)
    all_users = client.get_participants(group_entity, aggressive=True)
    return all_users

def add_members_to_group(client, members, group_username):
    target_group_entity = client.get_entity(group_username)
    for user in members:
        try:
            client(InviteToChannelRequest(target_group_entity, [user]))
            print(f"Added {user.id} successfully.")
        except (FloodWaitError, UserPrivacyRestrictedError) as e:
            print(f"Failed to add {user.id}: {e}")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <channel_name>")
        sys.exit(1)

    identifier = sys.argv[1]  # This should be the channel name or ID

    client = TelegramClient('session_name', api_id, api_hash)
    client.start(phone=phone_number)

    try:
        entity = client.get_entity(identifier)
        print(Fore.GREEN + Style.BRIGHT + "Entity retrieved: " + Style.NORMAL + f"{entity.title}")
        print_channel_info(client, entity)
        list_channel_users(client, entity)
    except ChannelPrivateError:
        print(Fore.RED + "The channel/group is private and cannot be joined.")
    except Exception as e:
        print(Fore.RED + f"Failed to retrieve entity by identifier '{identifier}': {str(e)}")

if __name__ == '__main__':
    main()
