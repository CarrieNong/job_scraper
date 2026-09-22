# Job Matching Criteria

## ⚠️ CRITICAL: Hard Requirements (Immediate Disqualification)

**FIRST CHECK THESE - If ANY hard requirement is not met, assign match score ≤ 3 immediately and stop evaluation.**

### 1. Language Requirements - MANDATORY CHECK
- ✅ **Must Have**: English (required)
- ✅ **Native**: Chinese

- ❌ **DISQUALIFY if**: The JD **explicitly states** German language as a **job requirement** (not just JD written in German)
  
  **IMPORTANT DISTINCTION**:
  - ❌ **DO NOT** disqualify just because the JD is written in German language
  - ✅ **ONLY** disqualify if German is explicitly listed in the requirements/qualifications section
  
  **DISQUALIFY if ANY of these appear anywhere in the job description**:
  
  *Explicit requirement keywords:*
  - "German required" / "Deutsch erforderlich" / "Deutsch ist erforderlich"
  - "Deutschkenntnisse erforderlich" / "German skills required"
  - "German mandatory" / "Deutsch zwingend erforderlich"
  - "Deutsch ist Voraussetzung" / "German is a must"
  - "Sehr gute Deutschkenntnisse erforderlich"
  
  *Language level declarations (these always mean German IS required):*
  - "Deutsch - Fließend" / "Deutsch - Verhandlungssicher" / "Deutsch - Konversationssicher"
  - "Deutsch - Grundkenntnisse" / "Deutsch - Muttersprache"
  - "Sprachanforderungen" / "Sprachanforderung" (= language requirements section header)
  - "Fluent German" / "Fließend Deutsch" / "Fließende Deutschkenntnisse"
  - "German C1" / "German C2" / "German B2" / "Deutsch (C1)" / "Deutsch (C2)" / "Deutsch (B2)"
  - "Native German" / "Muttersprache Deutsch" / "Deutsch auf Muttersprachniveau"
  
  *General proficiency requirements:*
  - "Gute Deutschkenntnisse" / "Gutes Deutsch" / "Sehr gute Deutschkenntnisse"
  - "Deutschkenntnisse" (when in requirements/Anforderungen/Qualifikationen section)
  - "Deutsch in Wort und Schrift"
  
  **DO NOT disqualify if**:
  - JD is written in German but none of the above signals appear
  - German is explicitly "nice to have" / "von Vorteil" / "wünschenswert"
  - German appears only in company description, not in job requirements

### 2. Backend Language Requirements - MANDATORY CHECK
**ONLY IF** the JD explicitly lists a backend language as **"required"** or **"mandatory"**:
- ✅ **Full Match**: Node.js (Express.js, Nest.js, Fastify, Koa, etc.)
- ❌ **DISQUALIFY if** ANY other backend language is explicitly required:
  - Python (Django, Flask, FastAPI)
  - Java (Spring Boot, Jakarta EE)
  - Go, PHP, Ruby, C#, .NET, Scala, Rust, Kotlin, etc.

**DO NOT DISQUALIFY if**:
- No backend language requirement mentioned
- Backend listed as "nice to have" or "plus"
- Frontend-focused role with backend as optional

### 3. DevOps/Operations Requirements - MANDATORY CHECK
❌ **DISQUALIFY if**:
- Job title includes "DevOps", "SRE", or "Infrastructure"
- JD explicitly requires "DevOps experience required", "SRE experience mandatory"
- Heavy infrastructure/operations listed as core responsibility (>50% of job)

✅ **Proceed if**:
- DevOps/SRE listed as "nice to have" or "plus"
- Basic CI/CD, Docker, Git mentioned (these are acceptable)
- No explicit DevOps requirement

---

## Evaluation Process (Only if Hard Requirements Passed)

### STEP 1: Evaluate REQUIRED/MANDATORY Skills Only
**Only evaluate skills explicitly marked as "required", "mandatory", or "must have" in JD.**

---

## Technical Stack Matching

### Frontend Frameworks (High Priority) ✅
**Core Competencies**: React, Angular, Vue (7 years experience)

- **Full Match**: If JD requires ANY of these:
  - **React ecosystem**: React, Next.js, Redux, React Query, Zustand, React Router, etc.
  - **Vue ecosystem**: Vue, Nuxt.js, Vuex, Pinia, Vue Router, etc.
  - **Angular ecosystem**: Angular, RxJS, NgRx, Angular Material, etc.
  - **Shared tools**: TypeScript, JavaScript, Tailwind CSS, CSS-in-JS, Webpack, Vite, etc.

### Backend Experience Level ✅
**Actual Experience**: 1 year of full-stack/backend with Node.js

- **Match Requirements**:
  - ✅ If backend requires: "1-2 years" or no specific years mentioned
  - ⚠️ Moderate penalty if requires: "3+ years backend experience"
  - ❌ Low match if requires: "5+ years backend" or "Senior backend developer"

### Other Technology Stack
**Resume Skills**: MongoDB, Git, Webpack, Vite, Sentry, Jest, Cypress, Playwright, AI tools

- **ONLY penalize** if JD explicitly requires as "mandatory":
  - Specialized databases: Oracle, SQL Server, DB2 (not on resume)
  - Specialized frameworks: Hadoop, Spark, Kafka (not on resume)
  - Niche technologies outside web development

- **Do NOT penalize** if:
  - Listed as "nice to have" or "bonus"
  - Related to existing skills (e.g., PostgreSQL is related to MongoDB)
  - Common web dev tools (e.g., Redis, GraphQL)

---

## Experience Level & Role Matching

### Total Experience ✅
- **7 years** frontend engineering experience
- **1 year** full-stack development experience
- Previous: B2B SaaS, B2C e-commerce, startup environments

