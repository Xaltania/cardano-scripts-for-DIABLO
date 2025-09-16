import urllib.request
import datetime
import subprocess
import pathlib
import tarfile 
import json
import re

class ShelleyCreds:
    def __init__(self, shelley_keyspath):
 
        self.shelley_keyspath = shelley_keyspath 
        
        # shelley genesis gov creds
        self.shelley_genesis_creds = None

        # shelley governance keys
        self.shelley_gen_vkey_file = f"{self.shelley_keyspath}/shelley_genesis.0.vkey"
        self.shelley_gen_skey_file = f"{self.shelley_keyspath}/shelley_genesis.0.skey"
        self.shelley_gen_hash_file = f"{self.shelley_keyspath}/shelley_genesis.0.hash"
        self.shelley_del_vkey_file = f"{self.shelley_keyspath}/shelley_delegate.0.vkey"
        self.shelley_del_skey_file = f"{self.shelley_keyspath}/shelley_delegate.0.skey"
        self.shelley_del_hash_file = f"{self.shelley_keyspath}/shelley_delegate.0.hash"
        self.shelley_del_op_counter = f"{self.shelley_keyspath}/shelley_delegate_opcert.0.counter"
        self.shelley_del_vrf_skey_file = f"{self.shelley_keyspath}/shelley_delegate_vrf.0.skey"
        self.shelley_del_vrf_vkey_file = f"{self.shelley_keyspath}/shelley_delegate_vrf.0.vkey"
        self.shelley_del_vrf_hash_file = f"{self.shelley_keyspath}/shelley_delegate_vrf.0.hash"

    def generate_keys(self, cli_path):
        try:

            # shelley governance keys
            genesis = (
                f"{cli_path}/cardano-cli conway genesis key-gen-genesis "
                f"--verification-key-file {self.shelley_gen_vkey_file} "
                f"--signing-key-file {self.shelley_gen_skey_file}"
            )
            response = subprocess.getstatusoutput(genesis)
            if response[0]:
                raise Exception(response[1])
            
            delegate = (
                f"{cli_path}/cardano-cli conway genesis key-gen-delegate "
                f"--verification-key-file {self.shelley_del_vkey_file} "
                f"--signing-key-file {self.shelley_del_skey_file} "
                f"--operational-certificate-issue-counter-file {self.shelley_del_op_counter }"
            )                
            response = subprocess.getstatusoutput(delegate)
            if response[0]:
                raise Exception(response[1])

            genesis_hash = (
                f"{cli_path}/cardano-cli conway genesis key-hash "
                f"--verification-key-file {self.shelley_gen_vkey_file} "
                f"> {self.shelley_gen_hash_file}"
            )
            response = subprocess.getstatusoutput(genesis_hash)
            if response[0]:
                raise Exception(response[1])
            
            delegate_hash = (
                f"{cli_path}/cardano-cli conway genesis key-hash "
                f"--verification-key-file {self.shelley_del_vkey_file} "
                f"> {self.shelley_del_hash_file}"
            )
            response = subprocess.getstatusoutput(delegate_hash)
            if response[0]:
                raise Exception(response[1])

            delegate_vrf = (
                f"{cli_path}/cardano-cli conway node key-gen-VRF "
                f"--verification-key-file {self.shelley_del_vrf_vkey_file} "
                f"--signing-key-file {self.shelley_del_vrf_skey_file}"
            )
            response = subprocess.getstatusoutput(delegate_vrf)
            if response[0]:
                raise Exception(response[1])
            
            delegate_vrf_hash = (
                f"{cli_path}/cardano-cli conway node key-hash-VRF "
                f"--verification-key-file {self.shelley_del_vrf_vkey_file} "
                f"--out-file {self.shelley_del_vrf_hash_file}"
            )
            response = subprocess.getstatusoutput(delegate_vrf_hash)
            if response[0]:
                raise Exception(response[1])
                
        except Exception as err:	
            return (False, err)
        return (True, response[1])          
    
    def set_credentials(self):
        try:
            # shelley genesis gov creds
            f = open(self.shelley_del_hash_file,"r")
            del_hash = f.read()
            f.close()
            # shelley genesis gov creds
            f = open(self.shelley_gen_hash_file,"r")
            gen_hash = f.read()
            f.close()
            # shelley genesis gov creds
            f = open(self.shelley_del_vrf_hash_file,"r")
            vrf_hash = f.read()
            f.close()
            
            self.shelley_genesis_creds = {
                gen_hash.strip(): {"delegate": del_hash.strip(),
                "vrf": vrf_hash.strip()}
            }
           
        except Exception as err:	
            return (False,err)
        return (True,)          
    
    def get_credentials(self):
        return self.shelley_genesis_creds  
        
