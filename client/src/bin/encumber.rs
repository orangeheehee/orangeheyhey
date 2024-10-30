use std::{fs::File, io::Write};

use client::{cockli::encumber_email, utils::get_random_password};
use dotenv::dotenv;
use x_rs::account::{login, Account};

#[tokio::main]
async fn main() {
    env_logger::init();
    //dotenv().ok();

    let username = std::env::var("X_USERNAME").unwrap();
    let password = std::env::var("X_PASSWORD").unwrap();
    let email = std::env::var("EMAIL").unwrap();
    let email_password = std::env::var("EMAIL_PASSWORD").unwrap();
    let totp = std::env::var("X_TOTP").ok();
    log::info!("x_username: {}", username);
    log::info!("x_password: {}", password);

    let mut login =
        login::Login::new(username, password.clone(), email.clone(), totp, None).unwrap();
    let auth = login.login().await.unwrap();

    let mut account = Account::from_auth(auth).unwrap();
    let new_password = get_random_password();
    account
        .change_password(&password, &new_password)
        .await
        .unwrap();
    log::info!("X password changed to: {}", new_password);
    account.refresh_cookies().await.unwrap();

    let oauth_applications = account.get_all_oauth_applications().await.unwrap();
    let filtered_applications: Vec<_> = oauth_applications
        .into_iter()
        .filter(|app| app.app_id != "29459355")
        .collect();
    for application in filtered_applications.iter() {
        account
            .revoke_oauth_application(&application.token)
            .await
            .unwrap();
    }
    let phone_email_info = account.get_email_phone_info().await.unwrap();
    assert!(phone_email_info.emails.len() == 1);
    assert!(phone_email_info.emails[0].email == email);
    assert!(phone_email_info.phone_numbers.is_empty());

    let new_email_password = encumber_email(&email, &email_password).await.unwrap();
    log::info!("Email password changed to: {}", new_email_password);

    let file_path = "temp.env";
    let mut file = File::create(file_path).expect("Failed to create file");
    writeln!(file, "X_PASSWORD={}", new_password).expect("Failed to write Twitter password");
    writeln!(file, "EMAIL_PASSWORD={}", new_email_password)
        .expect("Failed to write email password");

    let account_cookies = account.auth_cookie_string();
    let account_cookies_json =
        serde_json::to_string(&account_cookies).expect("Failed to serialize account cookies");
    writeln!(file, "X_AUTH_TOKENS={}", account_cookies_json)
        .expect("Failed to write account cookies");

    log::info!("Passwords saved to {}", file_path);
}
