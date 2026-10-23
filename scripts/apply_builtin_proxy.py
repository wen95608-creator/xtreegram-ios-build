#!/usr/bin/env python3
"""Inject a built-in self-hosted MTProto proxy into TelegramCore's Network.swift.

The proxy becomes the default connection path whenever the user has not
configured their own proxy, so a freshly installed app connects out of the box.
"""
import sys
import pathlib

src = pathlib.Path(sys.argv[1]) / "submodules/TelegramCore/Sources/Network/Network.swift"
text = src.read_text()

target = (
    '            if let effectiveActiveServer = proxySettings?.effectiveActiveServer {\n'
    '                apiEnvironment = apiEnvironment.withUpdatedSocksProxySettings(effectiveActiveServer.mtProxySettings)\n'
    '            }'
)

replacement = (
    '            // Built-in self-hosted SOCKS5 proxy: used whenever the user has no\n'
    '            // proxy of their own configured, so a fresh install connects out of\n'
    '            // the box. The user can still override it in Settings -> Data and\n'
    '            // Storage -> Proxy.\n'
    '            var effectiveProxySettings = proxySettings\n'
    '            if effectiveProxySettings?.effectiveActiveServer == nil {\n'
    '                let builtinServer = ProxyServerSettings(host: "147.135.213.72", port: 20290, connection: .socks5(username: "7250160120", password: "f073ac71-d471-4678-bc64-7abddc1e8220"))\n'
    '                effectiveProxySettings = ProxySettings(enabled: true, servers: [builtinServer], activeServer: builtinServer, useForCalls: false)\n'
    '            }\n'
    '            if let effectiveActiveServer = effectiveProxySettings?.effectiveActiveServer {\n'
    '                apiEnvironment = apiEnvironment.withUpdatedSocksProxySettings(effectiveActiveServer.mtProxySettings)\n'
    '            }'
)

count = text.count(target)
if count != 1:
    raise SystemExit(f"builtin proxy: expected exactly one target block, found {count}")

src.write_text(text.replace(target, replacement))
print("builtin proxy injected into", src)
