"""Data objects pertaining to building, signing, and parsing Transactions."""

from __future__ import annotations

from typing import Dict, List, Optional, Any

import attr

from terra_sdk.core.coins import Coins
from terra_sdk.core.msg import Msg
from terra_sdk.core.fee import Fee
from terra_sdk.util.json import JSONSerializable
from terra_sdk.core.public_key import PublicKey, LegacyAminoPubKey, SimplePublicKey

from terra_proto.cosmos.tx.v1beta1 import Tx as Tx_pb
from terra_proto.cosmos.tx.v1beta1 import TxBody as TxBody_pb
from terra_proto.cosmos.tx.v1beta1 import AuthInfo as AuthInfo_pb
from terra_proto.cosmos.tx.v1beta1 import SignerInfo as SignerInfo_pb
from terra_proto.cosmos.tx.v1beta1 import ModeInfo as ModeInfo_pb
from terra_proto.cosmos.tx.v1beta1 import ModeInfoSingle as ModeInfoSingle_pb
from terra_proto.cosmos.tx.v1beta1 import ModeInfoMulti as ModeInfoMulti_pb
from terra_proto.cosmos.tx.signing.v1beta1 import SignMode as SignMode_pb
from terra_proto.cosmos.crypto.multisig.v1beta1 import CompactBitArray as CompactBitArray_pb
from terra_proto.cosmos.base.abci.v1beta1 import TxResponse as TxResponse_pb
from terra_proto.cosmos.base.abci.v1beta1 import AbciMessageLog as AbciMessageLog_pb
from terra_proto.cosmos.base.abci.v1beta1 import StringEvent as StringEvent_pb
from terra_proto.cosmos.base.abci.v1beta1 import Attribute as Attribute_pb

from betterproto.lib.google.protobuf import Any as Any_pb

__all__ = [
    "SignMode",
    "AuthInfo",
    "Tx",
    "TxLog",
    "TxInfo",
    "parse_tx_logs",
    "ModeInfo",
    "ModeInfoSingle",
    "ModeInfoMulti",
    "SignerInfo",
    "SignerData"
]

# just alias
SignMode = SignMode_pb


@attr.s
class SignerData:
    sequence: int = attr.ib(converter=int)
    public_key: Optional[PublicKey] = attr.ib(default=None)


@attr.s
class Tx(JSONSerializable):
    """Data structure for a transaction which can be broadcasted.

    Args:
        body: the processable content of the transaction
        auth_info: the authorization related content of the transaction
        signatures: signatures is a list of signatures that matches the length and order of body and auth_info
    """
    body: TxBody = attr.ib()
    auth_info: AuthInfo = attr.ib()
    signatures: List[str] = attr.ib()

    def to_data(self) -> dict:
        return {
           "body": self.body.to_data(),
           "auth_info": self.auth_info.to_data(),
           "signatures": self.signatures
        }

    def to_proto(self) -> Tx_pb:
        proto = Tx_pb()
        proto.body = self.body.to_proto()
        proto.auth_info = self.auth_info.to_proto()
        proto.signatures = [sig.encode('utf-8') for sig in self.signatures]
        return proto

    @classmethod
    def from_data(cls, data: dict) -> Tx:
        data = data["value"]
        return cls(
            TxBody.from_data(data["body"]),
            AuthInfo.from_data(data["auth_info"]),
            data["signatures"]
        )

    @classmethod
    def from_proto(cls, proto: Tx_pb) -> Tx:
        return cls(
            TxBody.from_proto(proto["body"]),
            AuthInfo.from_proto(proto["auth_info"]),
            proto["signatures"]
        )

    def append_empty_signatures(self, signers: List[SignerData]):
        for signer in signers:
            if signer.public_key is not None: # no pubkey
                if isinstance(signer.public_key, LegacyAminoPubKey):
                    signer_info = SignerInfo(
                        public_key=signer.public_key,
                        sequence=signer.sequence,
                        mode_info=ModeInfo(
                            ModeInfoMulti(CompactBitArray.from_bits(len(signer.public_key.public_keys))
                                          )
                        )
                    )
                else:
                    signer_info = SignerInfo(
                        public_key=signer.public_key,
                        sequence=signer.sequence,
                        mode_info=ModeInfo(ModeInfoSingle(mode=SignMode.SIGN_MODE_DIRECT))
                    )
            else:
                signer_info = SignerInfo(
                    public_key=SimplePublicKey(''),
                    sequence=signer.sequence,
                    mode_info=ModeInfo(ModeInfoSingle(mode=SignMode.SIGN_MODE_DIRECT))
                )
            self.auth_info.signer_infos.append(signer_info)
            self.signatures.append(' ')

