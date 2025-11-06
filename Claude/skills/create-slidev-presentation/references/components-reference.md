# Slidev Components Reference

Complete reference for all built-in Slidev components and custom component patterns.

## Built-in Components

### Click Animation Components

#### `<v-click>`
Show elements on click.

```markdown
<v-click>Appears on first click</v-click>
<v-click>Appears on second click</v-click>

<!-- Absolute positioning -->
<v-click at="3">Appears on third click</v-click>

<!-- Relative positioning -->
<v-click at="+2">Skip one click</v-click>

<!-- Hide after click -->
<v-click hide>Hidden after click</v-click>
<v-click hide at="[2, 4]">Visible only clicks 2-3</v-click>
```

#### `v-click` Directive
Alternative syntax using directive:

```markdown
<div v-click>Directive syntax</div>
<div v-click="3">At click 3</div>
<div v-click.hide>Hide on click</div>
```

#### `<v-clicks>`
Batch click animations for lists:

```markdown
<v-clicks>

- Item 1
- Item 2
- Item 3

</v-clicks>

<!-- Nested lists with depth -->
<v-clicks depth="2">

- Parent 1
  - Child 1.1
  - Child 1.2
- Parent 2

</v-clicks>

<!-- Every N items -->
<v-clicks every="2">

- Items 1-2 (click 1)
- Items 3-4 (click 2)

</v-clicks>
```

#### `<v-after>`
Appears with previous click:

```markdown
<div v-click>First</div>
<div v-after>Also appears on first click</div>
```

#### `<v-switch>`
Switch content on specific clicks:

```markdown
<v-switch>
  <template #1>Content for click 1</template>
  <template #2>Content for click 2</template>
  <template #5-7>Content for clicks 5-6</template>
</v-switch>
```

### Interactive Components

#### `<v-drag>`
Draggable containers:

```markdown
<!-- Position: left,top,width,height,rotate -->
<v-drag pos="100,200,300,50,0">
  Drag me around!
</v-drag>

<!-- Bind to frontmatter -->
---
dragPos:
  myElement: 10,20,200,100,0
---

<v-drag pos="myElement">
  Draggable element
</v-drag>
```

#### `<v-drag-arrow>`
Draggable arrows:

```markdown
<v-drag-arrow />

<!-- Two-way arrow -->
<v-drag-arrow two-way />

<!-- With position -->
<v-drag-arrow pos="67,452,253,46" two-way op70 />
```

### Media Components

#### `<Tweet>`
Embed Twitter posts:

```markdown
<Tweet id="1390115482657726468" />

<!-- With scale -->
<Tweet id="1390115482657726468" scale="0.8" />

<!-- Options -->
<Tweet
  id="1390115482657726468"
  scale="0.65"
  conversation="none"
  cards="hidden"
/>
```

**Props**:
- `id` (required): Tweet ID
- `scale`: Size scaling (default: 1)
- `conversation`: Show conversation thread
- `cards`: Show/hide Twitter cards

#### `<Youtube>`
Embed YouTube videos:

```markdown
<Youtube id="luoMHjh-XcQ" />

<!-- With dimensions -->
<Youtube id="luoMHjh-XcQ" width="800" height="450" />

<!-- Start at specific time (60 seconds) -->
<Youtube id="luoMHjh-XcQ?start=60" />
```

**Props**:
- `id` (required): Video ID (optionally with ?start=N)
- `width`: Video width (default: 560)
- `height`: Video height (default: 315)

#### `<SlidevVideo>`
Video player with controls:

```markdown
<SlidevVideo autoplay controls>
  <source src="/demo.mp4" type="video/mp4" />
  <source src="/demo.webm" type="video/webm" />
</SlidevVideo>

<!-- With poster -->
<SlidevVideo controls poster="/thumbnail.jpg">
  <source src="/video.mp4" type="video/mp4" />
</SlidevVideo>
```

**Attributes**:
- `autoplay`: Auto-play video
- `controls`: Show controls
- `loop`: Loop video
- `muted`: Mute audio
- `poster`: Poster image URL

