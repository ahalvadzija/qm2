# Quiz Maker 2 (QM2) - Interactive Terminal Quiz Application

## Showcase

https://github.com/user-attachments/assets/850a7e4a-173a-4acb-b821-4a645c5115cf

## 📖 Overview

Quiz Maker 2 (QM2) is a powerful, interactive terminal-based quiz application written in Python. It provides a comprehensive solution for creating, managing, and taking quizzes with multiple question types, advanced features like flashcards mode, score tracking, and extensive import/export capabilities.

## 🚀 Features

<img width="850" height="628" alt="main-menu" src="https://github.com/user-attachments/assets/2d563a0a-9790-4c8c-918f-118ff8bbed20" />

### Core Functionality
- **Multiple Question Types**: Support for multiple choice, true/false, fill-in-the-blank, and matching questions
- **Interactive Quiz Sessions**: Timed questions with customizable timeout settings
- **Flashcards Mode**: Study mode for reviewing questions without scoring
- **Score Tracking**: Comprehensive statistics and performance analytics
- **Category Management**: Organize questions into categories and subcategories

<img width="850" height="628" alt="tools" src="https://github.com/user-attachments/assets/aba9f90c-2ec7-42a1-be7f-66907ebad0dd" />
<img width="850" height="628" alt="results" src="https://github.com/user-attachments/assets/9c75d1e0-a748-40de-ae41-757461ec9dd1" />


### Advanced Features
- **Import/Export**: Convert between CSV and JSON formats
- **Remote File Import**: Download and import quiz files from URLs
- **Template Generation**: Create starter templates for both CSV and JSON formats
- **Real-time Feedback**: Immediate scoring and correct answer display
- **Progress Tracking**: Monitor quiz completion and performance over time
<img width="850" height="628" alt="questions-type" src="https://github.com/user-attachments/assets/e016f42a-a26f-4dc7-8688-31789e70de31" />
<img width="850" height="628" alt="help" src="https://github.com/user-attachments/assets/2cd66899-86df-4d07-93dc-3e7afc4289ba" />

### Technical Features
- **Caching System**: Optimized performance for large question sets
- **Cross-platform Compatibility**: Works on Windows, macOS, and Linux
- **Rich Terminal UI**: Beautiful, colored interface using Rich library
- **Memory Management**: Automatic cache cleanup to prevent memory leaks

## 🖥️ Platform Support

### Supported Operating Systems
- **Windows**: Windows 10/11 (PowerShell, Command Prompt, Windows Terminal)
- **macOS**: macOS 10.14+ (Terminal, iTerm2)
- **Linux**: All major distributions (bash, zsh, fish shells)

### Terminal Requirements
- **Minimum**: 80x24 character display
- **Recommended**: 120x30 or larger for optimal experience
- **Color Support**: 256-color terminal recommended
- **Unicode Support**: UTF-8 encoding for special characters and emojis

## 📋 Prerequisites

### Required Dependencies
```bash
pip install questionary rich requests
```

### Individual Package Descriptions
- **questionary**: Interactive command-line prompts
- **rich**: Rich text and beautiful formatting in terminal
- **requests**: HTTP library for remote file downloads

### Python Version
- **Minimum**: Python 3.7+
- **Recommended**: Python 3.9+ for best performance

## 🚀 Installation & Setup

### Quick Start
1. **Clone or Download** the application file
2. **Install Dependencies**:
   ```bash
   pip install questionary rich requests
   ```
   or
   
   ```bash
   pip3 install questionary rich requests
   ```
4. **Run the Application**:
   ```bash
   python qm2-v1.1.py
   ```
   or

   ```bash
   python3 qm2-v1.1.py
   ```

### Directory Structure
The application creates the following structure:

<img width="922" height="520" alt="files" src="https://github.com/user-attachments/assets/7c64b668-cb2f-427d-8900-91e73179c0d0" />



```
qm2/
├── qm2-v1.1.py               # Main application
├── categories/               # Categories directory
│   ├── programming/
│   │   ├── python.json
│   │   └── javascript.json
│   └── science/
│       └── physics.json
├── csv/                      # CSV import/export directory
│   └── template.csv
├── scores/                   # Score tracking files
└── help.json                 # Help documentation
```

