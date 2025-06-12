# Ollama Modelfile Template Conversion Guide

# 1. Introduction

Ollama empowers users to run large language models (LLMs) locally, offering greater control and privacy. A key aspect of customising model behaviour within Ollama is the `Modelfile`, a configuration file acting as a blueprint for model creation and modification. Central to the `Modelfile` is the `TEMPLATE` instruction, which defines how user input, system messages, chat history, and potential tool interactions are structured into the final prompt sent to the LLM.

Understanding and effectively utilising the `TEMPLATE` syntax is crucial for achieving optimal results, especially with chat and instruction-following models that rely on specific formatting and special tokens. Ollama leverages Go's built-in `text/template` package for this purpose.

This guide provides an expert-level deep dive into Ollama's `TEMPLATE` directive. It meticulously analyses the underlying Go `text/template` features available within Ollama, details the data context and variables accessible during template execution, and illustrates practical usage through diverse examples including ChatML, Llama 3.2, Gemma 3, tool calling, and fill-in-the-middle scenarios. Furthermore, this report offers a refined comparison between Go's templating and the popular Jinja2 engine, highlighting key differences and limitations, and provides actionable strategies for converting Jinja2 templates to the Ollama `TEMPLATE` format, focusing on addressing the absence of built-in filters and macros.

## 2. Ollama `TEMPLATE` Fundamentals

Ollama's `TEMPLATE` instruction utilises the standard Go `text/template` engine. Understanding the core concepts of Go templates is fundamental to crafting effective Ollama prompts.

- **Actions (`{{... }}`)**: The primary syntax element. Any text outside of these double curly braces is treated as literal static text and copied directly to the output. Inside the braces, template logic, variable access, and function calls occur.
- **Pipelines (`|`)**: Commands within an action can be chained using the pipe character (`|`). The output of one command becomes the input (typically the last argument) of the next command, similar to Unix pipelines. For example, `{{.Name | printf "Name: %s" }}` passes the value of `.Name` to the `printf` function.
- **The Dot (`.`)**: Represents the current data context being processed. Initially, it refers to the root data object passed to the template. Control structures like `range` and `with` can change the value of the dot within their scope.
- **Variables (`$var`)**: Variables can be declared within templates using `:=` and assigned using `=`. They are prefixed with a dollar sign (`$`) and are scoped to the control structure block (`if`, `range`, `with`) where they are defined, or to the entire template if defined at the top level. The special variable `$` always refers to the root data object passed to the `Execute` method, which is useful for accessing root-level data from within nested scopes.
- **Comments (`{{/*... */}}`)**: Comments are ignored during execution and do not appear in the output. They can span multiple lines.
- **Whitespace Control (`-`)**: A hyphen (`-`) placed immediately inside the delimiters (`{{-` or `-}}`) can trim leading or trailing whitespace, respectively, from the action's output. This is crucial for generating clean prompts without unwanted newlines or spaces, especially within loops and conditionals.

## 3. Go `text/template` Features Available in Ollama

While Ollama uses Go's `text/template`, it's important to understand the specific features and limitations within the Ollama execution context. Analysis of Ollama's internal template handling code reveals the precise environment.

### 3.1. Custom Functions: The `json` Function

Go's `text/template` allows registering custom functions via the `Funcs` method. Ollama registers exactly *one* custom function named `json`.

Go

```go
// From Ollama's template.go source [17]
var funcs = template.FuncMap{
    "json": func(v any) string {
        b, _ := json.Marshal(v) // Ignores potential marshalling errors
        return string(b)
    },
}
```

The purpose of this `json` function is to marshal any given Go value (`v any`) into its JSON string representation. This is particularly useful for formatting complex data structures, such as the arguments for tool calls, directly within the template. For example: `{{.Function.Arguments | json }}` or `{{ json.Function.Arguments }}`.

### 3.2. Parsing Options: `missingkey=zero`

When parsing the `TEMPLATE` string, Ollama uses the `missingkey=zero` option.

Go

```go
// From Ollama's template.go source [17]
tmpl := template.New("").Option("missingkey=zero").Funcs(funcs)
```

This option controls the behaviour when a template tries to access a map key or struct field that doesn't exist in the provided data context. Instead of causing a runtime error (the default `missingkey=error`) or substituting a specific string (`missingkey=invalid`), `missingkey=zero` causes the template engine to substitute the *zero value* for the expected type (e.g., `""` for strings, `0` for integers, `false` for booleans, `nil` for slices/maps/pointers). While this can prevent crashes if optional data is missing, it can also mask errors where a required variable was misspelled or not provided, leading to unexpected empty output rather than an explicit error message.

