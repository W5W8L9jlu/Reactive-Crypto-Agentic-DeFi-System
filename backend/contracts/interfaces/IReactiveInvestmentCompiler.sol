// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IReactiveInvestmentCompiler {
    enum PositionState {
        PendingEntry,
        ActivePosition,
        Closed
    }

    struct InvestmentIntent {
        address owner;
        address inputToken;
        address outputToken;
        uint256 plannedEntrySize;
        uint256 entryMinOut;
        uint256 exitMinOutFloor;
    }

    error IntentAlreadyRegistered(bytes32 intentId);
    error IntentNotRegistered(bytes32 intentId);
    error ClosedIntentCannotExecute(bytes32 intentId);
    error EntryConstraintViolation(bytes32 intentId, uint256 observedOut, uint256 entryMinOut);
    error ExitConstraintViolation(bytes32 intentId, uint256 observedOut, uint256 runtimeExitMinOut);
    error RuntimeExitMinOutTooLow(bytes32 intentId, uint256 runtimeExitMinOut, uint256 exitMinOutFloor);
    error ActualPositionSizeNotRecorded(bytes32 intentId);

    event InvestmentIntentRegistered(bytes32 indexed intentId, address indexed owner);
    event InvestmentStateAdvanced(
        bytes32 indexed intentId,
        PositionState fromState,
        PositionState toState,
        uint256 observedOut,
        uint256 actualPositionSize
    );

    function registerInvestmentIntent(bytes32 intentId, InvestmentIntent calldata intent) external;

    function executeReactiveTrigger(bytes32 intentId, uint256 observedOut, uint256 runtimeExitMinOut) external;

    function getPositionState(bytes32 intentId) external view returns (PositionState);

    function getActualPositionSize(bytes32 intentId) external view returns (uint256);

    function getInvestmentIntent(bytes32 intentId) external view returns (InvestmentIntent memory);
}