class Utxo:
    def __init__(self, index , utxo_keyspath, magic):
 
        self.utxo_keyspath = utxo_keyspath
        self.index = index
        self.magic = magic
        
        self.utxo_stake_account_creds = None
        self.utxo_staked_address_creds = None
        self.utxo_genesis_address_creds = None
        
        # utxo keys
        self.utxo_payment_skey_file = f"{self.utxo_keyspath}/payment.{self.index}.skey"         
        self.utxo_payment_vkey_file = f"{self.utxo_keyspath}/payment.{self.index}.vkey"         
        self.utxo_stake_skey_file = f"{self.utxo_keyspath}/stake.{self.index}.skey"         
        self.utxo_stake_vkey_file = f"{self.utxo_keyspath}/stake.{self.index}.vkey"         
        self.utxo_genesis_skey_file = f"{self.utxo_keyspath}/genesis.{self.index}.skey"
        self.utxo_genesis_vkey_file = f"{self.utxo_keyspath}/genesis.{self.index}.vkey"
        self.utxo_staked_addr_info_file = f"{self.utxo_keyspath}/delegated.{self.index}.addr.info"
        self.utxo_stake_addr_info_file = f"{self.utxo_keyspath}/stake.{self.index}.addr.info"
        self.utxo_genesis_addr_info_file = f"{self.utxo_keyspath}/genesis.{self.index}.addr.info"
        
    def generate_keys(self, cli_path):
        try:
            
            # utxo keys
            utxo_payment = (
                f"{cli_path}/cardano-cli conway address key-gen "
                f"--verification-key-file {self.utxo_payment_vkey_file} "
                f"--signing-key-file {self.utxo_payment_skey_file}"
            )
            response = subprocess.getstatusoutput(utxo_payment)
            if response[0]:
                raise Exception(response[1])

            utxo_genesis = (
                f"{cli_path}/cardano-cli conway genesis key-gen-utxo "
                f"--verification-key-file {self.utxo_genesis_vkey_file} "
                f"--signing-key-file {self.utxo_genesis_skey_file}"
            )
            response = subprocess.getstatusoutput(utxo_genesis)
            if response[0]:
                raise Exception(response[1])
            
            utxo_stake = (
                f"{cli_path}/cardano-cli conway stake-address key-gen "
                f"--verification-key-file {self.utxo_stake_vkey_file} "
                f"--signing-key-file {self.utxo_stake_skey_file}"
            )
            response = subprocess.getstatusoutput(utxo_stake)
            if response[0]:
                raise Exception(response[1])

            utxo_del_addr = (
                f"{cli_path}/cardano-cli conway address build "
                f"--payment-verification-key-file {self.utxo_payment_vkey_file} "
                f"--stake-verification-key-file {self.utxo_stake_vkey_file} "
                f"--testnet-magic {self.magic}"
            )
            response = subprocess.getstatusoutput(utxo_del_addr)
            if response[0]:
                raise Exception(response[1])
            
            utxo_del_addr_info = (
                f"{cli_path}/cardano-cli conway address info --address {response[1]} "
                f"--out-file {self.utxo_staked_addr_info_file}"
            )
            response = subprocess.getstatusoutput(utxo_del_addr_info)
            if response[0]:
                raise Exception(response[1])

            utxo_stake_addr = (
                f"{cli_path}/cardano-cli conway stake-address build "
                f"--stake-verification-key-file {self.utxo_stake_vkey_file} "
                f"--testnet-magic {self.magic}"
            )
            response = subprocess.getstatusoutput(utxo_stake_addr)
            if response[0]:
                raise Exception(response[1])
            
            utxo_stake_addr_info = (
                f"{cli_path}/cardano-cli conway address info --address {response[1]} "
                f"--out-file {self.utxo_stake_addr_info_file}"
            )
            response = subprocess.getstatusoutput(utxo_stake_addr_info)
            if response[0]:
                raise Exception(response[1])

            utxo_genesis_addr = (
                f"{cli_path}/cardano-cli conway genesis initial-addr "
                f"--verification-key-file {self.utxo_genesis_vkey_file} "
                f"--testnet-magic {self.magic}"
            )
            response = subprocess.getstatusoutput(utxo_genesis_addr)
            if response[0]:
                raise Exception(response[1])

            utxo_genesis_addr_info = (
                f"{cli_path}/cardano-cli conway address info --address {response[1]} "
                f"--out-file {self.utxo_genesis_addr_info_file}"
            )
            response = subprocess.getstatusoutput(utxo_genesis_addr_info)
            if response[0]:
                raise Exception(response[1])
            
        except Exception as err:	
            return (False, err)
        return (True, response[1])          
    
    def set_credentials(self):
        try:
            # utxo stake creds
            f = open(self.utxo_stake_addr_info_file,"r")
            self.utxo_stake_account_creds = json.loads(f.read())
            f.close()
            
            # utxo staked address creds
            f = open(self.utxo_staked_addr_info_file,"r")
            self.utxo_staked_address_creds = json.loads(f.read())
            f.close()
           
            f = open(self.utxo_genesis_addr_info_file,"r")
            self.utxo_genesis_address_creds = json.loads(f.read())
            f.close()

        except Exception as err:	
            return (False,err)
        return (True,)          
    
    def get_credentials(self):
        return {
            'stake_acc_creds': self.utxo_stake_account_creds,  
            'staked_addr_creds': self.utxo_staked_address_creds,
            'genesis_addr_creds': self.utxo_genesis_address_creds
        }          
    
