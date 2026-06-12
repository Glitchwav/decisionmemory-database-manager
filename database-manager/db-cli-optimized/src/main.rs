use std::env;
use std::io::{Read, Write};
use std::net::TcpStream;

fn print_usage(program: &str) {
    println!("Database Manager CLI for Antigravity SurrealDB (0-dependency)");
    println!("Usage:");
    println!("  {} [--url <URL>] COMMAND [ARGS]", program);
    println!();
    println!("Options:");
    println!("  --url <URL>         SurrealDB URL (default: SURREAL_HOST/SURREAL_PORT or http://localhost:8000)");
    println!("  SURREAL_NS          Namespace (default: antigravity)");
    println!("  SURREAL_DB          Database (default: unified)");
    println!("  SURREAL_USER/PASS   Optional Basic auth; omitted unless both are set");
    println!();
    println!("Commands:");
    println!("  init");
    println!("  insert-ocr   --id <ID> --content <CONTENT>");
    println!("  link         --doc <DOC> --task <TASK>");
    println!("  query-graph  --task <TASK>");
    println!("  search       --keyword <WORD> [--table memory|concept|ocr_data]");
    println!("  query        --sql <SURREAL_SQL>");
}

/// Decode HTTP/1.1 chunked transfer-encoding
fn decode_chunked(body: &str) -> String {
    let mut result = String::new();
    let mut remaining = body;
    loop {
        let Some(crlf) = remaining.find("\r\n") else { break };
        let size_str = remaining[..crlf].split(';').next().unwrap_or("0").trim();
        let chunk_size = usize::from_str_radix(size_str, 16).unwrap_or(0);
        if chunk_size == 0 { break; }
        let data_start = crlf + 2;
        let data_end = data_start + chunk_size;
        if data_end > remaining.len() { break; }
        result.push_str(&remaining[data_start..data_end]);
        remaining = &remaining[data_end..];
        if remaining.starts_with("\r\n") { remaining = &remaining[2..]; }
    }
    result
}

fn base64_encode(input: &str) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let bytes = input.as_bytes();
    let mut out = String::new();
    let mut i = 0;
    while i < bytes.len() {
        let b0 = bytes[i];
        let b1 = if i + 1 < bytes.len() { bytes[i + 1] } else { 0 };
        let b2 = if i + 2 < bytes.len() { bytes[i + 2] } else { 0 };

        out.push(TABLE[(b0 >> 2) as usize] as char);
        out.push(TABLE[(((b0 & 0b0000_0011) << 4) | (b1 >> 4)) as usize] as char);
        if i + 1 < bytes.len() {
            out.push(TABLE[(((b1 & 0b0000_1111) << 2) | (b2 >> 6)) as usize] as char);
        } else {
            out.push('=');
        }
        if i + 2 < bytes.len() {
            out.push(TABLE[(b2 & 0b0011_1111) as usize] as char);
        } else {
            out.push('=');
        }

        i += 3;
    }
    out
}

fn run_sql(host: &str, port: u16, ns: &str, db: &str, auth: Option<&str>, sql: &str) -> Result<String, Box<dyn std::error::Error>> {
    let mut stream = TcpStream::connect((host, port))?;
    let body_len = sql.as_bytes().len();
    let auth_header = auth
        .map(|value| format!("Authorization: Basic {}\r\n", value))
        .unwrap_or_default();

    let request = format!(
        "POST /sql HTTP/1.1\r\nHost: {}:{}\r\nAccept: application/json\r\nConnection: close\r\nsurreal-ns: {}\r\nsurreal-db: {}\r\n{}Content-Length: {}\r\n\r\n{}",
        host, port, ns, db, auth_header, body_len, sql
    );

    stream.write_all(request.as_bytes())?;
    let mut response = String::new();
    stream.read_to_string(&mut response)?;

    let body = if let Some(pos) = response.find("\r\n\r\n") {
        &response[pos + 4..]
    } else {
        &response
    };

    let is_chunked = response
        .lines()
        .take_while(|l| !l.is_empty())
        .any(|l| l.to_lowercase().contains("transfer-encoding: chunked"));

    let clean = if is_chunked { decode_chunked(body) } else { body.to_string() };
    Ok(clean.trim().to_string())
}

