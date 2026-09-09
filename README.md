# Unity AI Gateway Lab

Govern a real generative AI application with **Unity Gateway**, the central control plane that extends Unity Catalog governance to live AI traffic: routing, rate limits, budgets, usage tracking, and content guardrails on every request and response.

**Duration** ~60 min  ·  **Level** Intermediate to Advanced (200/300)  ·  **Format** 1 short lecture + 1 hands-on demo

---

## What you'll do

You take a working agentic app (it generates Databricks-native diagrams as code) and progressively harden its governance through Unity Gateway. By the end you can:

- **Explain** how Unity Gateway adds a traffic control plane on top of Unity Catalog's asset governance.
- **Create and configure** a model service and grant an application's service principal access to it.
- **Set up** inference tables for request/response logging.
- **Apply** rate limits, an output guardrail (hallucination policy), traffic splitting, and fallback routing across models.
- **Query** `system.ai` and `system.ai_gateway` for usage, cost, and risk telemetry.

---

## Prerequisites

Check these before you start. The demo notebook opens with a **preflight cell** that verifies most of them automatically and prints a pass/fail checklist.

| Requirement | Why it matters | How to check |
|---|---|---|
| Unity Catalog-enabled workspace | The lab creates a catalog, schema, and governed assets | Catalog explorer is available in the workspace |
| **Serverless notebooks, environment version 5** | Setup runs only on this version | Environment side panel shows version `5` |
| A catalog you can write to | Setup creates the lab schema in it | You can create a schema (see Troubleshooting if catalog creation fails) |
| Foundation Model endpoints (Claude / GPT) | The gateway routes traffic to these | `databricks serving-endpoints list` shows `databricks-claude-*` / `databricks-gpt-*` |
| Databricks Apps enabled + create permission | Setup deploys the agent app | You can create an app in the workspace |
| **Beta preview: Service policies** | Required for the guardrail step | Enabled under Previews (account admin) |
| **Beta preview: Managed MLflow Prompt Registry** | Powers the "My Agent" prompt panel | Enabled under Previews (account admin) |

> **Tip:** If you cannot create a catalog (for example, your account uses UC Default Storage), point the lab at an existing catalog you can write to by adding an override on the setup line:
> ```
> %run ./Includes/Classroom-Setup-1 $catalog_override="an_existing_catalog"
> ```

---

## Quick start

1. Open **`01 Lecture - Unity Gateway Basics`** and read through the fundamentals.
2. Open **`02 Demo - Unity Gateway for Agent Applications`**:
   - Run the **preflight** cell and resolve any `[FAIL]` items.
   - Run the **Classroom Setup** cell. It deploys the agent app and takes about 3 to 4 minutes.
3. Work through the demo cells in order.

> **Expected:** right after setup, the app is running but shows an **onboarding overlay**. That is by design. The app has no model service or access grant yet; creating the model service and granting it `EXECUTE` is the first hands-on step. The chat starts working once you complete it.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `CREATE CATALOG` fails with **"Metastore storage root URL does not exist"** (UC Default Storage) | Add `$catalog_override="an_existing_catalog"` to the setup line (a catalog you can create schemas in), **or** set `catalog.managed_location` in `Includes/config/config-1.yaml` to a storage URL you own, **or** ask an admin to configure a metastore storage root. |
| **"This lab requires Serverless environment version 5"** | Open the Environment side panel, set version to `5`, click Apply, and re-run. If version 5 is not offered, it is not available in your workspace/region yet. |
| Guardrail step won't work / prompt panel is empty | Enable the two **Beta previews** (Service policies, Managed MLflow Prompt Registry) under Previews. This needs an account admin. Setup still completes without them. |
| Nothing to route to in the gateway | The workspace needs **Foundation Model API** endpoints (Claude/GPT). Confirm they are available in your region. |
| App can't list model services after setup | The app's service principal needs `USE CATALOG` / `USE SCHEMA` on the catalog. If you used a catalog you don't own, the setup log prints the exact `GRANT` statement for an admin to run. |
| App shows the onboarding overlay | Expected until you create a model service and grant it `EXECUTE` (first hands-on step). |

---

## Contents

- **`01 Lecture - Unity Gateway Basics`** — concepts and terminology
- **`02 Demo - Unity Gateway for Agent Applications`** — the hands-on demo (starts with a preflight check)
- **`agent-app/`** — the diagram-as-code agent application deployed and governed during the demo
- **`Includes/`** — classroom setup, configuration, and supporting library code
- Images and supporting materials

---

<sub>Original content by the **Databricks Curriculum Development Team**. Confidential: for internal use in individual customer engagements; keep this repository private. This is a hardened copy of the source lab with added deploy-robustness fixes (Default-Storage-safe catalog creation, a clearer serverless-version check, an exact grant hint, and a preflight prerequisite check) and expanded prerequisites and troubleshooting docs. Teaching flow, agent app, and gateway steps are unchanged from the original.</sub>