## 🎯 Application Options & Menus

### Main Menu Options

#### 1. 📚 Take Quiz
- Select from available categories
- Choose question types (all, multiple choice, true/false, etc.)
- Set custom question limits
- Real-time scoring and feedback

#### 2. 🃏 Flashcards Mode
- Study mode without scoring pressure
- Review questions at your own pace
- Perfect for learning and memorization

#### 3. ✏️ Manage Questions
- **View Questions**: Browse all questions with pagination
- **Add New Question**: Create questions interactively
- **Edit Questions**: Modify existing questions by number or selection
- **Delete Questions**: Remove unwanted questions
- **Search Functionality**: Find specific questions quickly

#### 4. 📊 View Statistics
- **Performance Analytics**: See correct/wrong/timeout ratios
- **Score History**: Track progress over time
- **Category Performance**: Analyze strengths and weaknesses
- **Reset Scores**: Clear statistics when needed

#### 5. 🧰 Tools & Utilities
- **CSV ↔ JSON Conversion**: Bidirectional file format conversion
- **Template Generation**: Create starter files
- **Remote Import**: Download quizzes from URLs
- **Bulk Operations**: Manage multiple files efficiently

#### 6. 📁 Category Management
- **Create Categories**: New quiz categories and subcategories
- **Rename Categories**: Update category names
- **Delete Categories**: Remove unused categories
- **Folder Organization**: Hierarchical category structure

## 📝 Usage Guide

### Starting the Application
```bash
python3 qm2-v1.1.py
```

The application will display a colorful main menu with navigation options.

### Taking a Quiz
1. Select **"📚 Take Quiz"** from main menu
2. Choose a category from the list
3. Optionally filter by question type
4. Set question limit (or use all questions)
5. Answer questions within the time limit
6. Review your final score and statistics

### Creating Categories

#### Method 1: Through Main Menu
1. Navigate to **"📁 Manage Categories"**
2. Select **"➕ Create new category"**
3. Enter folder path (e.g., `programming/python`)
4. Enter filename (e.g., `basics.json`)
5. The system creates the directory structure automatically

#### Method 2: Manual Directory Creation
```bash
mkdir -p categories/your-category
```

### Creating Questions

#### Interactive Question Creation
1. Select **"✏️ Manage Questions"**
2. Choose **"➕ Add new question"**
3. Select question type:
   - **Multiple Choice**: Question + correct answer + 3 wrong answers
   - **True/False**: Statement + correct boolean answer
   - **Fill-in**: Question with blank + correct answer
   - **Matching**: Items to match + correct pairs

#### JSON File Format
Create `.json` files in the `categories` directory:

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
      "answers": {
        "a": "1",
        "b": "2", 
        "c": "3"
      }
    }
  }
]
```

### CSV Import/Export

#### CSV Template Format
```csv
type,question,correct,wrong_answers,left,right,answers
multiple,"What is 2+2?",4,"3,5,6","","",""
truefalse,"Earth is flat",False,True,"","",""
fillin,"Capital of Italy is ______",Rome,"","","",""
match,"Match items","","","A|B","1|2","a:1,b:2"
```

#### Converting CSV to JSON
1. Place CSV file in `csv/` directory
2. Select **"🧰 Tools"** → **"🧾 Convert CSV to JSON"**
3. Choose source CSV file
4. Select destination category
5. System converts and validates automatically

## 🔧 Troubleshooting

### Common Issues

#### Import Errors
- **Issue**: `ModuleNotFoundError: No module named 'questionary'`
- **Solution**: Run `pip install questionary rich requests`

#### File Permission Errors
- **Issue**: Cannot create categories directory
- **Solution**: Ensure write permissions in application directory

#### Display Issues
- **Issue**: Broken characters or layout
- **Solution**: Use UTF-8 compatible terminal with 256-color support

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.


**Created by**: Adnan Halvadžija

**Version**: 1.1

**Last Updated**: 2025

For issues and feature requests, please create an issue in the project repository.

