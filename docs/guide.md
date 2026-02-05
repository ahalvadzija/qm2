## Quick Start

```bash
pip install qm2
```

```bash
qm2
```

Or install from source:

```bash
git clone https://github.com/ahalvadzija/qm2.git
cd qm2
pip install -e .
```

## Screenshots

### Quiz Features

![Gameplay](images/gameplay-qm2.png) ![Flashcards](images/flashcards-qm2.png)

### Tools & Help

![Tools](images/tools-qm2.png) ![Help](images/help-qm2.png)

## Installation

### From PyPI (Recommended)

```bash
pip install qm2
```

### From Source

```bash
git clone https://github.com/ahalvadzija/qm2.git
cd qm2
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/ahalvadzija/qm2.git
cd qm2
pip install -e ".[dev]"
```

### Docker Installation (Alternative)

If you prefer to run QM2 in an isolated environment without installing Python locally:

1. **Build the image**:
    ```bash
    docker build -t qm2 .
    ```

Run the application: Since QM2 is interactive, you must use the **-it** flags:

```bash
docker run -it qm2
```

Persist your data: To keep your **quiz data and scores** after the container stops, mount a local directory:
Bash

```bash
docker run -it -v qm2_data:/root/.local/share/qm2 qm2
```

## Usage

### Basic Usage

```bash
# Start the application
qm2

# Or if installed from source
python -m qm2
```

### Command Line Options

```bash
# Show help
qm2 --help

# Show version
qm2 --version

# Run with specific data directory
qm2 --data-dir /path/to/data
```

## Features in Detail

### Question Types

1. **Multiple Choice**: Question + correct answer + 3 wrong answers
2. **True/False**: Statement + boolean answer
3. **Fill-in-the-blank**: Question with blank + correct answer
4. **Matching**: Items to match with correct pairs

### Category Management

- Create hierarchical categories (e.g., `programming/python/basics`)
- Rename and delete categories
- Automatic directory structure creation

### Import/Export Capabilities

- **CSV ↔ JSON**: Bidirectional conversion
- **Template Generation**: Create starter templates
- **Remote Import**: Download from URLs
- **Bulk Operations**: Manage multiple files efficiently

## Configuration

QM2 uses platformdirs for cross-platform data storage:

- **Linux**: `~/.local/share/qm2/`
- **macOS**: `~/Library/Application Support/qm2/`
- **Windows**: `%APPDATA%\qm2\`

### Environment Variables

```bash
# Custom data directory
export QM2_DATA_DIR="/path/to/custom/data"

# Disable colors
export NO_COLOR=1
```

## Question Format

### JSON Format

```json
[
    {
        "type": "multiple",
        "question": "What is the capital of France?",
        "correct": "Paris",
        "wrong_answers": ["Rome", "Berlin", "Madrid"]
    },
    {
        "type": "truefalse",
        "question": "Python is a programming language.",
        "correct": "True",
        "wrong_answers": ["False"]
    },
    {
        "type": "fillin",
        "question": "The capital of Japan is ______.",
        "correct": "Tokyo",
        "wrong_answers": []
    },
    {
        "type": "match",
        "question": "Match programming languages with their types",
        "pairs": {
            "left": ["Python", "JavaScript", "C++"],
            "right": ["Interpreted", "Web scripting", "Compiled"],
            "answers": { "a": "1", "b": "2", "c": "3" }
        }
    }
]
```

### CSV Format

```csv
type,question,correct,wrong_answers,left,right,answers
multiple,"What is 2+2?",4,"3,5,6","","",""
truefalse,"Earth is flat",False,True,"","",""
fillin,"Capital of Italy is ______",Rome,"","","",""
match,"Match items","","","A|B","1|2","a:1,b:2"
```