@attr.s
class TxBody(JSONSerializable):
    """Body of a transaction.

    Args:
        messages: list of messages to include in transaction
        memo: transaction memo
        timeout_height:
    """
    messages: List[Msg] = attr.ib()
    memo: Optional[str] = attr.ib(default='')
    timeout_height: Optional[int] = attr.ib(default=None)

    def to_data(self) -> dict:
        return {
            "messages": [m.to_data() for m in self.messages],
            "memo": self.memo if self.memo else '',
            "timeout_height": self.timeout_height if self.timeout_height else 0
        }

    def to_proto(self) -> TxBody_pb:
        proto = TxBody_pb()
        proto.messages = [m.pack_any() for m in self.messages]
        proto.memo = self.memo or ''
        proto.timeout_height = self.timeout_height
        return proto

    @classmethod
    def from_data(cls, data: dict) -> TxBody:
        data = data["value"]
        return cls(
            [Msg.from_data(m) for m in data["messages"]],
            data["memo"],
            data["timeout_height"]
        )

    @classmethod
    def from_proto(cls, proto: TxBody_pb) -> TxBody:
        return cls(
            [Msg.unpack_any(m) for m in proto["messages"]],
            proto["memo"],
            proto["timeout_height"]
        )


@attr.s
class AuthInfo(JSONSerializable):
    """AuthInfo
    Args:
        signer_infos: information of the signers
        fee: Fee
    """
    signer_infos: List[SignerInfo] = attr.ib(converter=list)
    fee: Fee = attr.ib()

    def to_dict(self, casing, include_default_values) -> dict:
        return self.to_proto().to_dict(casing, include_default_values)

    def to_data(self) -> dict:
        return {
            "signer_infos": [si.to_data() for si in self.signer_infos],
            "fee": self.fee.to_data()
        }

    def to_proto(self) -> AuthInfo_pb:
        proto = AuthInfo_pb()
        proto.fee = self.fee.to_proto()
        proto.signer_infos = [signer.to_proto() for signer in self.signer_infos]
        return proto

    @classmethod
    def from_data(cls, data: dict) -> AuthInfo:
        data = data["value"]
        return cls(
            [SignerInfo.from_data(m) for m in data["signer_infos"]],
            Fee.from_data(data["fee"])
        )

    @classmethod
    def from_proto(cls, proto: TxBody_pb) -> TxBody:
        return cls(
            [SignerInfo.from_proto(m) for m in proto["signer_infos"]],
            Fee.from_proto(proto["fee"])
        )


@attr.s
class SignerInfo(JSONSerializable):
    """SignerInfo
    Args:
       public_key:
       sequence:
       mode_info:
    """
    public_key: PublicKey = attr.ib()
    sequence: int = attr.ib(converter=int)
    mode_info: ModeInfo = attr.ib()

    def to_data(self) -> dict:
        return {
            "public_key": self.public_key.to_data(),
            "sequence": self.sequence,
            "mode_info": self.mode_info.to_data()
        }

    def to_proto(self) -> SignerInfo_pb:
        proto = SignerInfo_pb()
        proto.public_key = self.public_key.pack_any()
        proto.sequence = self.sequence
        proto.mode_info = self.mode_info.to_proto()
        return proto

    @classmethod
    def from_data(cls, data: dict) -> SignerInfo:
        data = data["value"]
        return cls(
            PublicKey.from_data(data["public_key"]),
            data["sequence"],
            ModeInfo.from_data(data["mode_info"])
        )

    @classmethod
    def from_proto(cls, proto: SignerInfo_pb) -> SignerInfo:
        return cls(
            PublicKey.from_proto(proto["public_key"]),
            proto["sequence"],
            ModeInfo.from_proto(proto["mode_info"])
        )