### 3.3. Automatic Appending of `{{.Response }}`

Ollama's `Parse` function includes logic to automatically append `{{.Response }}` to the end of a template *if* the template does not explicitly reference either the `.Messages` variable or the `.Response` variable.

Go

```go
// Simplified logic from Ollama's template.go source [17]
//... after parsing the template 's' into 'tmpl'...
t := Template{Template: tmpl, raw: s}
if vars := t.Vars();!slices.Contains(vars, "messages") &&!slices.Contains(vars, "response") {
    // Append the equivalent of {{.Response }} to the template's parse tree
    tmpl.Tree.Root.Nodes = append(tmpl.Tree.Root.Nodes, &response) // 'response' is a pre-defined parse node
}
```

This behaviour ensures that simpler templates designed for basic prompt/response interactions (like the default `{{.Prompt }}` template used when none is specified ) implicitly include the placeholder where the model's generated response should be inserted. For more complex chat templates that manage the conversation flow using `.Messages`, this automatic appending does not occur because the template author is expected to handle the placement of responses explicitly.

### 3.4. Built-in Go Functions

Beyond the custom `json` function, Ollama templates have access to the standard set of built-in functions provided by Go's `text/template` package. These include:

- **Logical Functions:**
  - `and`: Logical AND (short-circuiting behaviour).
  - `or`: Logical OR (short-circuiting behaviour).
  - `not`: Logical NOT.
- **Comparison Functions:** (Operate on compatible types)
  - `eq`: Equal (`==`)
  - `ne`: Not Equal (`!=`)
  - `lt`: Less Than (`<`)
  - `le`: Less Than or Equal (`<=`)
  - `gt`: Greater Than (`>`)
  - `ge`: Greater Than or Equal (`>=`)
- **Length Function:**
  - `len`: Returns the length of strings, arrays, slices, maps.
- **Indexing/Slicing:**
  - `index`: Access elements of arrays, slices, or maps by index/key. Example: `{{ index.Messages 0 }}` gets the first message.
  - `slice`: Creates a slice of an array, slice, or string. Example: `{{ slice.Messages 1 }}` creates a slice from the second message onwards. `{{ slice.Content 0 5 }}` gets the first 5 characters (bytes) of `.Content`.
- **Printing/Formatting:**
  - `print`: Alias for `fmt.Sprint`.
  - `printf`: Alias for `fmt.Sprintf`. Useful for basic formatting, e.g., `{{ printf "%.2f".Value }}`.
  - `println`: Alias for `fmt.Sprintln`.
- **Function Calling:**
  - `call`: Calls a function value (less common in basic Ollama templates, requires the function to be part of the data context).

It's important to note that functions commonly found in web-focused Go templates like `html`, `js`, and `urlquery` are generally *not* relevant or available/safe in the `text/template` context used by Ollama, as the output is plain text for the LLM, not HTML/JS.

### 3.5. Control Structures

Ollama templates support the standard Go `text/template` control structures :

- **`if`/`else if`/`else`/`end`**: Conditional execution based on the truthiness of a pipeline. A value is considered false if it's the zero value of its type (false, 0, "", nil pointer/interface/slice/map/array, zero-length array/slice/map/string).Code snippet
 ```go
 {{ if.System }}System: {{.System }}{{ else }}No system prompt.{{ end }}
 ```
- **`range`/`else`/`end`**: Iterates over arrays, slices, maps, or channels. Inside the loop, the dot (`.`) is set to the current element. For maps, two variables can be captured: `{{ range $key, $value :=.Map }}`. The optional `else` block executes if the collection is empty or nil.Code snippet
 ```go
 {{ range.Messages }}Role: {{.Role }}, Content: {{.Content }}{{ else }}No messages.{{ end }}
 ```
  - **`break`**: Exits the innermost `range` loop early.
  - **`continue`**: Skips the rest of the current iteration and proceeds to the next iteration of the innermost `range` loop.
- **`with`/`else`/`end`**: Sets the dot (`.`) to the result of a pipeline if it's not empty/false, executing the block. Useful for simplifying access to nested data or checking for non-nil values.Code snippet
 ```go
 {{ with.Messages }}{{/* Dot is now the Messages slice */}}{{ range. }}...{{ end }}{{ end }}
 ```
