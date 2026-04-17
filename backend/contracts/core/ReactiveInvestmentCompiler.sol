pragma solidity ^0.8.24;

import {IReactiveInvestmentCompiler} from "../interfaces/IReactiveInvestmentCompiler.sol";

contract ReactiveInvestmentCompiler is IReactiveInvestmentCompiler {
    struct InvestmentPosition {
        InvestmentIntent intent;
        PositionState state;
        uint256 actualPositionSize;
        bool exists;
    }

    mapping(bytes32 intentId => InvestmentPosition) private _positions;
    mapping(address relayer => bool) private _authorizedRelayers;

    uint256 private constant _BPS_DENOMINATOR = 10_000;
    address private immutable _owner;

    constructor() {
        _owner = msg.sender;
    }

    function registerInvestmentIntent(bytes32 intentId, InvestmentIntent calldata intent) external override {
        if (_positions[intentId].exists) {
            revert IntentAlreadyRegistered(intentId);
        }

        _positions[intentId] = InvestmentPosition({
            intent: intent,
            state: PositionState.PendingEntry,
            actualPositionSize: 0,
            exists: true
        });

        emit InvestmentIntentRegistered(intentId, intent.owner);
    }

    function executeReactiveTrigger(
        bytes32 intentId,
        ReactiveTriggerType triggerType,
        uint256 observedOut
    ) external override {
        InvestmentPosition storage position = _positions[intentId];
        if (!position.exists) {
            revert IntentNotRegistered(intentId);
        }

        PositionState currentState = position.state;
        if (currentState == PositionState.Closed) {
            revert ClosedIntentCannotExecute(intentId);
        }

        if (currentState == PositionState.PendingEntry) {
            if (triggerType != ReactiveTriggerType.Entry) {
                revert InvalidTriggerForState(intentId, triggerType, currentState);
            }
            _executeEntry(position, intentId, observedOut);
            return;
        }

        if (triggerType == ReactiveTriggerType.Entry) {
            revert InvalidTriggerForState(intentId, triggerType, currentState);
        }
        if (triggerType != ReactiveTriggerType.StopLoss && triggerType != ReactiveTriggerType.TakeProfit) {
            revert InvalidTriggerForState(intentId, triggerType, currentState);
        }
        _executeExit(position, intentId, triggerType, observedOut);
    }

    function owner() external view override returns (address) {
        return _owner;
    }

    function setEmergencyAuthorizedRelayer(address relayer, bool authorized) external override {
        if (msg.sender != _owner) {
            revert UnauthorizedRelayerConfigCaller(msg.sender);
        }
        if (relayer == address(0)) {
            revert ZeroAddressRelayer();
        }

        _authorizedRelayers[relayer] = authorized;
        emit EmergencyRelayerAuthorizationUpdated(relayer, authorized);
    }

    function isEmergencyAuthorizedRelayer(address relayer) external view override returns (bool) {
        return _authorizedRelayers[relayer];
    }

    function emergencyForceClose(
        bytes32 intentId,
        uint256 maxSlippageBps
    ) external override returns (uint256 emergencyExitMinOut) {
        InvestmentPosition storage position = _positions[intentId];
        if (!position.exists) {
            revert IntentNotRegistered(intentId);
        }
        if (!_isEmergencyCallerAuthorized(msg.sender)) {
            revert UnauthorizedEmergencyForceCloseCaller(intentId, msg.sender);
        }

        PositionState currentState = position.state;
        if (currentState != PositionState.ActivePosition) {
            revert EmergencyForceCloseOnlyActivePosition(intentId, currentState);
        }
        if (maxSlippageBps > _BPS_DENOMINATOR) {
            revert EmergencySlippageBpsOutOfRange(intentId, maxSlippageBps);
        }
        if (position.actualPositionSize == 0) {
            revert ActualPositionSizeNotRecorded(intentId);
        }

        // Break-glass invariant: mark as closed first, then publish emergency exit constraint.
        position.state = PositionState.Closed;
        emergencyExitMinOut = _deriveEmergencyExitMinOut(position.actualPositionSize, maxSlippageBps);

        // TODO(domain): execution adapter / settlement receipt schema is not defined in current knowledge files.
        emit InvestmentStateAdvanced(intentId, currentState, PositionState.Closed, 0, position.actualPositionSize);
        emit EmergencyForceCloseExecuted(
            intentId,
            msg.sender,
            position.actualPositionSize,
            maxSlippageBps,
            emergencyExitMinOut
        );
    }

    function _executeEntry(InvestmentPosition storage position, bytes32 intentId, uint256 observedOut) private {
        if (block.timestamp > position.intent.entryValidUntil) {
            revert EntryValidityExpired(intentId, block.timestamp, position.intent.entryValidUntil);
        }
        uint256 maxGasPriceWei = position.intent.maxGasPriceGwei * 1 gwei;
        if (tx.gasprice > maxGasPriceWei) {
            revert MaxGasPriceExceeded(intentId, tx.gasprice, position.intent.maxGasPriceGwei);
        }
        if (observedOut < position.intent.entryMinOut) {
            revert EntryConstraintViolation(intentId, observedOut, position.intent.entryMinOut);
        }

        position.actualPositionSize = observedOut;
        if (position.actualPositionSize == 0) {
            revert ActualPositionSizeNotRecorded(intentId);
        }

        PositionState fromState = position.state;
        position.state = PositionState.ActivePosition;
        emit InvestmentStateAdvanced(intentId, fromState, PositionState.ActivePosition, observedOut, position.actualPositionSize);
    }

    function _executeExit(
        InvestmentPosition storage position,
        bytes32 intentId,
        ReactiveTriggerType triggerType,
        uint256 observedOut
    ) private {
        if (position.actualPositionSize == 0) {
            revert ActualPositionSizeNotRecorded(intentId);
        }
        uint256 slippageBps = triggerType == ReactiveTriggerType.StopLoss
            ? position.intent.stopLossSlippageBps
            : position.intent.takeProfitSlippageBps;
        if (slippageBps > _BPS_DENOMINATOR) {
            revert SlippageBpsOutOfRange(intentId, slippageBps);
        }
        uint256 derivedExitMinOut = _deriveMinOutFromSlippage(position.actualPositionSize, slippageBps);
        if (observedOut < derivedExitMinOut) {
            revert ExitConstraintViolation(intentId, observedOut, derivedExitMinOut);
        }

        PositionState fromState = position.state;
        position.state = PositionState.Closed;

        // TODO(domain): keep settlement/accounting out of this module until contract spec defines it explicitly.
        emit InvestmentStateAdvanced(intentId, fromState, PositionState.Closed, observedOut, position.actualPositionSize);
    }

    function _isEmergencyCallerAuthorized(address caller) private view returns (bool) {
        return caller == _owner || _authorizedRelayers[caller];
    }

    function _deriveEmergencyExitMinOut(
        uint256 actualPositionSize,
        uint256 maxSlippageBps
    ) private pure returns (uint256 emergencyExitMinOut) {
        return _deriveMinOutFromSlippage(actualPositionSize, maxSlippageBps);
    }

    function _deriveMinOutFromSlippage(
        uint256 amount,
        uint256 slippageBps
    ) private pure returns (uint256 minOut) {
        return (amount * (_BPS_DENOMINATOR - slippageBps)) / _BPS_DENOMINATOR;
    }

    function getPositionState(bytes32 intentId) external view override returns (PositionState) {
        InvestmentPosition storage position = _positions[intentId];
        if (!position.exists) {
            revert IntentNotRegistered(intentId);
        }
        return position.state;
    }

    function getActualPositionSize(bytes32 intentId) external view override returns (uint256) {
        InvestmentPosition storage position = _positions[intentId];
        if (!position.exists) {
            revert IntentNotRegistered(intentId);
        }
        return position.actualPositionSize;
    }

    function getInvestmentIntent(bytes32 intentId) external view override returns (InvestmentIntent memory) {
        InvestmentPosition storage position = _positions[intentId];
        if (!position.exists) {
            revert IntentNotRegistered(intentId);
        }
        return position.intent;
    }
}
