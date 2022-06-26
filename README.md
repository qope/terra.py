<br/>
<br/>

<div  align="center"> <p > <img src="https://raw.githubusercontent.com/terra-money/terra-sdk-python/main/docs/img/logo.png" width=500 alt="py-sdk-logo"></p>

# Usage Examples

Terra SDK can help you read block data, sign and send transactions, deploy and interact with contracts, and many more.
The following examples are provided to help you get started. Use cases and functionalities of the Terra SDK are not limited to the following examples and can be found in full <a href="https://terra-money.github.io/terra.py/index.html">here</a>.

In order to interact with the Terra blockchain, you'll need a connection to a Terra node. This can be done through setting up an LCDClient (The LCDClient is an object representing an HTTP connection to a Terra LCD node.):

```
>>> from terra_sdk.client.lcd import LCDClient
>>> cosmos = LCDClient(chain_id="cosmoshub-4", url="https://api.cosmos.network")
```

## Getting Blockchain Information

Once properly configured, the `LCDClient` instance will allow you to interact with the Terra blockchain. Try getting the latest block height:

```
>>> cosmos.tendermint.block_info()['block']['header']['height']
```

`'1687543'`

## Building and Signing Transactions

If you wish to perform a state-changing operation on the Terra blockchain such as sending tokens, swapping assets, withdrawing rewards, or even invoking functions on smart contracts, you must create a **transaction** and broadcast it to the network.
Terra SDK provides functions that help create StdTx objects.

### Example Using a Wallet (_recommended_)

A `Wallet` allows you to create and sign a transaction in a single step by automatically fetching the latest information from the blockchain (chain ID, account number, sequence).

Use `LCDClient.wallet()` to create a Wallet from any Key instance. The Key provided should correspond to the account you intend to sign the transaction with.
  
<sub>**NOTE:** *If you are using MacOS and got an exception 'bad key length' from MnemonicKey, please check your python implementation. if `python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"` returns LibreSSL 2.8.3, you need to reinstall python via pyenv or homebrew.*</sub>

```
>>> from terra_sdk.client.lcd import LCDClient
>>> from terra_sdk.key.mnemonic import MnemonicKey

>>> mk = MnemonicKey(mnemonic="test test test")
>>> cosmos = LCDClient("https://api.cosmos.network")", "cosmoshub-4")
>>> wallet = cosmos.wallet(mk)
```

Once you have your Wallet, you can simply create a StdTx using `Wallet.create_and_sign_tx`.

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

# License

This software is licensed under the MIT license. See [LICENSE](./LICENSE) for full disclosure.

© 2021 Terraform Labs, PTE.

<hr/>

<p>&nbsp;</p>
<p align="center">
    <a href="https://terra.money/"><img src="https://assets.website-files.com/611153e7af981472d8da199c/61794f2b6b1c7a1cb9444489_symbol-terra-blue.svg" alt="Terra-logo" width=200/></a>
<div align="center">
  <sub><em>Powering the innovation of money.</em></sub>
</div>
