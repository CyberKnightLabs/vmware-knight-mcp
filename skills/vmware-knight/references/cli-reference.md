# CLI Reference

Destructive and deploy commands ask for two confirmations and most write
commands take `--dry-run` (not `deploy iso`, `deploy mark-template`,
`vm cancel-ttl`, `vm guest-download`). These are CLI-only: over MCP the 22 destructive write tools take `confirm` and preview by
default, the other 21 write tools act immediately, and the enforcement boundary there is the RBAC of the vCenter/ESXi account — see
`capabilities.md` → "What gates a write".

```bash
# Diagnostics
vmware-knight doctor [--skip-auth]   # --skip-auth only skips doctor's own vSphere login check; no other command has it

# MCP Config Generator
vmware-knight mcp-config generate --agent <goose|cursor|claude-code|continue|vscode-copilot|localcowork|mcp-agent>
vmware-knight mcp-config list

# VM Operations
vmware-knight vm power-on <vm-name>
vmware-knight vm power-off <vm-name> [--force]
vmware-knight vm create <name> [--cpu <n>] [--memory <mb>] [--disk <gb>]
vmware-knight vm delete <vm-name>
vmware-knight vm reconfigure <vm-name> [--cpu <n>] [--memory <mb>]
vmware-knight vm snapshot-create <vm-name> --name <snap-name> [--description <text>] [--memory]
vmware-knight vm snapshot-list <vm-name>
vmware-knight vm snapshot-revert <vm-name> --name <snap-name>
vmware-knight vm snapshot-delete <vm-name> --name <snap-name> [--remove-children]
vmware-knight vm clone <vm-name> --new-name <name> [--to-host <host>] [--to-datastore <ds>] [--power-on]
vmware-knight vm migrate <vm-name> --to-host <host> [--to-datastore <ds>]
vmware-knight vm set-ttl <vm-name> --minutes <n>
vmware-knight vm cancel-ttl <vm-name>
vmware-knight vm list-ttl
vmware-knight vm clean-slate <vm-name> [--snapshot baseline]

# Guest Operations (requires VMware Tools)
vmware-knight vm guest-exec <vm-name> --cmd /bin/bash --args "-c 'ls -la /tmp'" --user root
vmware-knight vm guest-upload <vm-name> --local ./script.sh --guest /tmp/script.sh --user root
vmware-knight vm guest-download <vm-name> --guest /var/log/syslog --local ./syslog.txt --user root

# Plan → Apply (multi-step operations)
vmware-knight plan list

# Deploy
vmware-knight deploy ova <path> --name <vm-name> [--datastore <ds>] [--network <net>]
vmware-knight deploy template <template-name> --name <vm-name> [--datastore <ds>]
vmware-knight deploy linked-clone --source <vm> --snapshot <snap> --name <new-name>
vmware-knight deploy iso <vm-name> --iso "[datastore] path/file.iso"
vmware-knight deploy mark-template <vm-name>
vmware-knight deploy batch-clone --source <vm> --count <n> [--prefix <prefix>]
vmware-knight deploy batch <spec.yaml>

# Cluster
vmware-knight cluster info <name>
vmware-knight cluster create <name> [--ha] [--drs] [--drs-behavior fullyAutomated|partiallyAutomated|manual] [--datacenter <dc>]
vmware-knight cluster delete <name>
vmware-knight cluster add-host <cluster> --host <hostname>
vmware-knight cluster remove-host <cluster> --host <hostname>   # host must be in maintenance mode; moved to datacenter host folder as standalone
vmware-knight cluster configure <name> [--ha/--no-ha] [--drs/--no-drs] [--drs-behavior <behavior>]
vmware-knight cluster drs-rules <name>                                                # list VM-VM + VM-Host DRS rules
vmware-knight cluster drs-rule-set <name> --rule <name> --enable|--disable [--dry-run] # idempotent; double confirm
vmware-knight cluster drs-rule-create <name> --rule <name> --type affinity|antiAffinity --vm <vm1> --vm <vm2> [--disabled] [--dry-run]
vmware-knight cluster drs-rule-delete <name> --rule <name> [--dry-run]                 # VM-VM only; double confirm

# Alarm Management
vmware-knight alarm list [--target <name>]
vmware-knight alarm acknowledge <entity_name> <alarm_name> [--target <name>]
vmware-knight alarm reset <entity_name> <alarm_name> [--target <name>]
# NOTE: 'alarm reset' clears ALL triggered alarms matching the named alarm's
# entity type (host/VM/all) and current status (red/yellow) — vSphere has no
# per-alarm clear API. The CLI double confirmation applies; output reports the
# scope. The reset_vcenter_alarm MCP tool has no confirmation — it clears on the
# first call.

# Datastore
vmware-knight datastore browse <ds-name> [--path <subdir>]
vmware-knight datastore scan-images [--target <name>]

# Scanning & Daemon
vmware-knight scan now [--target <name>]   # alarms + events only; host logs are read by the daemon
vmware-knight daemon start
vmware-knight daemon stop
vmware-knight daemon status

# Moved to companion skills:
# vmware-monitor inventory vms/hosts/datastores/clusters, health alarms/events, vm info
# vmware-storage iscsi-enable/status/add-target/remove-target, rescan, vsan health/capacity
# vmware-vks list-namespaces, create-tkc, scale-tkc, etc.
```
