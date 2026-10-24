use redis::AsyncCommands;
use testcontainers::{runners::AsyncRunner, GenericImage, core::{IntoContainerPort, WaitFor}};
use std::time::Duration;

#[tokio::test]
async fn testcontainers_starts_redis_and_exchanges_data() {
    let container = GenericImage::new("redis", "7.4-alpine")
        .with_exposed_port(6379_u16.tcp())
        .with_wait_for(WaitFor::message_on_stdout("Ready to accept connections"))
        .start()
        .await
        .expect("start Redis container");
    let host = container.get_host().await.expect("Docker host");
    let port = container.get_host_port_ipv4(6379).await.expect("mapped port");
    let endpoint = format!("{host}:{port}");
    println!("Docker reported host={host} port={port}; test endpoint={endpoint}");
    let client = redis::Client::open(format!("redis://{endpoint}/")).unwrap();
    let mut connection = client.get_multiplexed_async_connection().await.unwrap();
    let _: () = connection.set("ojp-probe", "round-trip").await.unwrap();
    let value: String = connection.get("ojp-probe").await.unwrap();
    assert_eq!(value, "round-trip");
    drop(connection);
    drop(client);
    if std::env::var_os("OJP_TEST_FAILURE").is_some() {
        panic!("intentional Testcontainers cleanup probe failure");
    }
    if std::env::var_os("OJP_HOLD").is_some() {
        tokio::time::sleep(Duration::from_secs(600)).await;
    }
}
