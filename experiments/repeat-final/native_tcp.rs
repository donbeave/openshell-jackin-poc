use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::time::Duration;
use std::thread;

#[test]
fn executable_can_open_a_local_tcp_connection() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let address = listener.local_addr().unwrap();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let mut bytes = [0; 4];
        stream.read_exact(&mut bytes).unwrap();
        stream.write_all(b"pong").unwrap();
    });
    let mut client = TcpStream::connect(address).unwrap();
    client.write_all(b"ping").unwrap();
    let mut response = [0; 4];
    client.read_exact(&mut response).unwrap();
    server.join().unwrap();
    assert_eq!(&response, b"pong");
}

#[test]
fn executable_can_open_the_allowed_engine_service() {
    const MARKER: &str = "ojp-native-egress-v2";
    let host = std::env::var("OJP_EGRESS_HOST").unwrap_or_else(|_| "host.docker.internal".into());
    let port = std::env::var("OJP_EGRESS_PORT").unwrap_or_else(|_| "15433".into());
    let endpoint = format!("{host}:{port}");
    let mut stream = TcpStream::connect(&endpoint).expect("connect to allowed Docker child service");
    stream.set_read_timeout(Some(Duration::from_secs(5))).unwrap();
    write!(stream, "GET /index.html HTTP/1.0\r\nHost: {endpoint}\r\nX-OJP-Identity: {MARKER}\r\nConnection: close\r\n\r\n").unwrap();
    let mut response = String::new();
    stream.read_to_string(&mut response).unwrap();
    println!("native executable path={} endpoint={endpoint} marker={MARKER}", std::env::current_exe().unwrap().display());
    assert!(response.contains("200 OK"), "unexpected response: {response}");
    assert!(response.contains("repeat-source-v1"), "unexpected response: {response}");
}