- **`define`/`template`/`block`**: Used for defining and executing named sub-templates. `define` creates a template, `template` executes it, and `block` is shorthand for defining and executing in place. While powerful, these are less commonly seen in typical Ollama prompt templates compared to `if` and `range`.

## 4. Data Context (`.`): Structure and Variables

When Ollama executes a template (e.g., via the `/api/chat` or `/api/generate` endpoints), it passes a data object as the context. The fields of this object are accessible within the template, primarily starting with the dot (`.`) or the root context variable (`$`). The exact structure has evolved, but modern Ollama versions primarily use a map for chat interactions.

### 4.1. Modern Chat Data Structure (`/api/chat`)

For chat completions (`/api/chat`), the data passed to the template is typically a Go map of type `map[string]any`. The primary keys available at the root level (`.` or `$`) are :

- **`.System` (string):** The system prompt provided either in the `Modelfile`'s `SYSTEM` instruction or via the API request's `system` parameter.
- **`.Messages` (list/slice):** A list of message objects representing the conversation history. This is the core element for chat templates. Each message object within the list has the following structure :
  - **`.Role` (string):** The role of the message author. Common values are `"system"`, `"user"`, `"assistant"`. The `"tool"` role is used to provide the output from a tool call back to the model.
  - **`.Content` (string):** The textual content of the message.
  - **`.Images` (list/slice of strings, optional):** For multimodal models, this contains base64-encoded image data associated with the message.
  - **`.ToolCalls` (list/slice, optional):** Present on *assistant* messages when the model decides to call one or more tools. Each element in this list represents a requested tool call and has the structure :
    - **`.Function` (object/map):** Contains details of the function to call.
      - **`.Name` (string):** The name of the function to be called.
      - **`.Arguments` (map/object):** The arguments for the function, typically represented as a map or struct that can be marshalled to JSON.
- **`.Tools` (list/slice, optional):** A list of available tool definitions provided in the API request. This allows the model to know which tools it *can* call. Each tool definition object typically has the structure :
  - **`.Type` (string):** Currently always `"function"`.
  - **`.Function` (object/map):** Contains the definition of the function.
    - **`.Name` (string):** The name of the function.
    - **`.Description` (string):** A description of what the function does (crucial for the model to understand when to use it).
    - **`.Parameters` (object/map):** A schema (often JSON schema) describing the parameters the function accepts, including their types, descriptions, and whether they are required.
      - **`.Type` (string):** Typically `"object"`.
      - **`.Properties` (map):** Defines individual parameters (name, type, description).
      - **`.Required` (list/slice of strings):** Lists the names of mandatory parameters.
- **`.Response` (string):** A placeholder for where the model's final generated text response should be inserted. As mentioned, this is often handled implicitly or explicitly within `.Messages` loops in chat templates.

### 4.2. Simpler/Legacy Variables (`/api/generate`, Basic Templates)

For simpler interactions, particularly via `/api/generate` or when using basic templates without the `Messages` structure, other variables might be primary:

- **`.Prompt` (string):** The user's input prompt. This is the default variable used if no `TEMPLATE` is specified.
- **`.Suffix` (string):** Text intended to be inserted *after* the model's response, often used for fill-in-the-middle tasks.

### 4.3. Case Sensitivity

Go's `text/template` accesses data fields using reflection. While Go itself is strictly case-sensitive, template access to the *top-level* fields of the input data (like `.System` or `.Messages`) might exhibit some case-insensitivity depending on implementation details (e.g., `.system` might sometimes work if the underlying map key lookup is case-insensitive or if reflection finds a matching exported field regardless of initial letter case).

However, for *nested* fields within structs or maps (like `.Messages.Role` or `.ToolCalls.Function.Name`), access is almost certainly **case-sensitive**, matching the exact field names defined in the Go structs or map keys used internally by Ollama. It is best practice to always use the exact capitalization documented (`.System`, `.Messages`, `.Role`, `.Content`, `.ToolCalls`, `.Function`, `.Name`, `.Arguments`, `.Tools`) to ensure portability and avoid unexpected behaviour.

## 5. Ollama `TEMPLATE` Examples in Practice

The `TEMPLATE` instruction allows tailoring the prompt structure to match the specific format expected by different LLMs. Let's examine how various syntaxes are implemented using Ollama templates.

### 5.1. ChatML Template

ChatML is a common format used by models like Neural Chat and Orca 2. It uses `<|im_start|>` and `<|im_end|>` tokens to delimit messages.

Code snippet

