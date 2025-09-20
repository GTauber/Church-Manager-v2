# LangGraph Agent System

## Overview

Church Manager v4 leverages LangGraph to create a sophisticated agent-based system that processes natural language messages from WhatsApp users and executes appropriate actions.

## Core Concept

```mermaid
graph TD
    A[WhatsApp Message] -->|Input| B[Intent Classifier]
    B -->|Route| C{Intent Type}
    C -->|User Mgmt| D[User Agent]
    C -->|Scheduling| E[Schedule Agent]
    C -->|Ministry| F[Ministry Agent]
    C -->|Query| G[Query Agent]
    D --> H[Service Layer]
    E --> H
    F --> H
    G --> H
    H --> I[Response Generator]
    I -->|Plain Text| J[WhatsApp Reply]
```

## Agent Architecture

### State Management

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph

class ConversationState(TypedDict):
    messages: List[dict]          # Last 30 messages
    current_intent: str           # Identified intent
    entities: dict               # Extracted entities
    user_context: dict           # User session data
    response: str               # Generated response
```

### Memory System

The system maintains conversation memory to provide context-aware responses:

```mermaid
graph LR
    A[New Message] --> B[Memory Store]
    B --> C{Message Count}
    C -->|> 30| D[Remove Oldest]
    C -->|<= 30| E[Keep All]
    D --> F[Update Memory]
    E --> F
    F --> G[Context Window]
```

#### Memory Strategy
- **Capacity**: Last 30 messages per user
- **Priority**: Recent 2-3 messages have highest weight
- **Storage**: In-memory with Redis backup (future)
- **Retention**: Session-based with timeout

## Intent Recognition

### Intent Categories

```mermaid
mindmap
  root((Intents))
    User Management
      Create User
      Update Profile
      Check Availability
    Schedule Operations  
      Generate Schedule
      View Schedule
      Modify Schedule
    Ministry Management
      Create Ministry
      Assign Leader
      Add Members
    Volunteer Assignment
      Assign Role
      Remove Assignment
      Swap Volunteers
    Queries
      List Users
      Show Availability
      Ministry Members
```

### Intent Processing Pipeline

1. **Message Reception**
   ```python
   async def process_message(message: str, user_id: str):
       # Load conversation history
       history = await load_conversation(user_id)
       
       # Add new message
       history.append(message)
       
       # Extract intent and entities
       intent, entities = await classify_intent(message, history)
       
       # Route to appropriate agent
       result = await route_to_agent(intent, entities, history)
       
       # Generate response
       response = await format_response(result)
       
       return response
   ```

2. **Entity Extraction**
   - User names
   - Dates and date ranges
   - Ministry names
   - Role types
   - Time expressions (e.g., "next month", "all Sundays")

3. **Context Enhancement**
   - Previous conversation context
   - User preferences
   - Default values
   - Implicit references resolution

## Agent Workflows

### Schedule Generation Agent

```mermaid
stateDiagram-v2
    [*] --> ReceiveRequest
    ReceiveRequest --> ParseDateRange
    ParseDateRange --> ValidateMinistry
    ValidateMinistry --> GenerateOccurrences
    GenerateOccurrences --> CreateSchedule
    CreateSchedule --> NotifySuccess
    NotifySuccess --> [*]
    
    ValidateMinistry --> Error: Invalid Ministry
    GenerateOccurrences --> Error: Date Conflict
    Error --> [*]
```

### User Assignment Agent

```python
class AssignmentAgent:
    async def process(self, state: ConversationState):
        # Extract assignment details
        user = state.entities.get("user")
        date = state.entities.get("date")
        role = state.entities.get("role")
        
        # Validate user availability
        if not await check_availability(user, date):
            return "User not available on that date"
        
        # Check for conflicts
        conflicts = await check_conflicts(user, date)
        if conflicts:
            return f"User already assigned to {conflicts}"
        
        # Create assignment
        assignment = await create_assignment(user, date, role)
        
        return f"Successfully assigned {user} as {role} on {date}"
