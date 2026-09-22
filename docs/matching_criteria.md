# Job Matching Criteria

## ⚠️ CRITICAL: Hard Requirements (Immediate Disqualification)

**FIRST CHECK THESE - If ANY hard requirement is not met, assign match score ≤ 3 immediately and stop evaluation.**

### 1. Language Requirements - MANDATORY CHECK
- ✅ **Must Have**: English (required)
- ✅ **Native**: Chinese
- Candidate does **not** speak German.

German-language postings are already filtered out before matching. Do **not** re-filter based on the JD being (or looking) German, and do **not** use keyword lists.

**DISQUALIFY** only if the JD **explicitly states** that German is a mandatory job-language requirement (must-have / required / fluent / native / C1 for the role). An English JD can still do this in writing — only then disqualify.

**NEVER infer German from location or office.** These are **not** language requirements and must PASS:
- Location fields such as "Berlin, Germany (On-site)", "Germany (Hybrid)", "DACH"
- "Berlin office", "in-person culture in Berlin", "office in Germany", public-transport / gym perks
- Company being German, European, or based in Berlin / Munich / Hamburg
- The JD being about a German/European market or German customers/brands

**DO NOT disqualify if**:
- German is "nice to have" / "plus" / "advantage" / "preferred"
- German appears only in the company description, not as a job requirement
- German is never mentioned as a language skill at all

Do **not** invent "Fluency in German" (or similar) as a requirement if the JD never asked for it.

### 2. Backend Language Requirements - MANDATORY CHECK
Candidate backend:
- ✅ **Strong**: Node.js ecosystem (Express.js, Nest.js, Fastify, Koa, etc.)
- ⚠️ **Light**: a little Python — **not** enough for a Python-primary backend role
- ❌ **Does not know**: Java, Go, PHP, Ruby, C#, .NET, Scala, Rust, Kotlin, etc.

**DISQUALIFY** if a backend language the candidate cannot do is a **hard/mandatory** requirement, including:
- Python / Django / Flask / FastAPI as the required backend
- Java / Spring, Go, PHP, Ruby, C#, .NET, or similar as the required backend

**DO NOT DISQUALIFY if**:
- No backend language is required
- Backend is "nice to have" / "plus"
- Frontend-focused role with optional backend
- Required backend is Node.js
- Python is only mentioned as nice-to-have

### 3. Years of Experience - MANDATORY CHECK
Candidate:
- **7 years** professional frontend / software engineering
- **1 year** full-stack / backend (Node.js)

**DISQUALIFY** if a **must-have** requirement asks for more years than the candidate has in that dimension:
- Overall / frontend / software experience required **> 7 years**
- Backend-specific experience required **> 1 year** (a range that includes 1, e.g. "1-2 years", PASSES)

Do **not** disqualify on the title "Senior" alone if the stated year requirement is within range.
Nice-to-have year requirements do not disqualify.

### 4. DevOps/Operations Requirements - MANDATORY CHECK
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
**Core Competencies**: React, Angular, Vue (7 years experience); strong vanilla JavaScript / ES6+ foundation throughout.

- **Full Match**: If JD requires ANY of these:
  - **React ecosystem**: React, Next.js, Redux, React Query, Zustand, React Router, etc.
  - **Vue ecosystem**: Vue, Nuxt.js, Vuex, Pinia, Vue Router, etc.
  - **Angular ecosystem**: Angular, RxJS, NgRx, Angular Material, etc.
  - **Shared tools**: TypeScript, JavaScript, Tailwind CSS, CSS-in-JS, Webpack, Vite, etc.
  - **Vanilla / framework-agnostic JS roles**: If the JD primarily requires JavaScript/ES6+ skills (vanilla JS, DOM manipulation, browser APIs) rather than a specific proprietary framework, treat this as a FULL match — the candidate has 7 years of JavaScript development including vanilla JS.

