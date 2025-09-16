import argparse
import datetime
import pathlib
import yaml
import json
import pwd
import sys
import os

from libs.utils import Utxo
from libs.utils import StakePool
from libs.utils import ShelleyCreds
from libs.utils import get_bin
from libs.utils import cversion
from libs.utils import start_time
from libs.utils import get_pool_data
from libs.utils import get_topology
from libs.utils import get_scrape_target
from libs.utils import get_edge_topology
from libs.utils import build_static_topology
from libs.utils import build_p2p_topology
from libs.utils import validate_testnet
from libs.utils import synthesize
from libs.utils import truncate
from libs.utils import analyse
from libs.utils import trace

from rich.console import Console
from rich.progress import track

from libs.mainnet_env import byron as byron_file
from libs.mainnet_env import shelley as shelley_file
from libs.mainnet_env import alonzo as alonzo_file
from libs.mainnet_env import conway as conway_file
from libs.mainnet_env import config as config_file
from libs.mainnet_env import binary

from mergedeep import merge

byron = json.loads(byron_file)
shelley = json.loads(shelley_file)
alonzo = json.loads(alonzo_file)
conway = json.loads(conway_file)
config = json.loads(config_file)
binary = json.loads(binary)

removed = config.pop("AlonzoGenesisHash", None)
removed = config.pop("ByronGenesisHash", None)
removed = config.pop("ConwayGenesisHash", None)
removed = config.pop("ShelleyGenesisHash", None)

# Program description
descr = f"""generate custom cardano testnet environments, compatible with cardano-node {binary["version"]}"""

# Initiate the cli argument parser
arg_parser = argparse.ArgumentParser(description=descr)
arg_parser.add_argument("--version", action="version", version="%(prog)s version 0.1.0")

arg_parser.add_argument(
    "config_file",
    type=argparse.FileType("r", encoding="UTF-8"),
    nargs=1,
    help="YAML testnet config file",
    metavar="FILE",
)

arg_parser.add_argument(
    "-o",
    "--output-dir",
    type=pathlib.Path,
    nargs=1,
    required=True,
    help="path to output keys and config files",
    metavar="FILE",
)

arg_parser.add_argument(
    "-c",
    "--command",
    default="generate",
    type=str,
    nargs=1,
    required=True,
    choices=["generate", "synthesize", "truncate", "analyse", "trace"],
    help="generate testnet material or synthesize a db",
)

arg_parser.add_argument(
    "-s",
    "--slot-after",
    default=1,
    type=int,
    nargs=1,
    required=False,
    help="truncate db after slot",
)

# Read args from the command line
args = arg_parser.parse_args()

# Rich text console
console = Console()
err_console = Console(stderr=True, style="bold red")

# Read YAML config file from command line args
try:
    overide_config = yaml.safe_load_all(args.config_file[0])
    docs = list(overide_config)
    args.config_file[0].close()
except yaml.YAMLError as exc:
    args.config_file[0].close()
    err_console.print("ERROR: YAML config file error: ", exc)
    sys.exit()

# Required testnet parameters
testnet_domain = docs[0]["testnetDomain"]
pool_count = docs[0]["poolCount"]
pool_cost = docs[0]["poolCost"]
pool_margin = docs[0]["poolMargin"]
pool_pledge = docs[0]["poolPledge"]
delegated_supply = docs[0]["delegatedSupply"]
sys_start = docs[0]["systemStart"]
sys_start_delay = docs[0]["systemStartDelay"]
magic = docs[0]["networkMagic"]
vm_ips = docs[0].get("vmIps", [])
listen_port = int(docs[0].get("listenPort", 3001))
enable_p2p = bool(docs[0].get("enableP2P", False))
enable_recovery = bool(docs[0].get("enableRecoveryNode", False))
enable_monitoring = bool(docs[0].get("enableMonitoring", False))

if vm_ips and len(vm_ips) != int(pool_count):
    err_console.print("ERROR: vmIps length must equal poolCount.")
    sys.exit()


# Validate required parameters
test = validate_testnet(pool_count, delegated_supply)
if not test[0]:
    err_console.print(
        "CONSTRAINT: ",
        test[1],
    )
    sys.exit()

