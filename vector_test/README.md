## Running the embedding test
1. You will need a venv with the requirements installed. You can create a venv and install the requirements by running the following commands (assuming you're starting from the vector_test folder):
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. You will need Google and OpenAI API keys. The Google API key is the key to a service account, with the BigQuery Data Editor and BigQuery Job User roles. It can be obtained from the Service Accounts section of IAM & Admin in the Google Cloud Console. Use an existing or new service account, go to the Keys tab, and create a new JSON key. Save the resulting .json file as "google.json" in the vector_test folder. The OpenAI API key should be saved in "openai.json" in the vector_test folder as follows:
```json
{
    "key": "your_openai_key_here"
}
```

3. You can run the test by running the following command from the vector_test folder:
```bash
python vector_test.py
```

You should see two outputs, the first preceded by "TAKE 1" and the second preceded by "TAKE 2".