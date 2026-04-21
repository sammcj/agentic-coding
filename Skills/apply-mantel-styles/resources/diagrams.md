# Mantel Branding - Diagrams

## Mermaid Styles

Example Mermaid class definitions to apply Mantel brand styles to diagrams

### Mermaid Theme Class Definitions

#### Primary elements (Ocean with Cloud fill for readability)

```
classDef process fill:#EEF9FD,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef components fill:#EEF9FD,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef subprocess fill:#EEF9FD,stroke:#1E5E82,stroke-width:1px,color:#002A41,stroke-dasharray:5 5
```

#### Interactive/Input elements (Sky Blue)

```
classDef inputOutput fill:#81CCEA,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef api fill:#81CCEA,stroke:#002A41,stroke-width:2px,color:#002A41
classDef user fill:#81CCEA,stroke:#002A41,stroke-width:2px,color:#002A41
classDef external fill:#81CCEA,stroke:#002A41,stroke-width:2px,color:#002A41,stroke-dasharray:3 3
```

#### Decision points and important elements (Flamingo)

```
classDef decision fill:#D86E89,stroke:#002A41,stroke-width:2px,color:#FFFFFF
classDef critical fill:#D86E89,stroke:#002A41,stroke-width:2px,color:#FFFFFF
classDef error fill:#D86E89,stroke:#002A41,stroke-width:3px,color:#FFFFFF
classDef warning fill:#D86E8955,stroke:#D86E89,stroke-width:2px,color:#002A41
classDef security fill:#D86E89,stroke:#002A41,stroke-width:3px,color:#FFFFFF,stroke-dasharray:2 1
```

#### Data and storage (Deep Ocean)

```
classDef data fill:#002A41,stroke:#1E5E82,stroke-width:2px,color:#EEF9FD
classDef storage fill:#002A41,stroke:#1E5E82,stroke-width:2px,color:#EEF9FD
classDef database fill:#002A41,stroke:#1E5E82,stroke-width:2px,color:#EEF9FD
classDef cache fill:#002A4166,stroke:#1E5E82,stroke-width:2px,color:#002A41
```

#### State classes

```
classDef start fill:#1E5E82,stroke:#002A41,stroke-width:3px,color:#EEF9FD
classDef end fill:#002A41,stroke:#1E5E82,stroke-width:3px,color:#EEF9FD
classDef success fill:#1E5E8233,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef pending fill:#81CCEA55,stroke:#81CCEA,stroke-width:2px,color:#002A41,stroke-dasharray:5 5
classDef active fill:#1E5E82,stroke:#002A41,stroke-width:2px,color:#EEF9FD
classDef complete fill:#1E5E8255,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef disabled fill:#EEF9FD,stroke:#81CCEA66,stroke-width:1px,color:#81CCEA
classDef inactive fill:#EEF9FD,stroke:#81CCEA66,stroke-width:1px,color:#81CCEA
```

#### Process types

```
classDef manual fill:#EEF9FD,stroke:#D86E89,stroke-width:2px,color:#002A41
classDef automated fill:#EEF9FD,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef async fill:#81CCEA33,stroke:#81CCEA,stroke-width:2px,color:#002A41,stroke-dasharray:8 3
classDef sync fill:#EEF9FD,stroke:#1E5E82,stroke-width:2px,color:#002A41
```

#### System elements

```
classDef system fill:#002A4133,stroke:#002A41,stroke-width:2px,color:#002A41
classDef network fill:#81CCEA33,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef queue fill:#81CCEA55,stroke:#1E5E82,stroke-width:2px,color:#002A41
classDef monitoring fill:#EEF9FD,stroke:#81CCEA,stroke-width:2px,color:#002A41,stroke-dasharray:1 1
```

#### Emphasis and highlights

```
classDef highlight fill:#D86E8922,stroke:#D86E89,stroke-width:3px,color:#002A41
classDef focus fill:#1E5E8244,stroke:#1E5E82,stroke-width:3px,color:#002A41
classDef selected fill:#81CCEA44,stroke:#002A41,stroke-width:3px,color:#002A41
```

#### Secondary elements

```
classDef secondary fill:#EEF9FD,stroke:#81CCEA,stroke-width:2px,color:#002A41
classDef note fill:#EEF9FD,stroke:#81CCEA,stroke-width:1px,color:#1E5E82
classDef comment fill:#EEF9FD,stroke:#81CCEA,stroke-width:1px,color:#1E5E82,stroke-dasharray:3 3
classDef optional fill:#EEF9FD,stroke:#81CCEA,stroke-width:1px,color:#002A41,stroke-dasharray:5 5
```

#### Default styling

```
classDef default fill:#EEF9FD,stroke:#1E5E82,stroke-width:2px,color:#002A41
```

### Mermaid Usage Guide

**Core Process Elements:**
- Use 'process' for standard workflow steps
- Use 'subprocess' for nested or child processes
- Use 'components' for system components or modules

