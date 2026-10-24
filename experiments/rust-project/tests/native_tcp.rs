use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
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
