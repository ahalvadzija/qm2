## Project Structure

```text
qm2/
├── src/qm2/                # Core application package
│   ├── core/               # Business logic (engine, questions, scores)
│   ├── ui/                 # Rich terminal user interface
│   ├── utils/              # File I/O and helper utilities
│   └── __main__.py         # CLI entry point
├── tests/                  # Extensive test suite (325+ tests)
│   ├── test_engine.py      # Core logic benchmarks
│   ├── test_performance.py # Speed & stress tests
│   └── ...                 # App, UI, and integration tests
├── docs/                   # MkDocs documentation source
│   ├── index.md            # Homepage
│   ├── guide.md            # User guide
│   └── reference.md        # Technical reference
├── examples/               # Sample JSON/CSV question sets
├── Dockerfile              # Docker container configuration
├── .dockerignore           # Docker build exclusions
├── mkdocs.yml              # Documentation site configuration
├── pyproject.toml          # Build system and dependencies
├── requirements.txt        # Development dependencies
└── README.md               # Project overview and quick start
```

### Performance Features

- **Caching System**: Optimized for large question sets
- **Memory Management**: Automatic cache cleanup
- **Fast Loading**: Sub-second load times for thousands of questions

### Quality Assurance & Performance

Reliability is at the heart of QM2. The project maintains an 86% coverage rate backed by a massive suite of 325 individual tests. CI/CD pipeline ensures that every release is battle-tested.

#### Test Coverage Breakdown

- **App & UI (95+ tests)**: Comprehensive navigation testing including brute force menu traversal and submenu logic.
- **Engine & Core (45+ tests)**: Validation of all question types, session handling, and flashcards mode.
- **Validation & Security (40+ tests)**: Deep CSV/JSON schema validation and safe remote file importing.
- **Data & IO (35+ tests)**: Cross-platform path handling, concurrent file access, and encoding resilience.
- **Performance (12+ tests)**: Stress testing with large datasets and cache optimization benchmarks.

## Performance Benchmarks

QM2 is engineered for high-speed interactions and efficient resource management, verified by a dedicated performance suite:

- **Benchmarked Speed**: Processes 1,000+ questions in **< 1 second**, ensuring no lag during large quiz sessions.
- **Intelligent Caching**: Implements a caching layer that makes subsequent data loads **10x faster**.
- **Memory Efficiency**: Automatic cache cleanup prevents memory leaks during long-running sessions.
- **Thread Safety**: Verified safe concurrent file access, preventing data corruption during simultaneous read/write operations.

### Performance Testing (`tests/test_performance.py`)

- **Execution**: 12 specialized performance tests passed in **2.11s**.
- **Coverage focus**: Validated `core/engine.py` and `utils/files.py` for speed bottlenecks.

### Core Engine Testing (`tests/test_engine.py`)

- **Execution**: 23 core logic tests passed in **1.34s**.
- **Coverage**: High coverage (68%) of `src/qm2/core/engine.py`, ensuring question logic and scoring are flawless.

### Development Setup

```bash
git clone https://github.com/ahalvadzija/qm2.git
cd qm2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## How to Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=qm2

# Run specific test categories
pytest tests/test_engine.py    # Core engine tests
pytest tests/test_questions.py # Question management tests
pytest tests/test_files.py     # File operations tests
pytest tests/test_scores.py    # Score tracking tests
pytest tests/test_performance.py # Performance tests
```

### Code Style

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```
