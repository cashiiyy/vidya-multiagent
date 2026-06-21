# Vidya AI: Bridging the Education Gap
## A Multi-Agent Career & Education Mentor for Indian Students

**Track**: AI for Good

### 1. Introduction & The Problem Space
In India, millions of students face a critical lack of access to personalized career and educational counseling. Navigating the complex landscape of higher education, understanding the nuances of emerging career paths, discovering relevant scholarships before their deadlines, and analyzing skill gaps are daunting tasks. For many, language barriers further restrict access to crucial information.

Vidya AI addresses these pervasive issues head-on. It is a production-ready, multi-agent AI system specifically architected to democratize career counseling. Designed as a bilingual mentor (English and Malayalam), Vidya AI ensures that socio-economic status or linguistic background does not hinder a student's potential.

### 2. Detailed Analysis of the Submission

#### 2.1 Solution Architecture
Vidya AI leverages a decoupled, robust architecture built upon state-of-the-art AI standards:
- **Google Agent Development Kit (ADK)**: The core of the system is orchestrated by a network of 7 specialized AI agents, capable of complex reasoning and task delegation.
- **Model Context Protocol (MCP)**: A FastAPI server exposes 9 standardized tools (including 5 local data tools and 4 Gemini-powered grounding tools), allowing the agents to interact safely with external data sources.
- **Stateful Memory Management**: Thread-safe JSON persistence is implemented to maintain student profiles and conversation histories, allowing for a continuous and deeply personalized mentoring experience across sessions.
- **Security & Safety**: The system incorporates strict security middleware to prevent prompt injections, validate payloads, and enforce Gemini safety settings, ensuring a secure environment for students.

#### 2.2 The Multi-Agent Ecosystem
The system breaks down the complex problem of educational counseling into specialized tasks, handled by distinct agents:
1. **Router Agent**: The secure gateway that translates Malayalam to English, extracts key entities, and routes queries to the appropriate specialist.
2. **Planner Agent**: Orchestrates multi-intent queries, breaking them down into sequential tasks for other sub-agents.
3. **Career Agent**: Maps a student's unique interests and aptitude to viable careers, utilizing real-world salary and demand data.
4. **College Agent**: Recommends institutions based on complex constraints like geographic location, required courses, academic marks, and financial capacity.
5. **Scholarship Agent**: Acts as an equalizer by finding government and private scholarships, sorting them strictly by application deadlines.
6. **Skill Gap Agent**: Provides a reality check by analyzing a student's current skill set against the requirements of their target career.
7. **Roadmap Agent**: Synthesizes the findings into a highly personalized, month-by-month actionable learning plan.

#### 2.3 Impact & AI for Good
The "AI for Good" track emphasizes technology that creates positive societal impact. Vidya AI embodies this by:
- **Democratizing Knowledge**: Providing tier-1 quality career counseling to students in tier-2 and tier-3 cities who would otherwise lack access.
- **Promoting Inclusivity**: The bilingual capability (starting with Malayalam and English) ensures that language is not a barrier to accessing life-changing information.
- **Actionable Guidance**: Rather than generic advice, Vidya AI provides concrete steps, scholarship deadlines, and skill roadmaps, directly empowering students to take charge of their future.

### 3. Media Gallery

*Please find the associated visual materials for this submission below.*

**Cover Image:**
![Vidya AI Cover](C:\Users\Kasinathan P S\.gemini\antigravity-ide\brain\72337f06-de03-46fc-881d-5d958139ec85\vidya_ai_cover_1782045629623.png)
*A sleek, modern glassmorphic representation of an AI-powered education and career mentoring platform.*

**Video Demonstration:**
*(Please insert the required submission video here)*

---
*Built for the Kaggle AI Agents Intensive Vibe Coding Capstone.*