class StakePool:
    def __init__(self, index , pool_keyspath, magic):
 
        self.pool_keyspath = pool_keyspath
        self.index = index
        self.magic = magic
        
        self.pool_id = {}
        self.pool_reward_creds = None
        self.pool_vrf_creds = None
        self.bulk_creds = []

        # pool keys
        self.cold_skey_file = f"{self.pool_keyspath}/cold.skey"
        self.cold_vkey_file = f"{self.pool_keyspath}/cold.vkey"
        self.opcert_c_file = f"{self.pool_keyspath}/opcert.counter"        
        self.vrf_skey_file = f"{self.pool_keyspath}/vrf.skey"
        self.vrf_vkey_file = f"{self.pool_keyspath}/vrf.vkey"
        self.vrf_hash_file = f"{self.pool_keyspath}/vrf.hash"
        self.kes_skey_file = f"{self.pool_keyspath}/kes.skey"
        self.kes_vkey_file = f"{self.pool_keyspath}/kes.vkey"
        self.opcert_file = f"{self.pool_keyspath}/opcert.cert" 
        self.payment_vkey_file = f"{self.pool_keyspath}/payment.vkey"
        self.payment_skey_file = f"{self.pool_keyspath}/payment.skey"
        self.payment_addr_file = f"{self.pool_keyspath}/payment.addr.info"
        self.stake_vkey_file = f"{self.pool_keyspath}/stake.vkey"
        self.stake_skey_file = f"{self.pool_keyspath}/stake.skey"
        self.stake_addr_file = f"{self.pool_keyspath}/stake.addr.info"
        
        # pool creds
        self.pool_id_hex_file = f"{self.pool_keyspath}/pool_id.hex"
        self.pool_id_bech32_file = f"{self.pool_keyspath}/pool_id.bech32"

    def generate_keys(self, cli_path):
        try:
            # pool keys
            cold = (
                f"{cli_path}/cardano-cli conway node key-gen "
                f"--cold-verification-key-file {self.cold_vkey_file} "
                f"--cold-signing-key-file {self.cold_skey_file} "
                f"--operational-certificate-issue-counter-file {self.opcert_c_file}"
            )
            response = subprocess.getstatusoutput(cold)
            if response[0]:
                raise Exception(response[1])

            vrf = (
                f"{cli_path}/cardano-cli conway node key-gen-VRF "
                f"--verification-key-file {self.vrf_vkey_file} "
                f"--signing-key-file {self.vrf_skey_file}"
            )
            response = subprocess.getstatusoutput(vrf)
            if response[0]:
                raise Exception(response[1])
            
            vrf_hash = (
                f"{cli_path}/cardano-cli conway node key-hash-VRF "
                f"--verification-key-file {self.vrf_vkey_file} "
                f"--out-file {self.vrf_hash_file}"
            )
            response = subprocess.getstatusoutput(vrf_hash)
            if response[0]:
                raise Exception(response[1])

            kes = (
                f"{cli_path}/cardano-cli conway node key-gen-KES "
                f"--verification-key-file {self.kes_vkey_file} "
                f"--signing-key-file {self.kes_skey_file}"
            )
            response = subprocess.getstatusoutput(kes)
            if response[0]:
                raise Exception(response[1])

            opcert = (
                f"{cli_path}/cardano-cli conway node issue-op-cert "
                f"--kes-verification-key-file {self.kes_vkey_file } "
                f"--cold-signing-key-file {self.cold_skey_file} "
                f"--operational-certificate-issue-counter {self.opcert_c_file} "
                f"--kes-period 0 "
                f"--out-file {self.opcert_file}"            
            )
            response = subprocess.getstatusoutput(opcert)
            if response[0]:
                raise Exception(response[1])

            
            # pool creds 
            pool_id_hex = (
                f"{cli_path}/cardano-cli conway stake-pool id "
                f"--cold-verification-key-file {self.cold_vkey_file} "
                f"--output-format hex "
                f"--out-file {self.pool_id_hex_file}"
            )
            response = subprocess.getstatusoutput(pool_id_hex)
            if response[0]:
                raise Exception(response[1])
            
            pool_id_bech32 = (
                f"{cli_path}/cardano-cli conway stake-pool id "
                f"--cold-verification-key-file {self.cold_vkey_file} "
                f"--output-format bech32 "
                f"--out-file {self.pool_id_bech32_file}"
            )
            response = subprocess.getstatusoutput(pool_id_bech32)
            if response[0]:
                raise Exception(response[1])

            pool_payment = (
                f"{cli_path}/cardano-cli conway address key-gen "
                f"--verification-key-file {self.payment_vkey_file} "
                f"--signing-key-file {self.payment_skey_file}"
            )
            response = subprocess.getstatusoutput(pool_payment)
            if response[0]:
                raise Exception(response[1])
            
            pool_stake = (
                f"{cli_path}/cardano-cli conway stake-address key-gen "
                f"--verification-key-file {self.stake_vkey_file} "
                f"--signing-key-file {self.stake_skey_file}"
            )
            response = subprocess.getstatusoutput(pool_stake)
            if response[0]:
                raise Exception(response[1])
            
            pool_payment_addr = (
                f"{cli_path}/cardano-cli conway address build "
                f"--payment-verification-key-file {self.payment_vkey_file} "
                f"--testnet-magic {self.magic}"
            )
            response = subprocess.getstatusoutput(pool_payment_addr)
            if response[0]:
                raise Exception(response[1])
            
            pool_payment_addr_info = (
                f"{cli_path}/cardano-cli conway address info --address {response[1]} "
                f"--out-file {self.payment_addr_file}"
            )
            response = subprocess.getstatusoutput(pool_payment_addr_info)
            if response[0]:
                raise Exception(response[1])

            pool_stake_addr = (
                f"{cli_path}/cardano-cli conway stake-address build "
                f"--stake-verification-key-file {self.stake_vkey_file} "
                f"--testnet-magic {self.magic}"
            )
            response = subprocess.getstatusoutput(pool_stake_addr)
            if response[0]:
                raise Exception(response[1])
            
            pool_stake_addr_info = (
                f"{cli_path}/cardano-cli conway address info --address {response[1]} "
                f"--out-file {self.stake_addr_file}"
            )
            response = subprocess.getstatusoutput(pool_stake_addr_info)
            if response[0]:
                raise Exception(response[1])
            
        except Exception as err:	
            return (False, err)
        return (True, response[1])          

                           
    def set_credentials(self):
        try:
            # pool id
            f = open(self.pool_id_hex_file, "r")
            self.pool_id.update({"hex": f.read()})
            f.close()
            f = open(self.pool_id_bech32_file, "r")
            self.pool_id.update({"bech32": f.read()})
            f.close()            

            # pool reward credentials
            f = open(self.stake_addr_file, "r")
            self.pool_reward_creds = json.loads(f.read())
            f.close()

            # pool vrf creds
            f = open(self.vrf_hash_file ,"r")
            self.pool_vrf_creds = {"vrf_hash": f.read()}
            f.close()
          
            # opcert bulk cred
            f = open(self.opcert_file, "r")
            self.bulk_creds.append(json.loads(f.read()))
            f.close()
            # vrf bulk cred
            f = open(self.vrf_skey_file, "r")
            self.bulk_creds.append(json.loads(f.read()))
            f.close()
            # kes bulk cred
            f = open(self.kes_skey_file, "r")
            self.bulk_creds.append(json.loads(f.read()))
            f.close()
            
        except Exception as err:	
            return (False,err)
        return (True,)          
    
    def get_credentials(self):
        return {
            'pool_id': self.pool_id, 
            'reward_creds': self.pool_reward_creds, 
            'vrf_creds': self.pool_vrf_creds
        }          
    
    def get_bulk_creds(self):
        return self.bulk_creds          
    
