# Camunda 8 / Zeebe BPMN Rules Reference

## Required Namespace Declarations

Every Camunda 8 BPMN file exported by Camunda Modeler 5.x must declare these namespaces on the root `<bpmn:definitions>` element:

```xml
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:modeler="http://camunda.org/schema/modeler/1.0"
  id="Definitions_..."
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler"
  exporterVersion="5.x.x">
```

- `zeebe:` and `modeler:` are optional if the diagram has no Zeebe extensions or modeler metadata.
- `xsi:` is required whenever `xsi:type` is used (e.g., on `<bpmn:conditionExpression>`).

## Diagram Section (BPMNDiagram)

Every BPMN file that Camunda Modeler can open **must** include a `<bpmndi:BPMNDiagram>` section with a `<bpmndi:BPMNPlane>` referencing the process and `<bpmndi:BPMNShape>` / `<bpmndi:BPMNEdge>` for each element. Without it, Modeler treats the file as unrenderable.

```xml
<bpmndi:BPMNDiagram id="BPMNDiagram_1">
  <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="<process-id>">
    <bpmndi:BPMNShape id="<element-id>_di" bpmnElement="<element-id>">
      <dc:Bounds x="..." y="..." width="..." height="..." />
    </bpmndi:BPMNShape>
    <!-- one BPMNEdge per sequenceFlow -->
    <bpmndi:BPMNEdge id="<flow-id>_di" bpmnElement="<flow-id>">
      <di:waypoint x="..." y="..." />
      <di:waypoint x="..." y="..." />
    </bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane>
</bpmndi:BPMNDiagram>
```

Standard element sizes (Camunda Modeler defaults):
| Element | width | height |
|---|---|---|
| startEvent / endEvent | 36 | 36 |
| task (serviceTask, manualTask, etc.) | 100 | 80 |
| exclusiveGateway | 50 | 50 |
| parallelGateway | 50 | 50 |
| subProcess | 350 | 200 |

## Process Rules

```xml
<bpmn:process id="my-process" name="My Process" isExecutable="true">
```

- `isExecutable="true"` is required; Zeebe ignores non-executable processes.
- `id` must be unique across the file and must not start with a digit.

## Element Connectivity Rules

- Every flow node (task, gateway, event) must connect through sequence flows.
- `sourceRef` and `targetRef` on `<bpmn:sequenceFlow>` must reference element IDs in the same process.
- `<bpmn:incoming>` / `<bpmn:outgoing>` text must match the `id` of the corresponding `<bpmn:sequenceFlow>`.
- Start events must not have incoming flows; end events must not have outgoing flows.

## Sequence Flow Conditions

Use `xsi:type="bpmn:tFormalExpression"` for condition expressions. Camunda 8 uses FEEL syntax; the expression must be prefixed with `=`:

```xml
<bpmn:sequenceFlow id="Flow_to_high" sourceRef="Gateway_1" targetRef="End_high">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=amount &gt; 100</bpmn:conditionExpression>
</bpmn:sequenceFlow>
```

Use XML entities for comparison operators: `&gt;` (`>`), `&lt;` (`<`), `&amp;` (`&`), `&gt;=` (`>=`), `&lt;=` (`<=`).

## Exclusive Gateway

```xml
<bpmn:exclusiveGateway id="Gateway_1" name="Check?" default="Flow_default">
  <bpmn:incoming>Flow_in</bpmn:incoming>
  <bpmn:outgoing>Flow_cond</bpmn:outgoing>
  <bpmn:outgoing>Flow_default</bpmn:outgoing>
</bpmn:exclusiveGateway>
```

- `default` attribute references the ID of the default outgoing flow (no condition required on that flow).
- All non-default outgoing flows must have a `<bpmn:conditionExpression>`.
- If there is no default and no condition matches at runtime, Zeebe raises an incident.

## Service Task (Zeebe Extension Required)

```xml
<bpmn:serviceTask id="Task_1" name="Call Payment API">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="payment-service" retries="3" />
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_in</bpmn:incoming>
  <bpmn:outgoing>Flow_out</bpmn:outgoing>
</bpmn:serviceTask>
```

- `zeebe:taskDefinition` with `type` is mandatory; Zeebe rejects deployment without it.
- `retries` defaults to 3 if omitted.
- Alternatively, use `<zeebe:calledDecision decisionId="..." resultVariable="..."/>` for DMN-linked tasks.

## Manual Task

```xml
<bpmn:manualTask id="Task_1" name="Review Document">
  <bpmn:incoming>Flow_in</bpmn:incoming>
  <bpmn:outgoing>Flow_out</bpmn:outgoing>
</bpmn:manualTask>
```

No Zeebe extension required. Zeebe treats manual tasks as pass-through (auto-complete); they are wait states only in custom implementations.

## User Task (Zeebe with Tasklist)

```xml
<bpmn:userTask id="Task_1" name="Approve Order">
  <bpmn:extensionElements>
    <zeebe:assignmentDefinition assignee="=initiator" candidateGroups="managers" />
    <zeebe:formDefinition formKey="embedded:deployment:approval-form.form" />
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_in</bpmn:incoming>
  <bpmn:outgoing>Flow_out</bpmn:outgoing>
</bpmn:userTask>
```

## Variable Mapping (Input / Output)

```xml
<bpmn:extensionElements>
  <zeebe:taskDefinition type="my-worker" />
  <zeebe:ioMapping>
    <zeebe:input source="=orderId" target="inputOrderId" />
    <zeebe:output source="=result" target="taskResult" />
  </zeebe:ioMapping>
</bpmn:extensionElements>
```

## Timer Events

```xml
<!-- Timer Start Event -->
<bpmn:startEvent id="TimerStart">
  <bpmn:timerEventDefinition id="TimerDef_1">
    <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>
  </bpmn:timerEventDefinition>
</bpmn:startEvent>

<!-- Timer Intermediate Catch Event -->
<bpmn:intermediateCatchEvent id="Timer_1">
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration xsi:type="bpmn:tFormalExpression">PT30M</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:intermediateCatchEvent>
```

ISO 8601 formats: `PT30M` (duration), `2025-01-01T00:00:00Z` (date), `R3/PT1H` (repeating).

## Message Events

```xml
<bpmn:message id="Message_1" name="order-received" />

<bpmn:startEvent id="MsgStart">
  <bpmn:messageEventDefinition messageRef="Message_1" />
  <bpmn:outgoing>Flow_1</bpmn:outgoing>
</bpmn:startEvent>
```

For intermediate catch, add `<zeebe:subscription correlationKey="=orderId" />` inside `<bpmn:extensionElements>` on the catch event.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Missing `BPMNDiagram` section | Add full `<bpmndi:BPMNDiagram>` with shapes and edges |
| `>` / `<` unescaped in conditions | Use `&gt;` / `&lt;` |
| Condition missing leading `=` | FEEL expressions must start with `=` |
| `serviceTask` without `zeebe:taskDefinition` | Add `<zeebe:taskDefinition type="..."/>` |
| `sourceRef`/`targetRef` referencing wrong IDs | IDs must match exactly (case-sensitive) |
| `<bpmn:incoming>` / `<bpmn:outgoing>` text not matching flow ID | Text content must be the flow's `id` attribute |
| `isExecutable="false"` | Change to `"true"` |
| Duplicate IDs within definitions | Each `id` must be unique in the file |
