# ORANGE HEY HEY 
An autonomous AI agent living on X/Twitter with its own Solana wallet and token capabilities.

## 🚀 New Features
- **Solana Integration**: Full Solana wallet support replacing the previous ETH implementation
- **Token Operations**: Create and transfer SPL tokens
- **Enhanced Decision Making**: Intelligent asset transfer decisions using LLM
- **Transaction Tracking**: Complete database support for all blockchain operations

## 📋 TODO List
### Wallet Actions
- [x] Basic SOL transfer capabilities
- [x] SPL token creation and transfer
- [x] Wallet balance monitoring
- [ ] Advanced transaction strategies
- [ ] Token burning mechanism
- [ ] Token metadata handling

### Social Interactions
- [x] Reply handling
- [x] Mention tracking
- [ ] Enhanced context awareness
- [ ] Community token distribution
- [ ] Token-gated interactions

## 🏗 Project Structure

### Core Components
```
.
├── db/                 # Database setup and migrations
├── engines/           # Core processing engines
│   ├── post_retriever/    # Social media data retrieval
│   ├── wallet_send/       # Solana transaction handling
│   ├── token_actions/     # Token operations
│   └── ...
├── models/            # Database models
└── twitter/           # Twitter API integration
```

### Key Files
- `pipeline.py`: Main agent pipeline implementation
- `run_pipeline.py`: Pipeline execution and scheduling
- `wallet_send.py`: Solana wallet operations
- `token_actions.py`: SPL token management

## 💻 Setup & Dependencies

### Prerequisites
```bash
# Install required packages
pip install solana
pip install solders
pip install anchorpy
pip install -r requirements.txt
```

### Environment Variables
```env
SOLANA_RPC_URL=your_rpc_url
SOLANA_PRIVATE_KEY=your_base58_private_key
LLM_API_KEY=your_llm_api_key
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
```

## 🚀 Running the Agent

### Docker Setup (Recommended)
```bash
# Start the agent
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the agent
docker-compose down
```

### Local Development
```bash
# Run locally
python run_pipeline.py
```

## 🔧 Core Functionalities

### Wallet Operations
The agent can:
- Monitor SOL balance
- Transfer SOL to other addresses
- Create new SPL tokens
- Transfer existing tokens
- Track all transactions

### Social Media Integration
- Monitors mentions and replies
- Makes intelligent decisions about asset transfers
- Responds to community interactions
- Manages token-related requests

## 📊 Database Schema

### New Tables
```sql
-- Token Transactions
CREATE TABLE token_transactions (
    id INTEGER PRIMARY KEY,
    token_type TEXT,
    signature TEXT,
    recipient TEXT,
    amount FLOAT,
    timestamp BIGINT
);

-- Additional tables for token metadata, etc.
```

## 🤖 Agent Behavior

### Decision Making
The agent uses LLM to:
1. Analyze social interactions
2. Decide on asset transfers
3. Manage token creation/distribution
4. Engage with community

### Transaction Triggers
- Direct mentions with wallet addresses
- Community engagement levels
- Predefined conditions in posts
- Special events or milestones

## 🔐 Security Considerations

### Wallet Security
- Private key management
- Transaction limits
- Balance monitoring
- Error handling

### Social Integration
- Rate limiting
- Content filtering
- Transaction verification
- Community safety

## 🛠 Development Guidelines

### Adding New Features
1. Create new function in appropriate engine
2. Update pipeline integration
3. Add database models if needed
4. Update documentation

### Testing
```bash
# Run tests
python -m pytest tests/

# Test specific component
python -m pytest tests/test_wallet_operations.py
```

## 📈 Future Improvements
- [ ] Enhanced token economics
- [ ] Advanced community features
- [ ] Multi-wallet support
- [ ] Cross-chain integration
- [ ] DAO governance capabilities

## 🤝 Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Open pull request

## ⚠️ Important Notes
- Always test on devnet first
- Monitor wallet balances
- Keep security in mind
- Backup private keys
- Review transaction limits

## 🎉 Enjoy!
Watch the agent interact with its community and manage its own assets autonomously!

For questions or issues, please open a GitHub issue.