```go
# Modelfile TEMPLATE for ChatML [9]
TEMPLATE """{{- range.Messages }}
<|im_start|>{{.Role }}
{{.Content }}<|im_end|>
{{ end }}
<|im_start|>assistant
"""
```

- **`{{- range.Messages }}`**: Iterates through the `Messages` list. The `-` trims leading whitespace.
- **`<|im_start|>{{.Role }}`**: Prints the start token and the message `Role` (e.g., "user", "assistant").
- **`{{.Content }}<|im_end|>`**: Prints the message `Content` and the end token.
- **`{{ end }}`**: Ends the loop.
- **`<|im_start|>assistant`**: Appends the start token for the assistant's turn, prompting the model to generate its response.
- **Whitespace Control:** `{{-` is used to prevent extra newlines before each message block.

### 5.2. Llama 3.2 Template (with Tool Support)

Llama 3.2 uses specific tokens like `<|start_header_id|>`, `<|end_header_id|>`, and `<|eot_id|>` and has a complex structure for handling system prompts, user/assistant turns, and tool calls.

Code snippet

```go
# Modelfile TEMPLATE for Llama 3.2 [16]
TEMPLATE """<|start_header_id|>system<|end_header_id|>
Cutting Knowledge Date: December 2023.{{ if.System }}{{.System }}{{- end }}{{- if.Tools }}
When you receive a tool call response, use the output to format an answer to the orginal user question. You are a helpful assistant with tool calling capabilities.{{- end }}<|eot_id|>
{{- range $i, $_ :=.Messages }}
  {{- $last := eq (len (slice $.Messages $i)) 1 }}
  {{- if eq.Role "user" }}<|start_header_id|>user<|end_header_id|>
    {{- /* Tool handling for the last user message */ -}}
    {{- if and $.Tools $last }}
Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.
Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}. Do not use variables.
{{ range $.Tools }}
{{-. }}
{{ end }}
{{.Content }}<|eot_id|>
    {{- else }}
      {{.Content }}<|eot_id|>
    {{- end }}
    {{- /* Prompt assistant turn if this is the last message */ -}}
    {{ if $last }}<|start_header_id|>assistant<|end_header_id|>{{ end }}
  {{- else if eq.Role "assistant" }}<|start_header_id|>assistant<|end_header_id|>
    {{- /* Handle tool calls if present */ -}}
    {{- if.ToolCalls }}
      {{ range.ToolCalls }}
      {"name": "{{.Function.Name }}", "parameters": {{.Function.Arguments | json }}}{{/* Use json func */}}
      {{- end }}
    {{- else }}
      {{.Content }}
    {{- end }}
    {{- /* Add end token if not the last message (expecting potential tool response) */ -}}
    {{ if not $last }}<|eot_id|>{{ end }}
  {{- else if eq.Role "tool" }}<|start_header_id|>ipython<|end_header_id|>
    {{/* Note: Llama 3.2 uses 'ipython' role marker for tool results */}}
    {{.Content }}<|eot_id|>
    {{- /* Prompt assistant turn if this tool result was the last message */ -}}
    {{ if $last }}<|start_header_id|>assistant<|end_header_id|>{{ end }}
  {{- end }}
{{- end }}"""
```

- **System Prompt Handling:** Uses `{{ if.System }}` and `{{ if.Tools }}` to conditionally include system text and tool instructions.
- **Looping & Last Message:** `{{- range $i, $_ :=.Messages }}` iterates messages. `{{- $last := eq (len (slice $.Messages $i)) 1 }}` calculates if the current message is the last one using `len` and `slice`. `$.Messages` accesses the root context's `Messages`.
- **User Turn:** Uses `{{ if eq.Role "user" }}`. If it's the last message (`$last`) and tools are available (`$.Tools`), it includes instructions for tool use and lists the tools using `{{ range $.Tools }}`. Otherwise, it just prints the content. It prompts the assistant turn if it's the last message.
- **Assistant Turn:** Uses `{{ else if eq.Role "assistant" }}`. Checks for `.ToolCalls` using `{{ if.ToolCalls }}`. If present, iterates using `{{ range.ToolCalls }}` and formats the output as JSON, crucially using the `json` function for the `.Function.Arguments`: `{{.Function.Arguments | json }}`. If no tool calls, prints `.Content`. Adds `<|eot_id|>` only if *not* the last message.
- **Tool Turn:** Uses `{{ else if eq.Role "tool" }}`. Prints the tool result (`.Content`) using the `ipython` role marker specific to Llama 3.2. Prompts the assistant turn if it was the last message.
- **Whitespace:** `-` is used extensively (`{{-`, `-}}`) to manage newlines and spacing.

