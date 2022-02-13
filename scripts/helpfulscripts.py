from brownie import accounts, network, config

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "local-ganache", "mainnet-fork-dev"]


def get_account(id=None, index=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    if network.show_active() in config["networks"]:
        return accounts.add(config["wallets"]["from_key"])
    return None
