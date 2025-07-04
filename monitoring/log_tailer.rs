use std::{fs::File, io::{BufRead, BufReader}, thread::sleep, time::Duration};

fn main() {
    let file = File::open("/var/log/syslog").expect("Log file not found");
    let mut reader = BufReader::new(file);
    let mut line = String::new();

    loop {
        let bytes = reader.read_line(&mut line).unwrap();
        if bytes == 0 {
            sleep(Duration::from_millis(500));
        } else {
            print!("{}", line);
            line.clear();
        }
    }
}
