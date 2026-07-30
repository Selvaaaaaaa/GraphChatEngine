# GraphChatEngine – Project Directory Structure Guide

> Comprehensive breakdown of every directory and core file in the repository.

```
GraphChatEngine/
├── api/                        # REST API Microservice (Python 3.11 / FastAPI)
│   ├── chat/                   # Clean Architecture Chat Backend Package
│   │   ├── __init__.py         # Package exporter
│   │   ├── controller.py       # HTTP Router for POST /chat
│   │   ├── service.py          # Chat Service Layer (Timing, Metrics & Formatting)
│   │   ├── query_mapper.py     # Predefined Cypher Query Mapper
│   │   └── repository.py       # Read-Only Neo4j Repository
│   ├── core/                   # Infrastructure & Environment Configuration
│   │   ├── config.py           # Pydantic BaseSettings loading from .env
│   │   └── logging_config.py   # Root logger configuration
│   ├── routers/                # Ingestion API Routers
│   │   └── ingest.py           # HTTP Handler for POST /ingest
│   ├── schemas/                # Request & Response Pydantic Schemas
│   │   ├── chat.py             # ChatRequest & ChatResponse models
│   │   └── ingest.py           # IngestResponse & ErrorResponse models
│   ├── services/               # Core Ingestion Services
│   │   ├── ingest_service.py   # pandas CSV validation & orchestration
│   │   └── kafka_producer.py   # Kafka producer service module
│   ├── utils/                  # Utility Functions
│   │   └── file_helpers.py     # File extension & helper functions
│   ├── main.py                 # FastAPI Application Setup & Router Registration
│   ├── requirements.txt        # API Python dependencies
│   └── Dockerfile              # Docker image definition for API container
│
├── loader/                     # Asynchronous Worker Microservice (Python 3.11)
│   ├── services/               # Worker Services Package
│   │   ├── __init__.py         # Package exporter
│   │   ├── kafka_consumer.py   # Real-time Kafka consumer worker service
│   │   ├── graph_loader.py     # Graph loader orchestration service
│   │   └── neo4j_repository.py # Neo4j Cypher MERGE write repository
│   ├── consumer.py             # Worker execution entrypoint with signal handlers
│   ├── loader.py               # Loader entrypoint delegate
│   ├── requirements.txt        # Loader dependencies (kafka-python, neo4j)
│   └── Dockerfile              # Worker Docker image definition
│
├── ui/                         # Frontend Chat Interface (Vanilla Web)
│   ├── index.html              # Responsive HTML5 layout with sidebar & chat log
│   ├── style.css               # Dark glassmorphism CSS3 stylesheet & animations
│   └── app.js                  # Frontend JavaScript application logic & API fetch
│
├── sample-data/                # Synthetic Test Data Fixtures
│   ├── customers.csv           # 20-row customer dataset
│   ├── employees.csv           # 15-row employee hierarchy
│   ├── products.csv            # 15-row product catalogue
│   ├── orders.csv              # 15-row order dataset
│   ├── empty.csv               # Header-only CSV fixture (HTTP 400 test)
│   ├── invalid.csv             # Malformed CSV fixture (HTTP 422 test)
│   └── invalid.txt             # Wrong extension fixture (HTTP 400 test)
│
├── docs/                       # Architectural & Technical Documentation
│   ├── ARCHITECTURE.md         # Full system architecture specification
│   ├── REPORT_MILESTONE_01.md  # Milestone 01 report
│   ├── VIVA_MILESTONE_01.md    # Milestone 01 viva Q&As
│   ├── REPORT_MILESTONE_03.md  # Milestone 03 report
│   ├── VIVA_MILESTONE_03.md    # Milestone 03 viva Q&As
│   ├── REPORT_MILESTONE_04.md  # Milestone 04 report
│   ├── VIVA_MILESTONE_04.md    # Milestone 04 viva Q&As
│   ├── REPORT_MILESTONE_05.md  # Milestone 05 report
│   ├── VIVA_MILESTONE_05.md    # Milestone 05 viva Q&As
│   ├── REPORT_MILESTONE_07.md  # Milestone 07 report
│   └── VIVA_MILESTONE_07.md    # Milestone 07 viva Q&As
│
├── milestones/                 # Immutable Preservation Snapshots per Milestone
│   ├── step-01-project-foundation/
│   ├── step-01.5-project-hardening/
│   ├── step-02-csv-upload/
│   ├── step-03-kafka-producer/
│   ├── step-04-kafka-consumer/
│   ├── step-05-neo4j-loader/
│   ├── step-06-chat-backend/
│   ├── step-07-chat-ui/
│   └── step-08-final-polish/   # Milestone 08 Final Polish Snapshot
│
├── docker-compose.yml          # Multi-container service orchestration manifest
├── .env.example                # Environment variable documentation reference
├── .gitignore                  # Git tracking exclusion patterns
├── README.md                   # Primary repository documentation
├── REPORT_FINAL.md             # Final project submission report
├── PRESENTATION_NOTES.md       # Hackathon pitch & presentation notes
├── VIVA_FINAL.md               # 50 technical interview questions & answers
├── DEMO_SCRIPT.md              # 12-step step-by-step live demo script
├── TEST_CASES.md               # 32 comprehensive test cases
├── FINAL_VERIFICATION.md       # Final project verification matrix
├── SCREENSHOTS_REQUIRED.md     # Required screenshots manifest
└── PROJECT_STRUCTURE.md        # Directory tree reference
```
