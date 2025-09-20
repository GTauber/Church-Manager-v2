# API Documentation

## Overview

Church Manager v4 exposes a single webhook endpoint that receives messages from WAHA (WhatsApp HTTP API) and returns plain text responses.

## Architecture Flow

```mermaid
sequenceDiagram
    participant U as WhatsApp User
    participant W as WhatsApp
    participant WAHA as WAHA Container
    participant API as FastAPI Webhook
    participant LG as LangGraph Agents
    participant DB as PostgreSQL

    U->>W: Send message
    W->>WAHA: Receive message
    WAHA->>API: POST /webhook
    API->>LG: Process intent
    LG->>DB: Execute operations
    DB-->>LG: Return results
    LG-->>API: Generate response
    API-->>WAHA: Plain text response
    WAHA-->>W: Send reply
    W-->>U: Display message
```

## Webhook Endpoint

### POST /webhook

Receives WhatsApp messages via WAHA and processes them through LangGraph agents.

**Endpoint:** `/webhook`  
**Method:** `POST`  
**Content-Type:** `application/json`