### 5.3. Gemma 3 Template (with Tool Support)

Gemma 3 uses `<start_of_turn>` and `<end_of_turn>` tokens and has a slightly different structure for tool interactions compared to Llama 3.2.

Code snippet

```go
# Modelfile TEMPLATE for Gemma 3 [15]
TEMPLATE """{{- range $i, $_ :=.Messages }}
  {{- $last := eq (len (slice $.Messages $i)) 1 }}
  {{- if eq.Role "user" }}<start_of_turn>user
    {{- /* Handle Images if present and last message */ -}}
    {{- if and.Images $last }}
      {{- range.Images }}
<image>
{{. }}
</image>
      {{- end }}
    {{- end }}
    {{- /* Handle Tools if present and last message */ -}}
    {{- if and $.Tools $last }}
Given the following functions, please respond with a JSON for a function call with its proper...[source](https://ollama.com/bsahane/gemma3:27b/blobs/a6aa41160d5f)
  {{- else if eq.Role "assistant" }}<start_of_turn>model
    {{- /* Handle Tool Calls if present */ -}}
    {{- if.ToolCalls }}
      {{- range.ToolCalls }}
{"name": "{{.Function.Name }}", "parameters": {{.Function.Arguments | json }}} {{/* Use json func */}}
      {{- end }}
    {{- else }}
      {{.Content }}
    {{- end }}
    {{- /* End Turn if Not the Last Message */ -}}
    {{- if not $last }}<end_of_turn>
    {{ end }}
  {{- else if eq.Role "tool" }}<start_of_turn>user
    Tool result:
    {{.Content }}<end_of_turn>
    {{- /* Start Assistant Turn if it's the Last Message */ -}}
    {{ if $last }}<start_of_turn>model{{ end }}
  {{- end }}
{{- end }}"""
```

- **Tokens:** Uses `<start_of_turn>` and `<end_of_turn>`. Note the assistant role is marked as `model`.
- **Image Handling:** Includes a conditional block `{{- if and.Images $last }}` within the user turn to handle and format image data using `<image>` tags.
- **Tool Handling:** Similar logic to Llama 3.2 for `$.Tools` (instructions and listing) and `.ToolCalls` (JSON formatting using the `json` function), but nested within the user/assistant turns differently.
- **Tool Result Turn:** Formats the tool result within a `<start_of_turn>user` block, prefixes it with "Tool result:", and ends with `<end_of_turn>`. It starts the model's turn if the tool result was the last message.

### 5.4. Tool Calling Flow Explanation

The examples above illustrate the template's role in tool calling :

1. **Tool Definition:** The application provides available tools via the `tools` parameter in the API request. The template (like Llama 3.2/Gemma 3 examples) uses `{{ if and $.Tools $last }}` and `{{ range $.Tools }}` to present these definitions and instructions to the model on the final user turn.
2. **Model Request:** If the model determines a tool is needed based on the user prompt and tool descriptions, it generates a response containing a `tool_calls` structure within its message. The template's assistant role section (`{{ if.ToolCalls }}`) formats this request, often as a JSON string like `{"name": "...", "parameters": {...}}`, using `{{.Function.Name }}` and `{{.Function.Arguments | json }}`.
3. **Application Execution:** The application calling the Ollama API receives the response, parses the `tool_calls` field, identifies the requested function (`get_current_weather`) and its arguments (`{"city": "Toronto"}`), and executes the corresponding application code (e.g., calls a weather API).
4. **Tool Response:** The application takes the result from the executed tool (e.g., `"The weather in Toronto is sunny, 25°C"`) and sends a *new* chat request back to the Ollama API. This request includes the original message history *plus* a new message with `role: "tool"` and the tool's output as the `content`.
5. **Final Model Answer:** The template processes this updated message history. The `{{ if eq.Role "tool" }}` block formats the tool result appropriately for the model. The model now has the information it requested and generates a final natural language response to the user's original question (e.g., "The current weather in Toronto is sunny and 25°C.").

### 5.5. Fill-in-the-Middle (FIM) Template

FIM models, often used for code completion, require placeholders for text before and after the insertion point. This typically uses `.Prompt` and `.Suffix`.

Code snippet

