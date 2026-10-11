# depthreach
AI agent that researches prospects and generates personalised cold emails from a contact list.

## Usage

```bash
depthreach --input prospects.csv --output results.csv --tone professional --workers 2
```

### Flags
- `--input` – CSV or JSON file with contact information (name, email, company, LinkedIn URL, etc.)
- `--output` – Output file path (default: stdout)
- `--tone` – Email tone: `professional`, `casual`, or `direct` (default: `professional`)
- `--workers` – Number of parallel workers (default: 2)

### Single prospect
```bash
depthreach --name "Jane Doe" --company "Acme Corp" --email "jane@acme.com"
```

## Configuration

API keys and cache are stored in `~/.depthreach/`.

Set the following environment variables:
- `TAVILY_API_KEY` – Tavily Search API key
- `GEMINI_API_KEY` – Google Gemini API key
