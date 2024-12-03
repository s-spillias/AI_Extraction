# AI Extraction and Validation for Community-Based Fisheries Management (CBFM)

This project contains a collection of Python scripts for AI-assisted extraction, validation, and analysis of data related to Community-Based Fisheries Management (CBFM).

## Project Overview

The main purpose of this project is to extract information from scientific papers related to CBFM using AI-powered tools. The system uses language models to answer predefined questions about each paper and synthesize the information.

## Key Components

- `Extract.py`: The main script for extracting information from scientific papers. It uses AI models to answer questions about each paper and synthesize the responses.
- `chatbot.py`: Implements the AI-powered question-answering system.
- `auxiliary.py`: Contains helper functions used across multiple scripts, including text processing and file handling.
- `ask_AI.py`: Script for interacting with various AI models (OpenAI, Azure, Groq).
- `process_ELICIT.py`: Processes data from ELICIT (likely an external data source).
- `randomize_papers.py`: Randomizes the order of papers for analysis.
- `verbosity_check.py`: Checks the verbosity of extracted text.
- `widget.py`: Implements a GUI widget for data interaction.

## CBFM Directory

The CBFM directory contains additional scripts and resources:
- `AI_widget.py`: AI-assisted widget for CBFM data interaction.
- `FleissKappa.py`: Calculates Fleiss' Kappa for inter-rater reliability.
- `Extraction_Input/`: Contains input files such as PDFs of scientific papers and extraction questions.
- `Extraction_Output/`: Stores the results of the extraction process.

## Setup and Installation

1. Clone this repository
2. Install the required packages:

```
pip install -r requirements.txt
```

3. Set up environment variables for API keys (OpenAI, Azure, etc.) in a `.env` file

## Usage

The main extraction process is run using `Extract.py`. It performs the following steps:
1. Reads scientific papers from the `CBFM/Extraction_Input/pdfs/` directory.
2. Loads questions from `CBFM/Extraction_Input/ExtractionQuestions.csv`.
3. For each paper, it uses AI models to answer the questions.
4. Multiple AI agents are used for each question to ensure reliability.
5. Responses are synthesized and formatted according to predefined criteria.
6. Results are saved in the `CBFM/Extraction_Output/` directory.

To run the extraction process:

```
python Extract.py
```

## Data

- Input data: PDF files of scientific papers related to CBFM, stored in `CBFM/Extraction_Input/pdfs/`.
- Extraction questions: Defined in `CBFM/Extraction_Input/ExtractionQuestions.csv`.
- Output data: Extracted information is saved in CSV format in `CBFM/Extraction_Output/`.

## Customization

- The number of AI agents used for each question can be adjusted by changing the `n_agents` variable in `Extract.py`.
- The types of AI models used can be modified in the `identities` list in `Extract.py`.
- Extraction questions and their formats can be customized by editing the `ExtractionQuestions.csv` file.

## License

This project is licensed under the terms specified in the `LICENSE` file.

## Contributing

For contributions or issues, please open an issue or pull request in the project repository.
