// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ReactiveInvestmentCompiler} from "../core/ReactiveInvestmentCompiler.sol";
import {IReactiveInvestmentCompiler} from "../interfaces/IReactiveInvestmentCompiler.sol";

contract ReactiveInvestmentCompilerTest {
    function testCanonicalWaveOneFrozenPayloadHappyPath() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = bytes32(uint256(0x1111111111111111111111111111111111111111111111111111111111111111));
        IReactiveInvestmentCompiler.InvestmentIntent memory intent = IReactiveInvestmentCompiler.InvestmentIntent({
            owner: address(0x1),
            inputToken: address(0x2),
            outputToken: address(0x3),
            plannedEntrySize: 1_200_000_000,
            entryMinOut: 599_400_000_000_000_000,
            exitMinOutFloor: 594_005_400_000_000_000
        });

        compiler.registerInvestmentIntent(intentId, intent);

        IReactiveInvestmentCompiler.InvestmentIntent memory storedIntent = compiler.getInvestmentIntent(intentId);
        require(storedIntent.plannedEntrySize == intent.plannedEntrySize, "planned size should persist");
        require(storedIntent.entryMinOut == intent.entryMinOut, "entry min should persist");
        require(storedIntent.exitMinOutFloor == intent.exitMinOutFloor, "exit floor should persist");

        compiler.executeReactiveTrigger(intentId, 600_000_000_000_000_000, 0);
        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.ActivePosition),
            "canonical payload should activate"
        );
        require(
            compiler.getActualPositionSize(intentId) == 600_000_000_000_000_000,
            "canonical payload should record actual size"
        );

        compiler.executeReactiveTrigger(intentId, 595_000_000_000_000_000, 594_005_400_000_000_000);
        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.Closed),
            "canonical payload should close"
        );
    }

    function testRegisterStartsInPendingEntry() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());

        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.PendingEntry),
            "state should start pending"
        );
        require(compiler.getActualPositionSize(intentId) == 0, "actual size should start zero");
    }

    function testEntryTriggerAdvancesToActiveAndRecordsActualSize() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, 1 ether, 0);

        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.ActivePosition),
            "state should advance to active"
        );
        require(compiler.getActualPositionSize(intentId) == 1 ether, "actual size should be recorded");
    }

    function testExitTriggerAdvancesActiveToClosed() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, 1 ether, 0);
        compiler.executeReactiveTrigger(intentId, 0.96 ether, 0.95 ether);

        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.Closed),
            "state should advance to closed"
        );
        require(compiler.getActualPositionSize(intentId) == 1 ether, "actual size should persist after close");
    }

    function testClosedIntentCannotRetrigger() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, 1 ether, 0);
        compiler.executeReactiveTrigger(intentId, 0.96 ether, 0.95 ether);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, 0.96 ether, 0.95 ether))
        );

        require(!success, "closed state must reject retrigger");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.ClosedIntentCannotExecute.selector);
    }

    function testEntryConstraintViolationReverts() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, 0.98 ether, 0))
        );

        require(!success, "entry constraint must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.EntryConstraintViolation.selector);
    }

    function testExitConstraintViolationRevertsWhenObservedOutBelowRuntimeMin() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, 1 ether, 0);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, 0.94 ether, 0.95 ether))
        );

        require(!success, "exit constraint must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.ExitConstraintViolation.selector);
    }

    function testRuntimeExitMinOutBelowFloorReverts() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, 1 ether, 0);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, 0.96 ether, 0.94 ether))
        );

        require(!success, "runtime exit floor must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.RuntimeExitMinOutTooLow.selector);
    }

    function _intent() private pure returns (IReactiveInvestmentCompiler.InvestmentIntent memory) {
        return IReactiveInvestmentCompiler.InvestmentIntent({
            owner: address(0x1),
            inputToken: address(0x2),
            outputToken: address(0x3),
            plannedEntrySize: 1 ether,
            entryMinOut: 0.99 ether,
            exitMinOutFloor: 0.95 ether
        });
    }

    function _intentId() private pure returns (bytes32) {
        return bytes32(uint256(1));
    }

    function _expectRevertSelector(bytes memory revertData, bytes4 expectedSelector) private pure {
        require(revertData.length >= 4, "revert data too short");

        bytes4 actualSelector;
        assembly {
            actualSelector := mload(add(revertData, 0x20))
        }

        require(actualSelector == expectedSelector, "unexpected selector");
    }
}
