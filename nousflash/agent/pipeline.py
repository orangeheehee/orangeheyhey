import json
import time
from sqlalchemy.orm import Session
from db.db_setup import get_db
from engines.post_retriever import (
    retrieve_recent_posts,
    fetch_external_context,
    fetch_notification_context,
    format_post_list
)
from engines.short_term_mem import generate_short_term_memory
from engines.long_term_mem import (
    create_embedding,
    retrieve_relevant_memories,
    store_memory,
)
from engines.post_maker import generate_post
from engines.significance_scorer import score_significance
from engines.post_sender import send_post, send_post_API
from engines.wallet_send import (
    transfer_sol, 
    transfer_token,
    create_token,
    wallet_address_in_post, 
    get_wallet_balance
)
from engines.follow_user import follow_by_username, decide_to_follow_users
from engines.token_actions import decide_token_actions
from models import Post, User, TweetPost, TokenTransaction
from twitter.account import Account

def process_wallet_operations(
    db: Session,
    notif_context: list,
    private_key: str,
    solana_rpc_url: str,
    llm_api_key: str
):
    """Handle all wallet-related operations including SOL transfers and token actions"""
    balance_sol = get_wallet_balance(private_key, solana_rpc_url)
    print(f"Agent wallet balance is {balance_sol} SOL now.\n")
    
    # Process SOL transfers if balance is sufficient
    if balance_sol > 0.5:  # Adjusted threshold for SOL
        tries = 0
        max_tries = 2
        while tries < max_tries:
            wallet_data = wallet_address_in_post(
                notif_context, private_key, solana_rpc_url, llm_api_key
            )
            print(f"Wallet addresses and amounts chosen from Posts: {wallet_data}")
            try:
                wallets = json.loads(wallet_data)
                if len(wallets) > 0:
                    for wallet in wallets:
                        address = wallet["address"]
                        amount = wallet["amount"]
                        tx_signature = transfer_sol(
                            private_key, solana_rpc_url, address, amount
                        )
                        # Store transaction in database
                        store_transaction(db, "SOL", tx_signature, address, amount)
                    break
                else:
                    print("No wallet addresses or amounts to send SOL to.")
                    break
            except Exception as e:
                print(f"Error in wallet operations: {e}")
                tries += 1

def process_token_operations(
    db: Session,
    notif_context: list,
    private_key: str,
    solana_rpc_url: str,
    llm_api_key: str
):
    """Handle token-related operations including creation and transfers"""
    tries = 0
    max_tries = 2
    while tries < max_tries:
        try:
            # Get token action decisions from LLM
            token_actions = decide_token_actions(notif_context, llm_api_key)
            actions = json.loads(token_actions)
            
            for action in actions:
                if action["type"] == "create":
                    # Create new token
                    token_info = create_token(
                        private_key,
                        solana_rpc_url,
                        action["name"],
                        action["symbol"],
                        action.get("decimals", 9)
                    )
                    store_token_creation(db, token_info)
                
                elif action["type"] == "transfer":
                    # Transfer existing tokens
                    tx_signature = transfer_token(
                        private_key,
                        solana_rpc_url,
                        action["token_mint"],
                        action["to_address"],
                        action["amount"],
                        action.get("decimals", 9)
                    )
                    store_transaction(
                        db, 
                        action["token_mint"], 
                        tx_signature,
                        action["to_address"],
                        action["amount"]
                    )
            break
        except Exception as e:
            print(f"Error in token operations: {e}")
            tries += 1

def store_transaction(
    db: Session, 
    token_type: str,
    signature: str, 
    recipient: str, 
    amount: float
):
    """Store transaction details in database"""
    transaction = TokenTransaction(
        token_type=token_type,
        signature=signature,
        recipient=recipient,
        amount=amount,
        timestamp=time.time()
    )
    db.add(transaction)
    db.commit()

def store_token_creation(db: Session, token_info: dict):
    """Store token creation details in database"""
    # Add your token creation model and storage logic here
    pass