@attr.s
class ModeInfo(JSONSerializable):

    single_mode: Optional[ModeInfoSingle] = attr.ib(default=None)
    multi_mode: Optional[ModeInfoMulti] = attr.ib(default=None)

    def to_data(self) -> dict:
        return {
            "single": self.single_mode.to_data() if self.single_mode else None,
            "multi": self.multi_mode.todata() if self.multi_mode else None
        }

    @classmethod
    def from_data(cls, data: dict) -> ModeInfo:
        data = data["value"]
        return cls(
            ModeInfoSingle.from_data(data["single"]) if data["single"] else None,
            ModeInfoMulti.from_data(data["multi"]) if data["multi"] else None
        )

    def to_proto(self) -> ModeInfo_pb:
        proto = ModeInfo_pb()
        if self.single_mode:
            proto.single = self.single_mode.to_proto()
        else:
            proto.multi = self.multi_mode.to_proto()
        return proto

    @classmethod
    def from_proto(cls, proto: ModeInfo_pb) -> ModeInfo:
        sm=None
        mm=None
        if proto["single"]:
            sm=ModeInfoSingle.from_proto(proto["single"])
        else:
            mm=ModeInfoMulti.from_proto(proto["multi"])
        return cls(
            sm,
            mm
        )


@ attr.s
class ModeInfoSingle(JSONSerializable):
    mode: str = attr.ib()

    def to_data(self) -> dict:
        {
            "mode": self.mode
        }

    @classmethod
    def from_data(cls, data: dict) -> ModeInfoSingle:
        data = data["value"]
        return cls(
            data["mode"]
        )

    def to_proto(self) -> ModeInfoSingle_pb:
        proto = ModeInfoSingle_pb()
        proto.mode = 1# SignMode_pb(int(self.mode))
        return proto

    @classmethod
    def from_proto(cls, proto: ModeInfoSingle_pb) -> ModeInfoSingle:
        mode = SignMode.from_string(proto["mode"])
        return cls(
            mode=mode
        )


@ attr.s
class ModeInfoMulti(JSONSerializable):
    bitarray: CompactBitArray = attr.ib()
    mode_infos: List[ModeInfo] = attr.ib()

    @classmethod
    def from_data(cls, data: dict) -> ModeInfoMulti:
        data = data["value"]
        return cls(
            data["bitarray"],
            data["mode_infos"]
        )

    @classmethod
    def from_proto(cls, proto: ModeInfoMulti_pb) -> ModeInfoMulti:
        return cls(
            CompactBitArray.from_proto(proto["bitarray"]),
            ModeInfo_pb.from_proto(proto["mode_infos"])
        )


@attr.s
class CompactBitArray(JSONSerializable):
    extra_bits_stored: int = attr.ib(converter=int)
    elems: str = attr.ib()

    @classmethod
    def from_data(cls, data: dict) -> CompactBitArray:
        data = data["value"]
        return cls(
            data["extra_bits_stored"],
            data["elems"]
        )

    @classmethod
    def from_proto(cls, proto: CompactBitArray_pb) -> CompactBitArray:
        return cls(
            proto["extra_bits_stored"],
            proto["elems"]
        )

    @classmethod
    def from_bits(cls, len: int) -> CompactBitArray:
        raise NotImplementedError # TODO


def parse_events_by_type(event_data: List[dict]) -> Dict[str, Dict[str, List[str]]]:
    events: Dict[str, Dict[str, List[str]]] = {}
    for ev in event_data:
        for att in ev["attributes"]:
            if ev["type"] not in events:
                events[ev["type"]] = {}
            if att["key"] not in events[ev["type"]]:
                events[ev["type"]][att["key"]] = []
            events[ev["type"]][att["key"]].append(att.get("value"))
    return events

@attr.s
class TxLog(JSONSerializable):
    """Object containing the events of a transaction that is automatically generated when
    :class:`TxInfo` or :class:`BlockTxBroadcastResult` objects are read."""

    msg_index: int = attr.ib(converter=int)
    """Number of the message inside the transaction that it was included in."""

    log: str = attr.ib()
    """This field may be populated with details of the message's error, if any."""

    events: List[dict] = attr.ib()
    """Raw event log data"""

    events_by_type: Dict[str, Dict[str, List[str]]] = attr.ib(init=False)
    """Event log data, re-indexed by event type name and attribute type.

    For instance, the event type may be: ``store_code`` and an attribute key could be
    ``code_id``.

    >>> logs[0].events_by_type["<event-type>"]["<attribute-key>"]
    ['<attribute-value>', '<attribute-value2>']
    """

    def __attrs_post_init__(self):
        self.events_by_type = parse_events_by_type(self.events)

    @classmethod
    def from_proto(cls, tx_log: AbciMessageLog_pb) -> TxLog:
        events=[event for event in tx_log["events"]]
        return cls(
            msg_index=tx_log["msg_index"],
            log=tx_log["log"],
            events=events
            )

