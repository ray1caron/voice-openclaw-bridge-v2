# Creating GitHub Project via Web UI

Since the GraphQL API is complex, here's the fastest way to set up the project board:

## Step 1: Create Project

1. Go to: https://github.com/ray1caron/voice-openclaw-bridge-v2/projects
2. Click **"New project"**
3. Select **"Board"** template
4. Name: **"Voice Bridge v2 Development"**
5. Description: "Sprint-based development tracking"
6. Click **Create**

## Step 2: Add Columns

Once created, rename default columns or add these:

**Columns (left to right):**
1. 📋 **Backlog** (for unscheduled items)
2. 🔄 **Sprint 1 (Foundation)** 
3. 🔄 **Sprint 2 (Tools)**
4. 🔄 **Sprint 3 (Memory)**
5. 🔄 **Sprint 4 (Polish)**
6. ✅ **Done** (default)

## Step 3: Add Custom Fields

Click **Settings** (gear icon) → **Custom fields** → **+ New field**

**Field 1: Priority**
- Type: Single select
- Options: P0 (red), P1 (yellow), P2 (green)

**Field 2: Sprint**
- Type: Single select  
- Options: Sprint 1, Sprint 2, Sprint 3, Sprint 4, Backlog

**Field 3: Component**
- Type: Single select
- Options: bridge, audio, stt, tts, wake, openclaw, docs

**Field 4: Estimated Hours**
- Type: Number

## Step 4: Create Views

**View 1: Sprint Board (default)**
- Group by: Status
- Columns as above

**View 2: By Priority**
- Click **+ New view**
- Name: "By Priority"
- Group by: Priority

**View 3: By Component**
- Click **+ New view**  
- Name: "By Component"
- Group by: Component

## Step 5: Add Issues

Create these starter issues (assign to Sprint 1):

1. **WebSocket Client Implementation** (P0, component: bridge)
2. **Response Filtering Engine** (P0, component: bridge)
3. **Audio Pipeline Refactoring** (P0, component: audio)
4. **Configuration System** (P1, component: bridge)

---

**Done!** Your project board is now set up for sprint-based development.
