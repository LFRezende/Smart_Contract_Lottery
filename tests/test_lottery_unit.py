from brownie import accounts, Lottery, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.utils import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
from web3 import Web3
import pytest


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arange
    lottery = deploy_lottery()

    # Act
    # Initial Value: 2000 -> 2000 usd/eth -> entrance Fee = 50 -> 50usd/0.025eth (Mock)
    fee = lottery.getEntranceFee()
    expectedFee = Web3.toWei(0.025, "ether")
    # Assert
    assert expectedFee == fee


def test_cant_enter_unless_started():
    #Tests if, after deployed contract, it emits a VM Error due to unacessability to enter, since it hasn't been started.

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    account = get_account()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": account, "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    """
    Deploys the contract, starts it and then enter it.
    It asserts whether the first one to enter after deployment is, indeed, us.
    """
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Want to be certain that the first player is the first one who entered, not deployed.
    assert lottery.players(0) == account


def test_end_lottery():
    """
    Deploys lottery, starts it and then enter it, paying a Fee.
    After that, funds with LinkToken the contract and then ends it.
    """
    # If not a local chain, do not test.
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Deployment
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Let's begin to end the Lottery -> Fund with link!
    fund_with_link(lottery)
    # The EndLottery function, imediately, only changes the state of Lottery to 2.
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    # The original course puts these after endLottery, with is a mistake, since the lottery balance is 0
    initial_balance = account.balance()
    lottery_balance = lottery.balance()
    tx = lottery.endLottery({"from": account})
    request_id = tx.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    assert lottery.Winner() == account
    assert lottery.balance() == 0
    assert account.balance() == initial_balance + lottery_balance
