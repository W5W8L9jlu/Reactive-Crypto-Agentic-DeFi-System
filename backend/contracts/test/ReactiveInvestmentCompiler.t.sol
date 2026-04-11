// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ReactiveInvestmentCompiler} from "../core/ReactiveInvestmentCompiler.sol";
import {IReactiveInvestmentCompiler} from "../interfaces/IReactiveInvestmentCompiler.sol";

interface Vm {
    function txGasPrice(uint256 newGasPrice) external;
    function prank(address msgSender) external;
}

contract ReactiveInvestmentCompilerTest {
    Vm private constant VM = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    function testCanonicalWaveOneFrozenPayloadHappyPath() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = bytes32(uint256(0x1111111111111111111111111111111111111111111111111111111111111111));
        IReactiveInvestmentCompiler.InvestmentIntent memory intent = IReactiveInvestmentCompiler.InvestmentIntent({
            owner: address(0x1),
            inputToken: address(0x2),
            outputToken: address(0x3),
            plannedEntrySize: 1_200_000_000,
            entryMinOut: 599_400_000_000_000_000,
            entryValidUntil: type(uint256).max,
            maxGasPriceGwei: 1_000_000,
            stopLossSlippageBps: 900,
            takeProfitSlippageBps: 250
        });

        compiler.registerInvestmentIntent(intentId, intent);

        IReactiveInvestmentCompiler.InvestmentIntent memory storedIntent = compiler.getInvestmentIntent(intentId);
        require(storedIntent.plannedEntrySize == intent.plannedEntrySize, "planned size should persist");
        require(storedIntent.entryMinOut == intent.entryMinOut, "entry min should persist");
        require(storedIntent.entryValidUntil == intent.entryValidUntil, "entry valid until should persist");
        require(storedIntent.maxGasPriceGwei == intent.maxGasPriceGwei, "max gas should persist");
        require(storedIntent.stopLossSlippageBps == intent.stopLossSlippageBps, "stop bps should persist");
        require(storedIntent.takeProfitSlippageBps == intent.takeProfitSlippageBps, "take bps should persist");

        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 600_000_000_000_000_000);
        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.ActivePosition),
            "canonical payload should activate"
        );
        require(
            compiler.getActualPositionSize(intentId) == 600_000_000_000_000_000,
            "canonical payload should record actual size"
        );

        // take-profit slippage=250bps => minOut=600e15 * (10000-250)/10000 = 585e15
        compiler.executeReactiveTrigger(
            intentId,
            IReactiveInvestmentCompiler.ReactiveTriggerType.TakeProfit,
            595_000_000_000_000_000
        );
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
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether);

        require(
            uint256(compiler.getPositionState(intentId)) == uint256(IReactiveInvestmentCompiler.PositionState.ActivePosition),
            "state should advance to active"
        );
        require(compiler.getActualPositionSize(intentId) == 1 ether, "actual size should be recorded");
    }

    function testStopLossExitTriggerAdvancesActiveToClosed() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether);
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.StopLoss, 0.96 ether);

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
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether);
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.StopLoss, 0.96 ether);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(
                compiler.executeReactiveTrigger,
                (intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.StopLoss, 0.96 ether)
            )
        );

        require(!success, "closed state must reject retrigger");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.ClosedIntentCannotExecute.selector);
    }

    function testEntryConstraintViolationReverts() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 0.98 ether))
        );

        require(!success, "entry constraint must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.EntryConstraintViolation.selector);
    }

    function testEntryExpiredConstraintReverts() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();
        IReactiveInvestmentCompiler.InvestmentIntent memory expiredIntent = _intent();
        expiredIntent.entryValidUntil = 0;

        compiler.registerInvestmentIntent(intentId, expiredIntent);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether))
        );

        require(!success, "expired entry must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.EntryValidityExpired.selector);
    }

    function testEntryGasCapConstraintReverts() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();
        IReactiveInvestmentCompiler.InvestmentIntent memory strictGasIntent = _intent();
        strictGasIntent.maxGasPriceGwei = 1;

        compiler.registerInvestmentIntent(intentId, strictGasIntent);
        VM.txGasPrice(2 gwei);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether))
        );

        VM.txGasPrice(0);

        require(!success, "gas cap must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.MaxGasPriceExceeded.selector);
    }

    function testDynamicExitMinOutRevertsWhenObservedOutBelowStopLossDerivedFloor() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether);

        // stop-loss slippage=500bps => minOut=0.95 ether; observed=0.94 ether should revert
        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(compiler.executeReactiveTrigger, (intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.StopLoss, 0.94 ether))
        );

        require(!success, "dynamic stop-loss minOut must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.ExitConstraintViolation.selector);
    }

    function testEmergencyForceCloseOnlyOwnerOrAuthorizedRelayer() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether);

        VM.prank(address(0xBEEF));
        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(
                IReactiveInvestmentCompiler(address(compiler)).emergencyForceClose,
                (intentId, 700)
            )
        );

        require(!success, "unauthorized caller must revert");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.UnauthorizedEmergencyForceCloseCaller.selector);
    }

    function testEmergencyForceCloseRejectsNonActivePosition() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(
                IReactiveInvestmentCompiler(address(compiler)).emergencyForceClose,
                (intentId, 700)
            )
        );

        require(!success, "non-active position must reject emergency force-close");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.EmergencyForceCloseOnlyActivePosition.selector);
    }

    function testEmergencyForceCloseClosesBeforeAnyLateCallback() public {
        ReactiveInvestmentCompiler compiler = new ReactiveInvestmentCompiler();
        bytes32 intentId = _intentId();

        compiler.registerInvestmentIntent(intentId, _intent());
        compiler.executeReactiveTrigger(intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.Entry, 1 ether);
        IReactiveInvestmentCompiler(address(compiler)).emergencyForceClose(intentId, 600);

        (bool success, bytes memory revertData) = address(compiler).call(
            abi.encodeCall(
                compiler.executeReactiveTrigger,
                (intentId, IReactiveInvestmentCompiler.ReactiveTriggerType.StopLoss, 0.95 ether)
            )
        );

        require(!success, "late callback must revert after emergency close");
        _expectRevertSelector(revertData, IReactiveInvestmentCompiler.ClosedIntentCannotExecute.selector);
    }

    function _intent() private view returns (IReactiveInvestmentCompiler.InvestmentIntent memory) {
        return IReactiveInvestmentCompiler.InvestmentIntent({
            owner: address(0x1),
            inputToken: address(0x2),
            outputToken: address(0x3),
            plannedEntrySize: 1 ether,
            entryMinOut: 0.99 ether,
            entryValidUntil: block.timestamp + 1 days,
            maxGasPriceGwei: 1_000_000,
            stopLossSlippageBps: 500,
            takeProfitSlippageBps: 300
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