fn parse_url(url: &str) -> (&str, u16) {
    let url = url.trim_start_matches("http://").trim_start_matches("https://");
    let host_port = url.splitn(2, '/').next().unwrap_or("localhost:8000");
    let mut hp = host_port.splitn(2, ':');
    let host = hp.next().unwrap_or("localhost");
    let port: u16 = hp.next().unwrap_or("8000").parse().unwrap_or(8000);
    (host, port)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let program = &args[0];

    if args.len() < 2 { print_usage(program); return; }

    let env_host = env::var("SURREAL_HOST").unwrap_or_else(|_| "localhost".to_string());
    let env_port = env::var("SURREAL_PORT").unwrap_or_else(|_| "8000".to_string());
    let mut url = format!("http://{}:{}", env_host, env_port);
    let mut command_idx = 1;

    let mut i = 1;
    while i < args.len() {
        if args[i] == "--url" && i + 1 < args.len() {
            url = args[i + 1].clone(); i += 2;
        } else if !args[i].starts_with('-') {
            command_idx = i; break;
        } else {
            i += 1;
        }
    }

    if command_idx >= args.len() { print_usage(program); return; }

    let command = args[command_idx].clone();
    let (host, port) = parse_url(&url);
    let ns = env::var("SURREAL_NS").unwrap_or_else(|_| "antigravity".to_string());
    let db = env::var("SURREAL_DB").unwrap_or_else(|_| "unified".to_string());
    let auth = match (env::var("SURREAL_USER"), env::var("SURREAL_PASS")) {
        (Ok(user), Ok(pass)) if !user.is_empty() && !pass.is_empty() => {
            Some(base64_encode(&format!("{}:{}", user, pass)))
        }
        _ => None,
    };

    // Collect remaining args after command
    let rest = &args[command_idx + 1..];

    fn get_flag<'a>(rest: &'a [String], flag: &str) -> Option<&'a str> {
        rest.windows(2)
            .find(|w| w[0] == flag)
            .map(|w| w[1].as_str())
    }

    match command.as_str() {
        "init" => {
            println!("Initializing schema...");
            let sql = "DEFINE TABLE ocr_data SCHEMAFULL; \
                       DEFINE FIELD content ON ocr_data TYPE string; \
                       DEFINE FIELD recorded_at ON ocr_data TYPE datetime DEFAULT time::now(); \
                       DEFINE TABLE belongs_to TYPE RELATION IN ocr_data OUT task SCHEMAFULL; \
                       DEFINE FIELD relationship ON belongs_to TYPE string DEFAULT 'belongs_to'; \
                       DEFINE TABLE task SCHEMAFULL; \
                       DEFINE FIELD name ON task TYPE string;";
            match run_sql(host, port, &ns, &db, auth.as_deref(), sql) {
                Ok(_) => println!("✅ Schema successfully initialized."),
                Err(e) => eprintln!("Error: {}", e),
            }
        }
        "insert-ocr" => {
            let id = get_flag(rest, "--id").unwrap_or("").to_string();
            let content = get_flag(rest, "--content").unwrap_or("").to_string();
            if id.is_empty() || content.is_empty() {
                eprintln!("Usage: {} insert-ocr --id <ID> --content <CONTENT>", program); return;
            }
            println!("Inserting OCR data (id: {})...", id);
            let content_safe = content.replace('\'', "\\'");
            let sql = format!("CREATE ocr_data:{} CONTENT {{ content: '{}' }};", id, content_safe);
            match run_sql(host, port, &ns, &db, auth.as_deref(), &sql) {
                Ok(res) => { println!("{}", res); println!("✅ OCR data inserted."); }
                Err(e) => eprintln!("Error: {}", e),
            }
        }
        "link" => {
            let doc = get_flag(rest, "--doc").unwrap_or("").to_string();
            let task = get_flag(rest, "--task").unwrap_or("").to_string();
            if doc.is_empty() || task.is_empty() {
                eprintln!("Usage: {} link --doc <DOC> --task <TASK>", program); return;
            }
            println!("Linking doc {} to task {}...", doc, task);
            let sql = format!(
                "CREATE task:{task} SET name = '{task}'; RELATE ocr_data:{doc}->belongs_to->task:{task} SET relationship = 'belongs_to';"
            );
            match run_sql(host, port, &ns, &db, auth.as_deref(), &sql) {
                Ok(res) => { println!("{}", res); println!("✅ Link created."); }
                Err(e) => eprintln!("Error: {}", e),
            }
        }
        "query-graph" => {
            let task = get_flag(rest, "--task").unwrap_or("");
            if task.is_empty() {
                eprintln!("Usage: {} query-graph --task <TASK>", program); return;
            }
            let sql = format!("SELECT <-belongs_to<-ocr_data.* AS documents FROM task:{};", task);
            match run_sql(host, port, &ns, &db, auth.as_deref(), &sql) {
                Ok(res) => println!("{}", res),
                Err(e) => eprintln!("Error: {}", e),
            }
        }
        "search" => {
            let keyword = get_flag(rest, "--keyword").unwrap_or("");
            let table = get_flag(rest, "--table").unwrap_or("memory");
            if keyword.is_empty() {
                eprintln!("Usage: {} search --keyword <WORD> [--table memory|concept|ocr_data]", program); return;
            }
            println!("Searching '{}' in table '{}'...", keyword, table);
            // Use string-contains search for broad compatibility
            let sql = match table {
                "memory" => format!(
                    "SELECT id, title, tags, path FROM memory WHERE string::lowercase(title) CONTAINS string::lowercase('{}') OR tags CONTAINS '{}' LIMIT 20;",
                    keyword, keyword.to_lowercase()
                ),
                "concept" => format!(
                    "SELECT id, name, definition FROM concept WHERE string::lowercase(name) CONTAINS string::lowercase('{}') OR string::lowercase(definition) CONTAINS string::lowercase('{}') LIMIT 20;",
                    keyword, keyword
                ),
                _ => format!(
                    "SELECT * FROM {} WHERE string::lowercase(content) CONTAINS string::lowercase('{}') LIMIT 20;",
                    table, keyword
                ),
            };
            match run_sql(host, port, &ns, &db, auth.as_deref(), &sql) {
                Ok(res) => println!("{}", res),
                Err(e) => eprintln!("Error: {}", e),
            }
        }
        "query" => {
            let sql = get_flag(rest, "--sql").unwrap_or("");
            if sql.is_empty() {
                eprintln!("Usage: {} query --sql \"SELECT * FROM memory LIMIT 5;\"", program); return;
            }
            match run_sql(host, port, &ns, &db, auth.as_deref(), sql) {
                Ok(res) => println!("{}", res),
                Err(e) => eprintln!("Error: {}", e),
            }
        }
        _ => {
            println!("Unknown command: {}", command);
            print_usage(program);
        }
    }
}
