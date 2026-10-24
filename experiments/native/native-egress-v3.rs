use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::Duration;

const PROBE_MARKER: &str = "ojp-egress-v3";

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let host = std::env::var("OJP_EGRESS_HOST").unwrap_or_else(|_| "host.docker.internal".into());
    let port = std::env::var("OJP_EGRESS_PORT").unwrap_or_else(|_| "15432".into());
    let address = format!("{host}:{port}");
    let mut stream = TcpStream::connect(&address)?;
    stream.set_read_timeout(Some(Duration::from_secs(5)))?;
    stream.write_all(format!(
        "GET /?probe={PROBE_MARKER} HTTP/1.0\r\nHost: {host}:{port}\r\nUser-Agent: ojp-runtime-probe/3\r\nConnection: close\r\n\r\n"
    ).as_bytes())?;
    let mut response = String::new();
    stream.read_to_string(&mut response)?;
    println!("endpoint={address} marker={PROBE_MARKER}");
    print!("{response}");
    Ok(())
}
