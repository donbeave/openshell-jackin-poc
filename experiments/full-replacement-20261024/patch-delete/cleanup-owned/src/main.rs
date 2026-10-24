use std::{env, fs, time::Duration};

use openshell_sdk::{EdgeAuthInterceptor, OpenShellClient, raw::proto};
use tonic::{transport::{Certificate, ClientTlsConfig, Endpoint, Identity}};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let endpoint = env::var("PDEL_ENDPOINT")?;
    let ca = fs::read(env::var("PDEL_CA")?)?;
    let cert = fs::read(env::var("PDEL_CLIENT_CERT")?)?;
    let key = fs::read(env::var("PDEL_CLIENT_KEY")?)?;
    let tls = ClientTlsConfig::new()
        .ca_certificate(Certificate::from_pem(ca))
        .domain_name("localhost")
        .identity(Identity::from_pem(cert, key));
    let channel = Endpoint::from_shared(endpoint)?
        .tls_config(tls)?
        .connect()
        .await?;
    let client = OpenShellClient::from_parts(channel, EdgeAuthInterceptor::noop());
    let mut grpc = client.raw_grpc();
    for (name, id) in env::args().skip(1).map(|value| {
        let (name, id) = value.split_once('=')?;
        Some((name.to_owned(), id.to_owned()))
    }).collect::<Option<Vec<_>>>().ok_or("expected name=id arguments")? {
        let response = grpc.delete_sandbox(proto::DeleteSandboxRequest {
            workspace_scope: Some(proto::workspace_selector("default")),
            request_id: uuid::Uuid::new_v4().to_string(),
            sandbox_id: id.clone(),
            ..Default::default()
        }).await?.into_inner();
        if response.sandbox_id != id {
            return Err(format!("delete returned {} instead of recorded {id}", response.sandbox_id).into());
        }
        client.wait_deleted(&name, Duration::from_secs(60), Some(&id)).await?;
        println!("deleted_owned_sandbox_id={id} name={name}");
    }
    Ok(())
}
