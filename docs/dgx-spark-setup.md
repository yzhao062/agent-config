# NVIDIA DGX Spark, Setup and Operations Notes

> Personal setup notes kept in a public repo. Redacted to generic placeholders:
> `spark-<XXXX>` for the hostname suffix printed on the NVIDIA quick start card,
> `<admin>` for the primary admin user, `<collaborator>` for a second admin,
> `<student>` for student accounts, `192.168.1.X` for example LAN IPs.
> Substitute your own values when applying these instructions.

## Current state (as of 2026-04-28)

### Completed
- Order received: 2 units (this document currently covers unit A)
- Unit A onboarded via network-device mode; hostname `spark-<XXXX>` (auto-generated, suffix from quick-start card), primary admin user `<admin>`
- SSH access confirmed from Windows laptop over home Wi-Fi, using mDNS name `spark-<XXXX>.local`
- Second admin account created for a collaborator (in `sudo` and `docker` groups)
- Boot default switched to `multi-user.target` (headless) on 2026-04-13; Xorg and gnome-shell no longer running, GPU memory freed
- Tailscale 1.96.4 installed; `tailscaled` systemd service running, status `Needs login` (not yet authenticated)
- Claude Code 2.1.105 installed on Spark (native ARM64 binary) — gives a second agent session with local filesystem access
- SSH key-based auth set up from Windows daily driver to Spark — tools (Claude Code, scripts, `ssh`, `scp`) can now drive Spark non-interactively
- Miniforge3 installed at `~/miniforge3` with conda 26.1.1 / mamba 2.5.0
- `py312` conda environment created (Python 3.12.13), auto-activated via `~/.bashrc`
- PyTorch 2.11.0+cu128 installed in `py312` (aarch64 wheels from pytorch.org/whl/cu128), GPU access verified: `torch.cuda.is_available()` → True, device = NVIDIA GB10, compute capability 12.1 (Blackwell), real matmul test passed
- 2026-04-28: Hardened against runaway-memory crash after the 04-26 → 04-28 OOM-cascade incident; `systemd-oomd` enabled, `user.slice` capped at `MemoryMax=120G` with `ManagedOOMMemoryPressure=kill` at 80% PSI. See section 14.
- 2026-04-28: NOPASSWD sudo configured for the admin user (`/etc/sudoers.d/<admin>-nopasswd`) to enable agent automation; see Pattern A in section 18.

### In progress
- Tailscale authentication: next command is `sudo tailscale up --ssh`
- Collaborator password/SSH key handoff: account exists, temp password not yet set, no SSH key installed

### Pending next steps (when resuming)
1. Run `sudo tailscale up --ssh` on Spark and complete browser auth on Windows
2. Record the static Tailscale IP with `tailscale ip -4`
3. Enable MagicDNS in Tailscale admin console
4. Install Tailscale on Windows laptop; verify off-LAN access by tethering to phone hotspot
5. Set temporary password for `<collaborator>` and force expiry:
   ```
   sudo passwd <collaborator>
   sudo passwd --expire <collaborator>
   ```
6. Collect collaborator's SSH public key, install to their `~/.ssh/authorized_keys` (see section 9)
7. Send collaborator the onboarding message (template in section 9)
8. Install Tailscale on collaborator's machine, share Spark node from admin console
9. Move Spark to office (no network reconfiguration needed because of Tailscale)
10. Unit B: repeat the entire flow once it arrives

### Known issues / gotchas discovered so far

- **Termius paste bug, `&&`-chain failure mode**: pasting a long `&&`-chained command can silently misfire. Termius on Windows, combined with a shell that does not fully consume bracketed-paste control codes, sometimes splits a command at an awkward point so that a redirect operator ends up on a new line. Example:
  ```bash
  # Pasted as one logical line:
  echo 'some content' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo DONE
  # Actually executed as two lines:
  echo 'some content'                            # (1) prints "some content" to terminal (redirect missing!)
  >> ~/.ssh/authorized_keys && chmod ... && echo DONE  # (2) null redirect creates empty file, chmods it, echoes DONE
  ```
  Failure mode: **everything "succeeds" (you see DONE) but the file is empty.** The key contents went to stdout instead of to the file. Specifically dangerous for setup commands that install SSH keys, secrets, or config fragments.

  Workarounds:
  - Break into single-line commands — one command per shell prompt
  - Use `nano ~/.ssh/authorized_keys` and paste inside the editor
  - Use a Spark-side Claude Code instance to write the file natively (see section 18)
  - Fix bracketed paste in bash: `echo 'set enable-bracketed-paste on' >> ~/.inputrc` on Spark (may or may not help depending on terminal)
  - Switch to Windows Terminal + native OpenSSH, which handles paste cleanly

- **DHCP IP drift**: home Wi-Fi assigned Spark different IPs on different days (`192.168.1.X` → `192.168.1.Y`). Use the mDNS name or Tailscale address, never hardcode the IP.

---

