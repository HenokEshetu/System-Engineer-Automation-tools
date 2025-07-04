use std::fs::File;
use std::io::{BufReader, Read};
use sha2::{Sha256, Digest};

fn main() {
    let path = "example.txt";
    let file = File::open(path).expect("Unable to open file");
    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 1024];

    while let Ok(bytes_read) = reader.read(&mut buffer) {
        if bytes_read == 0 { break; }
        hasher.update(&buffer[..bytes_read]);
    }

    let result = hasher.finalize();
    println!("SHA256 for {}: {:x}", path, result);
}
