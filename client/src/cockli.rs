use eyre::OptionExt;
use reqwest::{Client, ClientBuilder};
use scraper::{Html, Selector};
use serde_json::json;

use crate::utils;

pub async fn encumber_email(email: &str, password: &str) -> eyre::Result<String> {
    let client = ClientBuilder::new().cookie_store(true).build()?;
    let login_token = get_token(&client, "https://cock.li/login").await?;
    login(&client, email, password, &login_token).await?;
    let change_password_token = get_token(&client, "https://cock.li/user/changepass").await?;
    let new_password = utils::get_random_password();
    change_password(&client, password, &new_password, &change_password_token).await?;
    Ok(new_password)
}

async fn change_password(
    client: &Client,
    current_password: &str,
    new_password: &str,
    token: &str,
) -> eyre::Result<()> {
    let form = json!({
        "_token": token,
        "current_password": current_password,
        "password": new_password,
        "password_confirmation": new_password,
    });

    let response = client
        .post("https://cock.li/user/changepass")
        .form(&form)
        .send()
        .await?;

    response.error_for_status()?;
    Ok(())
}

async fn login(client: &Client, email: &str, password: &str, token: &str) -> eyre::Result<()> {
    let form = json!({
        "_token": token,
        "email": email,
        "password": password,
    });

    let response = client
        .post("https://cock.li/login")
        .form(&form)
        .send()
        .await?;

    response.error_for_status()?;
    Ok(())
}

async fn get_token(client: &Client, url: &str) -> eyre::Result<String> {
    let response = client.get(url).send().await?;

    let html_content = response.text().await?;

    let document = Html::parse_document(&html_content);

    let selector = Selector::parse("input[type='hidden'][name='_token']")
        .map_err(|err| eyre::eyre!("{}", err))?;

    let token = document
        .select(&selector)
        .next()
        .ok_or_eyre("Could not find token")?
        .value()
        .attr("value")
        .ok_or_eyre("Could not find token value")?
        .to_string();

    Ok(token)
}
