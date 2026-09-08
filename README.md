# Unity Gateway

> **Attribution:** Original content by the **Databricks Curriculum Development Team** (Developer: Matthew McCoy). This repository is a hardened copy of the `genai-unity-gateway` lab from the internal `databricks-learning/enablement-medallion-labs` repo, with deploy-robustness fixes and expanded prerequisites/troubleshooting docs. Please credit the Curriculum Development Team if this content is shared or adapted.
>
> **Usage / distribution:** This content will later appear in paid, instructor-led courses. Keep it **private**. Use is limited to **individual customer engagements**, not at-scale or large events, unless you have approval from the **Learning & Enablement (L&E)** organization (contact Astrid Ng and Joey Frazee). **Do not publish it to a public repository.**

| Field           | Details       | Description                                                                 |
|-----------------|---------------|-----------------------------------------------------------------------------|
| Duration        | 60 minutes    | Estimated duration to complete the lab(s). |
| Level           | 200/300 | Target difficulty level for participants (100 = beginner, 200 = intermediate, 300 = advanced). |
| Lab Status      | Active | See descriptions in main repo README. |
| Course Location | N/A           | Lab is only available in this repo. |
| Developer       | Matthew McCoy | Primary developer(s) of the original lab. |
| Reviewer        | Michelle McSweeney, Joe Read, Jeffrey Lipkowitz, Julia Beck | Subject matter expert reviewer(s). |
| Product Version | N/A | Specify a product version if applicable. If not, use N/A. |
| Created Date    | 08/12/2026 | Original creation date (MM/DD/YYYY). |