@attr.s
class Attribute(JSONSerializable):
    key: str = attr.ib()
    value: str = attr.ib()

    def to_proto(self) -> Attribute_pb:
        proto = Attribute_pb()
        proto.key=self.key
        proto.value=self.value
        return proto

    @classmethod
    def from_proto(cls, attrib: Attribute_pb) -> Attribute:
        return cls(key=attrib["key"], value=attrib["value"])


@attr.s
class StringEvent(JSONSerializable):

    type: str = attr.ib()
    attributes = attr.ib()

    def to_proto(self) -> StringEvent_pb:
        return StringEvent_pb(type=self.type, attributes=self.attributes)

    @classmethod
    def from_proto(cls, str_event: StringEvent_pb) -> StringEvent:
        return cls(
            type=str_event["type"],
            attributes=str_event["attributes"]
        )

def parse_tx_logs(logs) -> Optional[List[TxLog]]:
    return (
        [
            TxLog(msg_index=i, log=log.get("log"), events=log.get("events"))
            for i, log in enumerate(logs)
        ]
        if logs
        else None
    )

def parse_tx_logs_proto(logs: List[AbciMessageLog_pb]) -> Optional[List[TxLog]]:
    return (
        [
            TxLog.from_proto(log)
            for log in logs
        ]
        if logs
        else None
    )

@ attr.s
class TxInfo(JSONSerializable):
    """Holds information pertaining to a transaction which has been included in a block
    on the blockchain.

    .. note::
        Users are not expected to create this object directly. It is returned by
        :meth:`TxAPI.tx_info()<terra_sdk.client.lcd.api.tx.TxAPI.tx_info>`
    """

    height: int = attr.ib(converter=int)
    """Block height at which transaction was included."""

    txhash: str = attr.ib()
    """Transaction hash."""

    rawlog: str = attr.ib()
    """Event log information as a raw JSON-string."""

    logs: Optional[List[TxLog]] = attr.ib()
    """Event log information."""

    gas_wanted: int = attr.ib(converter=int)
    """Gas requested by transaction."""

    gas_used: int = attr.ib(converter=int)
    """Actual gas amount used."""

    tx: Tx = attr.ib()
    """Transaction object."""

    timestamp: str = attr.ib()
    """Time at which transaction was included."""

    code: Optional[int] = attr.ib(default=None)
    """If this field is not ``None``, the transaction failed at ``DeliverTx`` stage."""

    codespace: Optional[str] = attr.ib(default=None)
    """Error subspace (used alongside ``code``)."""

    def to_data(self) -> dict:
        data = {
            "height": str(self.height),
            "txhash": self.txhash,
            "raw_log": self.rawlog,
            "logs": [log.to_data() for log in self.logs] if self.logs else None,
            "gas_wanted": str(self.gas_wanted),
            "gas_used": str(self.gas_used),
            "timestamp": self.timestamp,
            "tx": self.tx.to_data(),
            "code": self.code,
            "codespace": self.codespace,
        }

        if not self.logs:
            del data["logs"]

        if not self.code:
            del data["code"]

        if not self.codespace:
            del data["codespace"]

        return data

    @ classmethod
    def from_data(cls, data: dict) -> TxInfo:
        return cls(
            data["height"],
            data["txhash"],
            data["raw_log"],
            parse_tx_logs(data.get("logs")),
            data["gas_wanted"],
            data["gas_used"],
            Tx.from_data(data["tx"]),
            data["timestamp"],
            data.get("code"),
            data.get("codespace"),
        )

    def to_proto(self) -> TxResponse_pb:
        proto = TxResponse_pb()
        proto.height = self.height
        proto.txhash = self.txhash
        proto.raw_log = self.rawlog
        proto.logs = [log.to_proto() for log in self.logs] if self.logs else None
        proto.gas_wanted = self.gas_wanted
        proto.gas_used = self.gas_used
        proto.timestamp = self.timestamp
        proto.tx = self.tx.to_proto()
        proto.code = self.code
        proto.codespace = self.codespace
        return proto

    @classmethod
    def from_proto(cls, proto: TxResponse_pb) -> TxInfo:
        return cls(
            height=proto["height"],
            txhash=proto["txhash"],
            rawlog=proto["raw_log"],
            logs=parse_tx_logs_proto(proto["logs"]),
            gas_wanted=proto["gas_wanted"],
            gas_used=proto["gas_used"],
            timestamp=proto["timestamp"],
            tx=Tx.from_proto(proto["tx"]),
            code=proto["code"],
            codespace=proto["codespace"]
        )