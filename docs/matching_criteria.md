# Job Matching Criteria

## Language Requirements

### Mandatory Languages
- **English**: Required
- **Chinese**: Native speaker

### Language Exclusions
- **German**: If German is listed as a **mandatory/required** language skill, mark as low match
- If German is listed as "nice to have" or "preferred", it does not affect the match score

---

## Technical Stack Matching

### Frontend Frameworks (High Priority)
**Core Competencies**: React, Angular, Vue
- All three mainstream frontend frameworks and their common ecosystems should be considered a **full match**
- Include related ecosystems:
  - **React ecosystem**: Next.js, Redux, React Query, Zustand, React Router, etc.
  - **Vue ecosystem**: Nuxt.js, Vuex, Pinia, Vue Router, etc.
  - **Angular ecosystem**: RxJS, NgRx, Angular Material, etc.
  - **Shared tools**: TypeScript, JavaScript, Tailwind CSS, CSS-in-JS, Webpack, Vite, etc.

### Backend Requirements (Conditional Filter)
**Primary Backend Language**: Node.js only

**Important**: Only evaluate backend language match if the job description **explicitly requires** a specific backend language/technology.

- **Full Match**: 
  - Job requires Node.js with any framework (Express.js, Nest.js, Fastify, Koa, Hapi, etc.)
  - Job does NOT mention specific backend language requirements
  - Frontend-focused role with backend as "nice to have"

- **Low Match**: Jobs that **explicitly require** other backend languages as mandatory:
  - Python (Django, Flask, FastAPI)
  - Java (Spring Boot, Jakarta EE)
  - Go (Gin, Echo)
  - Ruby (Rails, Sinatra)
  - PHP (Laravel, Symfony)
  - C# (.NET, ASP.NET)
  - Scala, Rust, Kotlin, etc.

**Do NOT Penalize** if:
- No specific backend language mentioned in requirements
- Backend technologies listed as "nice to have", "plus", or "bonus"
- Job description mentions backend only for collaboration/understanding purposes
- Frontend-focused role where backend is secondary

### Backend Experience Level
**Actual Experience**: 1 year of full-stack/backend development

- **Low Match**: If job explicitly requires:
  - "3+ years backend experience" or higher
  - "Senior backend developer"
  - "Backend tech lead"
  
- **Good Match**: If job requires:
  - "1-2 years backend experience"
  - "Junior to mid-level backend experience"
  - Backend skills listed but no specific years mentioned

---

## DevOps & Operations Experience

**Actual Experience**: Limited DevOps experience

### Scoring Rules:
- **Do NOT factor into match calculation** if:
  - Listed as "nice to have"
  - Listed as "plus" or "bonus"
  - No explicit requirement mentioned
  
- **Reduce match score** only if:
  - DevOps/SRE is explicitly listed as "required" or "mandatory"
  - Job title includes "DevOps" or "SRE"
  - Job description emphasizes infrastructure/operations as core responsibility

### Acceptable DevOps Tools (No Penalty):
- Basic CI/CD: GitHub Actions, GitLab CI, Jenkins
- Cloud basics: AWS, GCP, Azure (basic deployment)
- Containerization basics: Docker
- Version control: Git

### Limited Experience (Penalty if Required):
- Kubernetes, container orchestration
- Infrastructure as Code: Terraform, CloudFormation, Ansible
- Monitoring/Observability: Prometheus, Grafana, DataDog
- Advanced cloud architecture and scaling

---

## Technology Stack Requirements

### Mandatory Technology Filtering
**Important**: If a JD explicitly requires technologies that are:
- **NOT** on the resume/profile
- **NOT** related to existing skill set
- Listed as "required" or "mandatory" (not "nice to have")

Then **reduce the match score**.

**Examples of Unrelated Tech Stack (Penalty if Required)**:
- Specialized databases: Oracle, SQL Server, DB2 (if not on resume)
- Specialized frameworks: Hadoop, Spark, Kafka (if not on resume)
- Specialized languages: Rust, Scala, Elixir (if not on resume)
- Niche technologies outside web development domain

**Do NOT Penalize** if:
- Technologies are listed as "nice to have" or "bonus"
- Technologies are related to existing skills (e.g., React developer learning Next.js)
- Technologies are commonly used alongside existing stack (e.g., TypeScript with React)