```

## Natural Language Understanding

### Pattern Recognition

Examples of understood patterns:

```yaml
Schedule Creation:
  - "Create schedule for December"
  - "Generate all Sunday services next month"
  - "Set up worship team for Christmas week"

User Assignment:
  - "Put John on sound this Sunday"
  - "Maria can do kids ministry on the 15th"
  - "Who's available for worship next week?"

Queries:
  - "Show me the schedule"
  - "Who's serving this Sunday?"
  - "List all worship team members"
```

### Contextual Understanding

The system understands context and pronouns:

```
User: "Create schedule for January"
Bot: "Created 4 Sunday services for January"
User: "Add João to the first one"  # "first one" understood as first Sunday
Bot: "João added to January 7th service"
```

## Response Generation

### Response Templates

Responses are generated based on action results:

```python
RESPONSE_TEMPLATES = {
    "schedule_created": "Created {count} {day} services for {month}",
    "user_assigned": "{user} assigned to {role} on {date}",
    "user_created": "New user {name} added successfully",
    "error": "Sorry, {error_message}. Please try again."
}
```

### Formatting Rules

- Keep responses concise
- Use natural language
- Include relevant details
- Confirm actions taken
- Suggest next steps when appropriate

## Error Handling

```mermaid
graph TD
    A[Error Occurs] --> B{Error Type}
    B -->|Validation| C[Return Helpful Message]
    B -->|Not Found| D[Suggest Alternatives]
    B -->|Conflict| E[Explain Conflict]
    B -->|System| F[Log and Retry]
    C --> G[User Response]
    D --> G
    E --> G
    F -->|Success| G
    F -->|Fail| H[Apologize and Log]
```

## Performance Optimization

### Strategies

1. **Parallel Processing**: Multiple agents can work simultaneously
2. **Caching**: Common queries cached for quick response
3. **Lazy Loading**: Load user context only when needed
4. **Batch Operations**: Group database operations

### Monitoring

Key metrics to track:
- Intent classification accuracy
- Response time per intent type
- Memory usage per user
- Error rates by agent

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Portuguese and English
2. **Voice Messages**: Process audio messages
3. **Proactive Notifications**: Remind users of assignments
4. **Learning System**: Improve intent recognition over time
5. **Advanced Queries**: Complex reporting and analytics

### Scalability Path

```mermaid
graph LR
    A[Current: In-Memory] --> B[Phase 1: Redis Cache]
    B --> C[Phase 2: Distributed Agents]
    C --> D[Phase 3: ML Model Training]
    D --> E[Phase 4: Multi-tenant]
```

## Integration with LangGraph

### Graph Definition

```python
from langgraph.graph import StateGraph, END

# Define the graph
workflow = StateGraph(ConversationState)

# Add nodes
workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("user_agent", user_agent_node)
workflow.add_node("schedule_agent", schedule_agent_node)
workflow.add_node("ministry_agent", ministry_agent_node)
workflow.add_node("query_agent", query_agent_node)
workflow.add_node("response_generator", response_generator_node)

# Add edges based on intent
workflow.add_conditional_edges(
    "classify_intent",
    route_by_intent,
    {
        "user": "user_agent",
        "schedule": "schedule_agent",
        "ministry": "ministry_agent",
        "query": "query_agent",
    }
)

# All agents lead to response generator
workflow.add_edge("user_agent", "response_generator")
workflow.add_edge("schedule_agent", "response_generator")
workflow.add_edge("ministry_agent", "response_generator")
workflow.add_edge("query_agent", "response_generator")

# Response generator ends the flow
workflow.add_edge("response_generator", END)

# Set entry point
workflow.set_entry_point("classify_intent")

# Compile
app = workflow.compile()
```

This architecture ensures clean separation of concerns, maintainable code, and scalable agent-based processing.