### Utility Components

#### `<Arrow>`
Draw arrows between elements:

```markdown
<!-- Basic arrow -->
<Arrow x1="10" y1="20" x2="100" y2="200" />

<!-- Styled arrow -->
<Arrow
  x1="10"
  y1="20"
  x2="100"
  y2="200"
  color="#953"
  width="2"
/>

<!-- Using v-bind -->
<Arrow v-bind="{ x1:10, y1:10, x2:200, y2:200 }" />
```

**Props**:
- `x1`, `y1`: Start coordinates
- `x2`, `y2`: End coordinates
- `width`: Line width (default: 2)
- `color`: Arrow colour (default: currentColor)

#### `<Link>`
Navigate to slides:

```markdown
<!-- By slide number -->
<Link to="42">Go to slide 42</Link>

<!-- By route alias -->
<Link to="solutions" title="Jump to solutions" />

<!-- With custom styling -->
<Link to="10" class="btn">Next Section</Link>
```

**Props**:
- `to` (required): Slide number or route alias
- `title`: Link text (optional)

#### `<Toc>`
Table of contents:

```markdown
<!-- Basic TOC -->
<Toc />

<!-- With depth limits -->
<Toc minDepth="1" maxDepth="2" />

<!-- Only level 1 headings -->
<Toc minDepth="1" maxDepth="1" />
```

**Props**:
- `minDepth`: Minimum heading level (default: 1)
- `maxDepth`: Maximum heading level (default: Infinity)

**Note**: Slides with `hideInToc: true` in frontmatter are excluded.

#### `<Transform>`
Scale content:

```markdown
<Transform :scale="0.8">
  <YourContent />
</Transform>

<!-- With origin -->
<Transform :scale="0.5" origin="top left">
  <YourContent />
</Transform>
```

**Props**:
- `scale`: Scale factor (required)
- `origin`: Transform origin (default: "center")

#### `<LightOrDark>`
Conditional rendering based on theme:

```markdown
<LightOrDark>
  <template #dark>
    <img src="/dark-logo.png" />
  </template>
  <template #light>
    <img src="/light-logo.png" />
  </template>
</LightOrDark>

<!-- With scoped slot props -->
<LightOrDark width="100" alt="Logo">
  <template #dark="props">
    <img src="/dark.png" v-bind="props" />
  </template>
  <template #light="props">
    <img src="/light.png" v-bind="props" />
  </template>
</LightOrDark>
```

#### `<RenderWhen>`
Conditional rendering by context:

```markdown
<!-- Only in presenter view -->
<RenderWhen context="presenter">
  This text only appears in presenter mode
</RenderWhen>

<!-- Multiple contexts -->
<RenderWhen context="['presenter', 'main']">
  Appears in presenter and main views
</RenderWhen>
```

**Props**:
- `context`: Context name or array of contexts

#### `<AutoFitText>`
Auto-resize text to fit:

```markdown
<AutoFitText :max="200" :min="100" modelValue="Some text" />
```

**Props**:
- `modelValue`: Text content (required)
- `max`: Maximum font size
- `min`: Minimum font size

### Motion Animations

#### `v-motion` Directive
From `@vueuse/motion`:

```markdown
<div
  v-motion
  :initial="{ x: -80, opacity: 0 }"
  :enter="{ x: 0, opacity: 1 }"
  :leave="{ x: 80, opacity: 0 }"
>
  Animated element
</div>

<!-- Click-triggered animations -->
<div
  v-motion
  :initial="{ x: -80 }"
  :enter="{ x: 0 }"
  :click-1="{ x: 0, y: 30 }"
  :click-2="{ y: 60 }"
  :click-3="{ scale: 1.2 }"
>
  Interactive animation
</div>

<!-- With transition config -->
<script setup>
const config = {
  x: 0,
  y: 0,
  transition: {
    type: 'spring',
    stiffness: 20,
    damping: 10
  }
}
</script>

<div v-motion :enter="config">
  Spring animation
</div>
```

