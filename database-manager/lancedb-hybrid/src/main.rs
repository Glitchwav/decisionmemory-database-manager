use std::env;
use std::fmt;
use std::io::{Read, Write};
use std::net::TcpStream;

// --- DOMAIN ONTOLOGY (Og Rule 1: No Stringly-Typed Logic) ---

#[derive(Debug, Clone)]
struct RecordId(String);

impl fmt::Display for RecordId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

pub enum Action {
    Ingest { id: RecordId, text: String, task: Option<String> },
    SemanticSearch { query: String },
    GraphWalk { id: RecordId },
}

pub struct HybridContext {
    pub vector_exact_text: String,
    pub graph_relationships: Vec<String>,
}

// --- SURREALDB NATIVE CLIENT ---

fn run_surreal_sql(host: &str, port: u16, sql: &str) -> Result<String, Box<dyn std::error::Error>> {
    let mut stream = TcpStream::connect((host, port))?;
    let body_len = sql.as_bytes().len();
    let ns = env::var("SURREAL_NS").unwrap_or_else(|_| "antigravity".to_string());
    let db = env::var("SURREAL_DB").unwrap_or_else(|_| "unified".to_string());
    let auth_header = match (env::var("SURREAL_USER"), env::var("SURREAL_PASS")) {
        (Ok(user), Ok(pass)) if !user.is_empty() && !pass.is_empty() => {
            format!("Authorization: Basic {}\r\n", base64_encode(&format!("{}:{}", user, pass)))
        }
        _ => String::new(),
    };

    let request = format!(
        "POST /sql HTTP/1.1\r\nHost: {}:{}\r\nAccept: application/json\r\nConnection: close\r\nsurreal-ns: {}\r\nsurreal-db: {}\r\n{}Content-Length: {}\r\n\r\n{}",
        host, port, ns, db, auth_header, body_len, sql
    );

    stream.write_all(request.as_bytes())?;
    let mut response = String::new();
    stream.read_to_string(&mut response)?;

    // Simplistic extraction for skeleton
    let body = if let Some(pos) = response.find("\r\n\r\n") {
        &response[pos + 4..]
    } else {
        &response
    };
    Ok(body.to_string())
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
        out.push(if i + 1 < bytes.len() {
            TABLE[(((b1 & 0b0000_1111) << 2) | (b2 >> 6)) as usize] as char
        } else {
            '='
        });
        out.push(if i + 2 < bytes.len() {
            TABLE[(b2 & 0b0011_1111) as usize] as char
        } else {
            '='
        });

        i += 3;
    }
    out
}

// --- LANCEDB COLD STORAGE ---

use std::sync::Arc;
use arrow::array::{FixedSizeListArray, Float32Array, StringArray, RecordBatch};
use arrow::datatypes::{DataType, Field, Schema};
use fastembed::{TextEmbedding, InitOptions, EmbeddingModel};

const LANCE_URI: &str = "data/lancedb";
const TABLE_NAME: &str = "vectors";

async fn ensure_db_table() -> Result<lancedb::Table, Box<dyn std::error::Error>> {
    let db = lancedb::connect(LANCE_URI).execute().await?;
    let tables = db.table_names().execute().await?;
    
    if tables.contains(&TABLE_NAME.to_string()) {
        Ok(db.open_table(TABLE_NAME).execute().await?)
    } else {
        // Define arrow schema for LanceDB
        let schema = Arc::new(Schema::new(vec![
            Field::new("id", DataType::Utf8, false),
            Field::new("text", DataType::Utf8, false),
            Field::new(
                "vector",
                DataType::FixedSizeList(Arc::new(Field::new("item", DataType::Float32, true)), 384),
                false,
            ),
        ]));
        
        // Create an empty batch to initialize the table
        let id_array = Arc::new(StringArray::from(Vec::<String>::new()));
        let text_array = Arc::new(StringArray::from(Vec::<String>::new()));
        let vector_data = Arc::new(Float32Array::from(Vec::<f32>::new()));
        
        let vector_field = Arc::new(Field::new("item", DataType::Float32, true));
        let vector_array = Arc::new(FixedSizeListArray::try_new(
            vector_field,
            384,
            vector_data,
            None,
        )?);
        
        let batch = RecordBatch::try_new(schema.clone(), vec![id_array, text_array, vector_array])?;
        use arrow::array::RecordBatchIterator;
        let iter = RecordBatchIterator::new(vec![Ok(batch)], schema);
        Ok(db.create_table(TABLE_NAME, iter).execute().await?)
    }
}