def run_pipeline(
    db: Session,
    account: Account,
    auth,
    private_key: str,
    solana_rpc_url: str,
    llm_api_key: str,
    openrouter_api_key: str,
    openai_api_key: str,
):
    """
    Run the main pipeline for generating and posting content.

    Args:
        db (Session): Database session
        account (Account): Twitter/X API account instance
        private_key (str): Base58 encoded Solana private key
        solana_rpc_url (str): Solana RPC URL
        llm_api_key (str): API key for LLM service
        openrouter_api_key (str): API key for OpenRouter
        openai_api_key (str): API key for OpenAI
    """
    # Step 1: Retrieve recent posts
    recent_posts = retrieve_recent_posts(db)
    formatted_recent_posts = format_post_list(recent_posts)
    print(f"Recent posts: {formatted_recent_posts}")

    # Step 2: Fetch external context
    notif_context_tuple = fetch_notification_context(account)
    notif_context_id = [context[1] for context in notif_context_tuple]

    # Filter notifications
    existing_tweet_ids = {tweet.tweet_id for tweet in db.query(TweetPost.tweet_id).all()}
    filtered_notif_context_tuple = [
        context for context in notif_context_tuple 
        if context[1] not in existing_tweet_ids
    ]

    # Store tweet IDs
    for id in notif_context_id:
        new_tweet_post = TweetPost(tweet_id=id)
        db.add(new_tweet_post)
        db.commit()

    notif_context = [context[0] for context in filtered_notif_context_tuple]
    print("New Notifications:\n")
    for notif in notif_context_tuple:
        print(f"- {notif[0]}, tweet at https://x.com/user/status/{notif[1]}\n")
    external_context = notif_context

    if len(notif_context) > 0:
        # Step 2.5: Process wallet and token operations
        process_wallet_operations(db, notif_context, private_key, solana_rpc_url, llm_api_key)
        time.sleep(5)
        
        process_token_operations(db, notif_context, private_key, solana_rpc_url, llm_api_key)
        time.sleep(5)

        # Step 2.75: Handle user following
        print("Deciding following now")
        tries = 0
        max_tries = 2
        while tries < max_tries:
            try:
                decision_data = decide_to_follow_users(db, notif_context, openrouter_api_key)
                decisions = json.loads(decision_data)
                if len(decisions) > 0:
                    for decision in decisions:
                        username = decision["username"]
                        score = decision["score"]
                        if score > 0.98:
                            follow_by_username(account, username)
                            print(f"user {username} has a high rizz of {score}, now following.")
                        else:
                            print(f"Score {score} for user {username} is below threshold.")
                    break
                else:
                    print("No users to follow.")
                    break
            except Exception as e:
                print(f"Error in following users: {e}")
                tries += 1

    time.sleep(5)

    # Steps 3-9: Memory and post generation (unchanged)
    short_term_memory = generate_short_term_memory(
        recent_posts, external_context, llm_api_key
    )
    print(f"Short-term memory: {short_term_memory}")

    short_term_embedding = create_embedding(short_term_memory, openai_api_key)
    long_term_memories = retrieve_relevant_memories(db, short_term_embedding)
    print(f"Long-term memories: {long_term_memories}")

    new_post_content = generate_post(
        short_term_memory, 
        long_term_memories, 
        formatted_recent_posts, 
        external_context, 
        llm_api_key
    )
    new_post_content = new_post_content.strip('"')
    print(f"New post content: {new_post_content}")

    significance_score = score_significance(new_post_content, llm_api_key)
    print(f"Significance score: {significance_score}")

    if significance_score >= 7:
        new_post_embedding = create_embedding(new_post_content, openai_api_key)
        store_memory(db, new_post_content, new_post_embedding, significance_score)

    ai_user = db.query(User).filter(User.username == "orange_hey_hey").first()
    if not ai_user:
        ai_user = User(username="orange_hey_hey", email="orange_hey_hey@example.com")
        db.add(ai_user)
        db.commit()

    if significance_score >= 3:
        res = send_post_API(auth, new_post_content)
        print(f"Posted API with tweet_id: {res}")

        if res is not None:
            print(f"Posted with tweet_id: {res}")
            new_db_post = Post(
                content=new_post_content,
                user_id=ai_user.id,
                username=ai_user.username,
                type="text",
                tweet_id=res,
            )
            db.add(new_db_post)
            db.commit()
        else:
            res = send_post(account, new_post_content)
            rest_id = (res.get('data', {})
                        .get('create_tweet', {})
                        .get('tweet_results', {})
                        .get('result', {})
                        .get('rest_id'))

            if rest_id is not None:
                print(f"Posted with tweet_id: {rest_id}")
                new_db_post = Post(
                    content=new_post_content,
                    user_id=ai_user.id,
                    username=ai_user.username,
                    type="text",
                    tweet_id=rest_id,
                )
                db.add(new_db_post)
                db.commit()

    print(
        f"New post generated with significance score {significance_score}: {new_post_content}"
    )