## 1. Order context
- Product: NVIDIA DGX Spark Founders Edition, 4 TB
- Quantity: 2 units
- MSRP (April 2026): $4,699 each (raised from $3,999 in late February 2026 due to memory supply constraints)

## 2. Role in daily workflow
Daily driver stays on Windows (PyCharm, Claude Code, Codex, Chrome, Office). Spark is a headless ML appliance, not a desktop replacement. Primary interaction model: PyCharm remote interpreter and SSH from the Windows box.

## 3. Operating system
- Ships with NVIDIA DGX OS (Ubuntu 24.04 LTS for ARM64 / aarch64)
- Kernel observed: `6.17.0-1014-nvidia aarch64`
- DGX OS version observed: 7.5.0
- Preinstalled: CUDA 13.0, cuDNN, NCCL, TensorRT, PyTorch containers, NIM, Docker runtime, NVIDIA driver 580.142
- Windows and macOS cannot be installed:
  - macOS has no ARM-for-non-Apple-hardware build and no NVIDIA GPU drivers
  - Windows on ARM has no Grace/Blackwell driver support
  - Spark is a single-OS appliance by design

## 4. OS restoration
- Built-in recovery partition reflashes to factory state from the UEFI menu
- Official DGX OS images are on the NVIDIA Enterprise portal for USB reinstall
- Warranty support covers firmware-level recovery
- Safe to experiment with kernels and drivers; reversible within an hour

## 5. First-boot setup
The quick start card prints two credentials:
- Host SSID: the temporary Wi-Fi network the Spark broadcasts on first power-on
- WPA2 password: password for that Wi-Fi access point

These are used once during onboarding, then never again. Flow:
1. Power on Spark (no display needed)
2. From a laptop or phone, join the `spark-<XXXX>` Wi-Fi using the printed password
3. Open the browser wizard at the printed URL
4. Set timezone, create an admin Linux user account, join the real network
5. The temporary AP shuts off after onboarding completes

Important: the Wi-Fi password on the card is NOT the SSH password. The SSH password is the one you create for your admin account during step 4.

## 6. Setup mode
Chosen mode for both units: network device (headless). Rationale: Spark's value is as a CUDA server reached over SSH, not as a second desktop. A monitor can still be plugged in later if needed.

## 7. Local network access (on-LAN only)
- Spark auto-advertises its hostname via mDNS as `spark-<XXXX>.local`
- Windows 11 recent builds resolve `.local` names natively; if resolution fails, install Apple Bonjour Print Services
- The mDNS name is stable across reboots; raw IP is not required and should not be hardcoded
- **Important limitation**: mDNS is link-local. `spark-<XXXX>.local` only resolves when the client is on the same Wi-Fi / broadcast domain as the Spark. For off-LAN access, use Tailscale (section 10).
- Fallback if mDNS is flaky on LAN: add a DHCP reservation on the router to pin the IP

## 8. SSH authentication

### Which password to use
- Quick start card passwords: Wi-Fi AP only, used once
- Admin user password you created during first-boot setup: what you use for SSH from then on

### Initial SSH test
```
ssh <admin>@spark-<XXXX>.local
```
Enter your admin password when prompted.

### Switch to key-based auth (do this right away)
1. On Windows, generate a key if none exists:
   ```
   ssh-keygen -t ed25519
   ```
2. Copy public key to Spark. Depending on whether bracketed-paste is reliable in your terminal, use one of these:

   **Method A: compound command** (works if paste is clean):
   ```
   type %USERPROFILE%\.ssh\id_ed25519.pub | ssh <admin>@spark-<XXXX>.local "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
   ```
   **Method B: single-line commands** (safest, avoids paste-split issue):
   On Spark, one command at a time:
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys   # paste the single key line inside nano, save with Ctrl+X Y Enter
   chmod 600 ~/.ssh/authorized_keys
   ```
   **Method C: ask a Spark-side Claude Code session** (see section 18): give it the key and let it write the file natively, no shell paste involved.

3. Test: `ssh spark-<XXXX>` should now log in without prompting
4. Repeat for each unit

### SSH config on Windows
`%USERPROFILE%\.ssh\config`:
```
Host spark-a
    HostName spark-<XXXX>.local
    User <admin>
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60