---

## Business Domain & Project Type Match

### Previous Work Experience
**Project Types**:
- **C端 (Consumer-facing)**: User-side applications, customer portals
- **B端 (Business-facing)**: Internal management systems, admin dashboards
- **SaaS Systems**: Software as a Service platforms

**Business Domains**:
- **E-commerce**: Online shopping platforms, retail systems
- **Food Compliance**: Food regulation verification, compliance systems

### Matching Rules:
- **Boost Match Score** if JD mentions:
  - E-commerce, online shopping, retail, marketplace
  - SaaS products, B2B platforms, B2C applications
  - Consumer-facing web applications
  - Internal management systems, admin tools, dashboards
  - Food industry, compliance, regulatory systems
  - Similar business domains (e.g., subscription services, product catalogs)

- **Consider Relevant Experience** for:
  - User experience optimization
  - Complex form handling and data validation
  - Multi-user role and permission systems
  - Product management interfaces
  - Compliance and regulatory workflows

---

## Experience Level Guidelines

### Total Experience
- **7 years** total frontend engineering experience
- **1 year** full-stack development experience
- Previous experience in B2B SaaS, B2C e-commerce, startup environments

### Position Level Match:
- **High Match**: Junior to Senior Frontend Developer, Full-Stack Developer (Frontend-focused)
- **Medium Match**: Senior Full-Stack Developer (if backend is Node.js)
- **Low Match**: 
  - Staff/Principal Engineer requiring 10+ years
  - Backend-focused positions
  - DevOps/SRE positions
  - Positions requiring 5+ years in specific backend technologies

---

## Additional Context

### Strong Fit Indicators:
- Frontend-focused or frontend-heavy full-stack roles
- Modern JavaScript/TypeScript stack
- Component library or design system work
- Performance optimization projects
- **E-commerce or SaaS products** (matches business domain experience)
- **Consumer-facing applications** (C端经验匹配)
- **Internal management systems or admin dashboards** (B端经验匹配)
- **Food industry, compliance, or regulatory systems** (业务领域匹配)
- Online shopping, retail, marketplace platforms
- AI-assisted development mentioned

### Red Flags (Low Match):
- Backend-heavy roles (>70% backend work)
- Non-Node.js backend **explicitly required** as mandatory skill
- **Mandatory required technologies that are not on resume and unrelated to skill set**
- German language mandatory
- 3+ years backend experience required
- Heavy DevOps/infrastructure focus
- Enterprise Java, .NET, or legacy tech stacks **explicitly required**
- Specialized niche technologies explicitly required (e.g., Hadoop, Spark, Oracle)

---

## Matching Score Weights

Suggested scoring weights for the AI matcher:

1. **Backend Language Match** (25%): 
   - Only evaluate if backend language is explicitly required
   - Node.js = full score
   - No backend requirement specified = full score (no penalty)
   - Other backend languages explicitly required = low score
2. **Frontend Framework Match** (20%): React/Vue/Angular and ecosystems
3. **Language Requirements** (20%): English + Chinese OK, German mandatory = exclude
4. **Technology Stack Requirements** (15%): Penalty for mandatory unrelated tech stack
5. **Experience Level Match** (10%): 7 years frontend, 1 year backend
6. **Business Domain & Project Type** (10%): Boost for e-commerce, SaaS, food compliance experience
7. **Role Focus** (5%): Frontend-focused or balanced full-stack
8. **DevOps Requirements** (0% unless mandatory): Only penalize if explicitly required

---

## Notes for AI Matcher

- Prioritize frontend-focused roles even if they mention backend technologies
- Be lenient with "nice to have" requirements
- **Backend language filtering**: Only penalize if a specific backend language is explicitly required AND it's not Node.js
- **No backend requirement = no penalty**: If JD doesn't mention backend language requirements, treat as full match
- **Unrelated tech stack penalty**: Only penalize if technologies are explicitly required AND not on resume AND not related to existing skills
- **Business domain boost**: Increase match score for e-commerce, SaaS, food compliance, C端/B端 applications
- Strict filtering on mandatory German language requirement
- Consider the overall role balance: a full-stack role requiring 80% frontend work is still a good match
- **Project type relevance**: Look for keywords like "user-facing", "admin dashboard", "management system", "online shopping", "marketplace", "SaaS platform"