```go
# Example FIM Template (e.g., for Code Llama) [9]
TEMPLATE """<PRE> {{.Prompt }} <SUF>{{.Suffix }} <MID>"""
```
- **`<PRE>`, `<SUF>`, `<MID>`**: Special tokens specific to the FIM model.
- **`{{.Prompt }}`**: Inserts the text preceding the cursor.
- **`{{.Suffix }}`**: Inserts the text following the cursor.
- **`<MID>`**: Indicates where the model should generate the inserted text.

### 5.6. Basic Prompt Template (e.g., Phi-3)

For simpler models or use cases not involving chat history or tools, a basic template using only `.Prompt` might suffice.

Code snippet

```go
# Modelfile TEMPLATE for basic prompt (e.g., Phi-3) [31]
TEMPLATE """<|user|>
{{.Prompt }}<|end|>
<|assistant|>"""
```

- This directly inserts the user's prompt (`{{.Prompt }}`) between model-specific user and assistant markers.

These examples demonstrate the flexibility of Ollama's `TEMPLATE` directive in accommodating diverse model requirements using Go `text/template` syntax, including conditionals (`if`), loops (`range`), built-in functions (`eq`, `len`, `slice`, `and`), the custom `json` function, variable access (`.`, `$.`), and whitespace control (`-`).

## 6. Comparison: Ollama Go Templates vs. Jinja2

Developers familiar with Jinja2, a popular templating engine in the Python ecosystem , will find both similarities and significant differences when working with Ollama's Go `text/template`\-based system. Understanding these distinctions is key for effective use and potential conversion.

### 6.1. Syntax Differences

While both engines use delimiters to separate logic from static text, the specifics differ:

- **Delimiters:** Go `text/template` uses `{{... }}` for all actions (output, logic, comments). Jinja2 uses `{{... }}` for expressions/output, `{%... %}` for statements (like `if`, `for`), and `{#... #}` for comments.
- **Function/Filter Calls:** Go uses `{{ func arg1 arg2 }}` or `{{ arg1 | func arg2 }}`. Jinja2 uses `{{ variable | filter(arg) }}` for filters and `{{ function(arg) }}` for function calls.
- **Variable Assignment:** Go uses `{{ $var := value }}` or `{{ $var = value }}`. Jinja2 uses `{% set var = value %}`.
- **Loop Context:** Go's `range` provides the current item as `.` and optionally index/value variables (`$i`, `$value`). Jinja2's `for` loop provides a special `loop` object with attributes like `loop.index`, `loop.first`, `loop.last`, etc..

### 6.2. Feature Gaps in Ollama/Go Templates

The most critical differences lie in the available built-in functionality:

- **Lack of Built-in Filters:** This is the most significant limitation compared to Jinja2. Go `text/template` offers a minimal set of built-in functions (primarily logical operators, comparisons, `len`, `index`, `slice`, `print*`). Jinja2, by contrast, comes with a rich library of standard filters for common tasks like string manipulation (`capitalize`, `lower`, `upper`, `title`, `trim`, `replace`, `striptags`), list operations (`join`, `sort`, `map`, `select`, `reject`, `batch`), mathematical operations (`sum`, `round`), dictionary manipulation (`dictsort`), and more. Ollama adds only the `json` function. Tasks easily done with a Jinja filter often require pre-processing the data in the application code before passing it to an Ollama template.
- **No In-Template Custom Function Definition (Macros):** Jinja2 allows defining reusable template fragments called macros directly within the template files using `{% macro... %}`... `{% endmacro %}`. These macros can accept arguments and be imported into other templates. Go `text/template` has no equivalent feature for defining reusable logic *within* the template string itself. Custom functions must be defined in the calling Go application code and registered with the template engine using the `Funcs` method. Since Ollama only pre-registers `json` , users cannot add their own helper logic directly into the `TEMPLATE` string in the `Modelfile`.
- **Limited Standard Function Library:** Consequently, the overall functional power available directly within an Ollama template (Go built-ins + `json`) is considerably less than what's typically available in a Jinja2 environment, which includes numerous standard filters and often application-specific functions or filters added by frameworks like Django or Flask.

### 6.3. Philosophical Difference

This feature gap reflects a fundamental design difference. Go templates intentionally minimize the logic allowed within the template itself, encouraging developers to handle complexity and data transformations in the main Go application code. This promotes separation of concerns and potentially easier testing of the core logic. Jinja2, while still advocating for separation, provides more built-in tools and flexibility for performing logic and transformations directly within the template, which can sometimes lead to more complex templates but potentially simpler calling code.

### 6.4. Feature Comparison Table

