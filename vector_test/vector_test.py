# Standard Libraries
import json
import os
import csv
import shutil
from itertools import islice
import concurrent.futures
import yaml

# Third-Party Libraries
import pandas as pd
import numpy as np
from PyPDF2 import PdfReader
import tiktoken
from dotenv import load_dotenv
import pyperclip

# OpenAI Libraries
from openai import OpenAI

# Google Cloud Identity and Credentials
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import functions_v1
from google.api_core.exceptions import Conflict

# Saving this as a variable to reference in function app in later step
openai_api_key = json.load(
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "openai.json"))
)["key"]
openai_client = OpenAI(api_key=openai_api_key)
embeddings_model = "text-embedding-3-small"  # We'll use this by default, but you can change to your text-embedding-3-large if desired

# Use default credentials
credentials = service_account.Credentials.from_service_account_file(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "google.json")
)
project_id = "cse-144-project"
region = "us-central1"  # e.g: "us-central1"


def batched(iterable, n):
    """Batch data into tuples of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def chunked_tokens(text, chunk_length, encoding_name="cl100k_base"):
    # Get the encoding object for the specified encoding name. OpenAI's tiktoken library, which is used in this notebook, currently supports two encodings: 'bpe' and 'cl100k_base'. The 'bpe' encoding is used for GPT-3 and earlier models, while 'cl100k_base' is used for newer models like GPT-4.
    encoding = tiktoken.get_encoding(encoding_name)
    # Encode the input text into tokens
    tokens = encoding.encode(text)
    # Create an iterator that yields chunks of tokens of the specified length
    chunks_iterator = batched(tokens, chunk_length)
    # Yield each chunk from the iterator
    yield from chunks_iterator


EMBEDDING_CTX_LENGTH = 8191
EMBEDDING_ENCODING = "cl100k_base"


def generate_embeddings(text, model):
    # Generate embeddings for the provided text using the specified model
    embeddings_response = openai_client.embeddings.create(model=model, input=text)
    # Extract the embedding data from the response
    embedding = embeddings_response.data[0].embedding
    return embedding


def len_safe_get_embedding(
    text,
    model=embeddings_model,
    max_tokens=EMBEDDING_CTX_LENGTH,
    encoding_name=EMBEDDING_ENCODING,
):
    # Initialize lists to store embeddings and corresponding text chunks
    chunk_embeddings = []
    chunk_texts = []
    # Iterate over chunks of tokens from the input text
    for chunk in chunked_tokens(
        text, chunk_length=max_tokens, encoding_name=encoding_name
    ):
        # Generate embeddings for each chunk and append to the list
        chunk_embeddings.append(generate_embeddings(chunk, model=model))
        # Decode the chunk back to text and append to the list
        chunk_texts.append(tiktoken.get_encoding(encoding_name).decode(chunk))
    # Return the list of chunk embeddings and the corresponding text chunks
    return chunk_embeddings, chunk_texts


categories = [
    "authentication",
    "models",
    "techniques",
    "tools",
    "setup",
    "billing_limits",
    "other",
]


def categorize_text(text, categories):

    # Create a prompt for categorization
    messages = [
        {
            "role": "system",
            "content": f"""You are an expert in LLMs, and you will be given text that corresponds to an article in OpenAI's documentation.
         Categorize the document into one of these categories: {', '.join(categories)}. Only respond with the category name and nothing else.""",
        },
        {"role": "user", "content": text},
    ]
    try:
        # Call the OpenAI API to categorize the text
        response = openai_client.chat.completions.create(
            model="gpt-4o", messages=messages
        )

        # Extract the category from the response
        category = response.choices[0].message.content
        return category
    except Exception as e:
        print(f"Error categorizing text: {str(e)}")
        return None


# Example usage


def extract_text_from_pdf(pdf_path):
    # Initialize the PDF reader
    reader = PdfReader(pdf_path)
    text = ""
    # Iterate through each page in the PDF and extract text
    for page in reader.pages:
        text += page.extract_text()
    return text


def process_file(file_path, idx, categories, embeddings_model):
    file_name = os.path.basename(file_path)
    print(f"Processing file {idx + 1}: {file_name}")

    # Read text content from .txt files
    if file_name.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
    # Extract text content from .pdf files
    elif file_name.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)

    title = file_name
    # Generate embeddings for the title
    title_vectors, title_text = len_safe_get_embedding(title, embeddings_model)
    print(f"Generated title embeddings for {file_name}")

    # Generate embeddings for the content
    content_vectors, content_text = len_safe_get_embedding(text, embeddings_model)
    print(f"Generated content embeddings for {file_name}")

    category = categorize_text(" ".join(content_text), categories)
    print(f"Categorized {file_name} as {category}")

    # Prepare the data to be appended
    data = []
    for i, content_vector in enumerate(content_vectors):
        data.append(
            {
                "id": f"{idx}_{i}",
                "vector_id": f"{idx}_{i}",
                "title": title_text[0],
                "text": content_text[i],
                "title_vector": json.dumps(
                    title_vectors[0]
                ),  # Assuming title is short and has only one chunk
                "content_vector": json.dumps(content_vector),
                "category": category,
            }
        )
        print(f"Appended data for chunk {i + 1}/{len(content_vectors)} of {file_name}")

    return data


PROCESS_FILES = True

if PROCESS_FILES:
    ## Customize the location below if you are using different data besides the OpenAI documentation. Note that if you are using a different dataset, you will need to update the categories list as well.
    folder_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    files = [
        os.path.join(folder_name, f)
        for f in os.listdir(folder_name)
        if f.endswith(".txt") or f.endswith(".pdf")
    ]
    data = []

    # Process each file concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(
                process_file, file_path, idx, categories, embeddings_model
            ): idx
            for idx, file_path in enumerate(files)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                data.extend(result)
            except Exception as e:
                print(f"Error processing file: {str(e)}")

    # Write the data to a CSV file
    csv_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "embedded_data.csv"
    )
    with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "id",
            "vector_id",
            "title",
            "text",
            "title_vector",
            "content_vector",
            "category",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
            print(f"Wrote row with id {row['id']} to CSV")

    # Convert the CSV file to a Dataframe
    article_df = pd.read_csv(
        csv_file,
    )
    # Read vectors from strings back into a list using json.loads
    article_df["title_vector"] = article_df.title_vector.apply(json.loads)
    article_df["content_vector"] = article_df.content_vector.apply(json.loads)
    article_df["vector_id"] = article_df["vector_id"].apply(str)
    article_df["category"] = article_df["category"].apply(str)
    article_df.head()

    # Define the dataset ID (project_id.dataset_id)
    raw_dataset_id = "oai_docs"
    dataset_id = project_id + "." + raw_dataset_id

    client = bigquery.Client(credentials=credentials, project=project_id)

    # Construct a full Dataset object to send to the API
    dataset = bigquery.Dataset(dataset_id)

    # Specify the geographic location where the dataset should reside
    dataset.location = "US"

    # Send the dataset to the API for creation
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {client.project}.{dataset.dataset_id}")
    except Conflict:
        print(f"dataset {dataset.dataset_id } already exists")

    # Read the CSV file, properly handling multiline fields
    df = pd.read_csv(csv_file, engine="python", quotechar='"', quoting=1)

    # Display the first few rows of the dataframe
    df.head()

    # Preprocess the data to ensure content_vector is correctly formatted
    # removing last and first character which are brackets [], comma splitting and converting to float
    def preprocess_content_vector(row):
        row["content_vector"] = [
            float(x) for x in row["content_vector"][1:-1].split(",")
        ]
        return row

    # Apply preprocessing to the dataframe
    df = df.apply(preprocess_content_vector, axis=1)

    # Define the schema of the final table
    final_schema = [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("vector_id", "STRING"),
        bigquery.SchemaField("title", "STRING"),
        bigquery.SchemaField("text", "STRING"),
        bigquery.SchemaField("title_vector", "STRING"),
        bigquery.SchemaField("content_vector", "FLOAT64", mode="REPEATED"),
        bigquery.SchemaField("category", "STRING"),
    ]

    # Define the final table ID
    raw_table_id = "embedded_data"
    final_table_id = f"{dataset_id}." + raw_table_id

    # Create the final table object
    idx = -1
    found = False

    while not found:
        idx += 1
        try:
            final_table = bigquery.Table(f"{final_table_id}_{idx}", schema=final_schema)
            client.get_table(final_table)
            print(f"Table {final_table_id}_{idx} already exists")
        except Exception as e:
            found = True
            print(f"Table {final_table_id}_{idx} does not exist")


    # Send the table to the API for creation
    final_table = client.create_table(final_table, exists_ok=True)  # API request
    print(
        f"Created final table {project_id}.{final_table.dataset_id}.{final_table.table_id}"
    )

    # Convert DataFrame to list of dictionaries for BigQuery insertion
    rows_to_insert = df.to_dict(orient="records")

    # Upload data to the final table
    errors = client.insert_rows_json(
        f"{final_table.dataset_id}.{final_table.table_id}", rows_to_insert
    )  # API request

    if errors:
        print(f"Encountered errors while inserting rows: {errors}")
    else:
        print(f"Successfully loaded data into {dataset_id}:{final_table_id}")
else:
    client = bigquery.Client(credentials=credentials, project=project_id)

print("\nTAKE 1")

query = "What model should I use to embed?"
category = "models"

embedding_query = generate_embeddings(query, embeddings_model)
embedding_query_list = ", ".join(map(str, embedding_query))

query = f"""
WITH search_results AS (
  SELECT query.id AS query_id, base.id AS base_id, distance
  FROM VECTOR_SEARCH(
    TABLE oai_docs.embedded_data, 'content_vector',
    (SELECT ARRAY[{embedding_query_list}] AS content_vector, 'query_vector' AS id),
    top_k => 2, distance_type => 'COSINE', options => '{{"use_brute_force": true}}')
)
SELECT sr.query_id, sr.base_id, sr.distance, ed.text, ed.title
FROM search_results sr
JOIN oai_docs.embedded_data ed ON sr.base_id = ed.id
ORDER BY sr.distance ASC
"""

query_job = client.query(query)
results = query_job.result()  # Wait for the job to complete

for row in results:
    print(
        f"query_id: {row['query_id']}, base_id: {row['base_id']}, distance: {row['distance']}, text_truncated: {row['text'][0:100]}"
    )

print("\nTAKE 2")

query = "What model should I use to embed?"
category = "models"

embedding_query = generate_embeddings(query, embeddings_model)
embedding_query_list = ", ".join(map(str, embedding_query))


query = f"""
WITH search_results AS (
  SELECT query.id AS query_id, base.id AS base_id, distance
  FROM VECTOR_SEARCH(
    (SELECT * FROM oai_docs.embedded_data WHERE category = '{category}'), 
    'content_vector',
    (SELECT ARRAY[{embedding_query_list}] AS content_vector, 'query_vector' AS id),
    top_k => 4, distance_type => 'COSINE', options => '{{"use_brute_force": true}}')
)
SELECT sr.query_id, sr.base_id, sr.distance, ed.text, ed.title, ed.category
FROM search_results sr
JOIN oai_docs.embedded_data ed ON sr.base_id = ed.id
ORDER BY sr.distance ASC
"""


query_job = client.query(query)
results = query_job.result()  # Wait for the job to complete

for row in results:
    print(
        f"category: {row['category']}, title: {row['title']}, base_id: {row['base_id']}, distance: {row['distance']}, text_truncated: {row['text'][0:100]}"
    )
