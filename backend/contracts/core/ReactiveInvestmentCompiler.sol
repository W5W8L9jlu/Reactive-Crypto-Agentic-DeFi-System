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
