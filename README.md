<div style="text-align: right;">
This repo is forked from Terra SDK to be enable to handle Cosmoshub chain. 

# Example Using a Wallet 

```
>>> from terra_sdk.client.lcd import LCDClient
>>> from terra_sdk.key.mnemonic import MnemonicKey
>>> mk = MnemonicKey(mnemonic="test test test")
>>> cosmos = LCDClient("https://api.cosmos.network", "cosmoshub-4")
>>> wallet = cosmos.wallet(mk, prefix="cosmos")
>>> wallet.key.acc_address
```

`'cosmos1rup4tdv6tzjxuzceqe5h2njneqcyfdz9yt2h6j'`

## Building and Signing Transactions

```
>>> from terra_sdk.core.fee import Fee
>>> from terra_sdk.core.bank import MsgSend
>>> from terra_sdk.client.lcd.api.tx import CreateTxOptions

>>> tx = wallet.create_and_sign_tx(CreateTxOptions(
        msgs=[MsgSend(
            wallet.key.acc_address,
            RECIPIENT,
            "1000000uatom"    # send 1 atom
        )],
        memo="test transaction!",
        fee=Fee(200000, "120000uatom")
    ))
```

You should now be able to broadcast your transaction to the network.

```
>>> result = cosmos.tx.broadcast(tx)
>>> print(result)
```
</div>