def cversion(cli_path):
    try:
        cli_version = (
            f"{cli_path}/cardano-cli --version"
        )
    
        response = subprocess.getstatusoutput(cli_version)
        if response[0]:
            raise Exception(response[1])
        
        node_version = (
            f"{cli_path}/cardano-node --version"
        )
    
        response_n = subprocess.getstatusoutput(node_version)
        if response_n[0]:
            raise Exception(response_n[1])
    
    except Exception as err:	
        return (False, err)
    return (True, response[1][0:18], response_n[1][0:18])          


def get_bin(url, path):
    try:

        binfile = pathlib.Path(path/'node.tar.gz').absolute()
        urllib.request.urlretrieve(url, binfile)

        file = tarfile.open(binfile)   
        file.extractall('./cardano-node') 
        file.close() 

        binfile.unlink(missing_ok=True)
    
    except Exception as  err:	
        return (False, err)
    return (True,)          

def start_time(delay, sys_start):
    
    utcnow = datetime.datetime.now(datetime.UTC)
    utc_delayed = utcnow + datetime.timedelta(minutes=delay)

    if sys_start == 'now':     

        epoch_time_utc = int(round(utc_delayed.timestamp()))
        system_start_utc = (
            datetime.datetime.fromtimestamp(
                    epoch_time_utc, datetime.UTC
                    )).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
    
        system_start_utx_str = sys_start
        system_start_utx_obj = datetime.datetime.strptime(system_start_utx_str+' +0000', "%Y-%m-%dT%H:%M:%SZ %z")
        system_start_delayed = system_start_utx_obj + datetime.timedelta(minutes=delay)
        epoch_time_utc = int(round(system_start_delayed.timestamp()))
        system_start_utc = (
            datetime.datetime.fromtimestamp(
                    epoch_time_utc, datetime.UTC
                    )).strftime("%Y-%m-%dT%H:%M:%SZ")

    return (epoch_time_utc, system_start_utc)


