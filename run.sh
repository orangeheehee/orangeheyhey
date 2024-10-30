#set -x
set -e

export TWEET_PROMPT_TEMPLATE=$(curl $TWEET_PROMPT_TEMPLATE_URL)

# Encumber the account by resetting the password

export PROTONMAIL_PASSWORD=$(python3 scripts/protonmail.py)
export TWITTER_PASSWORD=$(python3 scripts/twitter.py)

# pushd client
# RUST_LOG=info cargo run --release --bin encumber
# . temp.env
# export X_PASSWORD EMAIL_PASSWORD X_AUTH_TOKENS
# echo X_PASSWORD $X_PASSWORD
# echo EMAIL_PASSWORD $EMAIL_PASSWORD
# echo X_AUTH_TOKENS $X_AUTH_TOKENS
# popd

# The argument report_data accepts binary data encoding in hex string.
# The actual report_data passing the to the underlying TDX driver is sha2_256(report_data).

PAYLOAD="{\"report_data\": \"$(echo -n $TWITTER_ACCOUNT | od -A n -t x1 | tr -d ' \n')\"}"
curl -X POST --unix-socket /var/run/tappd.sock -d "$PAYLOAD" http://localhost/prpc/Tappd.TdxQuote?json | jq .

# Start the oauth client to receive the callback
pushd client
RUST_LOG=info cargo run --release --bin helper &
SERVER=$!
popd

# Do the twitter login
python3 scripts/tee.py
. cookies.env
export X_AUTH_TOKENS
wait $SERVER

# Start the time release server
bash timerelease.sh &

# Update the environment variables
. client/updated.env
export X_ACCESS_TOKEN X_ACCESS_TOKEN_SECRET

pushd client
RUST_LOG=info cargo run --release --bin helper &
popd

# Run the nous
pushd agent
python3 run_pipeline.py
popd