cwd = pathlib.Path.cwd().absolute()
basepath = args.output_dir[0].absolute()
deploy_path = (basepath / "deployment").absolute()
recovery_path = (basepath / "recovery").absolute()
recovery_keys_path = (basepath / "recovery" / "keys").absolute()
recovery_conf_path = (basepath / "recovery" / "configs").absolute()
utxo_keys_path = (basepath / "utxos" / "keys").absolute()
gov_keys_path = (basepath / "governance" / "shelley" / "keys").absolute()
infra_template_file = pathlib.Path("libs/infra.yaml").absolute()
bin_path = (cwd / "cardano-node").absolute()
cli_path = (cwd / "cardano-node/bin").absolute()


# Get binary
if not cli_path.exists():
    console.print("\nINFO: Fetching cardano-node binary ...", style="green")
    bin_path.mkdir(parents=True, exist_ok=False)
    resp = get_bin(binary["url"], cwd)
    if not resp[0]:
        err_console.print(
            "\nERROR: ",
            resp[1],
        )
        sys.exit()


# Validate cardano-node cli PATH
cli_vers = cversion(cli_path)
if not cli_vers[0]:
    err_console.print(
        "\nERROR: ",
        cli_vers[1],
    )
    console.print("\nIs cardano-cli in your PATH?\n", style="green")
    sys.exit()
else:
    console.print(
        "\nINFO: Using:", cli_vers[1], "\nINFO: Using:", cli_vers[2], style="green"
    )

# Synthesize db in recovery_path
if args.command[0] == "synthesize":
    resp = synthesize(recovery_path, recovery_conf_path, recovery_keys_path, cli_path)
    if not resp[0]:
        err_console.print(f"\nERROR: synthesizing blocks: \n", resp[1])
        sys.exit()

    console.print("\nINFO: ", resp[1], style="green")
    sys.exit()

# Analyse db in recovery_path
if args.command[0] == "analyse":
    resp = analyse(recovery_path, recovery_conf_path, recovery_keys_path, cli_path)
    if not resp[0]:
        err_console.print(f"\nERROR: analysing blocks: \n", resp[1])
        sys.exit()

    console.print("\nINFO: ", resp[1], style="green")
    sys.exit()

# Trace db in recovery_path
if args.command[0] == "trace":
    resp = trace(recovery_path, recovery_conf_path, recovery_keys_path, cli_path)
    if not resp[0]:
        err_console.print(f"\nERROR: tracing ledger: \n", resp[1])
        sys.exit()

    console.print("\nINFO: ", resp[1], style="green")
    sys.exit()

# Trunacte db in recovery_path
if args.command[0] == "truncate":
    if args.slot_after[0] == 1:
        err_console.print(f"\nERROR: --slot-after argument required \n")
        sys.exit()

    resp = truncate(
        recovery_path,
        recovery_conf_path,
        recovery_keys_path,
        cli_path,
        args.slot_after[0],
    )
    if not resp[0]:
        err_console.print(f"\nERROR: truncating blocks: \n", resp[1])
        sys.exit()

    console.print("\nINFO: ", resp[1], style="green")
    sys.exit()


shelley_gov = []
pools = []
utxos = []
bulk_creds = []

# Existing pool keys
pool_keys_flag = True
for index in range(pool_count):
    pool_keys_path = (basepath / "pools" / str(index + 1) / "keys").absolute()
    if pool_keys_path.exists():
        pool = StakePool(index + 1, pool_keys_path, magic)
        resp = pool.set_credentials()
        if not resp[0]:
            err_console.print(
                f"\nERROR: fetching pool {str(index + 1)} credentials: \n", resp[1]
            )
            sys.exit()
        pools.append(pool.get_credentials())
        bulk_creds.append(pool.get_bulk_creds())
    else:
        pool_keys_flag = False

