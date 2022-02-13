from brownie import network, config, interface
from scripts.helpfulscripts import get_account
from scripts.getWETH import get_weth
from web3 import Web3

amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    # call getweth(). if we are on kovan network we dont need to call getweth as we already have but
    # if we are in mainnet fork we do neet
    if network.show_active() in ["mainnet-fork-dev"]:
        get_weth()
    # now we will get the LendingPOol or POol contract address so we can deposit/supply weth to aave
    # ABI
    # Address
    lending_pool = get_lending_pool()
    # now we will deposit our erc20 token to aave
    # first we need to APPROVE the token. ERC20 tokens have an approve function to use before sending it to see if we had given the other side permission
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    # deposit it into aave: refferralCOde is deprecated
    print("depositing")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("deposited")
    # Now we can borrow!!!! but how much? what will result on a positive health factor
    # obtain stats -> user account in aave LendingPOol contract we have: getUserAccountData
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Lets borrow!")
    # DAI : we need a conversion rate, DAI in terms of ETH
    dai_eth_price_feed = config["networks"][network.show_active()]["dai_eth_price_feed"]
    dai_eth_price = get_asset_price(dai_eth_price_feed)

    # calculate amount of dai we want to borrow: jo tinc 1 dai quants eth son, i vull saber quans dais
    # tots el meus eth. 1 dai -> 0.000344 eth; x dai -> borrowable_eth? per tant haig de fer borrowable / 0.00034
    # multipliquem per 95% perque no volem liquidarnos (com mes baix sigui el valor, mes safe)
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow {amount_dai_to_borrow}")
    dai_addr = config["networks"][network.show_active()]["dai_addr_token"]
    # now we will borrow. 3rd param is interest rate mode: 1 is stable, 0 is variable
    borrow_tx = lending_pool.borrow(
        dai_addr,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!")
    get_borrowable_data(lending_pool, account)
    # repay all. WHen repaying u have to take into account that it will cost u more than the original borrowed
    # as interest as increased. SO it is better if u do: uint(-1) to repay the entire debt, but its recommended
    # to send an amount higher than the current amount
    # repay_all(amount, lending_pool, account)
    print("You just deposited, borrowed and repayed with aave, brownie and chainlink!")


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool.address,
        config["networks"][network.show_active()]["dai_addr_token"],
        account,
    )

    dai_addr = config["networks"][network.show_active()]["dai_addr_token"]
    tx = lending_pool.repay(dai_addr, amount, 1, account.address, {"from": account})
    tx.wait(1)
    print("you have been repayed!")
    get_borrowable_data(lending_pool, account)


def get_asset_price(prife_feed_address):
    # abi
    # address
    dai_eth_price_feed = interface.AggregatorV3Interface(prife_feed_address)
    (
        roundId,
        answer,
        startedAt,
        updatedAt,
        answeredInRound,
    ) = dai_eth_price_feed.latestRoundData()
    # an easy way (as we only want the 1st index) is: latest_price=dai_eth_price_feed.latestRoundData()[1]
    converted_answer = Web3.fromWei(answer, "ether")
    print(f"The DAI/ETH price is {converted_answer}")
    return float(converted_answer)
    # 0.000344427378852393


def get_borrowable_data(lending_pool, account):
    (  # tuple
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        healt_factor,
    ) = lending_pool.getUserAccountData(
        account.address
    )  # this is a view function SO WE DONT NEED TO SPEND GAS

    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited")
    print(f"You have {total_debt_eth} worth of ETH borrowed")
    print(f"You can borrow: {available_borrow_eth} worth of ETH")
    # we return a tuple () of float as later we will use decimals
    return (float(available_borrow_eth), float(total_debt_eth))


def get_lending_pool():
    # ABI -> but better with interfaces -> if we are working with one function we can make the interface ourself
    # Address
    lending_pool_addr_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addr_provider"]
    )
    lending_pool_addr = lending_pool_addr_provider.getLendingPool()
    # now we will return the full contract LendingPool as we now have de address
    # we have added the ILendingPool interface
    lending_pool = interface.ILendingPool(lending_pool_addr)
    return lending_pool


def approve_erc20(amount, spender, erc20_addr, account):
    # ABI
    # address
    # We will approve our sent token so that another address can use it. we will call the approve
    # function with a spender addr(of who to approve and spend our tokens) and value(how much they can spend)
    # also an erc20_address to know which token we are taking about and an account from where we are approving
    print("Approving ERC20 token")
    erc = interface.IERC20(erc20_addr)
    tx = erc.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("approved")
    return tx