def get_pool_data(
        index, 
        domain,
        pool_cost, 
        pool_margin, 
        pool_pledge, 
        pool_id_hex, 
        reward_cred, 
        vrf_cred
    ):
    
    pool_data = {
        "cost": pool_cost,
        "margin": pool_margin,
        "metadata": None,
        "owners": [],
        "pledge": pool_pledge,
        "publicKey": pool_id_hex,
        "relays": [{
            "single host name": {
                "dnsName": f"p{index+1}.{domain}",
                "port": 3001,
            }},
            { "multi host name": {
                "dnsName": f"p{index+1}.{domain}"
            }
        }],
        "rewardAccount": {
            "credential": {
                "keyHash": reward_cred
            },
            "network": "Testnet"
        },
        "vrf": vrf_cred
    }    
    return pool_data



def get_topology(index, pool_count):

    pool_range = list(range(pool_count))    
    port_range = pool_range.copy()
    port_range.insert(0,pool_range[-1])
    port_range.append(0)

    if pool_count == 1:
        topology_template = {
          "localRoots": [
            {
              "accessPoints": [],
              "advertise": False,
              "valency": 1
            }
          ],
          "publicRoots": [
            {
              "accessPoints": [],
              "advertise": False
            }
          ],
          "useLedgerAfterSlot": -1
        }
    elif pool_count == 2:
        topology_template = {
          "localRoots": [
            {
              "accessPoints": [
                {
                   "address": "127.0.0.1",
                   "port": 3001+(port_range[index])
                }
              ],
              "advertise": False,
              "valency": 1
            }
          ],
          "publicRoots": [
            {
              "accessPoints": [],
              "advertise": False
            }
          ],
          "useLedgerAfterSlot": -1
        }
    else:    
        topology_template = {
          "localRoots": [
            {
              "accessPoints": [],
              "advertise": False,
              "valency": 2
            }
          ],
          "publicRoots": [
            {
              "accessPoints": [
                {
                   "address": "127.0.0.1",
                   "port": 3001+(port_range[index])
                },
                {
                   "address": "127.0.0.1",
                   "port": 3001+(port_range[index+2])
                }       
                   ],
              "advertise": False
            }
          ],
          "useLedgerAfterSlot": 0
        }   
    return topology_template