# Generate pool keys if they do not exist
if not pool_keys_flag:
    pools = []
    bulk_creds = []
    for index in track(range(pool_count), description="Generating pool keys..."):
        pool_keys_path = (basepath / "pools" / str(index + 1) / "keys").absolute()
        if pool_keys_path.exists():
            pool = StakePool(index + 1, pool_keys_path, magic)
            resp = pool.set_credentials()
            if not resp[0]:
                err_console.print(
                    f"\nERROR: fetching pool {str(index + 1)} credentials: \n", resp[1]
                )
                sys.exit()

            pools.append(pool.get_credentials())
            bulk_creds.append(pool.get_bulk_creds())

        else:
            pool_keys_path.mkdir(parents=True, exist_ok=False)

            pool = StakePool(index + 1, pool_keys_path, magic)
            resp = pool.generate_keys(cli_path)
            if not resp[0]:
                err_console.print(
                    f"\nERROR: Generating pool {str(index + 1)} keys: \n", resp[1]
                )
                sys.exit()
            resp = pool.set_credentials()
            if not resp[0]:
                err_console.print(
                    f"\nERROR: fetching pool {str(index + 1)} credentials: \n", resp[1]
                )
                sys.exit()
            pools.append(pool.get_credentials())
            bulk_creds.append(pool.get_bulk_creds())

# Get utxo keys or generate new ones if they do not exist
if utxo_keys_path.exists():
    for index in range(pool_count):
        utxo = Utxo(index + 1, utxo_keys_path, magic)
        resp = utxo.set_credentials()
        if not resp[0]:
            err_console.print("\nERROR: fetching utxo credentials: \n", resp[1])
            sys.exit()
        utxos.append(utxo.get_credentials())
else:
    utxo_keys_path.mkdir(parents=True, exist_ok=False)
    for index in track(range(pool_count), description="Generating utxo keys..."):
        utxo = Utxo(index + 1, utxo_keys_path, magic)
        resp = utxo.generate_keys(cli_path)
        if not resp[0]:
            err_console.print("\nERROR: Generating utxo keys: \n", resp[1])
            sys.exit()
        resp = utxo.set_credentials()
        if not resp[0]:
            err_console.print("\nERROR: fetching utxo credentials: \n", resp[1])
            sys.exit()

        utxos.append(utxo.get_credentials())

# Get shelley keys or generate new ones if they do not exist
if gov_keys_path.exists():
    gov = ShelleyCreds(gov_keys_path)
    resp = gov.set_credentials()
    if not resp[0]:
        err_console.print("\nERROR: fetching shelley credentials: \n", resp[1])
        sys.exit()

    shelley_gov.append(gov.get_credentials())

else:
    gov_keys_path.mkdir(parents=True, exist_ok=False)
    gov = ShelleyCreds(gov_keys_path)
    resp = gov.generate_keys(cli_path)
    if not resp[0]:
        err_console.print("\nERROR: Generating shelley keys: \n", resp[1])
        sys.exit()
    resp = gov.set_credentials()
    if not resp[0]:
        err_console.print("\nERROR: fetching shelley credentials: \n", resp[1])
        sys.exit()

    shelley_gov.append(gov.get_credentials())

# Shelley genesis config
staking_conf = {"staking": {"pools": {}, "stake": {}}}
initial_funds = {"initialFunds": {}}
shelley_genDelegs = {"genDelegs": {}}

# Shelley delegate keys
for x in shelley_gov:
    shelley_genDelegs["genDelegs"] = x

# Pools, delegations and initial utxos
for x in range(pool_count):
    pool_data = get_pool_data(
        x,
        testnet_domain,
        pool_cost,
        pool_margin,
        pool_pledge,
        pools[x]["pool_id"]["hex"],
        (pools[x]["reward_creds"]["base16"])[2:],
        pools[x]["vrf_creds"]["vrf_hash"],
    )

    initial_funds["initialFunds"][utxos[x]["staked_addr_creds"]["base16"]] = int(
        delegated_supply
    ) // int(pool_count)
    initial_funds["initialFunds"][utxos[x]["genesis_addr_creds"]["base16"]] = int(
        delegated_supply
    ) // int(pool_count)
    staking_conf["staking"]["pools"][pools[x]["pool_id"]["hex"]] = pool_data
    staking_conf["staking"]["stake"][(utxos[x]["stake_acc_creds"]["base16"])[2:]] = (
        pools[x]["pool_id"]["hex"]
    )


