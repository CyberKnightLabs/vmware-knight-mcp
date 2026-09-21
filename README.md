<!-- mcp-name: io.github.cyberknightlabs/vmware-knight -->

# VMware Knight

VMware Knight is an MCP-powered VMware operations toolkit for managing **vCenter Server** and **standalone ESXi hosts** through AI-assisted and command-line workflows.

It is designed for environments where operators need to work across multiple VMware targets without constantly remembering long FQDNs, IP addresses, or editing configuration files by hand.

Two VMware Knight features are especially important:

- **Friendly target tags** — assign a simple alias such as `lab-vcenter`, `prod-vcenter`, or `esxi-lab-01` to each VMware target and use that alias directly from Claude, Codex, the MCP server, or the CLI.
- **Interactive management wizard** — add, edit, remove, tag, test, and configure VMware targets through a guided terminal interface.

VMware Knight also includes VMware lifecycle, deployment, guest operations, cluster management, datastore browsing, alarm operations, investigation workflows, scheduled scanning, plan/apply workflows, and an MCP server for AI-assisted operations.

> VMware Knight is a community project and is not an official VMware product.

> **Platforms:** macOS, Linux and Windows 10/11. Windows users: see [Option C — Windows](#option-c--windows) for installation, and [docs/windows-codex.md](docs/windows-codex.md) for Codex.

---

## About the Author

**[Ehsan Emad](https://www.linkedin.com/in/ehsanemad/)**

Technology Lead | Principal Solutions Architect | Strategic Advisory | Enterprise Networking | Cybersecurity | Data Center | Agentic AI Enthusiast | MBA | CCDE #20210029 | 4× CCIE #28551 | CISSP | 2× NSE 7 | OpenShift Certified | Cisco Champion | Cisco Fire Jumper Elite

Ehsan Emad is a technology leader and principal solutions architect with extensive experience across enterprise networking, cybersecurity, data center architecture, infrastructure automation, and technical advisory.

He is the creator of **VMware Knight**, **Cisco Knight Multi-Device MCP**, **Networking With Ehsan**, and the **TechLoungeCast** podcast.

VMware Knight was created to make VMware infrastructure easier to operate through modern AI and MCP workflows while keeping target selection explicit, understandable, and manageable across environments containing multiple vCenter Servers and standalone ESXi hosts.

- **GitHub:** [CyberKnightLabs](https://github.com/CyberKnightLabs)
- **LinkedIn:** [Ehsan Emad](https://www.linkedin.com/in/ehsanemad/)
- **Networking With Ehsan:** [networkingwithehsan.com](https://www.networkingwithehsan.com/)
- **TechLoungeCast:** [techloungecast.com](https://techloungecast.com/)
- **Podcast:** [Listen on Apple Podcasts](https://podcasts.apple.com/ca/podcast/techloungecast/id1847186556)

---

# 1. Friendly Target Tags

Managing several vCenter Servers and standalone ESXi hosts can become difficult when every operation depends on remembering IP addresses, FQDNs, or long infrastructure names.

VMware Knight adds an optional **friendly tag/alias** to every VMware target.

Instead of asking an AI assistant to operate against:

```text
vc.networkingwithehsan.local
```

you can assign:

```text
lab-vcenter
```

and then simply ask:

```text
Using VMware Knight, list all VMs on lab-vcenter.
```

The same idea works for standalone ESXi hosts:

```text
esxi-lab-01
esxi-lab-02
esxi-edge-01
```

## How target resolution works

A configured VMware target can be referenced by:

1. **Friendly tag**
2. **Configured target name**
3. **Hostname or IP address**

Example:

```yaml
targets:
  - name: vcenter
    tag: lab-vcenter
    host: vc.networkingwithehsan.local
    type: vcenter
    username: administrator@vsphere.local
    port: 443
    verify_ssl: false
```

All of the following resolve to the same target:

```text
lab-vcenter
vcenter
vc.networkingwithehsan.local
```

The friendly tag is normally the easiest identifier to use with Claude or Codex.

## Example prompts

```text
Show me the VMs on lab-vcenter.
```

```text
Check cluster health on prod-vcenter.
```

```text
List the VMs running on esxi-lab-01.
```

```text
Show active alarms on dr-vcenter.
```

## Tag safety

VMware Knight validates identifiers to prevent ambiguous target selection.

A tag cannot conflict with the name, hostname/IP, or tag of another configured target.

Target matching is case-insensitive, so these refer to the same configured identifier:

```text
lab-vcenter
LAB-VCENTER
Lab-vCenter
```

Tags are optional. Existing target names and hostname/IP references remain valid.

For multi-vCenter and multi-ESXi environments, descriptive tags are recommended.

---

# 2. Interactive Management Wizard

VMware Knight includes a guided terminal wizard so you do not need to manually edit the VMware target YAML configuration for normal day-to-day management.

Start it with:

```bash
vmware-knight wizard
```

The wizard displays:

```text
VMware Knight Management Wizard

1. List VMware targets
2. Add VMware target
3. Edit VMware target
4. Remove VMware target
5. Set/Change target tag
6. Test connections
7. Configure MCP clients
8. Exit
```

## 2.1 List VMware targets

Choose:

```text
1. List VMware targets
```

The wizard displays the configured targets with information such as:

- target name
- friendly tag
- target type
- hostname or IP address
- username
- port

This makes it easy to confirm the exact identifiers available to the MCP server.

---

## 2.2 Add a VMware target

Choose:

```text
2. Add VMware target
```

The wizard guides you through adding either:

- a **vCenter Server**
- a **standalone ESXi host**

You are prompted for the target information, including:

- target name
- friendly tag/alias
- hostname or IP address
- target type
- username
- HTTPS port
- TLS certificate verification preference
- password

The configuration is validated before it is accepted.

Example:

```text
Target name: vcenter
Friendly tag/alias: lab-vcenter
vCenter/ESXi host: vc.networkingwithehsan.local

Target type:
1. vCenter
2. ESXi

Select target type: 1
Username: administrator@vsphere.local
Port: 443
Verify TLS certificate? No
Password: ********
```

After enrollment, the target can be referenced by the friendly tag:

```text
lab-vcenter
```

---

## 2.3 Edit a VMware target

Choose:

```text
3. Edit VMware target
```

The wizard shows the configured targets and asks which one you want to modify.

You can update:

- name
- tag
- hostname/IP
- vCenter or ESXi target type
- username
- port
- TLS verification
- password

If you rename a target, VMware Knight migrates the stored credential reference to the new target name.

The configuration is validated before the change is accepted.

---

## 2.4 Remove a VMware target

Choose:

```text
4. Remove VMware target
```

The wizard asks you to select the target and confirm removal.

Removing a target removes:

- the target from VMware Knight configuration
- its stored password entry

The wizard requires confirmation before completing the removal.

---

## 2.5 Set or change a target tag

Choose:

```text
5. Set/Change target tag
```

This option provides a fast way to change only the friendly alias without editing the rest of the target configuration.

Example:

```text
vcenter -> lab-vcenter
```

or:

```text
esxi-01 -> esxi-lab-01
```

The new tag is validated against the identifiers of all other targets before it is saved.

---

## 2.6 Test VMware connections

Choose:

```text
6. Test connections
```

VMware Knight runs its connection and environment checks against the configured targets.

Use this after:

- adding a new vCenter
- adding an ESXi host
- changing a password
- changing a hostname/IP
- modifying TLS settings
- troubleshooting MCP connectivity

You can also run the diagnostic command directly:

```bash
vmware-knight doctor
```

---

## 2.7 Configure MCP clients

Choose:

```text
7. Configure MCP clients
```

VMware Knight currently focuses its wizard-driven MCP configuration on:

1. **Claude Desktop**
2. **OpenAI Codex**

The wizard asks for the VMware Knight executable path and writes or updates the selected MCP client configuration.

The default executable location is typically:

```text
~/.local/bin/vmware-knight                        # macOS / Linux
%USERPROFILE%\.local\bin\vmware-knight.exe        # Windows
```

Both options work on Windows: the wizard uses the Windows config locations, adds `.exe` to the path, and passes your home folder to the server (see [Claude Desktop on Windows](#claude-desktop-on-windows)).

The generated MCP server name is:

```text
vmware-knight
```

---

# 3. Installation

## Option A — Clone from GitHub

This is the recommended installation method.

```bash
git clone https://github.com/CyberKnightLabs/vmware-knight-mcp.git
cd vmware-knight-mcp
```

Install VMware Knight with `uv`:

```bash
uv tool install .
```

You can also install directly from GitHub without cloning:

```bash
uv tool install git+https://github.com/CyberKnightLabs/vmware-knight-mcp.git
```

Or with `pip`:

```bash
pip install git+https://github.com/CyberKnightLabs/vmware-knight-mcp.git
```

Verify the CLI installation:

```bash
vmware-knight --help
```

A successful installation provides these executables:

```text
vmware-knight
vmware-knight-mcp
```

> `vmware-knight-mcp` is a stdio MCP server entry point. It is normally started by an MCP client and may appear to wait silently if launched directly from a terminal. Use `vmware-knight --help` to verify the installation.

---

## Option C — Windows

VMware Knight runs natively on Windows 10 and 11. Run these commands in **PowerShell** (no administrator rights needed).

Install `uv` and Git, if you don't have them yet:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
winget install --id Git.Git -e
```

`uv` downloads a suitable Python automatically, so you don't need to install Python separately. Git is needed because VMware Knight is installed straight from GitHub.

Open a **new** PowerShell window, then install VMware Knight:

```powershell
uv tool install git+https://github.com/CyberKnightLabs/vmware-knight-mcp.git
uv tool update-shell
```

`uv tool update-shell` adds `%USERPROFILE%\.local\bin` to your `PATH`. Open a new PowerShell window again, then verify:

```powershell
where.exe vmware-knight
vmware-knight --help
```

`where.exe` should print a path like:

```text
C:\Users\USERNAME\.local\bin\vmware-knight.exe
```

Then run the wizard to add your targets, exactly as on macOS:

```powershell
vmware-knight wizard
```

Windows-specific notes:

| Topic | Windows |
|---|---|
| Config folder | `%USERPROFILE%\.vmware-knight\` (`config.yaml` and `.env`) |
| Executable | `%USERPROFILE%\.local\bin\vmware-knight.exe` |
| Codex config | `%USERPROFILE%\.codex\config.toml`: use the wizard, or the [Windows installer script](docs/windows-codex.md) |
| Claude Desktop config | `%APPDATA%\Claude\claude_desktop_config.json` (Microsoft Store installs: under `%LOCALAPPDATA%\Packages\Claude_*`): use the wizard; see [Claude Desktop on Windows](#claude-desktop-on-windows) |
| `.env` permissions | `vmware-knight doctor` reports the `.env` permission check as *unknown* on NTFS. This is expected, not a failure. |
| Find the executable | `where.exe vmware-knight` (instead of `which`) |

---

## Option B — Development Installation

Clone the repository:

```bash
git clone https://github.com/CyberKnightLabs/vmware-knight-mcp.git
cd vmware-knight-mcp
```

Create the project environment:

```bash
uv sync
```

Run VMware Knight directly from the source tree:

```bash
uv run vmware-knight --help
```

Start the management wizard:

```bash
uv run vmware-knight wizard
```

Start the MCP server:

```bash
uv run vmware-knight mcp
```

---

# 4. First-Time Setup

After installing VMware Knight, start the interactive management wizard:

```bash
vmware-knight wizard
```

The wizard can:

```text
1. List VMware targets
2. Add VMware target
3. Edit VMware target
4. Remove VMware target
5. Set/Change target tag
6. Test connections
7. Configure MCP clients
8. Exit
```

A recommended first-time sequence is:

```text
1. Add your vCenter or standalone ESXi target.
2. Assign a friendly tag such as lab-vcenter or production-vcenter.
3. Repeat for any additional VMware targets.
4. Run Test connections.
5. Configure your MCP client.
6. Start a fresh MCP client session.
7. Ask the AI client to use VMware Knight against one of your friendly tags.
```

Example environment:

```text
Name            Tag              Type       Host
--------------  ---------------  ---------  -------------------------------
vcenter         lab-vcenter      vcenter    vc.example.local
esxi-01         esxi-lab-01      esxi       10.10.10.51
esxi-02         esxi-lab-02      esxi       10.10.10.52
```

After setup, the AI assistant can use the friendly tag directly:

```text
Using VMware Knight, show me all VMs on lab-vcenter.
```

## Configure Codex

VMware Knight can install its MCP configuration directly into Codex.

> **Windows users:** the wizard (`vmware-knight wizard` → 7 → 2) and the command below both work on Windows. Use `where.exe vmware-knight` instead of `which`, and pass the `.exe` path, for example `--path "$env:USERPROFILE\.local\bin\vmware-knight.exe"`. There is also a standalone installer script that finds the executable for you; see [docs/windows-codex.md](docs/windows-codex.md).

First locate the installed VMware Knight executable:

```bash
which vmware-knight
```

Typical `uv` installations expose it through:

```text
~/.local/bin/vmware-knight
```

Install VMware Knight into Codex:

```bash
vmware-knight mcp-config install \
  --agent codex \
  --path ~/.local/bin/vmware-knight \
  --yes
```

VMware Knight resolves the real executable path and writes the MCP entry into:

```text
~/.codex/config.toml
```

The resulting Codex configuration is similar to:

```toml
[mcp_servers.vmware-knight]
command = "/Users/USERNAME/.local/share/uv/tools/vmware-knight/bin/vmware-knight"
args = ["mcp"]
enabled = true
startup_timeout_sec = 120
```

After installation, start a **fresh Codex session** so the MCP configuration is loaded.

If the Codex CLI is available, verify the server with:

```bash
codex mcp list
codex mcp get vmware-knight
```

On macOS installations where Codex is bundled inside the ChatGPT application but is not on your shell `PATH`, you can use:

```bash
/Applications/ChatGPT.app/Contents/Resources/codex mcp list
```

and:

```bash
/Applications/ChatGPT.app/Contents/Resources/codex mcp get vmware-knight
```

A healthy configuration should report:

```text
vmware-knight
  enabled: true
  transport: stdio
  args: mcp
```

Then test the live MCP connection from a fresh Codex session with a request such as:

```text
Use the VMware Knight MCP tool cluster_health_summary against target lab-vcenter with top_n=2.
```

A successful Codex session should show a tool call similar to:

```text
Called vmware-knight.cluster_health_summary(...)
```

This confirms Codex is using VMware Knight through MCP rather than reading local files.

---

# 5. Configuration Files

VMware Knight stores its configuration under:

```text
~/.vmware-knight/                     # macOS / Linux
%USERPROFILE%\.vmware-knight\         # Windows
```

Primary files include:

```text
~/.vmware-knight/config.yaml
~/.vmware-knight/.env
```

The main configuration can also be overridden with:

```text
VMWARE_KNIGHT_CONFIG
```

Example:

```bash
VMWARE_KNIGHT_CONFIG=/path/to/config.yaml vmware-knight doctor
```

On Windows (PowerShell):

```powershell
$env:VMWARE_KNIGHT_CONFIG = "C:\path\to\config.yaml"; vmware-knight doctor
```

## Example target configuration

```yaml
targets:
  - name: vcenter
    tag: lab-vcenter
    host: vc.networkingwithehsan.local
    type: vcenter
    username: administrator@vsphere.local
    port: 443
    verify_ssl: false

  - name: esxi-01
    tag: esxi-lab-01
    host: 10.10.10.51
    type: esxi
    username: root
    port: 443
    verify_ssl: false
```

For normal operation, use the wizard instead of manually editing this file.

---

# 6. MCP Client Setup

## Claude Desktop

VMware Knight can configure Claude Desktop automatically through the management wizard.

Start the wizard from any terminal after VMware Knight is installed:

```bash
vmware-knight wizard
```

Then select:

```text
7. Configure MCP clients
1. Claude Desktop
```

When prompted for the VMware Knight executable path, the default is typically:

```text
~/.local/bin/vmware-knight
```

Press **Enter** to accept the default path, then confirm the installation with **Y**.

VMware Knight resolves the real executable path automatically and writes the MCP configuration to:

```text
~/Library/Application Support/Claude/claude_desktop_config.json     # macOS
%APPDATA%\Claude\claude_desktop_config.json                         # Windows
```

A typical generated entry looks like:

```json
{
  "mcpServers": {
    "vmware-knight": {
      "command": "/Users/USERNAME/.local/share/uv/tools/vmware-knight/bin/vmware-knight",
      "args": ["mcp"]
    }
  }
}
```

After installation, fully quit Claude Desktop and reopen it so the new MCP server is loaded. Start a fresh chat before testing.

A simple validation prompt is:

```text
Using VMware Knight, list the configured VMware targets.
```

For an end-to-end live MCP test, use a request such as:

```text
Use the VMware Knight MCP tool cluster_health_summary against target lab-vcenter with top_n=2.
Do not inspect local files. Return the two live top issues from vCenter.
```

If Claude returns live vCenter data through VMware Knight, the MCP integration is working correctly.

If `vmware-knight` is not found before starting the wizard, verify the installation with:

```bash
which vmware-knight
vmware-knight --help
```

> `vmware-knight-mcp` is the stdio MCP server entry point used by MCP clients. You normally do not need to run it manually.

### Claude Desktop on Windows

The wizard works on Windows too: `vmware-knight wizard` → **7** → **1**, accept the default path, and confirm. It writes to the right place:

| Claude Desktop install | Config file |
|---|---|
| Installer from claude.ai | `%APPDATA%\Claude\claude_desktop_config.json` |
| Microsoft Store | `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json` |

On Windows, the generated entry also includes the `.exe` path and an `env` section with your home folder, so the server finds `%USERPROFILE%\.vmware-knight`:

```json
{
  "mcpServers": {
    "vmware-knight": {
      "command": "C:\\Users\\USERNAME\\.local\\bin\\vmware-knight.exe",
      "args": ["mcp"],
      "env": {
        "USERPROFILE": "C:\\Users\\USERNAME",
        "SYSTEMROOT": "C:\\WINDOWS",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

Then fully quit Claude Desktop (right-click its tray icon → **Quit**), reopen it, and start a new chat.

**Manual setup**, if you prefer to edit the file yourself or the wizard picked the wrong file:

1. In Claude Desktop, open **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json` in the right place for your install (usually `%APPDATA%\Claude\claude_desktop_config.json`).
2. Find your executable path with `where.exe vmware-knight`.
3. Add VMware Knight under `mcpServers`. In JSON, every backslash must be doubled:

```json
{
  "mcpServers": {
    "vmware-knight": {
      "command": "C:\\Users\\USERNAME\\.local\\bin\\vmware-knight.exe",
      "args": ["mcp"]
    }
  }
}
```

If the file already has other servers, add `"vmware-knight": { ... }` next to them inside the existing `mcpServers` object.

4. Fully quit Claude Desktop (right-click its tray icon → **Quit**), reopen it, and start a new chat.

---

## OpenAI Codex

The wizard can also configure Codex:

```bash
vmware-knight wizard
```

Then select:

```text
7. Configure MCP clients
2. Codex
```

A typical Codex configuration looks like:

```toml
[mcp_servers.vmware-knight]
command = "/Users/yourname/.local/bin/vmware-knight"
args = ["mcp"]
enabled = true
startup_timeout_sec = 120
```

On Windows, the wizard also adds `.exe` to the path and passes your home folder to the server:

```toml
[mcp_servers.vmware-knight]
command = "C:\\Users\\yourname\\.local\\bin\\vmware-knight.exe"
args = ["mcp"]
enabled = true
startup_timeout_sec = 120

[mcp_servers.vmware-knight.env]
USERPROFILE = "C:\\Users\\yourname"
SYSTEMROOT = "C:\\WINDOWS"
PYTHONUTF8 = "1"
# ...plus APPDATA, LOCALAPPDATA, TEMP and TMP
```

Codex does not need **Full Access** to use VMware Knight: MCP tools run outside the Codex shell sandbox. If Codex only works with Full Access, the MCP entry is not loading; see [docs/windows-codex.md](docs/windows-codex.md).

Restart Codex after changing its MCP configuration.

Example:

```text
Using VMware Knight, show me the VMs on esxi-lab-01.
```

---

# 7. How VMware Knight Works

The basic workflow is:

```text
User
  |
  v
Claude / Codex
  |
  v
VMware Knight MCP Server
  |
  +--> resolve target by tag / name / host
  |
  v
pyVmomi / vSphere APIs
  |
  +--> vCenter Server
  |      |
  |      +--> Clusters
  |      +--> ESXi Hosts
  |      +--> Virtual Machines
  |      +--> Datastores
  |
  +--> Standalone ESXi Host
```

When the AI sends a target such as:

```text
lab-vcenter
```

VMware Knight resolves that identifier to the configured VMware target before establishing the connection.

---

# 8. Capabilities Overview

VMware Knight includes operations across the following areas:

| Area | Capabilities |
|---|---|
| **VM Lifecycle** | Power operations, VM creation, deletion, reconfiguration, snapshots, clone, migration |
| **Deployment** | OVA deployment, templates, linked clones, ISO attachment, batch deployment |
| **Guest Operations** | Command execution, file upload, file download |
| **Plan / Apply** | Multi-step execution plans with review and rollback support |
| **Cluster Management** | Cluster information, creation, deletion, HA/DRS configuration, host membership |
| **Datastore** | Browse datastore content and discover deployment images |
| **Networking** | Distributed port group and host VMkernel management workflows |
| **Alarm Management** | List, acknowledge, and reset triggered alarms |
| **Investigation** | VM, host, datastore, cluster, and cross-vCenter investigation workflows |
| **Scanning** | Scheduled alarm, event, and ESXi host-log scanning |
| **Notifications** | JSONL logging and webhook-based notification workflows |
| **MCP** | Structured VMware operations through Claude and Codex |
| **CLI** | Direct command-line operation without an AI client |

---

# 9. Quick Investigation Workflows

VMware Knight includes read-oriented investigation commands that help identify problems before making changes.

Examples:

```bash
vmware-knight attention
```

Show issues requiring attention across configured vCenter targets.

```bash
vmware-knight summary
```

Show a cluster-oriented health summary.

```bash
vmware-knight investigate vm web-01 --hours 72
```

Correlate information around a VM.

```bash
vmware-knight investigate host esxi-01
```

Correlate information around a host.

```bash
vmware-knight investigate datastore datastore1
```

Correlate information around a datastore.

Offline HTML output is also available for supported investigation workflows:

```bash
vmware-knight investigate vm web-01 --html
```

Some investigation workflows delegate read-only aggregation to the companion `vmware-monitor` library.

---

# 10. VM Lifecycle

VMware Knight supports common virtual-machine lifecycle operations.

| Operation | CLI Example | vCenter | ESXi |
|---|---|:---:|:---:|
| Power On | `vm power-on <name>` | Yes | Yes |
| Graceful Shutdown | `vm power-off <name>` | Yes | Yes |
| Force Power Off | `vm power-off <name> --force` | Yes | Yes |
| Create VM | `vm create <name> --cpu --memory --disk` | Yes | Yes |
| Delete VM | `vm delete <name>` | Yes | Yes |
| Reconfigure VM | `vm reconfigure <name> --cpu --memory` | Yes | Yes |
| Create Snapshot | `vm snapshot-create <name> --name <snap>` | Yes | Yes |
| List Snapshots | `vm snapshot-list <name>` | Yes | Yes |
| Revert Snapshot | `vm snapshot-revert <name> --name <snap>` | Yes | Yes |
| Delete Snapshot | `vm snapshot-delete <name> --name <snap>` | Yes | Yes |
| Task Status | `vm task-status <task-id>` | Yes | Yes |
| Clone VM | `vm clone <name> --new-name <new>` | Yes | Yes |
| vMotion | `vm migrate <name> --to-host <host>` | Yes | No |
| Set TTL | `vm set-ttl <name> --minutes <n>` | Yes | Yes |
| Cancel TTL | `vm cancel-ttl <name>` | Yes | Yes |
| List TTLs | `vm list-ttl` | Yes | Yes |
| Clean Slate | `vm clean-slate <name> --snapshot baseline` | Yes | Yes |

Example using a target tag:

```bash
vmware-knight vm power-on web-01 --target lab-vcenter
```

---

# 11. Guest Operations

Guest operations require VMware Tools inside the guest operating system.

Examples:

```bash
vmware-knight vm guest-exec web-01 \
  --cmd /bin/bash \
  --args "-c 'whoami'" \
  --user root
```

Upload a file:

```bash
vmware-knight vm guest-upload web-01 \
  --local ./script.sh \
  --guest /tmp/script.sh \
  --user root
```

Download a file:

```bash
vmware-knight vm guest-download web-01 \
  --guest /var/log/syslog \
  --local ./syslog.txt \
  --user root
```

Guest usernames are explicit. VMware Knight does not silently assume `root`.

---

# 12. Plan / Apply Workflow

For multi-step operations, VMware Knight supports a plan-oriented workflow.

Typical sequence:

```text
Create Plan
    |
    v
Validate Operations
    |
    v
Review Affected Objects
    |
    v
Confirm
    |
    v
Apply Sequentially
    |
    +--> Success
    |
    +--> Failure --> Rollback available operations
```

Core MCP operations include:

```text
vm_create_plan
vm_apply_plan
vm_rollback_plan
```

Plans are stored under:

```text
~/.vmware-knight/plans/
```

Successful plans are automatically removed, and stale plans are cleaned up.

---

# 13. VM Deployment and Provisioning

VMware Knight includes several deployment workflows.

| Operation | Example |
|---|---|
| Deploy OVA | `deploy ova ./ubuntu.ova --name lab-vm --datastore ds1` |
| Deploy Template | `deploy template golden-ubuntu --name new-vm` |
| Linked Clone | `deploy linked-clone --source base-vm --snapshot clean --name test-vm` |
| Attach ISO | `deploy iso my-vm --iso "[datastore1] iso/ubuntu.iso"` |
| Mark Template | `deploy mark-template golden-vm` |
| Batch Clone | `deploy batch-clone --source base-vm --count 5 --prefix lab` |
| Batch Deploy | `deploy batch deploy.yaml` |

Example:

```bash
vmware-knight deploy ova ./ubuntu.ova \
  --name ubuntu-lab-01 \
  --datastore datastore1 \
  --target lab-vcenter
```

---

# 14. Cluster Management

Cluster operations include:

| Operation | Command |
|---|---|
| Cluster Info | `cluster info <name>` |
| Create Cluster | `cluster create <name> --ha --drs` |
| Delete Cluster | `cluster delete <name>` |
| Add Host | `cluster add-host <cluster> --host <host>` |
| Remove Host | `cluster remove-host <cluster> --host <host>` |
| Configure HA/DRS | `cluster configure <name> --ha --drs` |

Example:

```bash
vmware-knight cluster info LAB-CLUSTER --target lab-vcenter
```

Removing a host from a cluster requires the appropriate VMware state, including maintenance-mode requirements where applicable.

---

# 15. Alarm Management

VMware Knight supports VMware alarm workflows.

List triggered alarms:

```bash
vmware-knight alarm list --target lab-vcenter
```

Acknowledge an alarm:

```bash
vmware-knight alarm acknowledge esxi-01 "Host memory usage"
```

Reset alarms:

```bash
vmware-knight alarm reset esxi-01 "Host memory usage"
```

Reset operations should be reviewed carefully because VMware alarm-clear APIs may affect multiple alarms within the selected scope.

---

# 16. Datastore Operations

Browse datastore content:

```bash
vmware-knight datastore browse datastore1 --path "iso/"
```

Scan for deployment images:

```bash
vmware-knight datastore scan-images --target lab-vcenter
```

Image discovery can locate content such as:

```text
ISO
OVA
OVF
VMDK
```

---

# 17. Scheduled Scanning

VMware Knight includes scheduled scanning for operational visibility.

Start the daemon:

```bash
vmware-knight daemon start
```

Check status:

```bash
vmware-knight daemon status
```

Stop it:

```bash
vmware-knight daemon stop
```

Run a one-time scan:

```bash
vmware-knight scan now
```

The scanner can work across multiple configured targets and process operational information such as:

- triggered alarms
- vCenter events
- ESXi host logs
- scan findings
- incomplete/unreachable target conditions

Structured scan output is written under the VMware Knight configuration directory.

---

# 18. Safety Model

Infrastructure automation requires explicit safety controls.

VMware Knight includes safeguards around write and destructive operations.

Depending on the operation and interface, these include:

- dry-run or preview behavior
- explicit confirmation
- additional confirmation for destructive operations
- plan-before-apply workflows
- audit logging
- rollback information where supported
- explicit target selection
- identifier collision validation
- no silent target switching

The friendly-tag system is also part of the safety model because it lets operators use understandable infrastructure identifiers while VMware Knight still resolves the target against a validated inventory.

Always review destructive operations before approving them.

---

# 19. Common Workflows

## Deploy a lab VM

```bash
vmware-knight datastore browse datastore1 \
  --pattern "*.ova" \
  --target lab-vcenter
```

```bash
vmware-knight deploy ova ./ubuntu.ova \
  --name lab-vm \
  --datastore datastore1 \
  --target lab-vcenter
```

```bash
vmware-knight vm snapshot-create lab-vm \
  --name baseline \
  --target lab-vcenter
```

```bash
vmware-knight vm set-ttl lab-vm \
  --minutes 480 \
  --target lab-vcenter
```

---

## Work with multiple VMware environments

Configure tags such as:

```text
prod-vcenter
dr-vcenter
lab-vcenter
esxi-lab-01
esxi-lab-02
```

Then ask Claude or Codex:

```text
Using VMware Knight, show me all VMs on lab-vcenter.
```

```text
Using VMware Knight, check active alarms on prod-vcenter.
```

```text
Using VMware Knight, list VMs on esxi-lab-01.
```

This is easier and safer than repeatedly typing raw IP addresses.

---

# 20. CLI Quick Reference

Diagnostics:

```bash
vmware-knight doctor
vmware-knight doctor --skip-auth
```

Wizard:

```bash
vmware-knight wizard
```

MCP server:

```bash
vmware-knight mcp
```

VM operations:

```bash
vmware-knight vm power-on my-vm --target lab-vcenter
vmware-knight vm power-off my-vm --target lab-vcenter
vmware-knight vm create new-vm --cpu 4 --memory 8192 --disk 100 --target lab-vcenter
vmware-knight vm delete my-vm --target lab-vcenter
vmware-knight vm snapshot-create my-vm --name before-upgrade --target lab-vcenter
vmware-knight vm snapshot-list my-vm --target lab-vcenter
vmware-knight vm snapshot-revert my-vm --name before-upgrade --target lab-vcenter
vmware-knight vm clone my-vm --new-name my-vm-clone --target lab-vcenter
vmware-knight vm migrate my-vm --to-host esxi-02 --target lab-vcenter
vmware-knight vm set-ttl my-vm --minutes 60 --target lab-vcenter
vmware-knight vm list-ttl --target lab-vcenter
```

Deployment:

```bash
vmware-knight deploy ova ./ubuntu.ova --name my-vm --datastore ds1 --target lab-vcenter
vmware-knight deploy template golden-ubuntu --name new-vm --target lab-vcenter
vmware-knight deploy linked-clone --source base-vm --snapshot clean --name test-vm --target lab-vcenter
vmware-knight deploy iso my-vm --iso "[datastore1] iso/ubuntu.iso" --target lab-vcenter
```

Cluster:

```bash
vmware-knight cluster info LAB-CLUSTER --target lab-vcenter
vmware-knight cluster create LAB-CLUSTER --ha --drs --target lab-vcenter
vmware-knight cluster configure LAB-CLUSTER --ha --drs --target lab-vcenter
```

Alarms:

```bash
vmware-knight alarm list --target lab-vcenter
```

Datastore:

```bash
vmware-knight datastore browse datastore1 --path "iso/" --target lab-vcenter
vmware-knight datastore scan-images --target lab-vcenter
```

Scanning:

```bash
vmware-knight scan now
vmware-knight daemon start
vmware-knight daemon status
vmware-knight daemon stop
```

---

# 21. Project Structure

```text
vmware-knight-mcp/
├── vmware_knight/
│   ├── config.py
│   ├── connection.py
│   ├── doctor.py
│   ├── init_wizard.py
│   ├── setup_wizard.py
│   ├── cli/
│   ├── ops/
│   ├── scanner/
│   ├── notify/
│   └── mcp_server/
├── skills/
│   └── vmware-knight/
├── examples/
├── tests/
├── config.example.yaml
├── pyproject.toml
├── RELEASE_NOTES.md
└── README.md
```

---

# 22. Technology

VMware Knight is built primarily with:

- Python
- pyVmomi
- Typer
- FastMCP / Model Context Protocol
- YAML-based target configuration
- local credential/environment storage
- automated pytest coverage

---

# 23. Testing

Run the project tests with:

```bash
uv run pytest -q
```

The project includes tests for areas such as:

- configuration loading
- target resolution
- friendly tag resolution
- identifier collision handling
- wizard operations
- credential migration
- MCP configuration
- lifecycle safety gates
- plan/apply behavior
- cluster operations
- guest operations
- alarms
- deployment
- regression coverage

---

# 24. Updating VMware Knight

If installed directly from GitHub with `uv`, reinstall from the repository:

```bash
uv tool install --force \
  git+https://github.com/CyberKnightLabs/vmware-knight-mcp.git
```

The same command works in PowerShell on Windows, written on one line:

```powershell
uv tool install --force git+https://github.com/CyberKnightLabs/vmware-knight-mcp.git
```

For a cloned repository:

```bash
cd vmware-knight-mcp
git pull origin main
uv sync
```

---

# 25. Troubleshooting

## Check the installation

```bash
vmware-knight --help
```

On Windows, if PowerShell says `vmware-knight` is not recognized, run `uv tool update-shell`, open a new PowerShell window, and check with `where.exe vmware-knight`.

## Check VMware configuration

```bash
vmware-knight doctor
```

## Check targets

```bash
vmware-knight wizard
```

Choose:

```text
1. List VMware targets
```

## Test connectivity

From the wizard choose:

```text
6. Test connections
```

## MCP client does not show VMware Knight

Confirm that:

- the `vmware-knight` executable path exists
- the MCP configuration uses the correct executable
- the MCP server name is `vmware-knight`
- the client has been restarted after changing its MCP configuration

For Codex, a typical block is:

```toml
[mcp_servers.vmware-knight]
command = "/Users/yourname/.local/bin/vmware-knight"
args = ["mcp"]
enabled = true
startup_timeout_sec = 120
```

On Windows, also check:

- the `command` path ends in `.exe`
- in Codex's TOML, the path is either in single quotes (`'C:\Users\...'`) or has doubled backslashes (`"C:\\Users\\..."`); single backslashes inside double quotes break the whole file
- `codex mcp get vmware-knight` shows the entry; if it reports a parse error, re-run the wizard or the [Windows installer script](docs/windows-codex.md)

## TLS errors in a lab

If your lab uses a self-signed certificate, the wizard allows TLS certificate verification to be disabled for that target.

Do this only when you understand and accept the security implications.

---

# 26. Repository

GitHub:

```text
https://github.com/CyberKnightLabs/vmware-knight-mcp
```

Clone:

```bash
git clone https://github.com/CyberKnightLabs/vmware-knight-mcp.git
```

---

# 27. License

MIT

See [LICENSE](LICENSE) for the complete license text.
