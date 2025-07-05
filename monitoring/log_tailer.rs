/**
 * Usage Example:
 *     # Basic usage
 *     logmon /var/log/syslog
 *
 *     # Follow mode with color
 *     logmon -f /var/log/nginx/access.log
 *
 *     # Multiple files with glob pattern
 *     logmon /var/log/*.log
 *
 *     # Filter errors from Apache logs
 *     logmon /var/log/apache2/error.log --level error
 *
 *     # Follow and filter process with regex message
 *     logmon -f /var/log/syslog --process kernel --message "oom|out of memory"
 *
 *     # Show last 100 lines without color
 *     logmon -n 100 --no-color /var/log/large.log
 */*/

use std::{
    env, fs,
    fs::File,
    io::{self, BufRead, BufReader, Seek, SeekFrom},
    path::Path,
    process,
    sync::atomic::{AtomicBool, Ordering},
    sync::Arc,
    thread,
    time::{Duration, Instant},
};
use chrono::Utc;
use clap::{Arg, Command};
use crossterm::{
    style::{Color, Print, ResetColor, SetForegroundColor, Stylize},
    ExecutableCommand,
};
use regex::Regex;
use syslog_loose::{parse_message, ProcId, Protocol};

/// Log entry structure for parsed log messages
#[derive(Debug)]
struct LogEntry {
    timestamp: String,
    hostname: Option<String>,
    process: String,
    pid: Option<ProcId>,
    level: String,
    message: String,
}

/// Application configuration
struct Config {
    log_files: Vec<String>,
    follow: bool,
    filter_level: Option<String>,
    filter_process: Option<String>,
    filter_message: Option<String>,
    color_output: bool,
    tail_lines: Option<usize>,
    poll_interval: u64,
}

fn main() -> io::Result<()> {
    let matches = Command::new("logmon")
        .version("1.0.0")
        .author("Your Name <your.email@example.com>")
        .about("Professional Log Monitoring Tool")
        .arg(
            Arg::new("files")
                .help("Log files to monitor (supports glob patterns)")
                .required(true)
                .num_args(1..)
                .value_name("FILE(S)"),
        )
        .arg(
            Arg::new("follow")
                .short('f')
                .long("follow")
                .help("Tail log files (similar to tail -f)")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("level")
                .short('l')
                .long("level")
                .help("Filter by log level (e.g., error, warn, info)")
                .value_name("LEVEL"),
        )
        .arg(
            Arg::new("process")
                .short('p')
                .long("process")
                .help("Filter by process name")
                .value_name("PROCESS"),
        )
        .arg(
            Arg::new("message")
                .short('m')
                .long("message")
                .help("Filter by message pattern (supports regex)")
                .value_name("PATTERN"),
        )
        .arg(
            Arg::new("no-color")
                .long("no-color")
                .help("Disable colored output")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("tail")
                .short('n')
                .long("lines")
                .help("Number of lines to display at start")
                .value_name("NUM")
                .value_parser(clap::value_parser!(usize)),
        )
        .arg(
            Arg::new("poll-interval")
                .long("poll-interval")
                .help("File poll interval in milliseconds")
                .value_name("MS")
                .default_value("500")
                .value_parser(clap::value_parser!(u64)),
        )
        .get_matches();

    // Parse configuration
    let config = Config {
        log_files: expand_globs(matches.get_many::<String>("files").unwrap().map(|s| s.to_string())),
        follow: matches.get_flag("follow"),
        filter_level: matches.get_one::<String>("level").map(|s| s.to_lowercase()),
        filter_process: matches.get_one::<String>("process").cloned(),
        filter_message: matches.get_one::<String>("message").cloned(),
        color_output: !matches.get_flag("no-color"),
        tail_lines: matches.get_one::<usize>("tail").copied(),
        poll_interval: *matches.get_one::<u64>("poll-interval").unwrap_or(&500),
    };

    // Handle SIGINT for graceful shutdown
    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();
    ctrlc::set_handler(move || {
        r.store(false, Ordering::SeqCst);
    })
    .expect("Error setting Ctrl-C handler");

    // Process each log file
    for file_path in &config.log_files {
        if !Path::new(file_path).exists() {
            eprintln!("Warning: Log file {} does not exist", file_path);
            continue;
        }

        let config_clone = config.clone();
        let file_path_clone = file_path.clone();
        thread::spawn(move || {
            if let Err(e) = process_log_file(&file_path_clone, &config_clone, running.clone()) {
                eprintln!("Error processing {}: {}", file_path_clone, e);
            }
        });
    }

    // Keep main thread alive while child threads are running
    while running.load(Ordering::SeqCst) {
        thread::sleep(Duration::from_millis(100));
    }

    Ok(())
}

/// Expand glob patterns to file paths
fn expand_globs<I>(patterns: I) -> Vec<String>
where
    I: IntoIterator<Item = String>,
{
    let mut files = Vec::new();
    for pattern in patterns {
        match glob::glob(&pattern) {
            Ok(paths) => {
                for path in paths.filter_map(Result::ok) {
                    if let Some(path_str) = path.to_str() {
                        files.push(path_str.to_string());
                    }
                }
            }
            Err(e) => eprintln!("Invalid glob pattern '{}': {}", pattern, e),
        }
    }
    files
}