# Start time and start delay
testnet_start = start_time(int(sys_start_delay), sys_start)

# Byron static overide
byron["protocolConsts"]["protocolMagic"] = magic
byron.update(
    {
        "bootStakeholders": {},
        "heavyDelegation": {},
        "nonAvvmBalances": {},
        "avvmDistr": {},
        "vssCerts": {},
        "ftsSeed": {},
    }
)

byron.update({"startTime": testnet_start[0]})

# Shelley static overide
shelley["networkId"] = "Testnet"
shelley["networkMagic"] = magic
shelley["updateQuorum"] = 1
shelley.update({"genDelegs": {}, "initialFunds": {}})

shelley.update({"systemStart": testnet_start[1]})
shelley.update(staking_conf)
shelley.update(initial_funds)
shelley.update(shelley_genDelegs)

# Optional overides (deepmerge)
testnet_byron = merge(byron, docs[1]) if docs[1] else byron
testnet_shelley = merge(shelley, docs[2]) if docs[2] else shelley
testnet_alonzo = merge(alonzo, docs[3]) if docs[3] else alonzo
testnet_conway = merge(conway, docs[4]) if docs[4] else conway
testnet_config = merge(config, docs[5]) if docs[5] else config


# Overwrite configs if they exist
commands = []
for index in range(pool_count):
    configs_path = (basepath / "pools" / str(index + 1) / "configs").absolute()
    configs_path.mkdir(parents=True, exist_ok=True)
    testnet_config_mod = testnet_config.copy()
    testnet_config_mod["hasPrometheus"] = ["0.0.0.0", 9101 + index]
    log_path = f"{deploy_path}/node.{str(index + 1)}.log"
    testnet_config_mod["defaultScribes"] = [["FileSK", log_path]]
    testnet_config_mod["setupScribes"] = [
        {
            "scKind": "FileSK",
            "scName": log_path,
            "scFormat": "ScJson",
            "scRotation": None,
        }
    ]
    testnet_config_mod["hasEKG"] = 12788 + index
    topology = get_topology(index, pool_count)
    testnet_config_mod["hasEKG"] = 12788 + index
    if vm_ips:
        if enable_p2p:
            testnet_config_mod["EnableP2P"] = True
            topology = build_p2p_topology(vm_ips, index, listen_port, -1)
        else:
            testnet_config_mod["EnableP2P"] = False
            topology = build_static_topology(vm_ips, index, listen_port)
    else:
        topology = get_topology(index, pool_count)

    with (configs_path / "byron-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_byron, indent=2, sort_keys=True))
    with (configs_path / "shelley-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_shelley, indent=2, sort_keys=True))
    with (configs_path / "alonzo-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_alonzo, indent=2, sort_keys=True))
    with (configs_path / "conway-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_conway, indent=2, sort_keys=True))
    with (configs_path / "config.json").open(mode="w") as f:
        f.write(json.dumps(testnet_config_mod, indent=2, sort_keys=True))
    with (configs_path / "topology.json").open(mode="w") as f:
        f.write(json.dumps(topology, indent=2))

    cmd = (
        f"nohup {cli_path}/cardano-node run "
        f"--shelley-kes-key {basepath}/pools/{str(index + 1)}/keys/kes.skey "
        f"--shelley-vrf-key {basepath}/pools/{str(index + 1)}/keys/vrf.skey "
        f"--shelley-operational-certificate {basepath}/pools/{str(index + 1)}/keys/opcert.cert "
        f"--config {basepath}/pools/{str(index + 1)}/configs/config.json "
        f"--topology {basepath}/pools/{str(index + 1)}/configs/topology.json "
        f"--database-path {deploy_path}/db{index + 1} "
        f"--socket-path {deploy_path}/node.{index + 1}.socket "
        f"--host-addr 0.0.0.0 "
        f"--port {index + 3001} >/dev/null 2>&1 &"
        f"--port {listen_port} >/dev/null 2>&1 &"
    )

    commands.append(cmd)

batch = (
    f"{cli_path}/cardano-node run "
    f"--bulk-credentials-file {recovery_keys_path}/bulk.creds.json "
    f"--config {recovery_conf_path}/config.json "
    f"--topology {recovery_conf_path}/topology.json "
    f"--database-path {recovery_path}/db "
    f"--socket-path {recovery_path}/node.socket "
    f"--port 3001 >/dev/null 2>&1 &"
)
recover = (
    f"nohup {cli_path}/cardano-node run "
    f"--config {recovery_conf_path}/config.json "
    f"--topology {recovery_conf_path}/topology.json "
    f"--database-path {recovery_path}/db "
    f"--socket-path {recovery_path}/node.socket >/dev/null 2>&1 &"
)

# Recovery node <- typo earlier?
if enable_recovery:
    recovery_path.mkdir(parents=True, exist_ok=True)
    recovery_keys_path.mkdir(parents=True, exist_ok=True)
    recovery_conf_path.mkdir(parents=True, exist_ok=True)

if enable_recovery:
    testnet_config_mod = testnet_config.copy()
    testnet_config_mod["hasPrometheus"] = ["0.0.0.0", 9091]
    testnet_config_mod["hasEKG"] = 12787
    log_path = f"{recovery_path}/node.log"
    testnet_config_mod["defaultScribes"] = [["FileSK", log_path]]
    testnet_config_mod["setupScribes"] = [
        {"scKind": "FileSK", "scName": log_path, "scFormat": "ScJson", "scRotation": None}
    ]
    # Bootstrap to pool #1 if vm_ips provided
    edge_node_topology = get_edge_topology(vm_ips[0] if vm_ips else None, listen_port, -1)
    with (recovery_conf_path / "byron-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_byron, indent=2, sort_keys=True))
    with (recovery_conf_path / "shelley-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_shelley, indent=2, sort_keys=True))
    with (recovery_conf_path / "alonzo-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_alonzo, indent=2, sort_keys=True))
    with (recovery_conf_path / "conway-genesis.json").open(mode="w") as f:
        f.write(json.dumps(testnet_conway, indent=2, sort_keys=True))
    with (recovery_conf_path / "config.json").open(mode="w") as f:
        f.write(json.dumps(testnet_config_mod, indent=2, sort_keys=True))
    with (recovery_conf_path / "topology.json").open(mode="w") as f:
        f.write(json.dumps(edge_node_topology, indent=2))
    with (recovery_keys_path / "bulk.creds.json").open(mode="w") as f:
        f.write(json.dumps(bulk_creds, indent=2))


# Deploy scripts
with (basepath / "deploy.sh").open(mode="w") as f:
    f.write("#!/bin/bash\n")
    f.write("set -e\n")
    f.write(f"podman play kube {basepath}/monitoring.yaml\n")
    for c in range(pool_count):
        f.write(commands[c] + "\n")
        f.write(f"echo $! >{deploy_path}/pid.{c + 1}.file\n")
    if enable_recovery:
        f.write(recover + "\n")
        f.write(f"echo $! >{recovery_path}/pid.file\n")
    f.write(f'echo "Started {pool_count} pool nodes ..." \n')
    if enable_recovery:
        f.write(f'echo "Started recovery node ..." \n')
    if enable_monitoring:
        f.write('echo "monitoring: http://localhost:3000"')
os.chmod(basepath / "deploy.sh", 0o777)

with (basepath / "deploy-batch.sh").open(mode="w") as f:
    f.write("#!/bin/bash\n")
    f.write("set -e\n")
    if enable_monitoring:
        f.write(f"podman play kube {basepath}/monitoring.yaml\n")
    if enable_recovery:
        f.write(batch + "\n")
        f.write(f"echo $! >{recovery_path}/pid.file\n")
        f.write(f'echo "Started batch node ..." \n')
        if enable_monitoring:
            f.write('echo "monitoring: http://localhost:3000"')
os.chmod(basepath / "deploy-batch.sh", 0o777)


# Destroy scripts
destroy_script = f"""
#!/bin/bash
for i in {{1..{pool_count}}};
do kill $(cat {deploy_path}/pid.$i.file); 
done
{"kill $(cat " + str(recovery_path) + "/pid.file);" if enable_recovery else ""}
rm -rf {deploy_path}/db* 
rm -rf {deploy_path}/node*log 
rm {deploy_path}/node.*.socket 
rm {deploy_path}/pid.*.file 
{"rm " + str(recovery_path) + "/node*log" if enable_recovery else ""}
{"rm " + str(recovery_path) + "/node.socket" if enable_recovery else ""}
{"rm " + str(recovery_path) + "/pid.file" if enable_recovery else ""}
{ "podman kube down " + str(basepath) + "/monitoring.yaml" if enable_monitoring else "" }
{ "podman volume rm testnet_promentheus_data --force" if enable_monitoring else "" }
"""

with (basepath / "destroy.sh").open(mode="w") as f:
    f.write(destroy_script)
os.chmod((basepath / "destroy.sh"), 0o777)


# Monitoring configs (optional)
monitoring_prom_path = (basepath / "monitoring" / "prometheus").absolute()
monitoring_grafana_path = (basepath / "monitoring" / "grafana").absolute()
monitoring_grafana_prov = (
    basepath / "monitoring" / "grafana" / "provisioning" / "datasources"
).absolute()
monitoring_grafana_dash = (
    basepath / "monitoring" / "grafana" / "provisioning" / "dashboards"
).absolute()
monitoring_dashboards_path = (basepath / "monitoring" / "dashboards").absolute()
monitoring_dashboards_template = pathlib.Path("libs/dashboard.json").absolute()

if enable_monitoring:
    monitoring_prom_path.mkdir(parents=True, exist_ok=True)
    monitoring_grafana_path.mkdir(parents=True, exist_ok=True)
    monitoring_grafana_prov.mkdir(parents=True, exist_ok=True)
    monitoring_grafana_dash.mkdir(parents=True, exist_ok=True)
    monitoring_dashboards_path.mkdir(parents=True, exist_ok=True)

from libs.monitoring_env import grafana_ini
from libs.monitoring_env import dashboard_provisioning
from libs.monitoring_env import grafana_provisioning
from libs.monitoring_env import prometheus_conf

if enable_monitoring:
    grafana_ini = grafana_ini.replace("$PASS", str(magic))
    prometheus_conf_yml = yaml.safe_load(prometheus_conf)

    static_conf = []
    # Recovery node target
    static_conf.append(get_scrape_target(-10))
    # Pool targets
    for index in range(pool_count):
        static_conf.append(get_scrape_target(index))
    prometheus_conf_yml["scrape_configs"].append(
        {"job_name": "cardano-node", "static_configs": [{"targets": static_conf}]}
    )

    with (monitoring_prom_path / "prometheus.yml").open(mode="w") as f:
        yaml.dump(prometheus_conf_yml, f)

    with (monitoring_grafana_path / "grafana.ini").open(mode="w") as f:
        f.write(grafana_ini)

    with (monitoring_grafana_prov / "prometheus.yaml").open(mode="w") as f:
        f.write(grafana_provisioning)

    with (monitoring_grafana_dash / "default.yaml").open(mode="w") as f:
        f.write(dashboard_provisioning)

    with (monitoring_dashboards_path / "cardano-testnet-dashboard.json").open(
        mode="w"
    ) as f:
        f.write(monitoring_dashboards_template.read_text())

# Monitoring infra
infra_txt = infra_template_file.read_text()
infra_txt = infra_txt.replace("$TESTNET_DIR", str(basepath))
infra_containers = yaml.safe_load(infra_txt)
now = (datetime.datetime.now(datetime.UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")
infra_containers["metadata"].update({"creationTimestamp": now})
infra_containers["metadata"].update({"name": str(args.output_dir[0])})
infra_containers["metadata"]["labels"].update({"app": str(args.output_dir[0])})

# Deployment folder
deploy_path.mkdir(parents=True, exist_ok=True)

# Monitoring kubernetes yaml
if enable_monitoring:
    with (basepath / "monitoring.yaml").open(mode="w") as f:
        yaml.dump(infra_containers, f)
console.print(f"INFO: Genesis Start: {testnet_start[1]} (UTC)", style="green")
console.print("INFO: Complete\n", style="green")
