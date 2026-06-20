# Vidya AI Architecture

## Overview

Vidya AI implements a **multi-agent orchestration pattern** using Google ADK and Gemini.

```mermaid
graph TD
    User([User]) --> |Streamlit UI| Frontend
    Frontend --> |Query| Router[Router Agent]
    
    subgraph Memory Layer
        MM[(Memory Manager)]
    end
    
    subgraph Reasoning Layer
        Router --> |classify_intent| Gemini[Gemini Service]
        Gemini -.-> |Single Intent| SubAgents
        Gemini -.-> |Multi Intent| Planner[Planner Agent]
        
        Planner --> |Orchestrate| SubAgents
        
        subgraph SubAgents
            Career[Career Agent]
            College[College Agent]
            Schol[Scholarship Agent]
            Skill[Skill Gap Agent]
            Road[Roadmap Agent]
        end
    end
    
    subgraph Skills Layer
        Career --> S1[CareerAdviceSkill]
        College --> S2[CollegeRecSkill]
        Schol --> S3[ScholarshipFinderSkill]
        Skill --> S4[SkillGapSkill]
        Road --> S5[RoadmapGenSkill]
    end
    
    subgraph MCP Server
        S1 --> M1[career_lookup]
        S2 --> M2[college_lookup]
        S3 --> M3[scholarship_lookup]
        S4 --> M4[skill_lookup]
        S5 --> M5[roadmap_generator]
        
        M1 & M2 & M3 & M4 & M5 --> DataLoader
    end
    
    subgraph Data Layer
        DataLoader --> LocalJSON[(Local JSON Files)]
    end
    
    %% Connections
    Router -.-> MM
    Planner -.-> MM
    SubAgents -.-> MM
```

## Key Components

1. **Router Agent**: Gating mechanism. Performs language translation, input sanitization, and intent classification via Gemini structured output. Routes simple queries directly to a sub-agent, and complex queries to the Planner.
2. **Planner Agent**: For queries with multiple intents (e.g. "I want to be an AI Engineer and need scholarships"), it generates an execution plan, runs agents sequentially, and uses Gemini to synthesize a single coherent response.
3. **ADK Skills**: Decouples business logic from agents. Skills handle data fetching and formatting.
4. **MCP Server**: A FastAPI server that exposes both local JSON data tools and dynamic Gemini-powered tools (Google Custom Search integration).
5. **Memory Manager**: A thread-safe, file-based persistence layer storing student profiles (interests, marks, language preference) and conversation history. Works seamlessly across Streamlit's execution model.
