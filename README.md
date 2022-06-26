<div style="text-align: right;">
This repo is forked from Terra SDK to be enable to handle Cosmoshub chain. 

# Usage


```
>>> from terra_sdk.client.lcd import LCDClient
>>> cosmos = LCDClient(chain_id="cosmoshub-4", url="https://api.cosmos.network")
>>> cosmos.tendermint.block_info()['block']['header']['height']
```

`'1687543'`

# Example Using a Wallet (_recommended_)

```
>>> from terra_sdk.client.lcd import LCDClient
>>> from terra_sdk.key.mnemonic import MnemonicKey
>>> mk = MnemonicKey(mnemonic="test test test")
>>> cosmos = LCDClient("https://api.cosmos.network")", "cosmoshub-4")
>>> wallet = cosmos.wallet(mk, prefix="cosmos")
```

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