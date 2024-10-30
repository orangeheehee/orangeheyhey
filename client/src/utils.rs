use rand::{distributions::Alphanumeric, Rng};

pub fn get_random_password() -> String {
    let new_password: String = rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(12)
        .map(char::from)
        .collect();
    new_password
}