### Position Level Match:
- **High Match (8-10)**: Junior to Senior Frontend Developer, Full-Stack Developer (Frontend-focused)
- **Medium Match (5-7)**: Senior Full-Stack Developer (if backend is Node.js or not emphasized)
- **Low Match (≤4)**: 
  - Staff/Principal Engineer requiring 10+ years
  - Backend-focused positions (>70% backend work)
  - Positions requiring 5+ years in specific backend technologies

---

## Business Domain & Project Type Matching

### Strong Domain Experience ✅
**Boost match score** if JD mentions:
- **E-commerce**: Online shopping, retail, marketplace, product catalog
- **SaaS**: B2B platforms, subscription services
- **Consumer-facing (C端)**: User applications, customer portals
- **Admin systems (B端)**: Management dashboards, internal tools
- **Food compliance/regulatory**: Food industry, compliance systems

### Relevant Project Experience:
- User experience optimization
- Complex form handling and validation
- Multi-user role and permission systems
- Product management interfaces
- High-traffic applications (3M+ daily views)

---

## "Nice to Have" Skills Evaluation

**CRITICAL**: "Nice to have" / "Plus" / "Bonus" / "Preferred" skills should:
- ✅ **Add small bonus (+0.5 to +1.5 points)** if candidate HAS the skill
- ➖ **Add ZERO penalty** if candidate DOES NOT have the skill
- **Do NOT reduce base match score** for missing nice-to-have skills

### Examples of Nice to Have (No Penalty if Missing):
- Additional programming languages
- DevOps tools (if not required)
- Cloud certifications
- Specific testing frameworks beyond Jest/Cypress
- Design tools (Figma, Sketch)
- Project management tools
- Domain knowledge outside core experience

---

## Scoring Instructions for AI

### STEP 1: Hard Requirements Check (DISQUALIFY = Score ≤ 3)
1. ❌ German required/mandatory? → DISQUALIFY
2. ❌ Non-Node.js backend required? → DISQUALIFY  
3. ❌ DevOps/SRE required as core role? → DISQUALIFY

**If any hard requirement fails, assign score ≤ 3 and provide clear reason.**

---

### STEP 2: Required Skills Match (Base Score: 4-8)
Evaluate ONLY "required" or "mandatory" skills:

**Scoring Rubric**:
- **8 points**: 90%+ required skills match
  - Frontend framework matches perfectly
  - Experience level matches
  - All required tech stack present or highly related
  
- **7 points**: 70-89% required skills match
  - Frontend matches, minor gaps in secondary skills
  - Experience slightly below requirement (e.g., 1yr vs 2yr backend)
  
- **6 points**: 50-69% required skills match
  - Frontend matches but significant secondary gaps
  - Experience level somewhat below requirement
  
- **5 points**: 40-49% required skills match
- **4 points**: 30-39% required skills match

---

### STEP 3: Nice to Have Bonus (+0 to +2)
**ONLY ADD** points for nice-to-have skills candidate HAS:
- +0.5 points: Has 1-2 nice-to-have skills
- +1.0 points: Has 3-4 nice-to-have skills
- +1.5 points: Has 5+ nice-to-have skills
- +2.0 points: Has most/all nice-to-have skills

**NEVER SUBTRACT** points for missing nice-to-have skills.

---

### STEP 4: Domain/Business Fit Bonus (+0 to +1)
- +1.0: Perfect domain match (e-commerce, SaaS, food compliance)
- +0.5: Related domain match
- +0: Neutral/unrelated domain

---

### Final Score Range:
- **0-3**: Disqualified (hard requirements not met)
- **4-6**: Weak match (many required skills missing)
- **7-8**: Good match (most required skills present)
- **9-10**: Excellent match (all required + many nice-to-have)

---

## Red Flags (Automatic Low Match)

- ❌ German language mandatory (any form: Sprachanforderungen, Gutes Deutsch, Deutsch - Fließend/C1/C2, etc.)
- ❌ Backend-heavy roles (>70% backend) with non-Node.js stack
- ❌ Non-Node.js backend explicitly required as mandatory
- ❌ 5+ years backend experience explicitly required
- ❌ Heavy DevOps/infrastructure as core responsibility
- ❌ Enterprise legacy tech stacks explicitly required (Oracle, SAP, Mainframe)
- ❌ Highly specialized niche technologies required (Hadoop, Spark, specialized systems)
- ❌ Staff/Principal level requiring 10+ years experience

---

## Strong Fit Indicators (Boost Score)

- ✅ Frontend-focused or frontend-heavy (>60%) full-stack roles
- ✅ Modern JavaScript/TypeScript stack (React/Vue/Angular)
- ✅ Node.js backend (if backend required)
- ✅ Component library or design system work
- ✅ Performance optimization focus
- ✅ E-commerce or SaaS products
- ✅ Consumer-facing applications or admin dashboards
- ✅ AI-assisted development mentioned
- ✅ English + remote work options
- ✅ Startup or scale-up environment

---

## Summary for AI Matcher

**Evaluation Order**:
1. **Hard Requirements Check First** → Fail any = Score ≤ 3
2. **Required Skills Match** → Calculate base score (4-8)
3. **Nice to Have Bonus** → Add bonus ONLY for skills present (0-2)
4. **Domain Fit Bonus** → Add bonus for domain match (0-1)
5. **Final Score** → Sum all components (max 10)

**Key Principles**:
- Be STRICT on hard requirements (German, backend language, DevOps)
- Focus on REQUIRED skills only for base scoring
- NEVER penalize missing "nice to have" skills
- DO reward having "nice to have" skills with modest bonus
- Prioritize frontend-focused roles
- Consider overall role balance (frontend vs backend split)
