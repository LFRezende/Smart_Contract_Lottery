// SPDX-License-Identifier: MIT
// Coded while studying the Freebootcamp course of Patrick Collins.
// While 100% coded by LFRezende, the authorship of the project is HIS, and therefore here I credit him.

pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    uint256 public usdEntryFee;
    AggregatorV3Interface public priceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyhash;
    uint256 public randomness;
    address payable public Winner;

    // For inherited contracts, we can include in our constructors an inherited constructor, and its variables.
    constructor(
        address priceFeedAddress, //Address for updating the conversion rate
        address _vrfCoordinator, // Parametized address for vrfCoord, depending on the blockchain
        address _link, // Paramatized address for the sc receiving the LINK token
        uint256 _fee, // Required fee, dependent on the blockchain - just numbers: yaml in dev net
        bytes32 _keyhash // Hash for the chainlink node for randomness provision - jn: yaml in dev net
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * 10**18; // Minimum amount in USD, with 18 decimal places of precision.
        priceFeed = AggregatorV3Interface(priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED; // Same as setting it to 1
        fee = _fee;
        keyhash = _keyhash;
    }

    // Since we want to know when it calls the VRFCoordinator in the end lottery, we must use an event.
    event RequestedRandomness(bytes32 requestId);

    // Modifier inherited from OpenZeppelin!
    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED, // So that the Admin won't mess up.
            "Lottery has already been started!"
        );
        lottery_state = LOTTERY_STATE.OPEN; // If so, open it.
    }

    function getEntranceFee() public view returns (uint256) {
        // Getting the minimum fee of 50 USD in ether.
        (, int256 price, , , ) = priceFeed.latestRoundData(); // Collecting price ETH/USD
        uint256 actualprice = uint256(price) * 10**10; // Converting data type and to 18 dec.places.
        // BEWARE!!!
        // Multiply usdEntryFee directly by 10**18 -> it will floor the value if decimal...
        actualprice = (((usdEntryFee) * 10**18) / actualprice); // Minus 100 so 50 dolars in ETH is garantied to suffice.
        return actualprice;
    }

    function enter() public payable {
        require(
            lottery_state == LOTTERY_STATE.OPEN,
            "The lottery hasn't started yet."
        );
        require(
            msg.value >= getEntranceFee(),
            "This payment is not enough. Pay at least US 50.00."
        );
        players.push(msg.sender);
    }

    // Problems with randomness... (It is indeed impossible without VRF from Chainlink)
    function endLottery() public onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER; // So no one can enter the Lottery if I end it.
        bytes32 requestId = requestRandomness(keyhash, fee); // Request a random num to VRFCoord in 1st Tx.
        emit RequestedRandomness(requestId);
    }

    // Internalize the function so only the VRFCoordinator may access it, in a 2nd Tx.
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        // Guarantee the Lottery ended.
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Lottery must be finished first!"
        );
        // Guarantee a valid random number
        require(
            _randomness > 0,
            "Random number has not been sent by VRFCoordinator."
        );
        // Sort the winner by remainder
        uint256 indexOfWinner = _randomness % players.length;
        Winner = players[indexOfWinner];

        // Finally, we pay him the cash held in this smart contract.
        Winner.transfer(address(this).balance);
        // Resetting the Lottery
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