def get_edge_topology(bootstrap_ip: str | None = None, port: int = 3001, use_ledger_after_slot: int = -1):
    access = [{"address": bootstrap_ip, "port": port}] if bootstrap_ip else []
    return {
        "localRoots": [{"accessPoints": [], "advertise": False, "valency": 1}],
        "publicRoots": [{"accessPoints": access, "advertise": False}],
        "useLedgerAfterSlot": use_ledger_after_slot
    }


def get_scrape_target(index):
    
    scrape_target = "host.containers.internal:"+str(9101+index)
    return scrape_target    

def build_static_topology(vm_ips: list[str], me_idx: int, port: int) -> dict:
    """Classic static topology: {'Producers':[...]} using IPs across VMs."""
    return {
        "Producers": [
            {"addr": ip, "port": port, "valency": 1}
            for i, ip in enumerate(vm_ips) if i != me_idx
        ]
    }

def build_p2p_topology(vm_ips: list[str], me_idx: int, port: int,
                       use_ledger_after_slot: int = -1) -> dict:
    """P2P topology using IPs across VMs (no DNS)."""
    peers = [{"address": ip, "port": port}
             for i, ip in enumerate(vm_ips) if i != me_idx]
    return {
        "localRoots": [{
            "accessPoints": peers,
            "advertise": False,
            "trustable": False,
            "valency": len(peers) if len(peers) > 0 else 1
        }],
        "publicRoots": [],
        "useLedgerAfterSlot": use_ledger_after_slot
    }
    
def validate_testnet(pool_count, delegated_supply):
    if delegated_supply % pool_count != 0:
        return (False, "delegated supply must be divisible by the number of pools")
    else:
        return (True,)

def synthesize(recovery_path, recovery_conf_path, recovery_keys_path, cli_path):
    
    try:
        db_analyser = (
            f"{cli_path}/db-analyser --db {recovery_path}/db "
            f"--validate-all-blocks "
            f"--count-blocks cardano "
            f"--config {recovery_conf_path}/config.json"
        )
        response = subprocess.getstatusoutput(db_analyser)
        if response[0]:
            raise Exception(response[1])
    
        byronpath = (recovery_conf_path/'byron-genesis.json')
        shelleypath = (recovery_conf_path/'shelley-genesis.json')
        protocolMagicId = (recovery_path/'db/protocolMagicId')
        db_clean = (recovery_path/'db/clean')
        db_lock = (recovery_path/'db/lock')
        if protocolMagicId.is_file():
            protocolMagicId_tmp = protocolMagicId.read_bytes()
        else:
            protocolMagicId_tmp = str((json.loads(shelleypath.read_text()))['networkMagic']).encode('utf-8')  
                
        protocolMagicId.unlink(missing_ok=True)
        db_lock.unlink(missing_ok=True)
        db_clean.unlink(missing_ok=True)
        epoch_start = (json.loads(byronpath.read_text()))['startTime']    
        slotLength = (json.loads(shelleypath.read_text()))['slotLength']    
        
        blks = (response[1].split())[5]
        if int(blks) != 0:
            slots = (response[1].split())[16]
            db_slots = int((re.findall('\d+', slots))[0])
        else:    
            db_slots = 0
     
        db_tip_time = epoch_start + (db_slots * slotLength)

        utcnow = datetime.datetime.now(datetime.UTC)
        epoch_time_now_utc = int(round(utcnow.timestamp()))
        delta_time = epoch_time_now_utc - db_tip_time
        if delta_time < 0:
            raise Exception("db tip is in the future!")
        else:
            slots_to_forge = int(delta_time * (1/slotLength))

        db_synthesize = (
            f"{cli_path}/db-synthesizer --db {recovery_path}/db " 
            f"--config {recovery_conf_path}/config.json "
            f"--bulk-credentials-file {recovery_keys_path}/bulk.creds.json "
            f" -a -s {slots_to_forge}"
        )
        response = subprocess.getstatusoutput(db_synthesize)
        new_db_tip_time = epoch_start + ((db_slots + slots_to_forge) * slotLength)

        new_db_tip_str_utc = (
            datetime.datetime.fromtimestamp(
                    new_db_tip_time, datetime.UTC
                    )).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        protocolMagicId.write_bytes(protocolMagicId_tmp)
        
        if response[0]:
            raise Exception(response[1])
        
    except Exception as err:	
        return (False, err)
    msg = f"{response[1]}\n\nINFO: New DB tip at {new_db_tip_str_utc} UTC\n"     
    return (True, msg)          




