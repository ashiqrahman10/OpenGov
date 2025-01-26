# OpenGov API

## Overview

The OpenGov API is designed to facilitate the analysis and management of meeting content, reports, and citizen engagement. It leverages advanced AI models for transcription, summarization, and entity recognition, providing a comprehensive tool for government agencies and organizations.

## Features

- **Meeting Analysis**: Upload audio or PDF files of meetings for transcription and analysis.
- **Report Analysis**: Analyze corruption reports to extract key information and recommendations.
- **Named Entity Recognition**: Extract entities such as people, organizations, and locations from transcripts.
- **Action Item Management**: Create, update, and retrieve action items associated with meetings.
- **Sentiment Analysis**: Assess the sentiment of meeting discussions and reports.
- **Fallback Mechanism**: Use Gemini as a fallback when Groq API token limits are reached.

## Technologies Used

- **FastAPI**: For building the API.
- **SQLAlchemy**: For database interactions.
- **Google Speech-to-Text**: For audio transcription.
- **Groq and Gemini**: For natural language processing and analysis.
- **Pydantic**: For data validation and serialization.
- **PyPDF2**: For extracting text from PDF files.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/opengov-api.git
   cd opengov-api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```env
   DATABASE_URL=sqlite:///./test.db
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_CREDENTIALS_PATH=path/to/your/serviceAccountKey.json
   ```

5. Run the database migrations (if applicable):
   ```bash
   alembic upgrade head
   ```

6. Start the FastAPI server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

## API Endpoints

### Meeting Analysis

- **POST /meetings/analyze**
  - Upload audio or PDF files for analysis.
  - Request body:
    - `file`: The audio or PDF file.
    - `title`: Title of the meeting.
    - `file_type`: Type of the file (`audio` or `pdf`).

- **GET /meetings/{meeting_id}**
  - Retrieve details of a specific meeting.

- **GET /meetings/{meeting_id}/action-items**
  - Get action items associated with a specific meeting.

- **POST /meetings/{meeting_id}/action-items**
  - Create a new action item for a specific meeting.

- **GET /meetings/{meeting_id}/minutes**
  - Generate and retrieve formatted meeting minutes.

### Report Analysis

- **POST /reports/analyze**
  - Analyze a corruption report.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries, please contact [your_email@example.com].