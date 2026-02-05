# AgentCore Evaluations

LLM-as-a-Judge quality assessment for agents. Monitors AgentCore Runtime endpoints or CloudWatch LogGroups. Integrates with Strands and LangGraph via OpenTelemetry/OpenInference.

**Modes**: Online (continuous sampling) or on-demand
**Results**: CloudWatch GenAI dashboard, CloudWatch Metrics, configurable alerts

---

## Built-in Evaluators

**Quality Metrics**: Helpfulness, Correctness, Faithfulness, ResponseRelevance, Conciseness, Coherence, InstructionFollowing

**Safety Metrics**: Refusal, Harmfulness, Stereotyping

**Tool Performance**: GoalSuccessRate, ToolSelectionAccuracy, ToolParameterAccuracy, ContextRelevance

---

## Setup

**IAM Role** - Execution role needs:
- `logs:DescribeLogGroups`, `logs:GetLogEvents`
- `bedrock:InvokeModel`

**Instrumentation** - Requires ADOT (same as AgentCore Observability)

---

## Configuration

```python
from bedrock_agentcore_starter_toolkit import Evaluation

eval_client = Evaluation()

config = eval_client.create_online_config(
    config_name="my_agent_quality",
    agent_id="agent_myagent-ABC123xyz",
    sampling_rate=10.0,  # Evaluate 10% of interactions
    evaluator_list=["Builtin.Helpfulness", "Builtin.GoalSuccessRate", "Builtin.ToolSelectionAccuracy"],
    enable_on_create=True
)
```

**Data sources**:
- Agent endpoint (AgentCore Runtime)
- CloudWatch LogGroups (external agents, requires OTEL service name)

---

## Custom Evaluators

```python
custom_eval = eval_client.create_evaluator(
    evaluator_name="CustomerSatisfaction",
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    evaluation_prompt="""Assess customer satisfaction based on:
1. Query resolution (0-10)
2. Response clarity (0-10)
3. Tone appropriateness (0-10)
Return average score.""",
    level="Agent"  # or "Tool" for tool-level evaluation
)
```

---

## Results

**CloudWatch GenAI Dashboard**: CloudWatch → GenAI Observability → Evaluations tab

**CloudWatch Metrics**: `AWS/BedrockAgentCore/Evaluations`

**Alerts**:
```python
import boto3
cw = boto3.client('cloudwatch')

cw.put_metric_alarm(
    AlarmName='AgentQualityDegradation',
    MetricName='Helpfulness',
    Namespace='AWS/BedrockAgentCore/Evaluations',
    Statistic='Average',
    Period=3600,
    EvaluationPeriods=2,
    Threshold=7.0,
    ComparisonOperator='LessThanThreshold'
)
```