def analyse(recovery_path, recovery_conf_path, recovery_keys_path, cli_path):
    
    try:
        db_analyser = (
            f"{cli_path}/db-analyser --db {recovery_path}/db "
            f"--validate-all-blocks "
            f"--show-block-header-size cardano "
            f"--config {recovery_conf_path}/config.json"
        )
        response = subprocess.getstatusoutput(db_analyser)
        if response[0]:
            raise Exception(response[1])
    
        byronpath = (recovery_conf_path/'byron-genesis.json')
        shelleypath = (recovery_conf_path/'shelley-genesis.json')
        epoch_start = (json.loads(byronpath.read_text()))['startTime']    
        slotLength = (json.loads(shelleypath.read_text()))['slotLength']    
        
        blks = (response[1].split())[5]
        if int(blks) != 0:
            slots = (response[1].split())[16]
            db_slots = int((re.findall('\d+', slots))[0])
        else:    
            db_slots = 0
     
        db_tip_time = epoch_start + (db_slots * slotLength)

        db_tip_str_utc = (
            datetime.datetime.fromtimestamp(
                    db_tip_time, datetime.UTC
                    )).strftime("%Y-%m-%dT%H:%M:%SZ")
      
    except Exception as err:	
        return (False, err)
    msg = f"{response[1]}\n\nINFO: DB tip at {db_tip_str_utc} UTC\n"     
    return (True, msg)          

def trace(recovery_path, recovery_conf_path, recovery_keys_path, cli_path):
    
    try:
        db_analyser = (
            f"{cli_path}/db-analyser --db {recovery_path}/db "
            f"--validate-all-blocks "
            f"--trace-ledger cardano "
            f"--config {recovery_conf_path}/config.json"
        )
        response = subprocess.getstatusoutput(db_analyser)
        if response[0]:
            raise Exception(response[1])
    
     
    except Exception as err:	
        return (False, err)
    msg = f"{response[1]}\n"     
    return (True, msg)          

def truncate(recovery_path, recovery_conf_path, recovery_keys_path, cli_path, after_slot):
    
    try:
        protocolMagicId = (recovery_path/'db/protocolMagicId')
        db_clean = (recovery_path/'db/clean')
        db_lock = (recovery_path/'db/lock')
        byronpath = (recovery_conf_path/'byron-genesis.json')
        shelleypath = (recovery_conf_path/'shelley-genesis.json')
        if protocolMagicId.is_file():
            protocolMagicId_tmp = protocolMagicId.read_bytes()
        else:
            protocolMagicId_tmp = str((json.loads(shelleypath.read_text()))['networkMagic']).encode('utf-8')  
                
        protocolMagicId.unlink(missing_ok=True)
        db_lock.unlink(missing_ok=True)
        db_clean.unlink(missing_ok=True)

        db_truncator = (
            f"{cli_path}/db-truncater --db {recovery_path}/db "
            f"--truncate-after-slot {after_slot} "
            f"cardano "
            f"--config {recovery_conf_path}/config.json --verbose"
        )
        response = subprocess.getstatusoutput(db_truncator)
        protocolMagicId.write_bytes(protocolMagicId_tmp)
        
        if response[0]:
            raise Exception(response[1])
        
    except Exception as err:	
        return (False, err)
    msg = f"{response[1]}\n"     
    return (True, msg)          