Host spark-b
    HostName spark-<YYYY>.local
    User <admin>
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
```

### Optional hardening (after keys work)
Disable password SSH:
```
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl reload ssh
```
From then on, only SSH keys can log in.

## 9. User management

### Create a new user (collaborator or admin)
```bash
sudo adduser <username>
sudo usermod -aG sudo,docker <username>
id <username>
```
- `adduser` prompts for password and optional fields
- `sudo` group grants admin rights; omit for student accounts
- `docker` group grants access to NVIDIA container runtime (CUDA containers)
- `id` verifies group membership

### Force password change on first login
```bash
sudo passwd --expire <username>
```
On next login the user is required to set a new password before they get a shell. Equivalent: `sudo chage -d 0 <username>`.

### Install a user's SSH public key
Ask them for `~/.ssh/id_ed25519.pub` on their machine, then:
```bash
sudo -u <username> mkdir -p /home/<username>/.ssh
sudo -u <username> tee /home/<username>/.ssh/authorized_keys > /dev/null <<'EOF'
ssh-ed25519 AAAA...paste-their-key... user@hostname
EOF
sudo -u <username> chmod 700 /home/<username>/.ssh
sudo -u <username> chmod 600 /home/<username>/.ssh/authorized_keys
```
Using `sudo -u <username>` makes files owned by them from the start, so no separate `chown` step. Note: this command pattern has its own paste risk (the `<<'EOF'` heredoc), so consider pasting inside `nano` instead if your terminal has paste problems.

### Reset a forgotten password
```bash
sudo passwd <username>
```
Prompts you for a new password twice. Pair with `sudo passwd --expire <username>` to force the user to change it again after you hand it over.

### Remove a user
```bash
sudo deluser --remove-home <username>
```
Also unshare any Tailscale node access in the admin console.

### Onboarding message template (for collaborator / admin)
```
Hi <name>,

You now have an admin account on our new NVIDIA DGX Spark.

Connection:
  Host:     spark-<XXXX>.local   (when on our Wi-Fi)
            or spark-<XXXX>      (via Tailscale from anywhere, once set up)
  Username: <username>
  Temp password: <FILL IN>

To log in:
  ssh <username>@spark-<XXXX>.local

On your first login, the system will require you to change the
temporary password. Set a new one and you are in.

Quick orientation:
  - Home directory: /home/<username> (on a 4 TB NVMe)
  - You have sudo and docker group access
  - Full NVIDIA CUDA stack preinstalled
  - OS: DGX OS 7.5.0 (Ubuntu 24.04 LTS, ARM64)
  - Hardware: NVIDIA GB10 Grace Blackwell, 128 GB unified memory

Let me know once you are logged in.

<your name>
```
Deliver the temp password through an encrypted channel, not plain email.

### Home directory isolation
Each Linux user has their own private `/home/<username>/` directory. By default, one user cannot read inside another user's home (mode `0755` on the home directory; files inside are owned by the user). Everything — `~/.bashrc`, `~/.ssh`, `~/miniforge3`, `~/.cache`, datasets, model checkpoints — is fully isolated. When you run `sudo adduser`, Ubuntu copies the skeleton files from `/etc/skel` into the new home, so each user starts with the standard `Documents`, `Downloads`, etc. subfolders.

If you ever need to drop a file into another user's home (e.g., install their SSH key before they first log in), use `sudo` or `sudo -u <username>` so the file ends up owned by them.

## 10. Remote access via Tailscale (NVIDIA-official path)

This is the NVIDIA-documented remote-access approach at https://build.nvidia.com/spark/tailscale. It is treated as a supported component of DGX OS, not a third-party hack. Tailscale gives Spark a stable overlay IP in the `100.x.y.z` CGNAT range that follows the device between networks, so off-LAN access from anywhere works without port forwarding, DDNS, or a public IP.

### Why Tailscale over alternatives
- Free Personal plan is enough for you + a collaborator (3 users, 100 devices)
- Works through NAT; no router configuration needed
- Survives network changes: when you move Spark from home to office, the Tailscale address stays the same
- NVIDIA Sync (the Windows GUI) has first-party Tailscale integration

### Install on Spark
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```
Installs the ARM64 package and registers `tailscaled` as a systemd service that auto-starts on boot.

If `dpkg` complains about being interrupted from a prior operation:
```bash
sudo dpkg --configure -a
sudo apt-get install -f
sudo apt-get update
sudo apt-get install -y tailscale tailscale-archive-keyring
```

