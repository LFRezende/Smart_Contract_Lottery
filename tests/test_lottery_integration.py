from brownie import network, Lottery
from scripts.utils import get_account, fund_with_link, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from scripts.deploy_lottery import deploy_lottery
import pytest
import time


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    time.sleep(300)
    assert lottery.Winner() == account
    assert lottery.balance() == 0
