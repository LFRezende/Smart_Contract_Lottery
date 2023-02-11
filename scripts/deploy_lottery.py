from brownie import Lottery, config, network
from scripts.utils import get_account, get_contract, fund_with_link
import time


def deploy_lottery():
    """
    Deploys the smart contract for Lottery in the chain designated in terminal, grabbing the necessary
    addresses, verifications, remappings and variables from the config.YAML file.

    """
    account = get_account()
    # In your YAML, it's fine to set testnet keyhash/fee equal to development. It isn't chain-sensitive.
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    # lottery.wait(1) --> NO! Function deploy delivers a contract, not a transaction!
    print("\n\n>>>  Lottery Deployed!   <<<\n\n")
    return lottery

def start_lottery():
    """
    Initiates the lottery, grabbing the last deployed Lottery.
    The built-in functions of the Smart Contract check if the wallet address of the
    caller matches the one of the deployer.
    Only callable by the admin.
    """
    account = get_account()
    lottery = Lottery[-1]
    start = lottery.startLottery({"from": account})
    start.wait(1)  # Make sure the transaction is finished
    print("\n\n>>>  Lottery is started!     <<<")


def enter_lottery():
    """
    Allows a user to enter the lottery, paying an entrance Fee.
    """
    account = get_account()
    lottery = Lottery[-1]  # Latest Lottery Deployed
    value = (
        lottery.getEntranceFee() + 100000000
    )  # Grabs the mininum to enter, plus safety wei.
    enter = lottery.enter(
        {"from": account, "value": value}
    )  # When value is for payable, it is in dict.
    enter.wait(1)  # Wait the transaction to be finished.
    print("\n\n>>>      You are now in the Lottery!      <<<\n\n")


def end_lottery():
    """
    Finishes the most recently deployed Lottery, getting a random winner and
    sending him the money.
    Only callable by the admin.
    """
    account = get_account()
    lottery = Lottery[-1]
    # Need to fund the lottery contract with LINK so you request a random number.
    tx = fund_with_link(lottery.address)  # Wait again, because we're chickens
    tx.wait(1)
    # End the lottery is now possible.
    ending = lottery.endLottery({"from": account})
    ending.wait(1)
    time.sleep(60)
    print("\n\n>>>      Lottery is Finished!        <<<\n")
    print(f"    >>>>> The winner is ... {lottery.Winner()}! <<<<<\n")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