### Authenticate
```bash
sudo tailscale up --ssh
```
Prints a one-time authentication URL. Copy it into Chrome on your Windows laptop (where you are already signed into https://login.tailscale.com), click **Connect**. The Spark joins your tailnet.

The `--ssh` flag enables Tailscale SSH: optional, lets you authenticate SSH sessions via tailnet identity and ACLs instead of managing OpenSSH keys. Disable later with a plain `sudo tailscale up` if undesired.

### Record the static address
```bash
tailscale ip -4
tailscale status
```
- First command prints Spark's stable `100.x.y.z` IP. Write it down; it never changes for this device.
- Second command shows the full tailnet view.

### Enable MagicDNS (one-time, in admin console)
Go to https://login.tailscale.com/admin/dns → toggle **MagicDNS** on. Every tailnet device is then reachable by short hostname, e.g., `spark-<XXXX>`.

### Windows client setup
Download from https://tailscale.com/download/windows, install, sign in with the same account. Windows tray icon shows Spark when connected.

### Verify off-LAN access
Tether Windows laptop to phone hotspot so it leaves home Wi-Fi, then:
```
ssh <admin>@spark-<XXXX>
```
If this connects, remote access is proven working before Spark ever moves offices.

### Update Windows SSH config
```
Host spark
    HostName spark-<XXXX>
    User <admin>
    IdentityFile ~/.ssh/id_ed25519
```
From then on, `ssh spark` works from any terminal (Claude Code, Codex, PyCharm remote interpreter), regardless of network.

### Moving Spark between networks (home → office)
No reconfiguration needed. When Spark boots at the office, `tailscaled` auto-starts, reconnects to the coordination server, and keeps the same `100.x.y.z` / `spark-<XXXX>` address. You can SSH in from anywhere while still on the drive to the office.

Office firewalls: Tailscale tries direct peer-to-peer (UDP 41641), then STUN NAT traversal, then falls back to TCP 443 DERP relays. The 443 fallback works through almost any enterprise firewall.

## 11. Multi-user scaling for students

The free Personal plan caps at 3 users. For a research group with more members, three clean paths.

### Option A: Tailscale Node Sharing (recommended start)
- Keep the free Personal tailnet
- For each student, share Spark as a node from the admin console (**Machines → spark-<XXXX> → Share...**)
- Student creates their own free Personal tailnet and accepts the share
- They see only the Spark; none of your other tailnet devices
- Free for everyone, scales to unlimited students
- Revoke by unsharing in the admin console when they leave the lab

### Option B: Tailscale paid + 50% education discount
- Starter plan: normally $6/user/month, $3/user/month with the education discount
- Request the discount by emailing Tailscale support with documentation of institutional affiliation
- Unlocks centralized ACLs, tagged device groups, audit logs, and Tailscale SSH with identity-based access control
- Worth switching when share management becomes tedious (roughly 4+ active students) or when you want audit trails

### Option C: Self-hosted Headscale
- Open-source reimplementation of Tailscale's coordination server
- Free, unlimited users, full client compatibility
- Operational cost: TLS certs, backups, upgrades on a server you run
- Probably not worth it unless you specifically want no third-party SaaS

### Linux-level user management (always required)
Tailscale is only the network layer. You still need one Linux account per student (section 9). The lifecycle:
1. Create Linux account with `adduser`
2. Add to `docker` group (skip `sudo` unless they are an admin)
3. Install their SSH public key
4. Share the Spark node with them via Tailscale (or add them to the tailnet with ACL rules)
5. When they leave: `sudo deluser --remove-home <user>` on Spark and unshare in the Tailscale admin console

### Practical scaling concerns beyond networking
- **GPU contention**: Spark has a single GB10 GPU. Concurrent training jobs contend for it. Start with informal coordination (Slack, shared calendar). If that breaks down, add NVIDIA MPS for cooperative sharing, or a small queue tool.
- **Disk quotas**: one student filling `/home` wrecks the box for everyone. Install `quota`:
  ```bash
  sudo apt install quota
  # Edit /etc/fstab to add usrquota,grpquota to the root mount options
  sudo quotacheck -cum /
  sudo quotaon /
  sudo edquota -u <username>   # set soft / hard limits
  ```
  Or create a shared `/data` directory with rotation policies.
- **Shared monitoring**: install `nvitop` system-wide so students can self-check GPU state before launching a job. A "look before you launch" norm prevents most conflicts.
- **Slurm / scheduler**: probably not worth installing on a single-node one-GPU box until you have 5+ active users. A simple file-lock wrapper (`flock -x /tmp/gpu.lock python train.py`) handles most small-lab coordination needs.
- **Python environments**: install Miniforge per-user initially. When user count grows, consider a shared base install at `/opt/miniforge3` with each user's environments kept in `~/.conda/envs/`.

## 12. Power consumption and running costs

### Specs
| State | Power |
|---|---|
| Peak total system | 240 W |
| GB10 SoC TDP (CPU + GPU) | 140 W |
| Rest of system (ConnectX-7, SSD, USB-C) | 100 W |
| Under full CPU + GPU load | ~200 W |
| CPU-only load | 120–130 W |
| Idle (headless, post-update) | ~22 W |
| Idle (display attached) | ~25 W |
| Idle (pre-2026 firmware) | ~37 W |

Keep firmware current; the 2026 update fixed a ConnectX-7 hot-plug bug that held idle draw at 37 W.

### Running cost (example: LADWP Los Angeles residential, ~$0.30/kWh effective rate)

Per Spark, 24/7:
| Usage pattern | Avg draw | Per month | Per year |
|---|---|---|---|
| Headless idle only | 22 W | $4.75 | $58 |
| Light use (1 h training/day) | 30 W | $6.50 | $79 |
| Moderate (4 h training/day) | 52 W | $11.25 | $137 |
| Heavy (8 h training/day) | 81 W | $17.60 | $214 |
| Pegged 24/7 (unlikely) | 200 W | $43.20 | $526 |

Two units together, moderate usage: ~$22/month, ~$275/year at LADWP rates. Substitute your local rate for other regions.

### Reducing idle power
- Switch to `multi-user.target` to stop Xorg and gnome-shell (saves ~3 W and ~200 MiB memory, frees ~140 MiB GPU memory). See section 13 for full details, trade-offs, and verification steps.
- Keep display disconnected (saves additional ~3 W)
- Leave Tailscale running (negligible power, big usability gain)

### Monitoring commands
- `nvidia-smi` — GPU power, temp, utilization (one-shot)
- `nvidia-smi -l 1` — live updating every second
- `nvidia-smi dmon -s pucvmet -d 1` — streaming dashboard view
- `nvidia-smi --query-gpu=timestamp,power.draw,temperature.gpu,utilization.gpu,memory.used --format=csv -l 1` — CSV for scripting
- `pip install nvitop && nvitop` — interactive TUI (best day-to-day tool)
- `cat /sys/class/hwmon/hwmon*/power*_input` — raw sensor rails (microwatts)

### Quirks of `nvidia-smi` on GB10
- **Memory-Usage "Not Supported"**: expected. Spark uses unified LPDDR5X shared between Grace CPU and Blackwell GPU, so `nvidia-smi` cannot show a GPU-specific slice. Use `free -h` or framework APIs (`torch.cuda.memory_allocated()`) instead.
- **Power cap "N/A"**: expected. The SoC shares a power budget between CPU and GPU at the firmware level; there is no discrete per-GPU cap like on an H100.

## 13. Boot mode: headless vs graphical

DGX OS boots to `graphical.target` by default, which means `gdm3`, `Xorg`, and `gnome-shell` all start even when no monitor is attached. For a headless appliance this wastes memory, GPU memory, and idle power. Switching the systemd default to `multi-user.target` stops all of that.

### Comparison

| | `graphical.target` (default) | `multi-user.target` (headless) |
|---|---|---|
| What runs | SSH, networking, Docker, Tailscale, plus `gdm3`, `Xorg`, `gnome-shell`, GNOME desktop stack | SSH, networking, Docker, Tailscale, systemd services |
| Attached monitor shows | GNOME login screen → desktop | Text login prompt on tty1 |
| Memory held by GUI | 140–500 MiB | 0 |
| GPU memory held at idle | ~140 MiB (Xorg + gnome-shell compositing) | 0 |
| Idle power | ~25 W | ~22 W |
| Boot time | ~40–60 s | ~15–25 s |
| SSH remote access | Works identically | Works identically |

### Benefits of headless for an ML appliance
- More unified memory for models: the GUI holds 200–500 MiB that PyTorch could otherwise use. Every MiB matters on a unified-memory system.
- More GPU memory: the compositor releases ~140 MiB that was held just to draw an empty desktop.
- ~3 W lower idle draw (~$8/year per Spark at LADWP rates). Small in isolation, free to claim.
- ~2x faster reboot (skips gdm3, Xorg startup, and GNOME session init).
- Fewer background daemons, fewer surprise updates, fewer processes holding file locks.
- Unambiguously "an appliance" not "a desktop" — reduces the temptation to RDP in and poke around.

### What you give up
- **Local GNOME desktop on an attached monitor.** A plugged-in display now shows a text login prompt on tty1 instead of the graphical login screen. For an SSH-only workflow this is a non-issue.
- **GUI-only NVIDIA tools**: Nsight Systems GUI, `nvidia-settings` GUI, etc. All have CLI equivalents (`nsys` on the command line, most settings via `nvidia-smi`). You run the GUI versions on your daily driver connecting to Spark remotely.
- **Default GNOME remote desktop** stops working. You can temporarily bring the desktop back with `sudo systemctl isolate graphical.target`, or install Sunshine + Moonlight for on-demand streaming of a headless-friendly session.
- **Nothing else.** No package changes, no data loss. CUDA, Docker, Python, tmux, vim all work identically.

### Switch to headless (permanent)
```bash
sudo systemctl set-default multi-user.target
sudo reboot
```
After reboot, SSH back in as normal. The box is now headless from this point forward, including after power cycles.

### Switch to headless (immediate, no reboot)
```bash
sudo systemctl isolate multi-user.target
```
Switches the running system to multi-user mode on the spot. Kills Xorg and gnome-shell without touching SSH or Docker. Not persistent — the next reboot follows whatever the default target is. Combine with the permanent switch above if you want "right now" and "every boot after".

### Revert to graphical
```bash
sudo systemctl set-default graphical.target
sudo reboot
```
Fully reversible. No data loss, no package changes.

### Verify headless took effect
```bash
systemctl get-default          # should print: multi-user.target
pgrep -a Xorg                  # should print nothing
pgrep -a gnome-shell           # should print nothing
nvidia-smi                     # Processes section should no longer list Xorg or gnome-shell
free -h                        # should show ~200–500 MiB more available than before
```

### Temporarily bring the GUI back for a one-off task
```bash
sudo systemctl isolate graphical.target
```
Starts `gdm3`, `Xorg`, and GNOME on the spot. Reverts to text-mode at next reboot (because the default is still `multi-user.target`). Useful when you need a GUI session without changing the permanent default.

## 14. Reliability and OOM protection

### Background: 2026-04-28 incident

After ~48 hours of mixed CUDA workload, a Python process consumed all 128 GB of unified memory. The kernel's global OOM killer fired but ran into a cascade:
- NVIDIA NVRM driver could not allocate IOVA mapping metadata, triggered Xid 31 GPU MMU fault.
- `systemd-journald` reported `/dev/kmsg buffer overrun, some messages lost`; kernel logging fell behind.
- WiFi disconnected (`DEAUTH_LEAVING`).
- Kernel logged nothing for 1 h 47 m, leaving the system in an effective freeze.
- Recovery required physical hard power-off.

Root cause: on Grace Blackwell, GPU and CPU share LPDDR5X. CUDA "GPU memory" is system memory. A runaway CUDA allocation can exhaust the entire box, and once kernel global OOM cascades on a unified-memory ARM platform, recovery within the kernel is unreliable.

### Defense: two-layer protection

#### Layer 1: enable systemd-oomd

Ships with Ubuntu 24.04 (DGX OS base) but is not enabled by default. Monitors PSI (pressure stall info) and kills cgroups before kernel-level pressure forces global OOM.

```bash
sudo systemctl enable --now systemd-oomd
```

#### Layer 2: cap user-slice memory

Limit total memory across all per-user systemd slices. Leaves headroom for `system.slice` (sshd, NetworkManager, dockerd, tailscaled) so a runaway user process cannot starve infrastructure.

```bash
sudo mkdir -p /etc/systemd/system/user.slice.d
sudo tee /etc/systemd/system/user.slice.d/oom-protection.conf > /dev/null <<EOF
[Slice]
MemoryMax=120G
ManagedOOMMemoryPressure=kill
ManagedOOMMemoryPressureLimit=80%
EOF
sudo systemctl daemon-reload
```

`MemoryMax=120G` is a hard cap on the sum of all `user-<UID>.slice` instances. Reserves 8 GB for system services (DGX OS at idle uses ~3 GB; even with Docker, Tailscale, and several SSH sessions, system load stays below 6 GB).

`ManagedOOMMemoryPressure=kill` with `Limit=80%` lets `systemd-oomd` intervene before the hard limit. When sustained PSI inside `user.slice` exceeds 80%, oomd kills the offending cgroup, with the same outcome as cgroup OOM but quicker and with cleaner logs.

`MemoryHigh` is intentionally **not set**, so workloads near the limit are not throttled by reclaim. The trade-off: workloads either run at full speed under 120 GB, or get killed at the limit. No intermediate slow zone.

### Performance impact

None at normal workload sizes:
- The cgroup limit is enforced lazily; the kernel only intervenes when usage approaches the limit.
- Workloads under 115 GB run with zero overhead.
- `systemd-oomd` itself reads `/proc/pressure/*` every few seconds. CPU and memory overhead are negligible (single-digit MB RSS for the daemon).

### Optional: software-level CUDA guard rail

Cap the CUDA allocator from inside the workload as a courtesy soft-hint. This is not the hard backstop; Layers 1 and 2 are. But it can let a script fail gracefully instead of being killed.

In `~/.bashrc`:
```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

Or in PyTorch code:
```python
import torch
torch.cuda.set_per_process_memory_fraction(0.85)
```

### Verify

```bash
systemctl show user.slice -p MemoryMax,ManagedOOMMemoryPressure,ManagedOOMMemoryPressureLimit
# MemoryMax=128849018880 (= 120 GiB)
# ManagedOOMMemoryPressure=kill
# ManagedOOMMemoryPressureLimit=3435973836 (= 80% of 2^32)

systemctl is-active systemd-oomd
# active

cat /sys/fs/cgroup/user.slice/memory.current   # live usage in bytes
systemd-cgls user.slice                         # process tree under the slice
```

### What this does NOT protect against

- **Kernel hangs unrelated to OOM** (driver bugs, hardware faults). Would need the hardware watchdog (`/etc/systemd/system.conf.d/watchdog.conf` with `RuntimeWatchdogSec=30s`). Not enabled here because long legitimate CPU spikes during training would trigger spurious reboots.
- **Out-of-band access when sshd is up but the network is dead.** Tailscale (section 10) provides this fallback.
- **Disk-exhaustion runaways.** A separate problem; see `quota` in section 11.

## 15. Clustering the two units
- NVIDIA ships a "Connect Two Sparks" flow for stacking
- Uses ConnectX interfaces on the back for a direct high-speed link between the two machines
- Separate from the office LAN; needed only for multi-node jobs
- Guide: https://build.nvidia.com/spark/connect-two-sparks/stacked-sparks

## 16. Other tools (optional)
- **NVIDIA Sync**: Windows GUI device manager with first-party Tailscale integration. Nice if you want a clickable device list instead of `ssh`.
- **Sunshine + Moonlight**: low-latency virtual desktop streaming if you ever need a GUI session on Spark (e.g., for Nsight Systems, or viewing TensorBoard in a browser without port forwarding).

## 17. Fit assessment
Strong fit:
- Local prototyping and inference box: 128 GB unified memory holds quantized models up to ~200B params locally
- CUDA-native stack ports directly to cluster or cloud
- Quiet desktop form factor suitable for an office

Not a fit:
- Not a training cluster replacement: memory bandwidth and FP16 throughput are well below H100 / H200
- Not a Windows or macOS daily driver (cannot run those OSes at all)
- Two units justified only if workflow becomes "prototype on Spark, scale on cluster"; risk is under-use if most compute stays on university clusters or cloud

## 18. Agent access patterns (SSH automation and native Claude Code)

This section covers how to give Claude Code, Codex, and other tools the ability to drive Spark without requiring human interaction for every command. Two complementary patterns:

- **Pattern A**: Passwordless SSH from your daily-driver machine, so a locally-running agent can run commands on Spark via its Bash tool.
- **Pattern B**: Install a native Claude Code instance on Spark itself, giving a separate agent session that runs directly on the box with no SSH roundtrips.

Both are useful; they cover different use cases.

### Pattern A: Key-based SSH for tool automation

**Why**: Tools like Claude Code run commands via `bash`. If SSH requires a password, the tool cannot type it interactively. Setting up SSH key auth once lets the agent run `ssh spark <command>` non-interactively from then on.

**Setup on the daily-driver machine** (one-time):
```bash
# Generate a key pair if one does not already exist
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "daily-driver-for-agents"

# Write an SSH config entry so `ssh spark` works as a short alias
cat >> ~/.ssh/config <<'EOF'
Host spark
    HostName spark-<XXXX>.local
    User <admin>
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
chmod 600 ~/.ssh/config
```

**Install the public key on Spark**. Three reliable methods, listed from most-bulletproof to most-convenient:

1. **Use a Spark-side Claude Code session** (see Pattern B). Once Claude Code is installed on Spark, launch it, and give it a plain-English instruction:
   > Please write `~/.ssh/authorized_keys` containing exactly this one line: `<your pubkey here>`. Make sure `~/.ssh/` is mode 700 and `authorized_keys` is mode 600. Overwrite any existing empty file.

   Claude uses its native Write tool, bypassing the shell entirely — no paste, no redirect leaks, no terminal weirdness. This turned out to be the fastest way after a shell paste failed.

2. **Use `nano` inside any Spark SSH session** (safe, editor-based):
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   nano ~/.ssh/authorized_keys
   # Inside nano: paste the single-line pubkey, Ctrl+X, Y, Enter
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **Compound one-liner via `echo`** (fastest but risky — see the `&&` paste gotcha in "Known issues" above):
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '<pubkey>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo DONE
   ```
   Only use this if your terminal does not break multi-line pastes, OR if you carefully inspect the result afterward. The failure mode is silent: `DONE` prints even when the key is not actually saved.

**Verify from the daily-driver**:
```bash
ssh -o BatchMode=yes spark 'whoami && hostname'
```
`BatchMode=yes` disables password prompts entirely, so the command either succeeds with no input or fails hard. If it prints `<admin>` and `spark-<XXXX>`, key auth is working and any tool that runs `ssh spark <cmd>` now works without prompting.

**Revoke access later**: on Spark, delete the corresponding line from `~/.ssh/authorized_keys`:
```bash
sed -i '/daily-driver-for-agents/d' ~/.ssh/authorized_keys
```
(Matches by the comment you put in the key when you generated it.)

**Optional speed boost: SSH ControlMaster**. Each `ssh spark <command>` normally does a TCP+SSH handshake (~200–500 ms). Add these to `~/.ssh/config` so one connection is reused across multiple commands (~50 ms per command after the first):
```
Host spark
    # ... existing settings ...
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 5m
```
Then `mkdir -p ~/.ssh/cm-*` so the socket directory exists. Useful when an agent runs many small commands in a row during a setup session.

**Optional: passwordless sudo for the admin user**. With key-based SSH set up, `ssh spark <cmd>` works non-interactively for unprivileged commands. Anything requiring `sudo` still prompts for the admin password, which an agent cannot provide. Granting NOPASSWD removes that gate so an agent can run, e.g., `ssh spark 'sudo systemctl edit user.slice'` end-to-end without human intervention.

```bash
TMP=$(mktemp)
echo '<admin> ALL=(ALL:ALL) NOPASSWD: ALL' > "$TMP"
sudo visudo -c -f "$TMP" && \
  sudo install -m 0440 -o root -g root "$TMP" /etc/sudoers.d/<admin>-nopasswd && \
  rm "$TMP" && \
  sudo -n true && echo "NOPASSWD OK"
```

The temporary-file plus `visudo -c` validation pattern guarantees an invalid sudoers fragment never lands in `/etc/sudoers.d/`. Mode `0440` and ownership `root:root` are required by `visudo`; it will refuse the file otherwise.

**Security trade-off**: with NOPASSWD active, anyone who obtains the corresponding SSH private key has root immediately. Mitigations:
- Add a passphrase to the private key: `ssh-keygen -p -f ~/.ssh/id_ed25519`. Use ssh-agent to cache; the agent prompts once per session, not per command.
- Limit NOPASSWD to specific user accounts (here: admin only), not the whole `sudo` group. Other admins still type their password.
- Keep this off the collaborator account.

**Revoke**: `sudo rm /etc/sudoers.d/<admin>-nopasswd`.

### Pattern B: Native Claude Code on Spark

**Why**: SSH from the daily driver works, but every tool call has SSH overhead. For a workflow with many small file operations (navigating a large codebase, running many short commands, editing many files), that latency compounds. A Claude Code instance running **on Spark itself** uses Spark's local shell and filesystem directly — tool calls take single-digit milliseconds instead of hundreds.

You end up with two agent sessions:

```
┌──────────────────────┐       ┌──────────────────────┐
│ Daily-driver session │       │  Spark-native session│
│                      │       │                      │
│  Bash → local shell  │       │  Bash → local shell  │
│  Files → local disk  │       │  Files → Spark disk  │
│  To touch Spark:     │       │  Native access       │
│  ssh spark <cmd>     │       │  (no SSH)            │
└──────────────────────┘       └──────────────────────┘
```

**Install** on Spark:
```bash
# SSH into Spark as <admin>, then:
curl -fsSL https://claude.ai/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
claude --version
```
The installer detects aarch64 and downloads the right binary. Tested working: Claude Code 2.1.105 on DGX OS 7.5.0.

**First launch (browser auth)**:
```bash
claude
```
Prints a URL with a one-time code. Open the URL in a browser on your daily-driver, sign in to your Anthropic account, paste the code back into the Spark terminal. One-time; subsequent launches are silent. If Spark has a full browser (graphical.target), the flow can happen locally instead.

**Long-running sessions with tmux**:
Claude Code runs inside the SSH session. If the SSH drops (network blip, closing the terminal), the Claude instance exits. For longer work, wrap it in tmux so it survives disconnects:
```bash
sudo apt install -y tmux   # one-time
tmux new -s claude
claude
# Ctrl+B then D to detach; the session keeps running in the background
# Later, from any Spark shell:
tmux attach -t claude
```

**Bootstrap your shared agent-config on Spark** (so the Spark-side session uses the same skills, conventions, and command aliases as your daily-driver session):
```bash
mkdir -p ~/projects/spark-sandbox
cd ~/projects/spark-sandbox
git init -q
mkdir -p .agent-config .claude/commands
curl -sfL https://raw.githubusercontent.com/yzhao062/agent-config/main/bootstrap/bootstrap.sh -o .agent-config/bootstrap.sh
bash .agent-config/bootstrap.sh
claude
```

**Config location**: Spark-side Claude Code state lives in `~/.claude/` on Spark (auth token, conversation history, skills cache). It is completely independent from your daily-driver `~/.claude/`. Two independent installations, two independent logins, two independent conversation histories.

### When to use which pattern

| Task | Pattern A (SSH from daily driver) | Pattern B (Claude on Spark) |
|---|:---:|:---:|
| One-off setup commands | ✓ | |
| Cross-machine work (files on both sides) | ✓ | |
| Heavy ML development (training scripts, debugging) | | ✓ |
| High-frequency file operations | | ✓ |
| Large remote codebase navigation | | ✓ |
| Configuring Spark from outside | ✓ | |
| Need to stay in sync with daily-driver context | ✓ | |
| Latency-sensitive interactive work | | ✓ |

**Both are valid and complementary.** Daily-driver agent for cross-machine orchestration, Spark-native agent for in-depth work on Spark. You can even let them coordinate through shared files (e.g., daily-driver agent SSHes in, writes a task description to `/home/<admin>/task.md`; Spark-native agent picks it up and works on it). Overkill for most situations but possible.

## 19. Primary references
- DGX Spark User Guide (PDF): https://docs.nvidia.com/dgx/dgx-spark/dgx-spark.pdf
- Initial Setup, First Boot: https://docs.nvidia.com/dgx/dgx-spark/first-boot.html
- Set Up Local Network Access: https://build.nvidia.com/spark/connect-to-your-spark
- Set Up Tailscale on Your Spark (official): https://build.nvidia.com/spark/tailscale
- Connect Two Sparks: https://build.nvidia.com/spark/connect-two-sparks/stacked-sparks
- Spark Stacking: https://docs.nvidia.com/dgx/dgx-spark/spark-clustering.html
- Hardware Overview: https://docs.nvidia.com/dgx/dgx-spark/hardware.html
- NVIDIA Sync: https://docs.nvidia.com/dgx/dgx-spark/nvidia-sync.html
- Remote Access Playbook (DeepWiki): https://deepwiki.com/NVIDIA/dgx-spark-playbooks/2.3-setting-up-remote-access-with-tailscale
- Price change announcement (Feb 2026): https://forums.developer.nvidia.com/t/2-23-2026-price-change-announcement/361713
- LADWP Residential Electric Rates: https://www.ladwp.com/account/understanding-your-rates/residential-electric-rates
- Tailscale Node Sharing: https://tailscale.com/docs/features/sharing
- Tailscale Free Plans and Discounts: https://tailscale.com/kb/1154/free-plans-discounts
- Claude Code installation: https://claude.ai/install.sh