| **Feature**                           | **Go text/template (Ollama)**                                                                                                      | **Jinja2**                                                      |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| **Delimiter Syntax**                  | `{{... }}` for all actions; `{{/*... */}}` for comments                                                                            | `{{ expr }}`, `{% stmt %}`, `{# comment #}`                     |
| **Variable Output**                   | `{{.Field }}`, `{{ $var }}`                                                                                                        | `{{ variable }}`                                                |
| **Statement Blocks**                  | `{{ if }}`, `{{ range }}`, `{{ with }}`                                                                                            | `{% if %}`, `{% for %}`, `{% with %}`                           |
| **Built-in Filters/Functions**        | Minimal: logic (`and`, `or`, `not`), compare (`eq`, `ne`, `lt`...), `len`, `index`, `slice`, `print*`, `call`. Ollama adds `json`. | Rich: String case/manipulation, list/dict ops, math, date, etc. |
| **Custom Functions (In-Template)**    | Not supported (No macros)                                                                                                          | Supported (`{% macro... %}`)                                    |
| **Custom Functions (Pre-registered)** | Supported (`Funcs` method in Go code)                                                                                              | Supported (via Environment API)                                 |
| **Template Inheritance**              | Limited (`define`, `template`, `block`)                                                                                            | Robust (`{% extends %}`, `{% block %}`)                         |
| **Whitespace Control**                | `{{-... -}}`                                                                                                                       | `{%-... -%}`, `{{-... -}}`                                      |
| **Logic Complexity**                  | Intentionally limited                                                                                                              | More permissive                                                 |
| **Primary Ecosystem**                 | Go                                                                                                                                 | Python                                                          |


### 6.5. Implication for Conversion

The substantial differences, particularly the lack of filters and macros in Go `text/template` as used by Ollama, mean that converting a non-trivial Jinja2 template is rarely a direct line-by-line translation. The process necessitates adaptation, primarily by shifting data transformation logic from the template (where Jinja might handle it) to the application code that prepares the data *before* calling Ollama.

## 7. Converting Jinja2 Templates to Ollama `TEMPLATE`

Migrating templates from Jinja2 to Ollama's Go `text/template` format requires careful mapping of basic constructs and, more importantly, strategic handling of features not directly supported in Go templates, especially filters and macros.

### 7.1. Mapping Basic Constructs

- **Conditionals:**
- Jinja2: `{% if condition %}`... `{% elif other_condition %}`... `{% else %}`... `{% endif %}`
  - Go: `{{ if pipeline }}`... `{{ else if pipeline }}`... `{{ else }}`... `{{ end }}`
- **Loops:**
  - Jinja2: `{% for item in items %}`... `{% else %}`... `{% endfor %}` (uses `loop` variable)
  - Go: `{{ range pipeline }}`... `{{ else }}`... `{{ end }}` (uses `.` for item)
- **Variable Output:**
  - Jinja2: `{{ variable }}` or `{{ object.attribute }}`
  - Go: `{{.Field }}`, `{{ $variable }}`, `{{.MapKey }}`
- **Comments:**
  - Jinja2: `{# comment #}`
  - Go: `{{/* comment */}}`

### 7.2. Strategies for Handling Missing Filters (Data Pre-processing)

This is the most significant challenge. Since Go `text/template` lacks Jinja2's extensive filter library , and Ollama only adds `json` , the necessary data transformations must typically be performed *before* the data is passed to the Ollama template.

- **Primary Strategy: Pre-process Data:** The recommended approach is to modify the application code that calls the Ollama API. Perform any data manipulations (string formatting, list joining, calculations, sorting, etc.) that were previously handled by Jinja2 filters in your application logic, and then pass the *already transformed* data into the Ollama API context.
  - **Example (String Case):**
    - Jinja2: `{{ user.name | title }}`
    - Go/Ollama Approach: In the calling application (e.g., Python, Go, JavaScript), capitalize `user.name` *before* creating the API request payload. Pass the capitalized name (e.g., in a variable `UserName`).
    - Ollama Template: `{{.UserName }}`
  - **Example (List Joining):**
    - Jinja2: `{{ item_list | join(', ') }}`
    - Go/Ollama Approach: In the calling application, join the `item_list` into a single comma-separated string. Pass this string (e.g., `JoinedItems`).
    - Ollama Template: `{{.JoinedItems }}`
- **Limited Workarounds (`printf`):** For very simple formatting, Go's built-in `printf` function can sometimes be used, but it quickly becomes complex and is not a general replacement for filters. For instance, simple padding or basic type formatting is possible, but string replacements or complex manipulations are not.
- **The `json` Function:** Remember that Ollama *does* provide the `json` function, which is essential for handling structured data like tool call arguments.