- **Partial Match (treat as Good Match, ~7 points base)**: If JD uses a less common or legacy frontend framework (CanJS, Backbone, Ember, Knockout, Mootools, etc.) but:
  - Also lists React, Angular, Vue, or similar as reference keywords or "similar technologies", OR
  - The primary requirement is strong JavaScript / frontend engineering skill (framework is secondary / learnable)
  → Do NOT disqualify or heavily penalize. The candidate's 7 years of React/Vue/Angular + vanilla JS demonstrates framework-agnostic frontend engineering ability. These frameworks share the same JS foundations and are learnable. Score based on how well other requirements (JS depth, Node.js, CSS, architecture, etc.) match — framework gap is at most a minor deduction (-0.5 to -1 point), not a disqualifier.

- **Note on build tools**: Grunt/Gulp experience is NOT required — but the candidate's Webpack/Vite/npm-scripts experience covers the same responsibility (frontend build tooling). Do NOT penalize for Grunt/Gulp mismatch; treat as equivalent skill.

### Backend Experience Level ✅
**Actual Experience**: 1 year of full-stack/backend with Node.js

- **Match Requirements**:
  - ✅ If backend requires: "1 year", "1-2 years", or no specific years mentioned
  - ❌ DISQUALIFY if a must-have asks for more than 1 year of backend experience
  - ❌ DISQUALIFY if overall/frontend must-have years > 7

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
- **High Match (8-10)**: Junior to Senior Frontend Developer, Full-Stack Developer (Frontend-focused), JavaScript Developer (vanilla JS / framework-agnostic)
- **Medium Match (5-7)**: Senior Full-Stack Developer (if backend is Node.js or not emphasized), Frontend roles using legacy/niche frameworks where JS fundamentals are the core requirement
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
1. ❌ German is an **explicitly written** mandatory job-language requirement? → DISQUALIFY. Location/office in Germany or Berlin is NOT enough.
2. ❌ Hard-required backend language is not Node.js (Python-primary, Java, Go, etc.)? → DISQUALIFY
3. ❌ Must-have years of experience exceed candidate years (7 frontend / 1 backend)? → DISQUALIFY
4. ❌ DevOps/SRE required as core role? → DISQUALIFY

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
  
- **6 points**: 50-69% required skills match
  - Frontend matches but significant secondary gaps
  
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

- ❌ German language **explicitly** mandatory in the JD (nice-to-have German is OK; Berlin/Germany location alone is NOT a red flag)
- ❌ Backend-heavy roles (>70% backend) with non-Node.js stack
- ❌ Non-Node.js backend explicitly required as mandatory (including Python-primary)
- ❌ Must-have years exceed candidate years (7 frontend / 1 backend)
- ❌ 5+ years backend experience explicitly required
- ❌ Heavy DevOps/infrastructure as core responsibility
- ❌ Enterprise legacy tech stacks explicitly required (Oracle, SAP, Mainframe)
- ❌ Highly specialized niche technologies required (Hadoop, Spark, specialized systems)
- ❌ Staff/Principal level requiring 10+ years experience

---

## Strong Fit Indicators (Boost Score)

- ✅ Frontend-focused or frontend-heavy (>60%) full-stack roles
- ✅ Modern JavaScript/TypeScript stack (React/Vue/Angular)
- ✅ Vanilla JS / framework-agnostic JavaScript developer roles (candidate has 7 years of JS)
- ✅ Roles where primary skill is "strong JavaScript" even if framework is niche/legacy (CanJS, Backbone, etc.)
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
- Be STRICT on hard requirements (explicit mandatory German only — never infer from Berlin/Germany location, backend language, years of experience, DevOps)
- Focus on REQUIRED skills only for base scoring
- NEVER penalize missing "nice to have" skills
- DO reward having "nice to have" skills with modest bonus
- Prioritize frontend-focused roles
- Consider overall role balance (frontend vs backend split)