**Animation properties**:
- `x`, `y`: Translation
- `scale`: Scaling
- `rotate`: Rotation (degrees)
- `opacity`: Opacity (0-1)
- `transition`: Transition configuration

## Custom Components

### Creating Custom Components

**File**: `components/MyButton.vue`

```vue
<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v: string) => ['primary', 'secondary'].includes(v)
  }
})

const count = ref(0)
</script>

<template>
  <button
    class="btn"
    :class="`btn-${variant}`"
    @click="count++"
  >
    <slot /> ({{ count }})
  </button>
</template>

<style scoped>
.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #5b21b6;
  color: white;
}

.btn-primary:hover {
  background: #6d28d9;
}

.btn-secondary {
  background: #0891b2;
  color: white;
}
</style>
```

**Usage**:
```markdown
<MyButton>Click Me</MyButton>
<MyButton variant="secondary">Secondary Button</MyButton>
```

**Note**: Components in `/components` are auto-imported.

### Custom Component Patterns

#### Interactive Counter
```vue
<script setup lang="ts">
import { ref } from 'vue'

const count = ref(0)
const increment = () => count.value++
const decrement = () => count.value--
</script>

<template>
  <div class="counter">
    <button @click="decrement">-</button>
    <span>{{ count }}</span>
    <button @click="increment">+</button>
  </div>
</template>
```

#### Animated Card
```vue
<script setup lang="ts">
defineProps<{
  title: string
  icon?: string
}>()
</script>

<template>
  <div class="card" v-motion :initial="{ opacity: 0, y: 20 }" :enter="{ opacity: 1, y: 0 }">
    <div v-if="icon" class="icon" :class="icon" />
    <h3>{{ title }}</h3>
    <div class="content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.card {
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  background: white;
}
</style>
```

#### Code Demo Component
```vue
<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  code: string
  language?: string
}>()

const output = ref('')

const runCode = () => {
  try {
    output.value = eval(props.code)
  } catch (e) {
    output.value = `Error: ${e.message}`
  }
}
</script>

<template>
  <div class="code-demo">
    <div class="code-block">
      <slot />
    </div>
    <button @click="runCode">Run Code</button>
    <div v-if="output" class="output">
      {{ output }}
    </div>
  </div>
</template>
```

## Component Best Practices

### Performance
1. **Use `v-if` for conditional components**: More efficient than `v-show` for rarely-toggled content
2. **Minimize reactive dependencies**: Only make necessary data reactive
3. **Lazy load heavy components**: Import components dynamically when needed

### Accessibility
1. **Semantic HTML**: Use appropriate HTML elements
2. **Keyboard navigation**: Ensure interactive elements are keyboard-accessible
3. **ARIA labels**: Add aria-label for icon-only buttons
4. **Focus management**: Handle focus for modal-like components

### Styling
1. **Scoped styles**: Use `<style scoped>` to prevent style leakage
2. **UnoCSS classes**: Leverage utility classes for common styling
3. **CSS variables**: Use theme variables for consistency
4. **Responsive design**: Consider different screen sizes

### Composition
1. **Single responsibility**: Each component should do one thing well
2. **Props validation**: Define prop types and validators
3. **Emit events**: Use emits for parent communication
4. **Slots**: Provide slots for flexible content injection

## Component Selection Guide

| Use Case | Component |
|----------|-----------|
| Click animations | `<v-click>` or `<v-clicks>` |
| List animations | `<v-clicks>` |
| Content switching | `<v-switch>` |
| Draggable elements | `<v-drag>` |
| Arrows | `<Arrow>` or `<v-drag-arrow>` |
| Navigation | `<Link>` |
| TOC | `<Toc>` |
| Scaling | `<Transform>` |
| Theme switching | `<LightOrDark>` |
| Twitter posts | `<Tweet>` |
| YouTube videos | `<Youtube>` |
| Local videos | `<SlidevVideo>` |
| Motion | `v-motion` directive |
| Context-specific | `<RenderWhen>` |