### 7.3. Handling Macros

Jinja2 macros (`{% macro... %}`) have no direct equivalent for definition *within* the Ollama `TEMPLATE` string. The logic contained within Jinja2 macros must be refactored:

- **Move Logic to Application:** Implement the macro's functionality as a regular function or method in your calling application code.
- **Pass Results:** Call this application function and pass its results into the data context for the Ollama template.
- **Alternative (Go `define`/`template`):** For simple, reusable *static* or *data-driven* fragments *without complex logic*, Go's `{{ define "name" }}...{{ end }}` and `{{ template "name".Data }}` could be used, but they cannot replicate the argument passing and internal logic capabilities of Jinja2 macros. This is generally not a direct replacement.

### 7.4. Troubleshooting Common Conversion Issues

- **Variable Scope (`.` vs `$.`):** Remember that `range` and `with` change the context (`.`). If you need to access a variable from the root data context inside these blocks, use the `$` prefix (e.g., `$.System` or `$.Tools`).
- **Function/Filter Availability:** Double-check that you are only using Go's standard built-in functions (`eq`, `len`, `and`, etc.) and Ollama's custom `json` function. Calls to unavailable functions (like Jinja filters `title` or `join`) will result in errors.
- **Case Sensitivity:** Ensure correct capitalization for accessing data fields, especially nested ones (`.Messages`, `.Role`, `.ToolCalls`, `.Function.Name`). Mismatched cases might lead to missing data or errors (though `missingkey=zero` can mask some issues).
- **`missingkey=zero` Masking Errors:** Be aware that the `missingkey=zero` option used by Ollama can hide problems. If a template silently outputs an empty string or zero where data is expected, verify that the corresponding key/field exists in the data context and is spelled correctly (including case).
- **Syntax Clashes:** While less common for LLM prompts than web development, if generating output that itself uses `{{ }}` (e.g., templating code that uses Go templates), you would need escaping strategies. Jinja2 uses `{% raw %}`...`{% endraw %}` or variable expressions `{{ '{{' }}`. Go templates don't have a direct `raw` block, often requiring literal string construction or careful use of template variables containing the delimiters.

## 8. Conclusion & Best Practices

Ollama's `TEMPLATE` directive, powered by Go's `text/template` engine, offers a robust mechanism for structuring prompts tailored to specific LLMs. Its strengths lie in its integration with the Go ecosystem, relative simplicity for basic tasks, and the performance benefits of using a standard library component. However, its effectiveness hinges on understanding its specific implementation within Ollama and its inherent limitations compared to more feature-rich engines like Jinja2.

The most significant limitations are the minimal set of built-in functions (lacking common string/list manipulation filters) and the inability to define custom logic (macros) directly within the template string. This necessitates a different approach, particularly for those migrating from Jinja2, where data transformation logic often needs to be shifted from the template into the calling application code.

**Best Practices for Authoring Ollama Templates:**

- **Consult Model Defaults:** Before creating a custom template, inspect the model's default template using `ollama show --modelfile <model_name>`. This often provides the correct structure and special tokens.
- **Control Whitespace:** Use `{{-` and `-}}` judiciously, especially around control structures (`if`, `range`), to prevent unwanted whitespace and newlines in the final prompt.
- **Manage Dot Scope:** Be mindful that `.` changes within `range` and `with`. Use `$.` to reliably access fields from the root data context when needed.
- **Leverage the `json` Function:** Use `{{.Arguments | json }}` or similar when formatting structured data like tool call arguments to ensure correct JSON representation.
- **Keep Templates Focused:** Embrace the Go philosophy: use templates primarily for structuring the prompt and inserting pre-processed data. Avoid complex logic within the template; handle transformations in your application code.
- **Test Iteratively:** Build and test complex templates incrementally. Verify the output for different scenarios (e.g., with/without system prompt, with/without tools, varying message history). Use `ollama show --modelfile your-custom-model` to review the parsed template.

By understanding the specific features provided by Go's `text/template` within the Ollama context—including the crucial `json` function, the implications of `missingkey=zero`, the available variables (`.Messages`, `.Tools`, etc.), and the standard control structures—developers can effectively harness the `TEMPLATE` directive to guide LLM behaviour and integrate advanced features like chat history and tool calling. While conversion from systems like Jinja2 requires adapting data preparation strategies, mastering Ollama templates is essential for unlocking the full potential of locally run language models.
