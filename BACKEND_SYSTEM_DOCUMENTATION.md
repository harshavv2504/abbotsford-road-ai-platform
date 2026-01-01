# Backend System Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Components](#architecture-components)
4. [AI Flow & Processing](#ai-flow--processing)
5. [Database Structure](#database-structure)
6. [API Endpoints](#api-endpoints)
7. [Deployment & Infrastructure](#deployment--infrastructure)

---

## System Overview

**Abbotsford Road Coffee Specialists AI Platform** is a comprehensive AI-powered chatbot and CRM system. The system provides:

- **Outbound Chatbot**: Lead generation and qualification for potential café customers
- **Inbound Chatbot**: Customer support for existing authenticated users
- **CRM System**: Lead and deal management with Kanban workflow
- **Avatar Integration**: HeyGen avatar streaming for visual interaction
- **Speech-to-Text**: Deepgram integration for voice input

### Key Features
- Multi-stage intent detection and customer qualification
- RAG (Retrieval-Augmented Generation) for knowledge-based responses
- Real-time conversation state management
- Automated lead scoring and qualification
- MongoDB-based persistence with async operations
- Rate limiting and security middleware
- Docker containerization with multi-stage builds

---

## Technology Stack

### Core Framework
- **FastAPI**: Modern async web framework for Python
- **Uvicorn**: ASGI server with WebSocket support
- **Python 3.11**: Runtime environment

### AI & Machine Learning
- **OpenAI GPT-4o-mini**: Primary LLM for conversation and reasoning
- **FastEmbed**: Lightweight embedding generation (ONNX Runtime)
- **FAISS**: Vector similarity search (CPU-optimized)
- **Deepgram**: Speech-to-text transcription

### Database & Storage
- **MongoDB**: Primary database (Motor async driver)
- **Vector Store**: FAISS flat index for embeddings
- **File Storage**: Local filesystem for knowledge base documents

### Authentication & Security
- **JWT**: Token-based authentication
- **Passlib + Bcrypt**: Password hashing
- **SlowAPI**: Rate limiting middleware
- **CORS**: Cross-origin resource sharing

### External Integrations
- **HeyGen API**: Avatar streaming tokens

### Development & Deployment
- **Docker**: Multi-stage containerization
- **Docker Compose**: Service orchestration
- **Cloud Run**: Deployment target (Google Cloud)

---

## Architecture Components

### 1. Application Structure

```
backend/
├── app/
│   ├── config/          # Configuration management
│   │   ├── database.py      # MongoDB connection
│   │   ├── llm_config.py    # OpenAI settings
│   │   └── settings.py      # Environment variables
│   │
│   ├── models/          # Data models (Pydantic)
│   │   ├── user.py          # User authentication
│   │   ├── chat_conversation.py  # Chat sessions
│   │   └── crm_deal.py      # CRM deals
│   │
│   ├── schemas/         # Request/Response schemas
│   │   ├── auth.py          # Login/Register
│   │   ├── chat.py          # Chat messages
│   │   └── crm.py           # CRM operations
│   │
│   ├── routes/          # API endpoints
│   │   ├── auth.py          # Authentication
│   │   ├── chat.py          # Chat operations
│   │   ├── crm.py           # CRM management
│   │   └── heygen.py        # Avatar tokens
│   │
│   ├── services/        # Business logic
│   │   ├── llm_service.py   # OpenAI integration
│   │   ├── stt_service.py   # Speech-to-text
│   │   ├── outbound/        # Lead generation bot
│   │   ├── inbound/         # Customer support bot
│   │   └── rag/             # RAG components
│   │
│   ├── middleware/      # Request processing
│   │   └── rate_limiter.py  # Rate limiting
│   │
│   ├── utils/           # Helper functions
│   │   ├── auth.py          # JWT utilities
│   │   ├── logger.py        # Logging
│   │   ├── validators.py    # Input validation
│   │   └── helpers.py       # General utilities
│   │
│   ├── data/            # Persistent data
│   │   ├── knowledge_base/  # Documents for RAG
│   │   └── vector_db/       # FAISS indices
│   │
│   ├── static/          # Frontend build
│   │   └── assets/          # JS, CSS, images
│   │
│   └── main.py          # Application entry point
│
├── scripts/             # Utility scripts
│   └── init_rag.py          # RAG initialization
│
└── requirements.txt     # Python dependencies
```

### 2. Configuration Management

#### Settings (`config/settings.py`)
Centralized configuration using Pydantic Settings:
- Environment variable loading from `.env`
- Type validation and defaults
- MongoDB connection strings
- API keys (OpenAI, Deepgram, HeyGen)
- JWT configuration
- Rate limiting rules

#### Database (`config/database.py`)
- Async MongoDB client (Motor)
- Connection pooling
- Startup/shutdown lifecycle management
- Database instance accessor

#### LLM Config (`config/llm_config.py`)
- Model selection (gpt-4o-mini)
- Temperature and token limits
- API key management

### 3. Data Models

#### User Model
```python
- id: ObjectId
- email: EmailStr (validated)
- password: str (hashed with bcrypt)
- name: str
- role: str (admin/user)
- created_at: datetime
- last_login: datetime
- Additional fields: phone, country, city, coffee_style, serving_capacity
```

#### Chat Conversation Model
```python
- id: ObjectId
- session_id: str (client-generated)
- conversation_id: str (server-generated)
- chat_type: str (outbound/inbound)
- user_id: str (for inbound only)
- messages: List[Message] (user/bot pairs with timestamps)
- status: str (ongoing/closed)
- closed_reason: str (user_closed/auto_timeout)
- summarized: bool
- data: Dict (conversation state)
- created_at: datetime
- last_message_at: datetime
- ended_at: datetime
```

#### CRM Deal Model
```python
- id: ObjectId
- company_name: str
- deal_value: float
- contact_person: str
- email: str
- mobile: str
- summary: str
- priority: str (Low/Medium/High)
- status: str (new-lead/contacted/proposal-sent/negotiation/won)
- meeting_notes: str
- comments: str
- source_conversation_id: str (optional)
- created_at: datetime
- updated_at: datetime
```

---

## AI Flow & Processing

### 1. LLM Service Architecture

#### Core Service (`services/llm_service.py`)
The LLM service is the central hub for all AI interactions:

**Key Features:**
- Async OpenAI client initialization
- Function calling support (tools/tool_choice)
- Conversation history management
- Token usage tracking and logging
- MongoDB logging for all API calls

**API Call Flow:**
```
1. Prepare messages (system + conversation history)
2. Add tools if function calling needed
3. Make async API call to OpenAI
4. Parse response (text or function_call)
5. Log to MongoDB (api_logger collection)
6. Return structured response
```

**Logging Structure:**
```python
{
  "timestamp": datetime,
  "api_key": "...last4chars",
  "api_params": {...},
  "response_msg": str,
  "usage_tokens": {
    "prompt_tokens": int,
    "completion_tokens": int,
    "total_tokens": int,
    "cached_tokens": int
  },
  "tool_calls": [...],
  "finish_reason": str,
  "response_id": str
}
```

### 2. RAG (Retrieval-Augmented Generation) System

The RAG system provides knowledge-based responses using vector similarity search.

#### Components:

**A. Embedding Service (`services/rag/embedding_service.py`)**
- Model: BAAI/bge-small-en-v1.5 (384 dimensions)
- FastEmbed with ONNX Runtime (lightweight, no PyTorch)
- Automatic prefix addition:
  - `passage:` for documents
  - `query:` for search queries
- L2 normalization for Inner Product similarity
- Batch processing support

**B. Vector Store (`services/rag/vector_store.py`)**
- FAISS IndexFlatIP (Inner Product similarity)
- Metadata storage in JSON
- Persistent storage to disk
- Add/search/clear operations
- Thread-safe singleton pattern

**C. Document Loader (`services/rag/document_loader.py`)**
- Loads documents from knowledge_base directory
- Chunking strategies for long documents
- Metadata extraction (source, category)
- Batch embedding generation

**D. Retriever (`services/rag/retriever.py`)**
- Query embedding generation
- Top-k similarity search
- Category filtering
- Relevance scoring
- Context formatting for LLM

#### RAG Flow:
```
1. User asks question
2. Generate query embedding (with "query:" prefix)
3. Search vector store (FAISS Inner Product)
4. Retrieve top-k documents
5. Format context for LLM
6. Generate response with context
7. Return answer to user
```

### 3. Outbound Bot (Lead Generation)

The outbound bot qualifies potential café customers through multi-stage conversations.

#### Architecture:

**Core Orchestrator (`services/outbound/outbound_bot.py`)**
- Main entry point for all outbound messages
- Coordinates sub-services
- Manages conversation flow
- Delegates to FlowController and ExtractionPipeline

**Key Components:**

**A. State Manager (`services/outbound/state_manager.py`)**
- Tracks conversation state across turns
- Fields: name, email, phone, timeline, equipment, volume, etc.
- Intent stages: exploring → interest_detected → intent_confirmed → qualified
- Customer types: new_cafe, existing_cafe, casual_browser
- Field tracking (ask counts, skip logic)
- Qualification completion checks

**B. Flow Controller (`services/outbound/core/flow_controller.py`)**
- Handles conversation flow decisions
- Early exits (goodbye, human connection)
- Intent detection and upgrades
- RAG question routing
- Post-qualification flow

**C. Extraction Pipeline (`services/outbound/core/extraction_pipeline.py`)**
- Parallel field extraction using LLM
- Validation service integration
- Error handling and retry logic
- Field-specific extraction strategies

**D. Customer Type Detector (`services/outbound/customer_type_detector.py`)**
- Detects: new_cafe, existing_cafe, casual_browser
- Uses LLM with structured output
- Confidence scoring
- Context-aware detection

**E. Question Generator (`services/outbound/question_generator.py`)**
- Natural language question generation
- Field-specific questions
- Context-aware phrasing
- Avoids repetition

**F. Response Builder (`services/outbound/response_builder.py`)**
- Generates natural responses
- Integrates RAG context
- Acknowledgment of provided info
- Follow-up question generation

**G. Validation Service (`services/outbound/validation_service.py`)**
- Email validation (format, typo detection)
- Phone validation (phonenumbers library)
- Country code handling
- Error message generation

**H. RAG Handler (`services/outbound/rag_handler.py`)**
- Question detection
- Context retrieval
- Answer generation with RAG
- Unlimited vs. limited response modes

#### Outbound Bot Flow:

```
1. Receive user message
2. Load conversation state
3. Check for goodbye/exit signals
4. Parallel detection:
   - Customer type (new_cafe/existing_cafe/casual)
   - Flow state (continuing/wants_to_exit/refuses_contact)
   - Early field extraction
5. Handle special cases:
   - Human connection requests
   - Email typo confirmation
   - RAG questions during qualification
6. Intent detection (multi-stage):
   - exploring → interest_detected → intent_confirmed
7. Field extraction + validation:
   - Extract fields from message
   - Validate (email, phone)
   - Update state
   - Generate follow-up questions
8. Check qualification completion:
   - All required fields collected?
   - Mark as qualified
   - Offer human connection
9. Generate response:
   - Use prompt handler
   - Add context (RAG, state)
   - Natural language generation
10. Save state and return response
```

#### Qualification Fields:

**New Café:**
- name, email, phone
- timeline (when opening)
- coffee_style (bold/light/balanced)
- equipment (yes/no/unsure)
- volume (daily cups)

**Existing Café:**
- name, email, phone
- current_pain_points
- cafe_count (number of locations)
- support_needs
- coffee_preference

### 4. Inbound Bot (Customer Support)

The inbound bot provides support for authenticated customers with issue tracking.

#### Architecture:

**Core Bot (`services/inbound/inbound_bot.py`)**
- Authenticated user support
- Issue extraction and tracking
- Scenario-based troubleshooting
- Support ticket creation

**Key Components:**

**A. State Manager (`services/inbound/state_manager.py`)**
- Issue tracking (summary, details, category)
- Additional issues list
- Ticket creation state
- Questions asked counter

**B. Prompt Handler (`services/inbound/prompt_handler.py`)**
- Personalized system instructions
- User details integration (name, location, coffee style)
- Scenario-specific guidance
- Tone and style rules

**C. Extraction Service (`services/inbound/extraction_service.py`)**
- Problem intent detection
- Issue extraction (summary, details, category, urgency)
- Additional issue detection
- Ticket response classification

**D. Bot Functions (`services/inbound/bot_functions.py`)**
- End chat function
- Ticket creation
- User lookup

**E. User Service (`services/inbound/user_service.py`)**
- Fetch user details from database
- Personalization data

**F. Business Logic (`services/inbound/bot_business_logic.py`)**
- Clarifying question logic
- Issue categorization
- Troubleshooting guidance

#### Inbound Bot Flow:

```
1. Receive user message (with user_id)
2. Load conversation state
3. Fetch user details (name, location, preferences)
4. Check for goodbye/exit signals
5. Detect problem intent:
   - Is user reporting an issue?
   - Confidence scoring
6. Extract issue details:
   - Summary, details, category
   - Urgency level
   - When started, what tried, business impact
7. Handle special scenarios:
   - Coffee tastes different
   - Staff dialing in help
   - Urgent delivery
   - Machine issues
   - Milk problems
   - Menu complexity
8. Provide immediate help:
   - Troubleshooting steps
   - Quick fixes
   - Best practices
9. Offer support ticket:
   - Ask once per issue
   - Collect details
   - Create ticket
10. Generate response:
    - Use RAG for product questions
    - Personalized with user details
    - Scenario-specific guidance
11. Save state and return response
```

#### Support Scenarios:

**Scenario 1: Coffee Tastes Different**
- Detect: taste, flavor, bitter, weak, sour
- Causes: grinder drift, dose inconsistency, old beans
- Actions: Check grind, dose, shot time
- Offer: Support case after guidance

**Scenario 2: Staff Dialing In**
- Detect: staff, dial, training, barista
- Causes: new staff, high turnover, inconsistent technique
- Actions: Symptom-based logic, base recipe
- Offer: Dialing-in guide

**Scenario 3: Urgent Delivery**
- Detect: run out, missing delivery, urgent
- Priority: Immediate escalation
- Actions: Order number, tracking check
- Offer: Urgent replacement

**Scenario 4: Machine Issues**
- Detect: pressure, temperature, steam wand, group head
- Causes: Calibration, cleaning needed
- Actions: Simple troubleshooting
- Offer: Support case if unresolved

**Scenario 5: Milk Issues**
- Detect: milk, foam, froth, texture, splitting
- Causes: Temperature, technique, milk type
- Actions: Simple tips
- Offer: Support case if unresolved

**Scenario 6: Menu Problems**
- Detect: menu, recipe, complex, struggle
- Causes: Too many SKUs, complex drinks
- Actions: Recipe standardization
- Offer: Menu revision support

### 5. Speech-to-Text Service

**Deepgram Integration (`services/stt_service.py`)**
- REST API integration
- Base64 audio decoding
- Nova-3 model
- Smart formatting and punctuation
- Confidence scoring
- Error handling

**Flow:**
```
1. Receive base64 audio + MIME type
2. Decode to binary
3. Send to Deepgram API
4. Extract transcript
5. Return text
```

---

## Database Structure

### MongoDB Collections

#### 1. users
```javascript
{
  _id: ObjectId,
  email: String (unique),
  password: String (hashed),
  name: String,
  role: String,
  created_at: Date,
  last_login: Date,
  phone: String,
  country: String,
  city: String,
  coffee_style: String,
  current_serving_capacity: Number
}
```

#### 2. chat_conversations (Outbound)
```javascript
{
  _id: ObjectId,
  session_id: String,
  conversation_id: String,
  chat_type: "outbound",
  messages: [
    {user: String, timestamp: Date},
    {bot: String, timestamp: Date}
  ],
  status: String,
  closed_reason: String,
  summarized: Boolean,
  data: {
    // Conversation state
    intent_stage: String,
    customer_type: String,
    is_qualified: Boolean,
    name: String,
    email: String,
    phone: String,
    // ... other fields
  },
  last_debug: Object,
  backend_logs: String,
  debug_events: Array,
  openai_key_suffix: String,
  created_at: Date,
  last_message_at: Date,
  ended_at: Date
}
```

#### 3. inbound_conversations (Inbound)
```javascript
{
  _id: ObjectId,
  session_id: String,
  conversation_id: String,
  user_id: String,
  chat_type: "inbound",
  messages: Array,
  status: String,
  data: {
    issue_summary: String,
    issue_details: String,
    issue_category: String,
    additional_issues: Array,
    ticket_mentioned: Boolean,
    create_ticket: Boolean,
    // ... other fields
  },
  created_at: Date,
  last_message_at: Date,
  ended_at: Date
}
```

#### 4. chatbot_leads
```javascript
{
  _id: ObjectId,
  user_name: String,
  mobile: String,
  email: String,
  lead_score: Number,
  summary: String,
  conversation_history: Array,
  qualification_data: Object,
  status: String,
  date: Date,
  created_at: Date
}
```

#### 5. crm_deals
```javascript
{
  _id: ObjectId,
  company_name: String,
  deal_value: Number,
  contact_person: String,
  email: String,
  mobile: String,
  summary: String,
  priority: String,
  status: String,
  meeting_notes: String,
  comments: String,
  source_conversation_id: String,
  created_at: Date,
  updated_at: Date
}
```

#### 6. api_logger
```javascript
{
  _id: ObjectId,
  timestamp: Date,
  api_key: String,
  api_params: Object,
  payload: Object,
  response_msg: String,
  usage_tokens: Object,
  model: String,
  tool_calls: Array,
  finish_reason: String,
  response_id: String
}
```

### Vector Store Files

#### FAISS Index
- Location: `backend/app/data/vector_db/faiss_index.bin`
- Format: Binary FAISS index
- Type: IndexFlatIP (Inner Product)
- Dimension: 384

#### Metadata
- Location: `backend/app/data/vector_db/metadata.json`
- Format: JSON array
- Structure:
```javascript
[
  {
    "chunk_text": String,
    "source_file": String,
    "category": String,
    "chunk_index": Number
  }
]
```

---

## API Endpoints

### Authentication (`/api/auth`)

**POST /api/auth/register**
- Register new user
- Body: email, password, name, phone, country, city, coffee_style, serving_capacity
- Returns: JWT token + user info

**POST /api/auth/login**
- Login with credentials
- Body: email, password
- Returns: JWT token + user info

**POST /api/auth/logout**
- Logout (client-side token deletion)
- Returns: Success message

**GET /api/auth/me**
- Get current user info
- Headers: Authorization: Bearer <token>
- Returns: User details

### Chat (`/api/chat`)

**POST /api/chat/outbound/message**
- Outbound chatbot message
- Body: session_id, message, country_code
- Returns: response, conversation_id, ended

**POST /api/chat/inbound/message**
- Inbound chatbot message (authenticated)
- Body: session_id, message, user_id
- Returns: response, conversation_id, ended

**POST /api/chat/transcribe**
- Transcribe audio to text
- Body: audio (base64), mime_type
- Returns: transcription

### CRM (`/api/crm`)

**GET /api/crm/leads**
- Get all chatbot leads (Admin only)
- Returns: Array of leads

**GET /api/crm/leads/{lead_id}**
- Get single lead (Admin only)
- Returns: Lead details

**DELETE /api/crm/leads/{lead_id}**
- Delete lead (Admin only)
- Returns: Success message

**GET /api/crm/deals**
- Get all CRM deals (Kanban format) (Admin only)
- Returns: Array of columns with deals

**POST /api/crm/deals**
- Create new deal (Admin only)
- Body: Deal data
- Returns: Deal ID

**PUT /api/crm/deals/{deal_id}**
- Update deal (Admin only)
- Body: Updated fields
- Returns: Success message

**PATCH /api/crm/deals/{deal_id}/stage**
- Update deal stage (Admin only)
- Body: status
- Returns: Success message

**DELETE /api/crm/deals/{deal_id}**
- Delete deal (Admin only)
- Returns: Success message

### HeyGen (`/api/heygen`)

**POST /api/heygen/token**
- Get HeyGen streaming token
- Returns: token, avatarId

### Health Check

**GET /api/health**
- Health check endpoint
- Returns: status, version, database, rag info

---

## Deployment & Infrastructure

### Docker Configuration

#### Multi-Stage Build

**Stage 1: Frontend Builder**
- Base: node:20-slim
- Install npm dependencies
- Build React app
- Output to backend/app/static

**Stage 2: Backend Builder**
- Base: python:3.11-slim
- Install build dependencies (gcc, g++)
- Install Python packages
- User-level pip install

**Stage 3: Runtime**
- Base: python:3.11-slim
- Install runtime dependencies only
- Copy Python packages from builder
- Copy backend code
- Copy built frontend
- Expose port 8000
- Run uvicorn

#### Docker Compose

**Services:**
- app: Main application container
- Environment variables from .env
- Volume mount for data persistence
- Health check endpoint
- Restart policy: unless-stopped

**Optional:**
- MongoDB service (if not using cloud)

### Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://...
MONGODB_DB_NAME=echobot

# OpenAI
OPENAI_API_KEY=sk-...

# Deepgram
DEEPGRAM_API_KEY=...

# HeyGen
HEYGEN_API_KEY=...
HEYGEN_AVATAR_ID=SilasHR_public

# JWT
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# App
DEBUG=false
FRONTEND_URL=http://localhost:8000

# Rate Limiting
RATE_LIMIT_GLOBAL=60/minute
```

### Cloud Run Deployment

**Configuration:**
- Port: Dynamic (from PORT env var)
- Health check: /api/health
- Auto-scaling based on traffic
- Environment variables from secrets
- Persistent volume for data directory

**Build Command:**
```bash
docker build -t echobot-api .
docker tag echobot-api gcr.io/PROJECT_ID/echobot-api
docker push gcr.io/PROJECT_ID/echobot-api
```

**Deploy Command:**
```bash
gcloud run deploy echobot-api \
  --image gcr.io/PROJECT_ID/echobot-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Security Considerations

1. **Authentication**
   - JWT tokens with expiration
   - Bcrypt password hashing
   - Admin role checks

2. **Rate Limiting**
   - SlowAPI middleware
   - 60 requests/minute default
   - Per-endpoint limits

3. **CORS**
   - Configured allowed origins
   - Credentials support
   - Method restrictions

4. **Input Validation**
   - Pydantic schemas
   - Email/phone validators
   - Sanitization

5. **API Keys**
   - Environment variables
   - Masked in logs
   - Rotation support

### Monitoring & Logging

**Logging:**
- Structured logging with logger utility
- API call logging to MongoDB
- Token usage tracking
- Error tracking with tracebacks

**Metrics:**
- Conversation counts
- Lead qualification rates
- API usage statistics
- Response times

---

## Development Workflow

### Local Setup

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Initialize RAG**
```bash
python scripts/init_rag.py
```

4. **Run Development Server**
```bash
uvicorn app.main:app --reload --port 8000
```

### Testing

**Manual Testing:**
- Use FastAPI docs: http://localhost:8000/docs
- Test endpoints with Swagger UI
- Monitor logs in console

**API Testing:**
- Postman collections
- cURL commands
- Python requests

### Code Organization Best Practices

1. **Separation of Concerns**
   - Routes: API endpoints only
   - Services: Business logic
   - Models: Data structures
   - Utils: Helper functions

2. **Async/Await**
   - All I/O operations async
   - Database queries async
   - LLM calls async

3. **Error Handling**
   - Try/except blocks
   - HTTPException for API errors
   - Logging for debugging

4. **State Management**
   - ConversationState class
   - Immutable updates
   - Serialization support

---

## Future Enhancements

### Planned Features
1. WebSocket support for real-time chat
2. Multi-language support
3. Advanced analytics dashboard
4. A/B testing framework
5. Conversation summarization
6. Automated lead scoring improvements
7. Integration with more CRM systems
8. Voice response generation (TTS)

### Scalability Improvements
1. Redis caching layer
2. Message queue (Celery/RabbitMQ)
3. Horizontal scaling with load balancer
4. Database sharding
5. CDN for static assets

---

## Conclusion

The Abbotsford AI Platform backend is a sophisticated AI-powered system that combines modern web technologies, advanced NLP, and intelligent conversation management to provide seamless customer interactions. The modular architecture ensures maintainability, scalability, and extensibility for future enhancements.

For questions or contributions, please refer to the project repository and documentation.

---

**Last Updated:** December 26, 2025
**Version:** 1.0.0
**Maintainer:** Development Team
