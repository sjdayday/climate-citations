# Climate Citations

## Overview
The Climate Citations project provides a lightweight client for interacting with the OpenAlex API, focusing on retrieving topics and works related to climate research. This project aims to facilitate access to academic works and topics, making it easier for researchers and developers to gather relevant information.

## Installation
To install the required dependencies, you can use pip. Make sure you have Python 3.6 or higher installed.

```bash
pip install -r requirements.txt
```

## Usage
To use the OpenAlex client, you can import the `OpenAlexClient` class from the `climate_citations.openalex` module. Here is a simple example of how to retrieve topics and works:

```python
from climate_citations.openalex import OpenAlexClient

client = OpenAlexClient()

# Retrieve a topic by ID
topic = client.get_topic("T12345")
print(topic.display_name)

# Search for topics
for topic in client.search_topics("climate change"):
    print(topic.display_name)

# Get works for a specific topic
works = client.get_works_for_topic("T12345")
for work in works:
    print(work.title)
```

## Running Tests
To run the tests for this project, navigate to the `tests` directory and use a testing framework like `unittest` or `pytest`. For example:

```bash
pytest tests/test_openalex.py
```

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.