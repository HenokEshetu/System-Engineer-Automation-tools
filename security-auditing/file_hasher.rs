/*

Hash files recursively in a directory using various algorithms.
    cargo run --release -- hash -p ./testdata -a sha256

Verify files against a checksum file.
    checksums.txt:
    <hash> <file_path>
    cargo run --release -- verify -c checksums.txt -a sha256

*/

use std::{
    fs::File,
    io::{BufReader, Read},
    path::{Path, PathBuf},
};

use blake2::{Blake2b512, Blake2s256, Digest as BlakeDigest};
use clap::{Parser, Subcommand, ValueEnum};
use md5::{Digest as Md5Digest, Md5};
use rayon::prelude::*;
use sha2::{Digest as ShaDigest, Sha256, Sha512};
use walkdir::WalkDir;

#[derive(Parser)]
#[command(name = "Hasher", version, author, about = "Recursive & Parallel File Hasher & Verifier")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Recursively hash all files in a directory
    Hash {
        /// Path to a file or directory
        #[arg(short, long)]
        path: PathBuf,

        /// Hash algorithm
        #[arg(short, long, value_enum, default_value = "sha256")]
        algorithm: Algorithm,
    },

    /// Verify files using a checksum file
    Verify {
        /// Path to checksum file (format: <hash> <filepath>)
        #[arg(short, long)]
        checksum_file: PathBuf,

        /// Algorithm used in the checksum file
        #[arg(short, long, value_enum, default_value = "sha256")]
        algorithm: Algorithm,
    },
}

#[derive(Clone, ValueEnum)]
enum Algorithm {
    Sha256,
    Sha512,
    Md5,
    Blake2s,
    Blake2b,
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Hash { path, algorithm } => {
            let files = collect_files(&path);
            println!("Found {} files. Hashing...", files.len());

            files.par_iter().for_each(|file_path| {
                match hash_file(file_path, &algorithm) {
                    Ok(hash) => println!("{}  {}", hash, file_path.display()),
                    Err(e) => eprintln!("[Error] {}: {}", file_path.display(), e),
                }
            });
        }

        Commands::Verify {
            checksum_file,
            algorithm,
        } => {
            match verify_checksums(&checksum_file, &algorithm) {
                Ok(_) => println!("[Success] Verification complete."),
                Err(e) => eprintln!("[Error] {}", e),
            }
        }
    }
}

fn collect_files(path: &Path) -> Vec<PathBuf> {
    if path.is_file() {
        vec![path.to_path_buf()]
    } else {
        WalkDir::new(path)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .map(|e| e.path().to_path_buf())
            .collect()
    }
}

fn hash_file(path: &Path, algorithm: &Algorithm) -> Result<String, String> {
    let file = File::open(path).map_err(|e| e.to_string())?;
    let mut reader = BufReader::new(file);
    let mut buffer = [0u8; 8192];

    match algorithm {
        Algorithm::Sha256 => {
            let mut hasher = Sha256::new();
            while let Ok(bytes_read) = reader.read(&mut buffer) {
                if bytes_read == 0 {
                    break;
                }
                hasher.update(&buffer[..bytes_read]);
            }
            Ok(format!("{:x}", hasher.finalize()))
        }
        Algorithm::Sha512 => {
            let mut hasher = Sha512::new();
            while let Ok(bytes_read) = reader.read(&mut buffer) {
                if bytes_read == 0 {
                    break;
                }
                hasher.update(&buffer[..bytes_read]);
            }
            Ok(format!("{:x}", hasher.finalize()))
        }
        Algorithm::Md5 => {
            let mut hasher = Md5::new();
            while let Ok(bytes_read) = reader.read(&mut buffer) {
                if bytes_read == 0 {
                    break;
                }
                hasher.update(&buffer[..bytes_read]);
            }
            Ok(format!("{:x}", hasher.finalize()))
        }
        Algorithm::Blake2s => {
            let mut hasher = Blake2s256::new();
            while let Ok(bytes_read) = reader.read(&mut buffer) {
                if bytes_read == 0 {
                    break;
                }
                hasher.update(&buffer[..bytes_read]);
            }
            Ok(format!("{:x}", hasher.finalize()))
        }
        Algorithm::Blake2b => {
            let mut hasher = Blake2b512::new();
            while let Ok(bytes_read) = reader.read(&mut buffer) {
                if bytes_read == 0 {
                    break;
                }
                hasher.update(&buffer[..bytes_read]);
            }
            Ok(format!("{:x}", hasher.finalize()))
        }
    }
}

fn verify_checksums(
    checksum_file: &PathBuf,
    algorithm: &Algorithm,
) -> Result<(), Box<dyn std::error::Error>> {
    let file = File::open(checksum_file)?;
    let reader = BufReader::new(file);

    for line in reader.lines() {
        let line = line?;
        let mut parts = line.split_whitespace();
        let expected_hash = parts.next().ok_or("Missing hash")?;
        let file_path = parts.next().ok_or("Missing file path")?;
        let file_path = Path::new(file_path);

        match hash_file(file_path, algorithm) {
            Ok(computed_hash) => {
                if computed_hash != expected_hash {
                    eprintln!("[FAIL] {}: expected {}, got {}", file_path.display(), expected_hash, computed_hash);
                } else {
                    println!("[OK]   {}", file_path.display());
                }
            }
            Err(e) => {
                eprintln!("[Error] {}: {}", file_path.display(), e);
            }
        }
    }

    Ok(())
}
