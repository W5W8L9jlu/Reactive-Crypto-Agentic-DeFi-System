// SPDX-License-Identifier: MIT
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

    error UnauthorizedEmergencyForceCloseCaller(bytes32 intentId, address caller);
    error EmergencyForceCloseOnlyActivePosition(bytes32 intentId, PositionState currentState);
    error EmergencySlippageBpsOutOfRange(bytes32 intentId, uint256 maxSlippageBps);
    error UnauthorizedRelayerConfigCaller(address caller);
    error ZeroAddressRelayer();

    event EmergencyRelayerAuthorizationUpdated(address indexed relayer, bool authorized);
    event EmergencyForceCloseExecuted(
        bytes32 indexed intentId,
        address indexed caller,
        uint256 actualPositionSize,
        uint256 maxSlippageBps,
        uint256 emergencyExitMinOut
    );

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
        uint256 observedOut,
        uint256 runtimeExitMinOut
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
            _executeEntry(position, intentId, observedOut);
            return;
        }

        _executeExit(position, intentId, observedOut, runtimeExitMinOut);
    }

    function owner() external view returns (address) {
        return _owner;
    }

    function setEmergencyAuthorizedRelayer(address relayer, bool authorized) external {
        if (msg.sender != _owner) {
            revert UnauthorizedRelayerConfigCaller(msg.sender);
        }
        if (relayer == address(0)) {
            revert ZeroAddressRelayer();
        }

        _authorizedRelayers[relayer] = authorized;
        emit EmergencyRelayerAuthorizationUpdated(relayer, authorized);
    }

    function isEmergencyAuthorizedRelayer(address relayer) external view returns (bool) {
        return _authorizedRelayers[relayer];
    }

    function emergencyForceClose(bytes32 intentId, uint256 maxSlippageBps) external returns (uint256 emergencyExitMinOut) {
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
        uint256 observedOut,
        uint256 runtimeExitMinOut
    ) private {
        if (runtimeExitMinOut < position.intent.exitMinOutFloor) {
            revert RuntimeExitMinOutTooLow(intentId, runtimeExitMinOut, position.intent.exitMinOutFloor);
        }
        if (observedOut < runtimeExitMinOut) {
            revert ExitConstraintViolation(intentId, observedOut, runtimeExitMinOut);
        }
        if (position.actualPositionSize == 0) {
            revert ActualPositionSizeNotRecorded(intentId);
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
        return (actualPositionSize * (_BPS_DENOMINATOR - maxSlippageBps)) / _BPS_DENOMINATOR;
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