**Interactive Elements:**
- Use 'inputOutput' for user interactions or system I/O
- Use 'user' for user/actor specific elements
- Use 'api' for external service connections
- Use 'external' for third-party systems or external dependencies

**Decision and Alert Elements:**
- Use 'decision' for branching logic or critical choices
- Use 'critical' for important warnings or highlights
- Use 'error' for error states or failure conditions
- Use 'warning' for caution states (less severe than errors)
- Use 'security' for security-related checkpoints or processes

**Data Elements:**
- Use 'data' for data objects or data flow
- Use 'storage' or 'database' for persistent storage
- Use 'cache' for temporary storage or caching layers

**State Elements:**
- Use 'start' for process start points
- Use 'end' for process end points
- Use 'success' for successful completion states
- Use 'pending' for waiting or queued states
- Use 'active' for currently running processes
- Use 'complete' for finished processes
- Use 'disabled' or 'inactive' for unavailable elements

**Process Types:**
- Use 'manual' for human/manual processes
- Use 'automated' for automatic processes
- Use 'async' for asynchronous operations
- Use 'sync' for synchronous operations

**System Elements:**
- Use 'system' for internal system components
- Use 'network' for network-related elements
- Use 'queue' for message queues or buffers
- Use 'monitoring' for logging or monitoring components

**Emphasis Elements:**
- Use 'highlight' for temporarily emphasised elements
- Use 'focus' for elements requiring attention
- Use 'selected' for user-selected items

**Supporting Elements:**
- Use 'secondary' for supporting or auxiliary elements
- Use 'note' for annotations or explanatory text
- Use 'comment' for inline comments or documentation
- Use 'optional' for optional steps or components

### Transparency Note

Some classes use transparency via hex alpha values (e.g., #81CCEA55):
- Last 2 digits represent opacity: FF=100%, CC=80%, 99=60%, 66=40%, 55=33%, 33=20%, 22=13%
- Used for: warning, cache, pending, disabled, system, network, queue, highlight states
- This creates visual hierarchy without introducing non-brand colours

### Mermaid Rules

- Use `<br>` instead of `\n` for line breaks
- Apply standard colour theme unless specified otherwise
- Do NOT use round brackets `( )` within item labels or descriptions
- Mermaid does not support unordered lists within item labels

---

## PlantUML Styles

### PlantUML Colour Definitions

Apply these at the start of PlantUML diagrams:

```plantuml
!define OCEAN #1E5E82
!define FLAMINGO #D86E89
!define DEEP_OCEAN #002A41
!define SKY_BLUE #81CCEA
!define CLOUD #EEF9FD

skinparam backgroundColor CLOUD
skinparam defaultFontColor DEEP_OCEAN

' Activity Diagrams
skinparam activity {
   BackgroundColor CLOUD
   BorderColor OCEAN
   FontColor DEEP_OCEAN
   StartColor OCEAN
   EndColor DEEP_OCEAN
   BarColor FLAMINGO
   DiamondBackgroundColor SKY_BLUE
   DiamondBorderColor OCEAN
}

' Class Diagrams
skinparam class {
   BackgroundColor CLOUD
   BorderColor OCEAN
   FontColor DEEP_OCEAN
   AttributeFontColor OCEAN
   StereotypeFontColor SKY_BLUE
   ArrowColor OCEAN
   HeaderBackgroundColor SKY_BLUE
}

' Sequence Diagrams
skinparam sequence {
   ParticipantBackgroundColor SKY_BLUE
   ParticipantBorderColor OCEAN
   ActorBackgroundColor CLOUD
   ActorBorderColor DEEP_OCEAN
   LifeLineBorderColor OCEAN
   ArrowColor OCEAN
   GroupBackgroundColor CLOUD
   GroupBorderColor SKY_BLUE
   NoteBackgroundColor CLOUD
   NoteBorderColor FLAMINGO
}

' Component Diagrams
skinparam component {
   BackgroundColor CLOUD
   BorderColor OCEAN
   FontColor DEEP_OCEAN
   InterfaceBackgroundColor SKY_BLUE
   InterfaceBorderColor DEEP_OCEAN
}

' State Diagrams
skinparam state {
   BackgroundColor CLOUD
   BorderColor OCEAN
   FontColor DEEP_OCEAN
   StartColor OCEAN
   EndColor DEEP_OCEAN
   AttributeFontColor OCEAN
}

' Use Case Diagrams
skinparam usecase {
   BackgroundColor CLOUD
   BorderColor OCEAN
   FontColor DEEP_OCEAN
   ActorBackgroundColor SKY_BLUE
   ActorBorderColor DEEP_OCEAN
}

' Error/Warning States
skinparam note {
   BackgroundColor<<warning>> FLAMINGO
   BorderColor<<warning>> DEEP_OCEAN
   FontColor<<warning>> CLOUD
}
```