**Required Previews**: Unity Gateway and model services are Generally Available, but this lab also uses two features that are still in Beta and must be enabled by an account admin under **Previews**: **Service policies** and **Managed MLflow Prompt Registry**. See [Known gotchas](#known-gotchas--troubleshooting) for what breaks if these are off.

---

## Description
[Unity Gateway](https://www.databricks.com/blog/unity-ai-gateway-generally-available) extends Unity Catalog governance to AI traffic. Unity Catalog already governs your models, MCP services, functions, and connections as securable objects; Unity Gateway adds a central control plane over the traffic to them, enforcing routing, rate limits, budgets, usage tracking, and **service policies** (guardrails) on every request and response.

This lab introduces the fundamentals through a short lecture and then puts them into practice with a hands-on demo. In the demo, you govern a real agentic application, one that generates Databricks-native diagrams as code, by routing it through Unity Gateway and progressively hardening its governance: creating a model service, granting permissions, adding inference tables, rate limits, a hallucination guardrail policy, traffic splitting across Claude models, and fallback routing. Finally, you explore the `system.ai` and `system.ai_gateway` schemas to see how telemetry and observability complement payload-level inference logging.

By the end of the lab, you will understand how asset, traffic, and behavior governance combine into a single control plane for AI, and how to apply those controls to a production-style generative AI application on Databricks.

## Learning Objectives
By the end of this lab, you will be able to:
- **Explain** what Unity Gateway is and how asset, traffic, and behavior governance combine into a single control plane for AI.
- **Distinguish** Unity Catalog (which governs AI assets as securables) from Unity Gateway (which governs the live traffic to them).
- **Describe** how the gateway manages routing and traffic, including endpoint fallback, rate limits, and budgets across multiple models and providers.
- **Differentiate** access policies (who can reach a service, via UC grants) from guardrails (what content is allowed, via service policies), including the allow / require-approval / deny outcomes.
- **Identify** how to monitor usage, cost, and risk using inference tables and usage tracking, and where that data lives for auditing and analysis.
- **Create and configure** a model service in Unity Gateway for an agentic application and grant EXECUTE permissions to the application's service principal.
- **Set up** inference tables for request/response logging and observability.
- **Configure** rate limits, an output guardrail (hallucination policy), traffic splitting, and fallback routing across multiple models.
- **Query** the system catalog tables (`system.ai`, `system.ai_gateway`) for usage telemetry.

## Requirements & Prerequisites

Confirm each of these before you run the classroom setup. The demo notebook includes an optional **preflight cell** (top of `02 Demo`) that checks most of them automatically and prints a PASS / WARN / FAIL checklist.

| Prerequisite | Why | How to verify |
|---|---|---|
| **Unity Catalog enabled** workspace | The lab creates a catalog, schema, and UC-governed assets | Workspace shows a Catalog explorer; `databricks catalogs list` returns results |
| **Serverless notebooks, environment version 5** | The setup hard-gates on Serverless env v5 and stops otherwise | Environment side panel in the notebook shows version `5`. If it is not offered, your workspace/region does not have it yet |
| **A catalog you can write to** | Setup creates the lab schema in it | You can create a schema in the target catalog. See gotcha #1 if catalog creation itself fails |
| **Foundation Model API endpoints** (Claude / GPT pay-per-token) | The gateway routes to `system.ai` model services backed by these | `databricks serving-endpoints list` shows `databricks-claude-*` and/or `databricks-gpt-*` |
| **Databricks Apps enabled + permission to create apps** | Setup deploys the agent app via the SDK | You can open Apps in the workspace and create one |
| **Beta preview: Service policies** | Required for the hallucination guardrail step | Account admin confirms it is ON under Previews |
| **Beta preview: Managed MLflow Prompt Registry** | Powers the "My Agent" prompt panel (setup degrades gracefully if off) | Account admin confirms it is ON under Previews |
| **Basic familiarity with Unity Catalog** | Navigating catalog/schema/object and the workspace UI | N/A |

If your catalog access is restricted, or your account uses UC Default Storage, pass a `$catalog_override` (see gotcha #1):

```
%run ./Includes/Classroom-Setup-1 $catalog_override="an_existing_catalog_you_can_write_to"
```

## Known gotchas & troubleshooting

These are the failure modes most likely to trip up a clone-and-deploy in a workspace other than the one the lab was built in.

**1. `CREATE CATALOG` fails: "Metastore storage root URL does not exist" / Default Storage.**
On accounts that use UC **Default Storage** (or whose metastore has no storage root), the default path that auto-creates `labuser_<user>` fails because a catalog needs an explicit `MANAGED LOCATION`. Fix with any one of:
- Pass `$catalog_override="<existing_catalog>"` on the `%run ./Includes/Classroom-Setup-1` line, pointing at a catalog you can already `CREATE SCHEMA` in. (Simplest.)
- Set `catalog.managed_location` in `Includes/config/config-1.yaml` to an external-location URL you own (e.g. `s3://<bucket>/uc/`), then re-run.
- Ask an account admin to configure a metastore storage root.

The hardened setup catches this error and prints these three options instead of a raw stack trace.

**2. "This lab requires Serverless environment version 5."**
The setup only runs on Serverless with runtime `client.5.*`. On classic compute or an older serverless version it stops immediately. Open the Environment side panel, set version to `5`, click Apply, and re-run. If version 5 is not offered in your workspace or region, it is not available to you yet; contact your workspace admin.

**3. The two Beta previews are account-admin toggles.**
**Service policies** and **Managed MLflow Prompt Registry** must be enabled under Previews by an account admin, which can be slow in customer orgs. Impact if off: setup still succeeds (prompt registration is best-effort and falls back to the app's built-in prompt), but the **hallucination guardrail** step (Service policies) cannot be completed and the prompt-registry panel degrades. Enable both before the engagement.

**4. Foundation Model API availability.**
The gateway steps route to `system.ai` model services backed by Foundation Model API endpoints, and the traffic-splitting step assumes multiple Claude endpoints exist. A workspace/region without pay-per-token Foundation Model APIs (or restricted to external models only) will have nothing to route to.

**5. App service-principal grant fails when you don't own the override catalog.**
Setup grants the app's service principal `USE CATALOG` / `USE SCHEMA` so the app can list model services. If you pointed `$catalog_override` at a **shared** catalog you don't own/MANAGE, the grant fails (best-effort, non-fatal) and the app stays in its onboarding overlay. The setup log prints the exact `GRANT ... TO <app-sp>` statement for an admin to run.

**6. The app boots into an onboarding overlay. That is expected.**
After setup the app is RUNNING but shows an onboarding overlay, because no model service exists in the lab schema yet and the app SP has no `EXECUTE` grant. Creating the model service and granting `EXECUTE` in Unity AI Gateway is the first hands-on step (section B1). The chat does not answer until you complete it.

**Minor.** App names are `agent-<userslug>` truncated to 30 chars and catalogs use `labuser_<user>` truncated to 19; in a shared workspace two similar usernames can collide. Setup pins `databricks-sdk==0.123.0` over the serverless built-in.

## Deploying with or for a customer

- This repo is **private** by license. To let a customer clone it, add them as a collaborator on this repo rather than making it public. Alternatively, import the folder into their workspace for them (`databricks workspace import-dir . /Workspace/Users/<them>/genai-unity-gateway`).
- Walk the [prerequisites table](#requirements--prerequisites) with them first, especially the **Beta previews** (need their account admin) and **Serverless env v5**, since those have the longest lead time.
- Run the preflight cell together before setup.

## Contents
This repository includes:
- **01 Lecture - Unity Gateway Basics** notebook
- **02 Demo - Unity Gateway for Agent Applications** notebook (with an added preflight cell)
- **agent-app** the diagram-as-code agent application deployed and governed during the demo
- **Includes** classroom setup, configuration, and supporting library code (includes the added `_lib/preflight_check.py`)
- Images and supporting materials

## Getting Started
1. Open the notebook **01 Lecture - Unity Gateway Basics** and read through the basics.
1. Open **02 Demo - Unity Gateway for Agent Applications**. Run the **preflight** cell first and resolve any `[FAIL]` items, then run the classroom setup cell (this deploys the agent app and takes ~3-4 minutes).
1. Follow the instructions step by step, progressing through the notebooks in numerical order.

## What changed vs. the original lab

This is a hardened copy. The teaching flow, agent app, and gateway steps are unchanged. Modifications:

- `Includes/_lib/catalog_utils.py`: `build_user_catalog` accepts an optional `managed_location`, and catches the "no metastore storage root" (Default Storage) failure to re-raise it with three concrete fixes.
- `Includes/_lib/setup_orchestrator.py`: passes `catalog.managed_location` through; the serverless-version check now reports the detected environment and the exact steps to switch to version 5.
- `Includes/_lib/app_deployer.py`: the best-effort model-service grant now prints the exact `GRANT ... TO <app-sp>` statement and notes the shared-catalog case.
- `Includes/_lib/preflight_check.py` (new): non-fatal prerequisite checklist.
- `02 Demo - Unity Gateway for Agent Applications`: added a preflight cell above Classroom Setup.
- `Includes/config/config-1.yaml`: documented the optional `catalog.managed_location` knob.
- `README.md`: expanded prerequisites, added this section, the gotchas/troubleshooting section, and the customer-deploy notes.