/// Process a single log file
fn process_log_file(
    path: &str,
    config: &Config,
    running: Arc<AtomicBool>,
) -> io::Result<()> {
    let mut file = File::open(path)?;
    let mut reader = BufReader::new(&file);
    let mut line = String::new();
    let mut last_pos = 0;

    // Display file header
    print_file_header(path, config.color_output);

    // Handle tail option
    if let Some(n) = config.tail_lines {
        let total_lines = count_lines(&file)?;
        let start_line = if total_lines > n { total_lines - n } else { 0 };
        file.seek(SeekFrom::Start(0))?;
        reader = BufReader::new(&file);

        for _ in 0..start_line {
            reader.read_line(&mut String::new())?;
        }
        last_pos = reader.stream_position()?;
    } else if config.follow {
        // Seek to end for follow mode
        last_pos = file.seek(SeekFrom::End(0))?;
    }

    // Main processing loop
    while running.load(Ordering::SeqCst) {
        let bytes_read = reader.read_line(&mut line)?;
        
        if bytes_read > 0 {
            if let Some(entry) = parse_log_line(&line) {
                if should_display(&entry, config) {
                    print_log_entry(&entry, config.color_output);
                }
            } else {
                print_unknown_line(&line, config.color_output);
            }
            
            line.clear();
            last_pos = reader.stream_position()?;
        } else {
            if !config.follow {
                break;
            }
            
            // Check for file rotation
            let metadata = fs::metadata(path)?;
            if metadata.len() < last_pos {
                // File was rotated or truncated
                file = File::open(path)?;
                reader = BufReader::new(&file);
                last_pos = 0;
                print_file_header(path, config.color_output);
            }
            
            thread::sleep(Duration::from_millis(config.poll_interval));
        }
    }

    Ok(())
}

/// Parse a log line into structured data
fn parse_log_line(line: &str) -> Option<LogEntry> {
    // Try syslog format first
    if let Some((header, message)) = line.split_once(' ') {
        if let Some(parsed) = parse_message(header, Protocol::RFC3164) {
            return Some(LogEntry {
                timestamp: parsed.timestamp.to_rfc3339(),
                hostname: parsed.hostname,
                process: parsed.appname.unwrap_or_else(|| "unknown".to_string()),
                pid: parsed.procid,
                level: parsed.severity.as_str().to_string(),
                message: message.trim().to_string(),
            });
        }
    }

    // Try common log formats
    let re = Regex::new(r"^(\S+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s+(.*)$").ok()?;
    let caps = re.captures(line)?;

    Some(LogEntry {
        timestamp: caps.get(1)?.as_str().to_string(),
        hostname: None,
        process: caps.get(3)?.as_str().to_string(),
        pid: caps.get(4).and_then(|m| m.as_str().parse().ok()),
        level: caps.get(2)?.as_str().to_string(),
        message: caps.get(5)?.as_str().to_string(),
    })
}

/// Determine if an entry should be displayed based on filters
fn should_display(entry: &LogEntry, config: &Config) -> bool {
    // Level filter
    if let Some(level) = &config.filter_level {
        if !entry.level.to_lowercase().contains(&level.to_lowercase()) {
            return false;
        }
    }

    // Process filter
    if let Some(process) = &config.filter_process {
        if !entry.process.to_lowercase().contains(&process.to_lowercase()) {
            return false;
        }
    }

    // Message filter
    if let Some(pattern) = &config.filter_message {
        if let Ok(re) = Regex::new(&pattern.to_lowercase()) {
            if !re.is_match(&entry.message.to_lowercase()) {
                return false;
            }
        }
    }

    true
}

/// Print file header with colored border
fn print_file_header(path: &str, color: bool) {
    let header = format!("──┤ {} ├──", path);
    let border = "─".repeat(header.len());
    
    let mut stdout = io::stdout();
    if color {
        stdout.execute(SetForegroundColor(Color::DarkMagenta)).ok();
    }
    println!("┌{}┐", border);
    println!("│{}│", header);
    println!("└{}┘", border);
    if color {
        stdout.execute(ResetColor).ok();
    }
}

/// Print a log entry with appropriate coloring
fn print_log_entry(entry: &LogEntry, color: bool) {
    let mut stdout = io::stdout();
    let pid_display = entry.pid.map_or_else(String::new, |pid| format!("[{}]", pid));
    
    // Set color based on log level
    if color {
        let color = match entry.level.to_lowercase().as_str() {
            "error" | "emerg" | "alert" | "crit" => Color::Red,
            "warn" | "warning" => Color::Yellow,
            "info" | "notice" => Color::Green,
            "debug" => Color::Blue,
            _ => Color::Cyan,
        };
        stdout.execute(SetForegroundColor(color)).ok();
    }

    // Print structured log information
    print!(
        "[{}] {}{}: ",
        entry.timestamp,
        entry.process,
        pid_display
    );
    
    // Print message (with different color if enabled)
    if color {
        stdout.execute(SetForegroundColor(Color::White)).ok();
    }
    println!("{}", entry.message);
    
    if color {
        stdout.execute(ResetColor).ok();
    }
}

/// Print unparsed lines
fn print_unknown_line(line: &str, color: bool) {
    let mut stdout = io::stdout();
    if color {
        stdout.execute(SetForegroundColor(Color::DarkGrey)).ok();
    }
    println!("{}", line.trim());
    if color {
        stdout.execute(ResetColor).ok();
    }
}

/// Count lines in a file efficiently
fn count_lines(file: &File) -> io::Result<usize> {
    let mut reader = BufReader::new(file);
    let mut count = 0;
    let mut buf = [0; 1024 * 64];
    
    loop {
        let bytes = reader.read(&mut buf)?;
        if bytes == 0 {
            break;
        }
        count += buf[..bytes].iter().filter(|&&b| b == b'\n').count();
    }
    
    file.seek(SeekFrom::Start(0))?;
    Ok(count)
}
