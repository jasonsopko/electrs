## Bitcoin Knots BLAKE2b chain

`blake2b` is romanz/electrs 0.10.10 plus support for the Bitcoin Knots proof-of-work change ([Knots #359](https://github.com/bitcoinknots/bitcoin/pull/359)): 164-byte header v2 blocks are parsed, hashed (`src/knots.rs`, adapted from Retropex/electrs) and stored, on mainnet from height 961640 and on testnet4 from 150308. Upstream declined it ([#1333](https://github.com/romanz/electrs/pull/1333)), so this fork carries it and is rebased onto upstream releases. For a pruned node see [paulscode/electrs-pruned](https://github.com/paulscode/electrs-pruned), which also carries the Electrum protocol 1.8 header proposal that wallets need.

### Running it against a Knots node

1. Build as upstream ([doc/install.md](doc/install.md)): `git clone -b blake2b https://github.com/jasonsopko/electrs && cd electrs && cargo build --locked --release`.
2. Configure as upstream ([doc/config.md](doc/config.md)); nothing is BLAKE2b-specific. The node must be Bitcoin Knots 29.4.1 or later. An unpatched electrs against that node crash-loops at the first v2 header.
3. Start with a fresh `db_dir`. Whether a database left by an unpatched electrs can be continued is untested.
4. Check it: `python3 contrib/knots-check.py 127.0.0.1 50001` runs nine Electrum calls against the server: the tip is a 164-byte header with the v2 bit, 961639 is still 80 bytes, 961640 is 164, `block.headers` across the fork concatenates both sizes, and a scripthash history and coinbase transaction from a BLAKE2b block come back.
5. mempool: point the backend's `ELECTRUM` block in `mempool-config.json` at it (`HOST`, `PORT`, `TLS_ENABLED: false` for a plain local socket). The rest of the mempool side is in [jasonsopko/mempool, branch `knots-blake2b`](https://github.com/jasonsopko/mempool/blob/knots-blake2b/KNOTS-BLAKE2B.md).

Wallets that verify headers themselves (Electrum, Sparrow) need to understand the v2 format before they follow the chain; that is a client change, see [paulscode's proposal](https://github.com/paulscode/electrs-pruned/blob/main/docs/electrum-header-v2.md).

### Verifying the signatures

Commits and tags on this branch are signed with

```
89F0 E41D 72CE 523F 4AA1 CDB6 92CD FFB7 C40C D1BA   Jason Sopko <jason@sopko.net>, RSA-4096, created 2026-08-22
```

Fetch it from https://github.com/jasonsopko.gpg, https://sopko.net/jason.gpg.txt, or [Keybase](https://keybase.io/jasonsopko), then `git verify-tag v0.10.10-blake2b.1`. My older key, `0F48 86DC D57D A2EC 2D2C 9B57 EA70 527E E3B8 AE8D` (2022), is still published on sopko.net and Keybase but has never signed anything here, and I no longer hold its secret half, so do not encrypt to it.

![Logo](logo/logo.svg)

# Electrum Server in Rust

[![CI](https://github.com/romanz/electrs/actions/workflows/rust.yml/badge.svg)](https://github.com/romanz/electrs/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://github.com/jasonsopko/electrs/compare)
[![crates.io](https://img.shields.io/crates/v/electrs.svg)](https://crates.io/crates/electrs)
[![gitter.im](https://badges.gitter.im/romanz/electrs.svg)](https://gitter.im/romanz/electrs)

An efficient re-implementation of Electrum Server, inspired by [ElectrumX](https://github.com/kyuupichan/electrumx), [Electrum Personal Server](https://github.com/chris-belcher/electrum-personal-server) and [bitcoincore-indexd](https://github.com/jonasschnelli/bitcoincore-indexd).

The motivation behind this project is to enable a user to self host an Electrum server,
with required hardware resources not much beyond those of a [full node](https://en.bitcoin.it/wiki/Full_node#Why_should_you_use_a_full_node_wallet).
The server indexes the entire Bitcoin blockchain, and the resulting index enables fast queries for any given user wallet,
allowing the user to keep real-time track of balances and transaction history using the [Electrum wallet](https://electrum.org/).
Since it runs on the user's own machine, there is no need for the wallet to communicate with external Electrum servers,
thus preserving the privacy of the user's addresses and balances.

[BTC Prague 2024 dev/hack/day](https://btcprague.com/dev-hack-day/) slides are here: https://bit.ly/electrs


## Usage

**Please prefer to use OUR usage guide!**

External guides can be out-of-date and have various problems.
At least double-check that the guide you're using is actively maintained.
If you can't use our guide, please ask about what you don't understand or consider using automated deployments.

Note that this implementation of Electrum server is optimized for **personal/small-scale (family/friends) usage**.
It's a bad idea to run it publicly as it'd expose you to DoS and maybe also other attacks.
If you want to run a public server you may be interested in the [Blockstream fork of electrs](https://github.com/Blockstream/electrs)
which is better optimized for public usage at the cost of consuming *significantly* more resources.

 * [Installation from source](doc/install.md)
 * [Pre-built binaries](doc/binaries.md) (No official binaries available but a beta repository is available for installation)
 * [Configuration](doc/config.md)
 * [Usage](doc/usage.md)
 * [Monitoring](doc/monitoring.md)
 * [Upgrading](doc/upgrading.md) - **contains information about important changes from older versions**

## Features

 * Supports Electrum protocol [v1.4](https://electrumx-spesmilo.readthedocs.io/en/latest/protocol.html)
 * Maintains an index over transaction inputs and outputs, allowing fast balance queries
 * Fast synchronization of the Bitcoin blockchain (~6.5 hours for ~504GB @ August 2023) using HDD storage.
 * Low index storage overhead (~10%), relying on a local full node for transaction retrieval
 * Efficient mempool tracker (allowing better fee [estimation](https://github.com/spesmilo/electrum/blob/59c1d03f018026ac301c4e74facfc64da8ae4708/RELEASE-NOTES#L34-L46))
 * Low CPU & memory usage (after initial indexing)
 * [`txindex`](https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch03_bitcoin-core.adoc#txindex) is not required for the Bitcoin node
 * Uses a single [RocksDB](https://github.com/spacejam/rust-rocksdb) database, for better consistency and crash recovery

## Altcoins, and why this fork exists

Upstream electrs does not support altcoins or hard forks of Bitcoin, and closed the BLAKE2b change under that policy ([#1333](https://github.com/romanz/electrs/pull/1333)). The chain this fork indexes is not an altcoin: it is Bitcoin, carried on by Bitcoin Knots after a change to the proof-of-work hash. The ledger, the coins, addresses, scripts and transaction rules are all unchanged. What changed at height 961640 is the function the block header is checked against (BLAKE2b in place of double SHA256, in a 164-byte header). That is a hard fork in the technical sense, since software that does not know the new header cannot follow the chain, and it is exactly why this fork is needed. Issues and pull requests about the BLAKE2b chain are welcome here; do not file them upstream.

## Index database

The database schema is described [here](doc/schema.md).

## Contributing

All contributions to this project are welcome. Please refer to the [Contributing Guidelines](CONTRIBUTING.md) for more details.

## Logo

[Our logo](logo/) is generously provided by [Dominik Průša](https://github.com/DominoPrusa) under the MIT license.
Based on the [Electrum logo](https://github.com/spesmilo/electrum/blob/master/LICENCE)
and the [Rust language logo](https://www.rust-lang.org/policies/media-guide).
