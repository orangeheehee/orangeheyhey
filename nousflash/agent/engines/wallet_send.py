import os
import re
import requests
import base58
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.commitment import Confirmed
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    initialize_mint, 
    create_associated_token_account,
    mint_to,
    transfer as token_transfer
)
from engines.prompts import get_wallet_decision_prompt

def get_wallet_balance(private_key: str, solana_rpc_url: str) -> float:
    """
    Get SOL balance for a wallet
    
    Parameters:
    - private_key (str): Base58 encoded private key
    - solana_rpc_url (str): Solana RPC URL
    
    Returns:
    - float: Balance in SOL
    """
    try:
        client = Client(solana_rpc_url)
        keypair = Keypair.from_base58_string(private_key)
        balance = client.get_balance(keypair.pubkey())
        return float(balance['result']['value']) / 1e9  # Convert lamports to SOL
    except Exception as e:
        print(f"Error getting balance: {e}")
        return 0.0

def transfer_sol(private_key: str, solana_rpc_url: str, to_address: str, amount_in_sol: float) -> str:
    """
    Transfer SOL to another address
    
    Parameters:
    - private_key (str): Base58 encoded private key
    - solana_rpc_url (str): Solana RPC URL
    - to_address (str): Recipient's Solana address
    - amount_in_sol (float): Amount of SOL to send
    
    Returns:
    - str: Transaction signature or error message
    """
    try:
        client = Client(solana_rpc_url)
        keypair = Keypair.from_base58_string(private_key)
        recipient = Pubkey.from_string(to_address)
        
        # Create transfer instruction
        transfer_params = TransferParams(
            from_pubkey=keypair.pubkey(),
            to_pubkey=recipient,
            lamports=int(amount_in_sol * 1e9)  # Convert SOL to lamports
        )
        
        # Create and sign transaction
        transaction = Transaction().add(transfer(transfer_params))
        signature = client.send_transaction(
            transaction,
            keypair,
            opts={"skip_confirmation": False, "preflight_commitment": "confirmed"}
        )
        
        return signature['result']
    except Exception as e:
        return f"Transfer failed: {e}"

def transfer_token(
    private_key: str,
    solana_rpc_url: str,
    token_mint: str,
    to_address: str,
    amount: float,
    decimals: int = 9
) -> str:
    """
    Transfer SPL tokens to another address
    
    Parameters:
    - private_key (str): Base58 encoded private key
    - solana_rpc_url (str): Solana RPC URL
    - token_mint (str): Token mint address
    - to_address (str): Recipient's Solana address
    - amount (float): Amount of tokens to send
    - decimals (int): Token decimals
    
    Returns:
    - str: Transaction signature or error message
    """
    try:
        client = Client(solana_rpc_url)
        keypair = Keypair.from_base58_string(private_key)
        mint_pubkey = Pubkey.from_string(token_mint)
        recipient = Pubkey.from_string(to_address)
        
        # Get associated token accounts
        sender_ata = get_associated_token_address(keypair.pubkey(), mint_pubkey)
        recipient_ata = get_associated_token_address(recipient, mint_pubkey)
        
        # Create recipient's ATA if it doesn't exist
        if not client.get_account_info(recipient_ata)['result']['value']:
            create_ata_ix = create_associated_token_account(
                payer=keypair.pubkey(),
                owner=recipient,
                mint=mint_pubkey
            )
            transaction = Transaction().add(create_ata_ix)
            client.send_transaction(
                transaction,
                keypair,
                opts={"skip_confirmation": False}
            )
        
        # Create transfer instruction
        transfer_ix = token_transfer(
            TOKEN_PROGRAM_ID,
            sender_ata,
            recipient_ata,
            keypair.pubkey(),
            amount=int(amount * (10 ** decimals))
        )
        
        # Send transaction
        transaction = Transaction().add(transfer_ix)
        signature = client.send_transaction(
            transaction,
            keypair,
            opts={"skip_confirmation": False, "preflight_commitment": "confirmed"}
        )
        
        return signature['result']
    except Exception as e:
        return f"Token transfer failed: {e}"

def create_token(
    private_key: str,
    solana_rpc_url: str,
    name: str,
    symbol: str,
    decimals: int = 9
) -> dict:
    """
    Create a new SPL token
    
    Parameters:
    - private_key (str): Base58 encoded private key
    - solana_rpc_url (str): Solana RPC URL
    - name (str): Token name
    - symbol (str): Token symbol
    - decimals (int): Token decimals
    
    Returns:
    - dict: Token information including mint address
    """
    try:
        client = Client(solana_rpc_url)
        keypair = Keypair.from_base58_string(private_key)
        
        # Create mint account
        mint_keypair = Keypair()
        mint_pubkey = mint_keypair.pubkey()
        
        # Calculate minimum rent exemption
        min_rent = client.get_minimum_balance_for_rent_exemption(
            82)['result']  # Mint account size
        
        # Create mint account transaction
        transaction = Transaction().add(
            # Create account
            create_account(
                CreateAccountParams(
                    from_pubkey=keypair.pubkey(),
                    new_account_pubkey=mint_pubkey,
                    lamports=min_rent,
                    space=82,
                    program_id=TOKEN_PROGRAM_ID
                )
            ),
            # Initialize mint
            initialize_mint(
                TOKEN_PROGRAM_ID,
                mint_pubkey,
                keypair.pubkey(),
                None,  # Freeze authority
                decimals
            )
        )
        
        # Send transaction
        signature = client.send_transaction(
            transaction,
            [keypair, mint_keypair],
            opts={"skip_confirmation": False, "preflight_commitment": "confirmed"}
        )
        
        return {
            "mint_address": str(mint_pubkey),
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "signature": signature['result']
        }
    except Exception as e:
        return f"Token creation failed: {e}"

def wallet_address_in_post(posts, private_key, solana_rpc_url: str, llm_api_key: str):
    """
    Detects Solana wallet addresses from a list of posts
    
    Parameters:
    - posts (List): List of posts
    - private_key (str): Base58 encoded private key
    - solana_rpc_url (str): Solana RPC URL
    - llm_api_key (str): API key for LLM service
    
    Returns:
    - str: LLM response with addresses and amounts
    """
    # Convert everything to strings first
    str_posts = [str(post) for post in posts]
    
    # Look for Solana addresses (base58 encoded, usually 32-44 characters)
    sol_pattern = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
    matches = []
    
    for post in str_posts:
        found_matches = sol_pattern.findall(post)
        matches.extend(found_matches)
    
    wallet_balance = get_wallet_balance(private_key, solana_rpc_url)
    prompt = get_wallet_decision_prompt(posts, matches, wallet_balance)
    
    response = requests.post(
        url="https://api.hyperbolic.xyz/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_api_key}",
        },
        json={
            "messages": [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": "Respond only with the wallet address(es) and amount(s) you would like to send to."
                }
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "presence_penalty": 0,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
        }
    )
    
    if response.status_code == 200:
        print(f"SOL Addresses and amounts chosen from Posts: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating short-term memory: {response.text}")