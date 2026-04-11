// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IReactiveInvestmentCompiler {
    enum PositionState {
        PendingEntry,
        ActivePosition,
        Closed
    }

    enum ReactiveTriggerType {
        Entry,
        StopLoss,
        TakeProfit
    }

    struct InvestmentIntent {
        address owner;
        address inputToken;
        address outputToken;
        uint256 plannedEntrySize;
        uint256 entryMinOut;
        uint256 entryValidUntil;
        uint256 maxGasPriceGwei;
        uint256 stopLossSlippageBps;
        uint256 takeProfitSlippageBps;
    }

    error IntentAlreadyRegistered(bytes32 intentId);
    error IntentNotRegistered(bytes32 intentId);
    error ClosedIntentCannotExecute(bytes32 intentId);
    error InvalidTriggerForState(bytes32 intentId, ReactiveTriggerType triggerType, PositionState currentState);
    error EntryConstraintViolation(bytes32 intentId, uint256 observedOut, uint256 entryMinOut);
    error EntryValidityExpired(bytes32 intentId, uint256 blockTimestamp, uint256 entryValidUntil);
    error MaxGasPriceExceeded(bytes32 intentId, uint256 txGasPriceWei, uint256 maxGasPriceGwei);
    error ExitConstraintViolation(bytes32 intentId, uint256 observedOut, uint256 derivedExitMinOut);
    error SlippageBpsOutOfRange(bytes32 intentId, uint256 slippageBps);
    error ActualPositionSizeNotRecorded(bytes32 intentId);
    error UnauthorizedEmergencyForceCloseCaller(bytes32 intentId, address caller);
    error EmergencyForceCloseOnlyActivePosition(bytes32 intentId, PositionState currentState);
    error EmergencySlippageBpsOutOfRange(bytes32 intentId, uint256 maxSlippageBps);
    error UnauthorizedRelayerConfigCaller(address caller);
    error ZeroAddressRelayer();

    event InvestmentIntentRegistered(bytes32 indexed intentId, address indexed owner);
    event InvestmentStateAdvanced(
        bytes32 indexed intentId,
        PositionState fromState,
        PositionState toState,
        uint256 observedOut,
        uint256 actualPositionSize
    );
    event EmergencyRelayerAuthorizationUpdated(address indexed relayer, bool authorized);
    event EmergencyForceCloseExecuted(
        bytes32 indexed intentId,
        address indexed caller,
        uint256 actualPositionSize,
        uint256 maxSlippageBps,
        uint256 emergencyExitMinOut
    );

    function registerInvestmentIntent(bytes32 intentId, InvestmentIntent calldata intent) external;

    function executeReactiveTrigger(bytes32 intentId, ReactiveTriggerType triggerType, uint256 observedOut) external;

    function owner() external view returns (address);

    function setEmergencyAuthorizedRelayer(address relayer, bool authorized) external;

    function isEmergencyAuthorizedRelayer(address relayer) external view returns (bool);

    function emergencyForceClose(bytes32 intentId, uint256 maxSlippageBps) external returns (uint256 emergencyExitMinOut);

    function getPositionState(bytes32 intentId) external view returns (PositionState);

    function getActualPositionSize(bytes32 intentId) external view returns (uint256);

    function getInvestmentIntent(bytes32 intentId) external view returns (InvestmentIntent memory);
}
