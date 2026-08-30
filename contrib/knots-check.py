#!/usr/bin/env python3
"""Check a BLAKE2b-capable electrs over the Electrum protocol.
usage: electrs-check.py [host] [port]   (default 127.0.0.1 50002)"""
import hashlib, json, socket, sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 50002
PAYOUT = "bc1qha649flkdtn4tjrypw4yycxs8nr8vjnhr2zd8e"
COINBASE_961672 = "7cc78fde738ba774f7bab4a6bd75bb348a625c23081c3477f80f489c755c5162"

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
def bech32_decode(addr):
    hrp, data = addr.lower().rsplit("1", 1)
    vals = [CHARSET.index(c) for c in data][:-6]
    ver, prog5 = vals[0], vals[1:]
    acc = bits = 0; out = []
    for v in prog5:
        acc = (acc << 5) | v; bits += 5
        while bits >= 8:
            bits -= 8; out.append((acc >> bits) & 0xff)
    return ver, bytes(out)

ver, prog = bech32_decode(PAYOUT)
assert ver == 0 and len(prog) == 20
script = bytes([0x00, 0x14]) + prog
scripthash = hashlib.sha256(script).digest()[::-1].hex()

s = socket.create_connection((HOST, PORT), timeout=30)
f = s.makefile("rw")
def call(method, params):
    f.write(json.dumps({"id": 1, "method": method, "params": params}) + "\n"); f.flush()
    r = json.loads(f.readline())
    if "error" in r and r["error"]: raise SystemExit(f"{method}: {r['error']}")
    return r["result"]

ok = True
def check(name, cond, detail):
    global ok
    print(("PASS" if cond else "FAIL"), name, "-", detail); ok = ok and cond

v = call("server.version", ["electrs-check", "1.4"]); print("server:", v)
tip = call("blockchain.headers.subscribe", [])
check("tip is past the fork", tip["height"] >= 961640, f"height {tip['height']}")
check("tip header is 164 bytes", len(tip["hex"]) == 328, f"{len(tip['hex'])//2} bytes")
check("tip header has the v2 flag", int.from_bytes(bytes.fromhex(tip["hex"][:8]), "little") & 0x80000000 != 0, tip["hex"][:8])
h39 = call("blockchain.block.header", [961639]); check("961639 is a legacy 80-byte header", len(h39) == 160, f"{len(h39)//2} bytes")
h40 = call("blockchain.block.header", [961640]); check("961640 is a 164-byte header", len(h40) == 328, f"{len(h40)//2} bytes")
h72 = call("blockchain.block.header", [961672]); check("961672 is a 164-byte header", len(h72) == 328, f"{len(h72)//2} bytes")
hs = call("blockchain.block.headers", [961638, 4]); check("headers 961638..961641 concatenate", len(hs["hex"]) == 160*2 + 328*2 and hs["count"] == 4, f"{len(hs['hex'])//2} bytes, count {hs['count']}")
hist = call("blockchain.scripthash.get_history", [scripthash])
found = [h for h in hist if h.get("tx_hash") == COINBASE_961672]
check("payout scripthash history has the 961672 coinbase", bool(found), f"{len(hist)} entries; coinbase at height {found[0]['height'] if found else '?'}")
tx = call("blockchain.transaction.get", [COINBASE_961672]); check("coinbase tx retrievable", isinstance(tx, str) and len(tx) > 200, f"{len(tx)//2} bytes")
bal = call("blockchain.scripthash.get_balance", [scripthash]); print("payout balance (sats):", bal)
print("ALL PASS" if ok else "SOME CHECKS FAILED")
