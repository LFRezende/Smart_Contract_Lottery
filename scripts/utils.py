from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["ganache-local2", "development"]
FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork-dev", "mainnet-fork"]


def get_account(
    id=None, index=None
):  # More general function of getting your account - more versatile.
    if id:
        account = accounts.load(
            id
        )  # If you wish to get an account on your list with name id = 'name'.
        return account
    if index:
        account = accounts[
            index
        ]  # If you wish to access a specific account on brownie development network.
        return account
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        account = accounts[0]
        return account
    account = accounts.add(
        config["wallets"]["from_key"]
    )  # Remember: accounts.add(x), x an env variable.
    return account


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(
    contract_name,
):  # Parametized input so we can get more than just priceFeed in YAML.
    """
    get_contract() receives a string for the desired network. If referred in brownie_config,
    it returns the contract address. Otherwise, the mocks will be deployed, and it will be returned.

    Arguments:
        contract_name - string
    Returns:
        brownie.network.contract.ProjectContract: the most recent version of the contract deployed
    """
    contract_type = contract_to_mock[contract_name]
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
    ):  # NO NEED TO MOCK FORKED --> use the forked address
        if (
            len(contract_type) <= 0
        ):  # If there is no deployed and is local --> deploy mockv3agg
            deploy_mocks()
        contract = contract_type[
            -1
        ]  # Get the most recent contract deployed on local chain.
    else:
        contract_address = config["networks"][network.show_active()][
            contract_name
        ]  ## YAML gives address required.
        # Passing the contract by grabbing the abi and the address of the contract.
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        #  Grabs the name of Mock (f the name); grabs the address of testnet ; ABI of Mock is the same as a testnets
    return contract

    ### OLHAR REPOSITÓRIO GITHUB ^^^^


DECIMALS = 8
INITIAL_VALUE = 2000 * 10**8  # 200 gwei


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    # Deploying Mock for AggregatorV3Interface
    mock_price_feed = MockV3Aggregator.deploy(
        decimals, initial_value, {"from": account}
    )  # First two are from constructor.

    # Deploying Mock for Link Token
    link_token = LinkToken.deploy({"from": account})  # There are no constructor inputs

    # Deploying Mock for VRF Coordinator
    VRFCoordinatorMock.deploy(
        link_token.address, {"from": account}
    )  # Constructor requires address for LinkToken

    print("\n\n>>>   MOCKS DEPLOYED!    <<<\n")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=0.1 * 10**18
):
    account = account if account else get_account()  # Okay, this is SICK!!!
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(
        contract_address, amount, {"from": account}
    )  # If you have linktoken Mock
    # tx = interface.LinkTokenInterface(link_token.address)
    # link_token_contract = link_token.transfer(..., ..., ...) -> This if you have the interface.
    tx.wait(1)
    print("\n\n>>>  Funded with Link!!  <<<")
    return tx
