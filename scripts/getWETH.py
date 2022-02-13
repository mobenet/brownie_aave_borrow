from scripts.helpfulscripts import get_account
from brownie import interface, network, config


def main():
    get_weth()


def get_weth():
    """
    Mints WETH by depositing ETH
    """
    account = get_account()
    # to call weth contract we need: from interface! we could also use the get_contract function but we will not be using mocks so it doesnt make sense
    # ABI
    # address
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    # now we can call the deposit function. We deposit eth and get weth
    tx = weth.deposit({"from": account, "value": 0.1 * 10 ** 18})
    tx.wait(1)
    print("deposited 0.1 eth and received 0.1WETH")
    return tx
