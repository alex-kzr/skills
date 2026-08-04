---
name: camunda-8-bpmn-update
description: Create or update BPMN 2.0 diagram files that are valid for Camunda 8 (Zeebe engine) and renderable in Camunda Modeler 5.x. Use when the task involves writing a new .bpmn file, fixing an invalid .bpmn file, adding or modifying BPMN elements (service tasks, gateways, events, conditions), or validating an existing diagram against the BPMN 2.0 XSD and Camunda 8 semantic rules.
---

# Camunda 8 BPMN Update

## Workflow

1. Read [references/camunda8-bpmn-rules.md](references/camunda8-bpmn-rules.md) for required namespaces, element patterns, and common mistakes.
2. Create or edit the `.bpmn` file.
3. Validate with [scripts/validate_bpmn.py](scripts/validate_bpmn.py).
4. Fix any reported errors and re-validate until the output is `OK: <file> is valid for Camunda 8.`

## Validation Script

```bash
python .agents/skills/diagramming/camunda-8-bpmn-update/scripts/validate_bpmn.py <file.bpmn>
python .agents/skills/diagramming/camunda-8-bpmn-update/scripts/validate_bpmn.py <file.bpmn> --strict
```

Requires `lxml`. Exit code 0 = valid, 1 = errors, 2 = IO/usage error.

Dependencies are provided by the shared agents runtime:

- Python: `agents/runtime/python/base/.venv`

Do not install dependencies inside this skill directory.

The script runs two passes:
- **XSD pass** — validates against the OMG BPMN 2.0 XSD ([references/xsd/BPMN20.xsd](references/xsd/BPMN20.xsd) + imports).
- **Semantic pass** — checks Camunda 8 / Zeebe rules not covered by XSD: `isExecutable`, `zeebe:taskDefinition` on service tasks, condition presence on exclusive gateway flows, end event without outgoing flows, broken `sourceRef`/`targetRef` references.

`--strict` upgrades warnings (best-practice violations) to errors.

## Minimal Valid Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  id="Definitions_1"
  targetNamespace="http://bpmn.io/schema/bpmn"
  exporter="Camunda Modeler"
  exporterVersion="5.0.0">

  <bpmn:process id="my-process" name="My Process" isExecutable="true">
    <bpmn:startEvent id="Start_1">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="End_1">
      <bpmn:incoming>Flow_1</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="End_1" />
  </bpmn:process>

  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="my-process">
      <bpmndi:BPMNShape id="Start_1_di" bpmnElement="Start_1">
        <dc:Bounds x="152" y="82" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="End_1_di" bpmnElement="End_1">
        <dc:Bounds x="352" y="82" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="100" />
        <di:waypoint x="352" y="100" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

## Key Rules (Quick Reference)

- `BPMNDiagram` section is **required** — Modeler cannot open files without it.
- Conditions use FEEL with leading `=` and XML-escaped operators: `=amount &gt; 100`.
- `<bpmn:serviceTask>` requires `<zeebe:taskDefinition type="..."/>` inside `<bpmn:extensionElements>`.
- `<bpmn:outgoing>` / `<bpmn:incoming>` text must exactly match the `id` of the `<bpmn:sequenceFlow>`.
- Non-default flows on `<bpmn:exclusiveGateway>` must have `<bpmn:conditionExpression>`.

See [references/camunda8-bpmn-rules.md](references/camunda8-bpmn-rules.md) for full patterns including timers, messages, user tasks, and variable mapping.

## XSD Files

The [references/xsd/](references/xsd/) directory contains the official OMG BPMN 2.0 schema:
- `BPMN20.xsd` — root entry point (imports BPMNDI, includes Semantic)
- `Semantic.xsd` — all BPMN element definitions
- `BPMNDI.xsd` — diagram interchange types
- `DC.xsd`, `DI.xsd` — diagram common / interchange base types

Source: [bpmn-io/bpmn-moddle](https://github.com/bpmn-io/bpmn-moddle/tree/main/resources/bpmn/xsd) (same XSD used by Camunda Modeler internally).