async fn ingest_to_cold_storage(id: &RecordId, text: &str) -> Result<(), Box<dyn std::error::Error>> {
    let table = ensure_db_table().await?;
    
    // 1. Local Daemonless Embedding (AllMiniLML6V2 = 384 dims)
    println!("   > generating offline local embeddings for {}...", id.0);
    let mut model = TextEmbedding::try_new(InitOptions::new(EmbeddingModel::AllMiniLML6V2))?;
    let embeddings = model.embed(vec![text], None)?;
    let vec_f32 = embeddings[0].clone();
    
    // 2. Build Arrow Arrays
    let id_array = Arc::new(StringArray::from(vec![id.0.clone()]));
    let text_array = Arc::new(StringArray::from(vec![text.to_string()]));
    let vector_data = Arc::new(Float32Array::from(vec_f32));
    
    let vector_field = Arc::new(Field::new("item", DataType::Float32, true));
    let vector_array = Arc::new(FixedSizeListArray::try_new(
        vector_field.clone(),
        384,
        vector_data,
        None,
    )?);
    
    let schema = Arc::new(Schema::new(vec![
        Field::new("id", DataType::Utf8, false),
        Field::new("text", DataType::Utf8, false),
        Field::new("vector", DataType::FixedSizeList(vector_field, 384), false),
    ]));
    
    // 3. Insert RecordBatch
    let batch = RecordBatch::try_new(schema.clone(), vec![id_array, text_array, vector_array])?;
    use arrow::array::RecordBatchIterator;
    let iter = RecordBatchIterator::new(vec![Ok(batch)], schema);
    table.add(iter).execute().await?;
    
    println!("   > LanceDB Cold Storage vector committed.");
    Ok(())
}

use lancedb::query::*;

async fn search_cold_storage(query: &str) -> Result<Vec<(RecordId, f32)>, Box<dyn std::error::Error>> {
    let table = ensure_db_table().await?;
    
    let mut model = TextEmbedding::try_new(InitOptions::new(EmbeddingModel::AllMiniLML6V2))?;
    let embeddings = model.embed(vec![query], None)?;
    let query_vec = embeddings[0].clone();
    
    let mut results = table
        .query()
        .nearest_to(query_vec)?
        .limit(5)
        .execute()
        .await?;
    
    let mut matching_ids = Vec::new();
    
    use futures::stream::StreamExt;
    while let Some(batch_res) = results.next().await {
        let batch: RecordBatch = batch_res?;
        let id_array: &StringArray = batch.column_by_name("id").unwrap().as_any().downcast_ref().unwrap();
        let dist_array: &Float32Array = batch.column_by_name("_distance").unwrap().as_any().downcast_ref().unwrap();
        
        for i in 0..batch.num_rows() {
            matching_ids.push((
                RecordId(id_array.value(i).to_string()),
                dist_array.value(i)
            ));
        }
    }
    
    Ok(matching_ids)
}

// --- ORCHESTRATION ---

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("lancedb-hybrid <ingest|search|walk> [args]");
        return Ok(());
    }

    let command = &args[1];

    match command.as_str() {
        "ingest" => {
            // e.g. ingest --id "doc_123" --text "Hello world"
            let id = RecordId("doc_123".to_string());
            let text = "Hello world";
            println!("1. Og: Validated RecordId({})", id);
            
            println!("2. Bu: Writing strict topology to SurrealDB...");
            let sql = format!("CREATE ocr_data:{} CONTENT {{ title: 'Placeholder' }};", id);
            let _ = run_surreal_sql("localhost", 8000, &sql);

            println!("3. Bu: Writing text/vectors to LanceDB Cold Storage...");
            ingest_to_cold_storage(&id, text).await?;
        }
        "search" => {
            let query = "How do lifetimes work?";
            println!("1. Semantic Search LanceDB for: {}", query);
            let matching_ids = search_cold_storage(query).await?;

            println!("2. Taking Top 1 ID and walking SurrealDB Graph...");
            if let Some(top_id) = matching_ids.get(0) {
                let sql = format!("SELECT <-belongs_to<-ocr_data FROM {};", top_id.0);
                let graph_context = run_surreal_sql("localhost", 8000, &sql)?;
                println!("Graph Context: {}", graph_context);
            }
        }
        _ => {
            println!("Unknown action");
        }
    }

    Ok(())
}
